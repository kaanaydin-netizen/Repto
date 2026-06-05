"""add contacts table + conversations.contact_id + backfill

Increment 1 — kanaal-overschrijdende identiteit + lead-scoring.

De backfill DEDUPLICEERT per persoon, niet per gesprek: een terugkerende klant op
hetzelfde nummer kreeg na een afgesloten gesprek een nieuwe conversations-rij, dus we
groeperen op (org_id, wa_contact_phone) en koppelen alle gesprekken van die groep aan
één Contact. Alle bestaande wa_contact_phone-waarden komen uit Meta (wa_id-vorm), dus de
ruwe waarde is al de canonieke sleutel — geen app-normalisatie nodig in deze migratie.

Revision ID: 003
Revises: 002
Create Date: 2026-06-05
"""
import uuid

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


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

    # ── backfill: één Contact per (org_id, wa_contact_phone) ────
    bind = op.get_bind()
    groups = bind.execute(sa.text(
        "SELECT org_id, wa_contact_phone, MAX(wa_contact_name) AS nm "
        "FROM conversations GROUP BY org_id, wa_contact_phone"
    )).fetchall()

    for grp in groups:
        contact_id = str(uuid.uuid4())
        bind.execute(
            sa.text(
                "INSERT INTO contacts "
                "(id, org_id, name, phone, first_channel, channels_json) "
                "VALUES (:id, :org_id, :nm, :phone, 'whatsapp', '[\"whatsapp\"]')"
            ),
            {"id": contact_id, "org_id": grp.org_id, "nm": grp.nm, "phone": grp.wa_contact_phone},
        )
        bind.execute(
            sa.text(
                "UPDATE conversations SET contact_id = :cid "
                "WHERE org_id = :org_id AND wa_contact_phone = :phone"
            ),
            {"cid": contact_id, "org_id": grp.org_id, "phone": grp.wa_contact_phone},
        )


def downgrade() -> None:
    op.drop_constraint("fk_conversations_contact_id", "conversations", type_="foreignkey")
    op.drop_index("ix_conversations_contact_id", table_name="conversations")
    op.drop_column("conversations", "contact_id")
    op.drop_index("ix_contacts_phone", table_name="contacts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_index("ix_contacts_org_id", table_name="contacts")
    op.drop_table("contacts")
