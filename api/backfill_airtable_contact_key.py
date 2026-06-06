"""
PROVISIONEEL — productie-aanrakende backfill voor increment 2, stap C.

⚠️  NIET GETEST TEGEN ECHTE AIRTABLE-DATA. Dit script is geschreven op basis van het
    verwachte schema; de pre-migratie-gate hieronder inspecteert de ECHTE records en
    moet eerst handmatig nagelezen worden. Draai NOOIT --apply vóór expliciete sign-off.

WAAROM dit nodig is
-------------------
Sinds increment 2 keyt de Airtable-sync op contact.id i.p.v. conversation.id
("Bron ID" = merge-sleutel). Bestaande live records zijn nog op conversation.id gekeyd.
Deploy je de nieuwe code ZONDER deze backfill, dan vindt de eerste upsert van een bestaande
lead geen match meer (andere Bron ID) en maakt een DUPLICAAT record aan.

Bovendien: had één persoon meerdere gesprekken (bv. terugkerende klant), dan bestaan er nu
meerdere records — één per conversation.id. Die moeten COLLABEREN tot één record per
contact.id; het script houdt er één over en verwijdert de rest.

Werking
-------
1. Bouw conversation.id → contact.id uit de DB.
2. Haal alle Leads-records uit Airtable; lees hun huidige "Bron ID".
3. Pre-migratie-gate (altijd, ook in dry-run): rapporteer
     - records waarvan Bron ID 1-op-1 op een gesprek mapt (→ herschrijven naar contact.id);
     - records die op DEZELFDE contact.id uitkomen (→ collaberen, n-1 verwijderen);
     - records waarvan Bron ID NIET resolvet (→ handmatig nakijken, niet aanraken).
4. Dry-run (standaard): print het plan, wijzig niets.
   --apply: PATCH de survivor naar Bron ID = contact.id en DELETE de duplicaten.

Gebruik:
    cd api
    DATABASE_URL="postgresql://..." python backfill_airtable_contact_key.py            # dry-run
    DATABASE_URL="postgresql://..." python backfill_airtable_contact_key.py --apply     # NA sign-off
"""
import argparse
import asyncio
import json
import os
import sys

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(__file__))

from app.models.conversation import Organization, Conversation  # noqa: E402

AIRTABLE_API_URL = "https://api.airtable.com/v0"


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("❌ Stel DATABASE_URL in.")
        sys.exit(1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def _list_airtable_records(client, base_id, api_key, table):
    """Alle records uit de Leads-tabel (volgt Airtable-paginatie)."""
    records, offset = [], None
    headers = {"Authorization": f"Bearer {api_key}"}
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = await client.get(f"{AIRTABLE_API_URL}/{base_id}/{table}", headers=headers, params=params)
        if resp.status_code != 200:
            raise ValueError(f"Airtable list-fout {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            return records


async def backfill_org(db: AsyncSession, org: Organization, apply: bool) -> None:
    config = json.loads(org.crm_credentials_encrypted or "{}")
    api_key, base_id = config.get("api_key"), config.get("base_id")
    leads_table = config.get("table_name", "Leads")
    if not api_key or not base_id:
        print(f"  ⏭  {org.name}: geen Airtable-creds — overslaan.")
        return

    # conversation.id → contact.id uit de DB.
    rows = (await db.execute(
        select(Conversation.id, Conversation.contact_id).where(Conversation.org_id == org.id)
    )).all()
    conv_to_contact = {r.id: r.contact_id for r in rows}
    known_contact_ids = set(filter(None, conv_to_contact.values()))

    async with httpx.AsyncClient(timeout=30) as client:
        records = await _list_airtable_records(client, base_id, api_key, leads_table)

        groups: dict = {}      # contact.id -> [record, ...] (te herschrijven/collaberen)
        already_ok, unresolved = [], []
        for rec in records:
            bron = (rec.get("fields") or {}).get("Bron ID")
            if bron in known_contact_ids:
                already_ok.append(rec)                 # idempotent: al op contact.id
            elif bron in conv_to_contact and conv_to_contact[bron]:
                groups.setdefault(conv_to_contact[bron], []).append(rec)
            else:
                unresolved.append(rec)                 # geen bekend gesprek → niet aanraken

        collapses = {cid: recs for cid, recs in groups.items() if len(recs) > 1}
        n_rewrite = sum(len(r) for r in groups.values())
        n_delete = sum(len(r) - 1 for r in collapses.values())

        print(f"  📋 {org.name}: {len(records)} records | "
              f"al-ok={len(already_ok)} | herschrijven={n_rewrite} | "
              f"collapse-groepen={len(collapses)} (verwijderen={n_delete}) | "
              f"onresolvebaar={len(unresolved)}")
        if unresolved:
            print(f"     ⚠️  {len(unresolved)} record(s) met onbekende Bron ID — handmatig nakijken, "
                  f"NIET automatisch aangeraakt.")

        if not apply:
            print("     (dry-run — niets gewijzigd. Voeg --apply toe NA sign-off.)")
            return

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        for contact_id, recs in groups.items():
            survivor = recs[0]                          # houd er één over
            patch = await client.patch(
                f"{AIRTABLE_API_URL}/{base_id}/{leads_table}/{survivor['id']}",
                headers=headers, json={"fields": {"Bron ID": contact_id}},
            )
            if patch.status_code != 200:
                print(f"     ❌ PATCH faalde voor {survivor['id']}: {patch.text[:200]}")
                continue
            for dup in recs[1:]:                        # verwijder de duplicaten
                await client.delete(
                    f"{AIRTABLE_API_URL}/{base_id}/{leads_table}/{dup['id']}", headers=headers,
                )
        print(f"     ✅ Toegepast: {n_rewrite} herschreven, {n_delete} verwijderd.")


async def main(apply: bool) -> None:
    engine = create_async_engine(_db_url(), echo=False)
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        orgs = (await db.execute(
            select(Organization).where(Organization.crm_type == "airtable")
        )).scalars().all()
        if not orgs:
            print("Geen organisaties met crm_type='airtable'.")
        print(f"{'APPLY' if apply else 'DRY-RUN'} — {len(orgs)} Airtable-org(s)\n")
        for org in orgs:
            await backfill_org(db, org, apply)
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Voer de wijzigingen écht uit (standaard: dry-run). Alleen na sign-off.")
    args = parser.parse_args()
    asyncio.run(main(args.apply))
