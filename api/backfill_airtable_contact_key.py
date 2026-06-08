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

# Airtable staat ~5 requests/sec toe. Mutaties (PATCH/DELETE) lopen sequentieel; een korte
# pauze houdt ons veilig onder de limiet. Tests zetten dit op 0.
_THROTTLE_SECONDS = 0.2


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

        # Groepeer ÁLLE records per uiteindelijke contact.id — zowel de records die al correct
        # op contact.id staan ("correct") als de oude, op conversation.id gekeyde ("rewrite").
        # Eén persoon kan meerdere records hebben (meerdere gesprekken); die collaberen tot één.
        # Door de al-correcte records mee te groeperen blijft het script idempotent én veilig
        # als het ooit ná de code-deploy draait (anders zou een rewrite een duplicaat maken
        # naast een reeds-correct record).
        groups: dict = {}      # contact.id -> {"correct": [...], "rewrite": [...]}
        unresolved = []
        for rec in records:
            bron = (rec.get("fields") or {}).get("Bron ID")
            if bron in known_contact_ids:
                groups.setdefault(bron, {"correct": [], "rewrite": []})["correct"].append(rec)
            elif bron in conv_to_contact and conv_to_contact[bron]:
                cid = conv_to_contact[bron]
                groups.setdefault(cid, {"correct": [], "rewrite": []})["rewrite"].append(rec)
            else:
                unresolved.append(rec)                 # geen bekend gesprek → niet aanraken

        # Plan per contact: houd één survivor over (bij voorkeur een al-correct record, dan
        # is geen PATCH nodig), herschrijf anders de eerste oude record, en verwijder de rest.
        plan = []              # (survivor_rec, needs_patch: bool, [dup_recs])
        for contact_id, g in groups.items():
            if g["correct"]:
                survivor, needs_patch = g["correct"][0], False
                dups = g["correct"][1:] + g["rewrite"]
            else:
                survivor, needs_patch = g["rewrite"][0], True
                dups = g["rewrite"][1:]
            plan.append((contact_id, survivor, needs_patch, dups))

        n_patch = sum(1 for _, _, needs_patch, _ in plan if needs_patch)
        n_delete = sum(len(dups) for _, _, _, dups in plan)
        n_noop = sum(1 for _, _, needs_patch, dups in plan if not needs_patch and not dups)

        print(f"  📋 {org.name}: {len(records)} records | "
              f"al-ok={n_noop} | herschrijven={n_patch} | "
              f"contact-groepen={len(plan)} | verwijderen={n_delete} | "
              f"onresolvebaar={len(unresolved)}")
        if unresolved:
            print(f"     ⚠️  {len(unresolved)} record(s) met onbekende Bron ID — handmatig nakijken, "
                  f"NIET automatisch aangeraakt.")

        if not apply:
            print("     (dry-run — niets gewijzigd. Voeg --apply toe NA sign-off.)")
            return

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        n_patched = n_deleted = 0
        for contact_id, survivor, needs_patch, dups in plan:
            if needs_patch:
                patch = await client.patch(
                    f"{AIRTABLE_API_URL}/{base_id}/{leads_table}/{survivor['id']}",
                    headers=headers, json={"fields": {"Bron ID": contact_id}},
                )
                await asyncio.sleep(_THROTTLE_SECONDS)
                if patch.status_code != 200:
                    print(f"     ❌ PATCH faalde voor {survivor['id']}: {patch.text[:200]} "
                          f"— duplicaten van deze groep NIET verwijderd.")
                    continue                            # survivor niet bevestigd → dups behouden
                n_patched += 1
            for dup in dups:                            # verwijder de overtollige records
                await client.delete(
                    f"{AIRTABLE_API_URL}/{base_id}/{leads_table}/{dup['id']}", headers=headers,
                )
                await asyncio.sleep(_THROTTLE_SECONDS)
                n_deleted += 1
        print(f"     ✅ Toegepast: {n_patched} herschreven, {n_deleted} verwijderd.")


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
