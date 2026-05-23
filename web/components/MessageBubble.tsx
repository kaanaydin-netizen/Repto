import { format } from 'date-fns'
import { nl } from 'date-fns/locale'
import { Bot, User } from 'lucide-react'
import clsx from 'clsx'
import type { Message } from '@/lib/types'

export default function MessageBubble({ msg }: { msg: Message }) {
  const isOut = msg.direction === 'outbound'

  return (
    <div className={clsx('flex gap-2.5', isOut ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div className={clsx(
        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white',
        isOut ? 'bg-indigo-600' : 'bg-gray-300',
      )}>
        {isOut
          ? <Bot className="h-4 w-4" />
          : <User className="h-4 w-4 text-gray-600" />
        }
      </div>

      {/* Bubble */}
      <div className={clsx('max-w-[75%]', isOut ? 'items-end' : 'items-start', 'flex flex-col gap-1')}>
        <div className={clsx(
          'rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap',
          isOut
            ? 'rounded-tr-sm bg-indigo-600 text-white'
            : 'rounded-tl-sm bg-white text-gray-900 border border-gray-200 shadow-sm',
        )}>
          {msg.content}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-gray-400">
            {format(new Date(msg.sent_at), 'HH:mm', { locale: nl })}
          </span>
          {isOut && msg.ai_generated && (
            <span className="text-[10px] text-indigo-400">· AI-gegenereerd</span>
          )}
        </div>
      </div>
    </div>
  )
}
