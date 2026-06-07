"""
WhatsApp Service — communicatie via de Meta WhatsApp Cloud API.
Berichten sturen, gesprekken beheren en CRM-sync triggeren.

Meta Cloud API: POST https://graph.facebook.com/{version}/{phone_number_id}/messages
met een Bearer access-token. Eén system-user token (agency-WABA) kan namens
meerdere telefoonnummers sturen; het afzendernummer wordt bepaald door phone_number_id.
"""
from __future__ import annotations
from typing import Optional, List
import logging
import httpx
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.conversation import Conversation, Message, Organization, CrmSyncLog, Contact
from app.services.crm_sync_service import CrmSyncService
from app.services.identity_service import normalize_email, compute_lead_score, resolve_contact
from app.services.lead_intake_service import create_or_update_conversation

settings = get_settings()
logger = logging.getLogger(__name__)


def graph_messages_url(phone_number_id: str) -> str:
    """Bouw de Cloud API messages-endpoint voor een specifiek afzendernummer."""
    return (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{phone_number_id}/messages"
    )


def _normalize_recipient(to_phone: str) -> str:
    """Meta verwacht het nummer in internationaal formaat zonder '+' (wa_id)."""
    return to_phone.lstrip("+").strip()


class WhatsAppService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crm_sync = CrmSyncService(db)

    async def get_or_create_conversation(
        self,
        phone_number_id: str,
        contact_phone: str,
        contact_name: Optional[str],
    ) -> Conversation:
        """
        Haal een bestaand gesprek op of maak een nieuw aan.
        phone_number_id: het Meta Cloud API phone_number_id van het ontvangende
                         bedrijfsnummer (uit webhook metadata.phone_number_id).
        contact_phone:   het nummer van de klant (wa_id, internationaal zonder '+').
        """
        # Organisatie zoeken op basis van het Meta phone_number_id
        org_result = await self.db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id == phone_number_id
            )
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise ValueError(
                f"Geen organisatie gevonden voor phone_number_id: {phone_number_id}. "
                f"Koppel dit nummer aan een organisatie (zie seed_dev.py)."
            )

        # Conversatie + kanaal-overschrijdende identiteit via de gedeelde intake-helper,
        # zodat WhatsApp identiek door dezelfde poort loopt als web-form/e-mail/web-chat.
        return await create_or_update_conversation(
            self.db, org,
            channel="whatsapp", name=contact_name, phone=contact_phone,
        )

    async def save_message(
        self,
        conversation_id: str,
        direction: str,
        content: str,
        ai_generated: bool = False,
        wa_message_id: Optional[str] = None,
    ) -> Message:
        """Sla een bericht op in de database."""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            ai_generated=ai_generated,
            wa_message_id=wa_message_id,
        )
        self.db.add(message)
        await self.db.commit()
        return message

    async def _post(self, phone_number_id: str, payload: dict) -> dict:
        """Verstuur één bericht-payload naar de Meta Cloud API."""
        url = graph_messages_url(phone_number_id)
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                # Meta geeft gestructureerde foutinfo terug — log het volledig voor debugging
                logger.error(
                    "Meta Cloud API fout (HTTP %s) bij verzenden naar %s: %s",
                    response.status_code, payload.get("to"), response.text[:500],
                )
            response.raise_for_status()
            return response.json()

    async def send_message(
        self,
        to_phone: str,
        message: str,
        phone_number_id: Optional[str] = None,
    ) -> dict:
        """
        Stuur een vrij tekstbericht via de Meta Cloud API.
        Let op: vrije tekst mag enkel binnen het 24u-klantvenster — buiten dat
        venster gebruik je send_template_message.

        to_phone:        nummer van de ontvanger (internationaal, '+' optioneel).
        phone_number_id: afzendernummer; valt terug op de default uit settings.
        """
        sender = phone_number_id or settings.whatsapp_phone_number_id
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalize_recipient(to_phone),
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        return await self._post(sender, payload)

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str,
        body_params: Optional[List[str]] = None,
        phone_number_id: Optional[str] = None,
    ) -> dict:
        """
        Stuur een vooraf goedgekeurde template (voor berichten buiten het 24u-venster,
        zoals afspraakherinneringen).

        body_params: waarden voor de {{1}}, {{2}}, … placeholders in de template-body,
                     in volgorde. De template moet vooraf goedgekeurd zijn in Meta.
        """
        sender = phone_number_id or settings.whatsapp_phone_number_id
        template: dict = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if body_params:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in body_params
                    ],
                }
            ]
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalize_recipient(to_phone),
            "type": "template",
            "template": template,
        }
        return await self._post(sender, payload)

    async def extract_and_enrich(self, conversation: Conversation) -> Optional[dict]:
        """
        CRM-ONAFHANKELIJKE verrijking: extraheer de lead-data één keer, verrijk het
        gekoppelde Contact (e-mail + warm/lauw/koud-score) en geef de lead-dict terug,
        zodat de notificatie én de CRM-sync exact dezelfde extractie hergebruiken
        (coherente score — geen tweede, mogelijk afwijkende Haiku-call).

        Draait LOS van de crm_type-branch — anders zou de identiteits-/score-ruggengraat
        inert blijven voor orgs met crm_type='none'. Gate: ≥3 berichten (zelfde drempel
        als de CRM-sync). Geeft None terug als er nog te weinig berichten zijn.
        """
        try:
            msgs_result = await self.db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.sent_at.asc())
            )
            messages = list(msgs_result.scalars().all())
            if len(messages) < 3:
                return None

            lead = await self.crm_sync._extract_lead_data(messages)

            if conversation.contact_id:
                contact_result = await self.db.execute(
                    select(Contact).where(Contact.id == conversation.contact_id)
                )
                contact = contact_result.scalar_one_or_none()
                if contact:
                    merged_conv_ids: list = []
                    norm_email = normalize_email(lead.get("email"))
                    if norm_email and not contact.email:
                        # Nieuwe e-mail ontdekt in het gesprek. NIET rechtstreeks toewijzen:
                        # bestaat er al een Contact met deze e-mail (via web/e-mail), dan moeten
                        # die worden SAMENGEVOEGD — anders krijg je twee contacten met dezelfde
                        # e-mail (DoD §3 kanaal-overschrijdend profiel). resolve_contact regelt
                        # zowel het aanvullen (geen match) als de merge (botsing).
                        old_contact_id = contact.id
                        contact = await resolve_contact(
                            self.db, conversation.org_id,
                            phone=contact.phone, email=norm_email, name=contact.name,
                            channel=conversation.channel, merged_out=merged_conv_ids,
                        )
                        if conversation.contact_id != contact.id:
                            conversation.contact_id = contact.id
                            # Anoniem gestarte web-chat: het oude contact had geen e-mail/telefoon,
                            # dus resolve_contact vond het NIET als match en _merge_contacts ruimde
                            # het niet op. Was dit gesprek het enige van dat oude contact, dan is het
                            # nu verweesd: behandel het als merge-verliezer — z'n (mogelijk reeds
                            # gesyncte) record opruimen via merged_conv_ids en het lege contact weg.
                            # (WhatsApp/e-mail bereiken dit pad óók, maar no-oppen: daar deed
                            # _merge_contacts de opruiming al — db.get(old) is None, conv staat al in
                            # merged_conv_ids. Bewezen door test_cross_channel_merge_cleans_orphan.)
                            await self._reap_abandoned_contact(
                                conversation, old_contact_id, merged_conv_ids
                            )
                    score, reason = compute_lead_score(lead)
                    contact.score = score
                    contact.score_reason = reason
                    await self.db.commit()
                    await self.db.refresh(contact)

                    # Na een merge: ruim de verweesde Airtable-records van de verliezer op
                    # (de upsert op de winnaar-key raakt ze niet → ze zouden blijven hangen).
                    if merged_conv_ids:
                        await self.crm_sync.cleanup_merged_records(conversation, merged_conv_ids)

            return lead

        except Exception as e:
            # Niet-kritisch: een fout hier mag de reply/notificatie/sync nooit blokkeren.
            logger.error("extract_and_enrich fout voor gesprek %s: %s", conversation.id, e)
            return None

    async def _reap_abandoned_contact(
        self, conversation: Conversation, old_contact_id: str, merged_conv_ids: list
    ) -> None:
        """
        Verwijder een contact dat door een identiteits-onthulling verweesd raakte.

        Treedt op bij een anoniem gestarte web-chat: het beginpunt is een sleutelloos
        Contact; zodra de bezoeker z'n e-mail noemt, herkoppelt extract_and_enrich het
        gesprek naar het bestaande e-mail-Contact. Bezat het oude Contact enkel dit ene
        (nu herkoppelde) gesprek, dan staat het nu leeg. Het stale Airtable-record van dat
        gesprek is nog op het óúde Contact gekeyd; we voegen het gesprek toe aan
        merged_conv_ids zodat cleanup_merged_records het opruimt, en verwijderen het Contact.
        """
        if old_contact_id == conversation.contact_id:
            return
        # conversation.contact_id is al herkoppeld (autoflush vóór deze query) → een
        # resterend gesprek betekent dat het oude Contact nog elders in gebruik is.
        remaining = (await self.db.execute(
            select(Conversation.id)
            .where(Conversation.contact_id == old_contact_id)
            .limit(1)
        )).first()
        if remaining is not None:
            return
        if conversation.id not in merged_conv_ids:
            merged_conv_ids.append(conversation.id)
        old_contact = await self.db.get(Contact, old_contact_id)
        if old_contact is not None:
            await self.db.delete(old_contact)

    async def sync_to_crm(self, conversation: Conversation, lead: Optional[dict] = None) -> None:
        """
        Synchroniseer het gesprek naar het geconfigureerde CRM.

        Logica:
        - Wacht tot er minstens 3 berichten zijn (zodat de AI al naam/adres/type werk
          heeft kunnen verzamelen) voordat de eerste sync plaatsvindt.
        - Bij elke volgende sync wordt het bestaande Airtable-record bijgewerkt (upsert),
          zodat de lead altijd up-to-date is terwijl het gesprek vordert.
        - lead: een reeds geëxtraheerde lead-dict (van extract_and_enrich) zodat extractie
          niet dubbel gebeurt; None → de sync extraheert zelf (standalone-pad).
        """
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == conversation.org_id)
        )
        org = org_result.scalar_one_or_none()
        if not org or org.crm_type == "none":
            return

        # Tel het aantal berichten — wacht op minstens 3 (≈ 2 inbound + 1 outbound)
        msg_result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation.id)
        )
        msg_count = len(msg_result.scalars().all())
        if msg_count < 3:
            return  # Nog te weinig info om te synchroniseren

        # Controleer of er al een sync-log bestaat (voor upsert)
        sync_result = await self.db.execute(
            select(CrmSyncLog).where(CrmSyncLog.conversation_id == conversation.id)
        )
        existing_log = sync_result.scalar_one_or_none()

        # Alleen een Airtable record ID (begint met "rec") gebruiken voor PATCH.
        # Google Sheets IDs (bijv. "sheets_...") zijn geen geldig Airtable ID.
        existing_record_id = None
        existing_log_id = None
        if existing_log:
            existing_log_id = existing_log.id
            ext_id = existing_log.external_id or ""
            if ext_id.startswith("rec"):
                existing_record_id = ext_id

        await self.crm_sync.sync(
            conversation=conversation,
            org=org,
            existing_record_id=existing_record_id,
            existing_log_id=existing_log_id,
            lead=lead,
        )
