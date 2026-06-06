"""add contacts table + conversations.contact_id + backfill

Increment 1 — kanaal-overschrijdende identiteit + lead-scoring.

De backfill DEDUPLICEERT per persoon, niet per gesprek: een terugkerende klant op
hetzelfde nummer kreeg na een afgesloten gesprek een nieuwe conversations-rij, dus we
groeperen op (org_id, GENORMALISEERD telefoonnummer) en koppelen alle gesprekken van die
groep aan één Contact, met het genormaliseerde nummer als sleutel.

Waarom normaliseren (en niet de ruwe waarde): pré-Meta-rijen (Twilio-tijdperk) kunnen in
'+32…'- of nationale vorm staan, terwijl resolve_contact runtime op de canonieke wa_id-
vorm ('32…') matcht. Sloeg de backfill de ruwe waarde op, dan vond een volgend bericht het
Contact niet terug → duplicaat (precies de invariant die deze increment vestigt). Daarom
past de backfill dezelfde normalisatie toe — hieronder als BEVROREN kopie ingelined, zodat
de migratie zelfstandig en stabiel blijft, los van latere app-wijzigingen.

Revision ID: 003
Revises: 002
Create Date: 2026-06-05
"""
import re
import uuid

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

_DEFAULT_COUNTRY_CODE = "32"  # KMO-markt = België (zie identity_service.normalize_phone)


def _normalize_phone(raw):
    """Bevroren kopie van identity_service.normalize_phone (increment 1).

    Reduceert tot de canonieke wa_id-vorm: internationaal, enkel cijfers, zonder '+'.
    Bewust hier ingelined i.p.v. geïmporteerd — een migratie moet reproduceerbaar blijven
    ook als de app-versie van deze functie later evolueert.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    has_plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    if digits.startswith("00"):
        digits = digits[2:]
    elif not has_plus and digits.startswith("0"):
        digits = _DEFAULT_COUNTRY_CODE + digits[1:]
    return digits or None


def upgrade() -> None:
    # ── contacts ───────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("first_channel", sa.String(), nullable=True),
        sa.Column("channels_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("score", sa.String(), nullable=True),
        sa.Column("score_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_org_id", "contacts", ["org_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_index("ix_contacts_phone", "contacts", ["phone"])

    # ── conversations.contact_id ───────────────────────────────
    op.add_column("conversations", sa.Column("contact_id", sa.String(), nullable=True))
    op.create_index("ix_conversations_contact_id", "conversations", ["contact_id"])
    op.create_foreign_key(
        "fk_conversations_contact_id", "conversations", "contacts",
        ["contact_id"], ["id"],
    )

    # ── backfill: één Contact per (org_id, genormaliseerd nummer) ────
    # Groeperen gebeurt in Python op de canonieke sleutel: twee ruwe vormen van hetzelfde
    # nummer (bv. '+32470…' en '32470…') vallen zo samen i.p.v. te splitsen. Updates gaan
    # per conversation-id, want binnen één groep kunnen de ruwe waarden verschillen.
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, org_id, wa_contact_phone, wa_contact_name FROM conversations"
    )).fetchall()

    groups: dict = {}  # (org_id, norm_phone) -> {"name": str|None, "conv_ids": [str]}
    for r in rows:
        key = (r.org_id, _normalize_phone(r.wa_contact_phone))
        grp = groups.setdefault(key, {"name": None, "conv_ids": []})
        grp["conv_ids"].append(r.id)
        if r.wa_contact_name and not grp["name"]:
            grp["name"] = r.wa_contact_name

    for (org_id, norm_phone), grp in groups.items():
        contact_id = str(uuid.uuid4())
        bind.execute(
            sa.text(
                "INSERT INTO contacts "
                "(id, org_id, name, phone, first_channel, channels_json) "
                "VALUES (:id, :org_id, :nm, :phone, 'whatsapp', '[\"whatsapp\"]')"
            ),
            {"id": contact_id, "org_id": org_id, "nm": grp["name"], "phone": norm_phone},
        )
        for conv_id in grp["conv_ids"]:
            bind.execute(
                sa.text("UPDATE conversations SET contact_id = :cid WHERE id = :id"),
                {"cid": contact_id, "id": conv_id},
            )


def downgrade() -> None:
    op.drop_constraint("fk_conversations_contact_id", "conversations", type_="foreignkey")
    op.drop_index("ix_conversations_contact_id", table_name="conversations")
    op.drop_column("conversations", "contact_id")
    op.drop_index("ix_contacts_phone", table_name="contacts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_index("ix_contacts_org_id", table_name="contacts")
    op.drop_table("contacts")
