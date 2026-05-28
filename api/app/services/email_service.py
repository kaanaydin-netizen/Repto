"""
Email Service — lead-notificaties via Resend REST API.
Wordt getriggerd zodra een gesprek wordt afgesloten (GESPREK_AFGEROND).
"""
from __future__ import annotations
import logging
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.conversation import Conversation, Organization, Message

settings = get_settings()
logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
DASHBOARD_URL  = "https://repto.be"


async def send_lead_notification(conversation: Conversation, db: AsyncSession) -> None:
    """
    Stuur een e-mailnotificatie naar de agencyeigenaar wanneer een lead is gekwalificeerd.
    Faalt stil als Resend niet geconfigureerd is.
    """
    if not settings.resend_api_key or not settings.notification_email:
        logger.debug("E-mailnotificatie overgeslagen — RESEND_API_KEY of NOTIFICATION_EMAIL niet ingesteld")
        return

    try:
        # Organisatie ophalen
        org_result = await db.execute(
            select(Organization).where(Organization.id == conversation.org_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            return

        # Laatste berichten ophalen voor samenvatting
        msgs_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sent_at.asc())
            .limit(20)
        )
        messages = list(msgs_result.scalars().all())

        # Eerste inbound bericht als preview
        first_msg = next((m for m in messages if m.direction == "inbound"), None)
        preview = (first_msg.content[:200] + "…") if first_msg and len(first_msg.content) > 200 else (first_msg.content if first_msg else "")

        html = _build_html(conversation, org, preview, messages)
        subject = f"🎉 Nieuwe lead via Repto — {org.name}"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from":    settings.notification_from,
                    "to":      [settings.notification_email],
                    "subject": subject,
                    "html":    html,
                },
            )

        if resp.status_code in (200, 201):
            logger.info(f"📧 E-mail verstuurd naar {settings.notification_email} voor gesprek {conversation.id}")
        else:
            logger.warning(f"⚠️ E-mail mislukt ({resp.status_code}): {resp.text[:200]}")

    except Exception as e:
        # Nooit een exception laten propageren — notificatie is niet-kritisch
        logger.error(f"E-mailnotificatie fout: {e}")


def _build_html(
    conversation: Conversation,
    org: Organization,
    preview: str,
    messages: list[Message],
) -> str:
    naam     = conversation.wa_contact_name or "Onbekend"
    telefoon = conversation.wa_contact_phone
    datum    = datetime.now().strftime("%d/%m/%Y om %H:%M")
    detail_url = f"{DASHBOARD_URL}/gesprekken/{conversation.id}"
    msg_count  = len(messages)

    # CRM status chip
    crm_label = (
        '<span style="background:#dcfce7;color:#15803d;border-radius:999px;padding:2px 10px;font-size:11px;font-weight:600;">✓ Gesynchroniseerd naar Airtable</span>'
        if org.crm_type == "airtable"
        else '<span style="background:#f3f4f6;color:#6b7280;border-radius:999px;padding:2px 10px;font-size:11px;">Geen CRM</span>'
    )

    return f"""
<!DOCTYPE html>
<html lang="nl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:32px 0;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

      <!-- Header -->
      <tr><td style="background:#4f46e5;border-radius:16px 16px 0 0;padding:28px 32px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <div style="display:inline-flex;align-items:center;gap:8px;">
                <div style="background:rgba(255,255,255,0.2);border-radius:8px;width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;">
                  <span style="color:white;font-size:16px;">⚡</span>
                </div>
                <span style="color:white;font-size:18px;font-weight:700;">Repto</span>
              </div>
              <p style="color:rgba(255,255,255,0.8);font-size:13px;margin:6px 0 0;">Nieuwe gekwalificeerde lead</p>
            </td>
          </tr>
        </table>
      </td></tr>

      <!-- Body -->
      <tr><td style="background:white;padding:32px;">

        <!-- Lead info -->
        <h1 style="margin:0 0 4px;font-size:22px;font-weight:700;color:#111827;">
          🎉 {naam} heeft contact opgenomen
        </h1>
        <p style="margin:0 0 24px;color:#6b7280;font-size:14px;">
          Via WhatsApp · {datum} · {org.name}
        </p>

        <!-- Info tabel -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:24px;">
          {_info_row('👤 Naam',     naam)}
          {_info_row('📱 Telefoon', telefoon)}
          {_info_row('🏢 Klant',    org.name)}
          {_info_row('💬 Berichten', f'{msg_count} berichten gewisseld')}
          <tr>
            <td style="padding:12px 16px;border-top:1px solid #f3f4f6;font-size:13px;color:#6b7280;font-weight:500;width:140px;">
              📊 CRM
            </td>
            <td style="padding:12px 16px;border-top:1px solid #f3f4f6;font-size:13px;">
              {crm_label}
            </td>
          </tr>
        </table>

        <!-- Preview eerste bericht -->
        {'<div style="background:#f9fafb;border-radius:10px;padding:16px;margin-bottom:24px;"><p style="margin:0 0 6px;font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Eerste bericht</p><p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">' + preview + '</p></div>' if preview else ''}

        <!-- CTA -->
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr><td align="center">
            <a href="{detail_url}"
               style="display:inline-block;background:#4f46e5;color:white;border-radius:10px;padding:14px 28px;font-size:15px;font-weight:600;text-decoration:none;">
              Gesprek bekijken →
            </a>
          </td></tr>
        </table>

      </td></tr>

      <!-- Footer -->
      <tr><td style="background:#f9fafb;border-radius:0 0 16px 16px;padding:20px 32px;text-align:center;border-top:1px solid #e5e7eb;">
        <p style="margin:0;font-size:12px;color:#9ca3af;">
          Repto · AI-receptionist voor KMO's<br>
          <a href="{DASHBOARD_URL}" style="color:#6b7280;">Dashboard openen</a>
          &nbsp;·&nbsp;
          <a href="{DASHBOARD_URL}/instellingen" style="color:#6b7280;">Notificaties uitschakelen</a>
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>

</body>
</html>
"""


def _info_row(label: str, value: str) -> str:
    return f"""
<tr>
  <td style="padding:12px 16px;border-top:1px solid #f3f4f6;font-size:13px;color:#6b7280;font-weight:500;width:140px;">
    {label}
  </td>
  <td style="padding:12px 16px;border-top:1px solid #f3f4f6;font-size:13px;color:#111827;font-weight:500;">
    {value}
  </td>
</tr>
"""
