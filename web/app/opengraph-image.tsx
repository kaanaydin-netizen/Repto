/**
 * Automatisch gegenereerde OG-afbeelding voor social sharing.
 * Next.js App Router serveert dit als /opengraph-image (1200×630px).
 *
 * Let op: ImageResponse gebruikt Satori voor rendering — enkel flexbox,
 * geen backdrop-filter, geen radial-gradient, geen grid.
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
          width: '1200px',
          height: '630px',
          background: '#4338ca',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'sans-serif',
          padding: '72px 80px',
        }}
      >
        {/* Logo rij */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            marginBottom: '40px',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '18px',
              background: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '38px',
            }}
          >
            ⚡
          </div>
          <span
            style={{
              fontSize: '56px',
              fontWeight: '800',
              color: 'white',
              letterSpacing: '-2px',
            }}
          >
            Repto
          </span>
        </div>

        {/* Headline */}
        <div
          style={{
            fontSize: '66px',
            fontWeight: '800',
            color: 'white',
            textAlign: 'center',
            lineHeight: '1.15',
            letterSpacing: '-2px',
            marginBottom: '24px',
          }}
        >
          Mis geen enkele
          offerte-aanvraag meer.
        </div>

        {/* Subtitel */}
        <div
          style={{
            fontSize: '30px',
            color: 'rgba(255, 255, 255, 0.75)',
            textAlign: 'center',
            marginBottom: '48px',
          }}
        >
          WhatsApp AI-receptionist voor Belgische KMO&apos;s
        </div>

        {/* Stat badges */}
        <div style={{ display: 'flex', gap: '24px' }}>
          {[
            { value: '24/7', label: 'Bereikbaar' },
            { value: '< 5s', label: 'Gem. reactietijd' },
            { value: '9+', label: 'Sectoren' },
            { value: '100%', label: 'Automatisch' },
          ].map(({ value, label }) => (
            <div
              key={label}
              style={{
                background: 'rgba(255, 255, 255, 0.15)',
                border: '1.5px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '16px',
                padding: '16px 28px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span
                style={{
                  fontSize: '32px',
                  fontWeight: '800',
                  color: 'white',
                }}
              >
                {value}
              </span>
              <span
                style={{
                  fontSize: '17px',
                  color: 'rgba(255, 255, 255, 0.65)',
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
