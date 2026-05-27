import type { Conversation, Message, DashboardStats, Organization, OrganizationCreate, Appointment } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID || ''

// ─── Fetch helper ─────────────────────────────────────────────────────────────

async function fetcher<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: 0 }, // altijd verse data (geen cache)
    ...options,
  })
  if (!res.ok) throw new Error(`API fout ${res.status}: ${path}`)
  return res.json()
}

// ─── API functies ──────────────────────────────────────────────────────────────

export const api = {
  conversations: {
    list: (orgId: string, status?: string) =>
      fetcher<(Conversation & { last_message?: string })[]>(
        `/conversations/?org_id=${orgId}${status ? `&status=${status}` : ''}`
      ),

    get: (id: string) =>
      fetcher<Conversation>(`/conversations/${id}`),

    messages: (id: string) =>
      fetcher<Message[]>(`/conversations/${id}/messages`),

    updateStatus: (id: string, status: string) =>
      fetcher<{ success: boolean; status: string }>(
        `/conversations/${id}/status?status=${status}`,
        { method: 'PATCH' }
      ),

    stats: (orgId: string) =>
      fetcher<DashboardStats>(`/conversations/stats?org_id=${orgId}`),
  },

  appointments: {
    list: (orgId: string, status?: string) =>
      fetcher<Appointment[]>(
        `/appointments/?org_id=${orgId}${status ? `&status=${status}` : ''}`
      ),

    get: (id: string) =>
      fetcher<Appointment>(`/appointments/${id}`),

    updateStatus: (id: string, status: string) =>
      fetcher<Appointment>(`/appointments/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
  },

  organizations: {
    list: () =>
      fetcher<Organization[]>(`/organizations/`),

    get: (id: string) =>
      fetcher<Organization>(`/organizations/${id}`),

    create: (data: OrganizationCreate) =>
      fetcher<Organization>(`/organizations/`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: string, data: Partial<OrganizationCreate>) =>
      fetcher<Organization>(`/organizations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
  },
}
