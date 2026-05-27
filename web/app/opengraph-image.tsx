/**
 * Automatisch gegenereerde OG-afbeelding voor social sharing.
 * Next.js App Router serveert dit als /opengraph-image (1200×630px).
 */
import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = "Repto — AI-Receptionist voor KMO's"
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: 'linear-gradient(135deg, #4338ca 0%, #6d28d9 60%, #4f46e5 100%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          padding: '72px 80px',
        }}
      >
        {/* Logo */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            marginBottom: '44px',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '20px',
              background: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '36px',
              boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
            }}
          >
            ⚡
          </div>
          <span
            style={{
              fontSize: '52px',
              fontWeight: '800',
              color: 'white',
              letterSpacing: '-1.5px',
            }}
          >
            Repto
          </span>
        </div>

        {/* Headline */}
        <div
          style={{
            fontSize: '64px',
            fontWeight: '800',
            color: 'white',
            textAlign: 'center',
            lineHeight: '1.15',
            letterSpacing: '-2px',
            marginBottom: '28px',
            maxWidth: '960px',
          }}
        >
          Mis geen enkele
          <br />
          offerte-aanvraag meer.
        </div>

        {/* Subtitel */}
        <div
          style={{
            fontSize: '30px',
            color: 'rgba(255,255,255,0.75)',
            textAlign: 'center',
            marginBottom: '52px',
          }}
        >
          WhatsApp AI-receptionist voor Belgische KMO&apos;s
        </div>

        {/* Stat badges */}
        <div style={{ display: 'flex', gap: '28px' }}>
          {[
            { value: '24/7', label: 'Bereikbaar' },
            { value: '< 5s', label: 'Gem. reactietijd' },
            { value: '9+', label: 'Sectoren' },
            { value: '100%', label: 'Automatisch' },
          ].map(({ value, label }) => (
            <div
              key={label}
              style={{
                background: 'rgba(255,255,255,0.15)',
                border: '1.5px solid rgba(255,255,255,0.3)',
                borderRadius: '18px',
                padding: '18px 32px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                backdropFilter: 'blur(8px)',
              }}
            >
              <span
                style={{
                  fontSize: '34px',
                  fontWeight: '800',
                  color: 'white',
                  letterSpacing: '-0.5px',
                }}
              >
                {value}
              </span>
              <span
                style={{
                  fontSize: '18px',
                  color: 'rgba(255,255,255,0.65)',
                  fontWeight: '500',
                }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size },
  )
}
