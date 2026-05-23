export type ConversationStatus = 'new' | 'in_progress' | 'appointment_set' | 'closed'

export interface Conversation {
  id: string
  org_id: string
  wa_contact_phone: string
  wa_contact_name: string | null
  status: ConversationStatus
  crm_synced_at: string | null
  created_at: string
  updated_at: string
  last_message?: string
}

export interface Message {
  id: string
  conversation_id: string
  direction: 'inbound' | 'outbound'
  content: string
  ai_generated: boolean
  sent_at: string
}

export interface Appointment {
  id: string
  conversation_id: string
  org_id: string
  title: string
  start_at: string
  end_at: string
  status: 'confirmed' | 'cancelled'
  reminder_sent: boolean
}

export interface DashboardStats {
  total_conversations: number
  new_leads: number
  appointments_today: number
  avg_response_time_min: number
}
