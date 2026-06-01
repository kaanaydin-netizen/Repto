import type { Conversation, Message, DashboardStats, Organization, OrganizationCreate, Appointment } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID || ''

// ─── Fetch helper ─────────────────────────────────────────────────────────────
// `token` is het Clerk session-token. Server components halen het op met
// `auth().getToken()`, client components met `useAuth().getToken()`. Zolang de
// backend-auth uit staat wordt het token genegeerd; daarna is het verplicht.

async function fetcher<T>(path: string, token?: string | null, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API_URL}${path}`, {
    headers,
    next: { revalidate: 0 }, // altijd verse data (geen cache)
    ...options,
  })
  if (!res.ok) throw new Error(`API fout ${res.status}: ${path}`)
  return res.json()
}

// ─── API functies ──────────────────────────────────────────────────────────────

export const api = {
  conversations: {
    list: (orgId: string, status?: string, token?: string | null) =>
      fetcher<(Conversation & { last_message?: string })[]>(
        `/conversations/?org_id=${orgId}${status ? `&status=${status}` : ''}`,
        token
      ),

    get: (id: string, token?: string | null) =>
      fetcher<Conversation>(`/conversations/${id}`, token),

    messages: (id: string, token?: string | null) =>
      fetcher<Message[]>(`/conversations/${id}/messages`, token),

    updateStatus: (id: string, status: string, token?: string | null) =>
      fetcher<{ success: boolean; status: string }>(
        `/conversations/${id}/status?status=${status}`,
        token,
        { method: 'PATCH' }
      ),

    stats: (orgId: string, token?: string | null) =>
      fetcher<DashboardStats>(`/conversations/stats?org_id=${orgId}`, token),
  },

  appointments: {
    list: (orgId: string, status?: string, token?: string | null) =>
      fetcher<Appointment[]>(
        `/appointments/?org_id=${orgId}${status ? `&status=${status}` : ''}`,
        token
      ),

    get: (id: string, token?: string | null) =>
      fetcher<Appointment>(`/appointments/${id}`, token),

    updateStatus: (id: string, status: string, token?: string | null) =>
      fetcher<Appointment>(`/appointments/${id}`, token, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
  },

  organizations: {
    list: (token?: string | null) =>
      fetcher<Organization[]>(`/organizations/`, token),

    get: (id: string, token?: string | null) =>
      fetcher<Organization>(`/organizations/${id}`, token),

    create: (data: OrganizationCreate, token?: string | null) =>
      fetcher<Organization>(`/organizations/`, token, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: string, data: Partial<OrganizationCreate>, token?: string | null) =>
      fetcher<Organization>(`/organizations/${id}`, token, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    // Eenmalige claim van een nog-ongeclaimde org (zie backend POST /{id}/claim).
    claim: (id: string, token?: string | null) =>
      fetcher<Organization>(`/organizations/${id}/claim`, token, {
        method: 'POST',
      }),
  },
}
