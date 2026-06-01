import { api } from '@/lib/api'
import { getOrgId } from '@/lib/org'
import { getServerToken } from '@/lib/server-token'
import GesprekkenClient from './GesprekkenClient'

export const dynamic = 'force-dynamic'

export default async function GesprekkenPage() {
  const ORG_ID = await getOrgId()
  const token = await getServerToken()
  const conversations = await api.conversations.list(ORG_ID, undefined, token).catch(() => [])
  return <GesprekkenClient initialConversations={conversations} orgId={ORG_ID} />
}
