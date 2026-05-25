import { api, ORG_ID } from '@/lib/api'
import GesprekkenClient from './GesprekkenClient'

export const dynamic = 'force-dynamic'

export default async function GesprekkenPage() {
  const conversations = await api.conversations.list(ORG_ID).catch(() => [])
  return <GesprekkenClient initialConversations={conversations} />
}
