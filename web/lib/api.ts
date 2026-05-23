import type { Conversation } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetcher<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API fout: ${res.status}`)
  return res.json()
}

export const api = {
  conversations: {
    list: (orgId: string, status?: string) =>
      fetcher<any[]>(`/conversations/?org_id=${orgId}${status ? `&status=${status}` : ''}`),
    messages: (id: string) =>
      fetcher<any[]>(`/conversations/${id}/messages`),
    updateStatus: (id: string, status: string) =>
      fetcher(`/conversations/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
  },
}

// Mock data voor ontwikkeling (verwijder zodra backend actief is)
export const MOCK_CONVERSATIONS: (Conversation & { last_message?: string })[] = [
  { id: '1', org_id: 'org1', wa_contact_phone: '+32 412 34 56 78', wa_contact_name: 'Jan Peeters',      status: 'new',             created_at: new Date(Date.now() - 1000*60*5).toISOString(),       updated_at: new Date(Date.now() - 1000*60*5).toISOString(),       last_message: 'Hallo, mijn boiler is kapot, wanneer kunnen jullie langskomen?', crm_synced_at: null },
  { id: '2', org_id: 'org1', wa_contact_phone: '+32 478 90 12 34', wa_contact_name: 'Marie Janssen',    status: 'in_progress',     created_at: new Date(Date.now() - 1000*60*45).toISOString(),      updated_at: new Date(Date.now() - 1000*60*20).toISOString(),      last_message: 'Dankjewel, we verwachten u woensdag om 14u?',                    crm_synced_at: new Date().toISOString() },
  { id: '3', org_id: 'org1', wa_contact_phone: '+32 496 55 66 77', wa_contact_name: 'Thomas De Smedt',  status: 'appointment_set', created_at: new Date(Date.now() - 1000*60*60*3).toISOString(),   updated_at: new Date(Date.now() - 1000*60*60*2).toISOString(),   last_message: 'Perfect, tot woensdag!',                                          crm_synced_at: new Date().toISOString() },
  { id: '4', org_id: 'org1', wa_contact_phone: '+31 6 12 34 56 78', wa_contact_name: 'Sofie Vermeersch', status: 'new',            created_at: new Date(Date.now() - 1000*60*2).toISOString(),       updated_at: new Date(Date.now() - 1000*60*2).toISOString(),       last_message: 'Hoeveel kost een nieuwe warmtepomp inclusief installatie?',       crm_synced_at: null },
  { id: '5', org_id: 'org1', wa_contact_phone: '+32 470 11 22 33', wa_contact_name: 'Pieter Leclercq',  status: 'closed',          created_at: new Date(Date.now() - 1000*60*60*24).toISOString(),  updated_at: new Date(Date.now() - 1000*60*60*20).toISOString(),  last_message: 'Alles werkt prima, bedankt!',                                     crm_synced_at: new Date().toISOString() },
]

export const MOCK_MESSAGES = [
  {
    id: 'm1',
    conversation_id: '1',
    direction: 'inbound' as const,
    content: 'Hallo, mijn boiler is kapot, wanneer kunnen jullie langskomen?',
    ai_generated: false,
    sent_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: 'm2',
    conversation_id: '1',
    direction: 'outbound' as const,
    content: 'Hallo! Vervelend dat je boiler het heeft begeven. 😕\n\nWanneer schikt het jou het beste? Geef me even je naam, adres en een voorkeursdatum/-tijdstip, dan plan ik zo snel mogelijk iets in voor je!\n\n⚠️ Heb je geen warm water of is er sprake van een lek? Dan raden we aan direct te bellen voor spoedhulp.',
    ai_generated: true,
    sent_at: new Date(Date.now() - 1000 * 60 * 4).toISOString(),
  },
]
