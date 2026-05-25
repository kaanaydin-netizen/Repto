import { api } from '@/lib/api'
import { getOrgId } from '@/lib/org'
import GesprekkenClient from './GesprekkenClient'

export const dynamic = 'force-dynamic'

export default async function GesprekkenPage() {
  const ORG_ID = await getOrgId()
  const conversations = await api.conversations.list(ORG_ID).catch(() => [])
  return <GesprekkenClient initialConversations={conversations} />
}
