import { notFound } from 'next/navigation'
import { api } from '@/lib/api'
import GesprekDetailClient from './GesprekDetailClient'

export const dynamic = 'force-dynamic'

export default async function GesprekDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const [conv, messages] = await Promise.all([
    api.conversations.get(params.id).catch(() => null),
    api.conversations.messages(params.id).catch(() => []),
  ])

  if (!conv) notFound()

  return <GesprekDetailClient conv={conv} initialMessages={messages} />
}
