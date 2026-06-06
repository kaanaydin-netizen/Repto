"""generalize conversations: nullable phone + channel column

Increment 2 — multi-channel intake (web-form + e-mail + web-chat).

Maakt `conversations` kanaal-agnostisch zodat een lead zónder telefoonnummer
(web-form/e-mail) een gesprek kan krijgen en identiek door verrijking → score →
notificatie → CRM loopt als WhatsApp:

  - `wa_contact_phone` NOT NULL → NULL (web-/e-maillead heeft geen nummer; het
    canonieke nummer leeft toch al genormaliseerd op `contacts.phone`).
  - nieuwe kolom `channel` ("whatsapp" | "email" | "web_form" | "web_chat"),
    server_default "whatsapp" voor nieuwe rijen + expliciete backfill van
    bestaande rijen op "whatsapp" (alle pré-increment-2 gesprekken zijn WhatsApp).

Forward-safe / additief-relaxerend (kolom toevoegen + NOT NULL → NULL), dus deze
migratie kan vóór de nieuwe code op Supabase draaien zonder de werkende WhatsApp-
flow te raken — draai 'm vóór de code leads zonder telefoon begint aan te maken.

downgrade is enkel veilig zolang er nog GEEN niet-WhatsApp-leads zijn: het herstelt
NOT NULL op wa_contact_phone en faalt (terecht) zodra er een rij met NULL-telefoon
bestaat (web/e-mail). Documenteer dat downgrade pré-2a-only is.

Revision ID: 004
Revises: 003
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── channel toevoegen (server_default dekt nieuwe rijen) ───────────────
    op.add_column(
        "conversations",
        sa.Column("channel", sa.String(), nullable=False, server_default="whatsapp"),
    )
    # Expliciete backfill: alle bestaande gesprekken zijn WhatsApp. server_default
    # dekt enkel NIEUWE rijen; bestaande rijen krijgen hier hun waarde hard gezet
    # (idempotent — server_default zet ze al op 'whatsapp', dit pint het vast).
    op.execute("UPDATE conversations SET channel = 'whatsapp' WHERE channel IS NULL")

    # ── wa_contact_phone relaxeren naar NULL-baar ─────────────────────────
    op.alter_column(
        "conversations",
        "wa_contact_phone",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    # LET OP: enkel veilig vóór er niet-WhatsApp-leads bestaan. Faalt bewust als er
    # een gesprek met NULL wa_contact_phone is (dan zou je data verliezen/liegen).
    op.alter_column(
        "conversations",
        "wa_contact_phone",
        existing_type=sa.String(),
        nullable=False,
    )
    op.drop_column("conversations", "channel")
