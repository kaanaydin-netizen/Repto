'use client'

// TODO: vervang door het ECHTE WhatsApp-businessnummer zodra dat live is
// (internationaal formaat zonder + of spaties, bv. '32470123456').
// Zolang dit de placeholder is, blijft de widget verborgen.
const WHATSAPP_NUMBER = '32XXXXXXXXX'
const PREFILLED = 'Hallo, ik wil meer info over Repto'

/**
 * Zwevende WhatsApp-knop rechtsonder. Demonstreert meteen het product:
 * een bezoeker die klikt, chat met de Repto AI.
 * Verschijnt pas zodra WHATSAPP_NUMBER een echt nummer is.
 */
export default function WhatsAppWidget() {
  if (WHATSAPP_NUMBER.includes('X')) return null

  const href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(PREFILLED)}`

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Chat met ons via WhatsApp"
      // Boven de web-chat-launcher (die op bottom-6 z-50 zit) zodat ze niet overlappen;
      // z-40 < het chat-paneel (z-50) → bij een geopende chat verdwijnt deze erachter.
      className="fixed bottom-24 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] shadow-lg shadow-green-600/30 transition-transform hover:scale-110"
    >
      <svg viewBox="0 0 32 32" className="h-7 w-7 fill-white" aria-hidden="true">
        <path d="M16.004 0h-.008C7.174 0 0 7.176 0 16c0 3.49 1.124 6.726 3.036 9.354L1.05 31.27l6.124-1.958A15.9 15.9 0 0 0 16.004 32C24.826 32 32 24.822 32 16S24.826 0 16.004 0Zm9.318 22.594c-.386 1.09-1.918 1.994-3.14 2.258-.836.178-1.928.32-5.604-1.204-4.7-1.948-7.726-6.724-7.962-7.034-.226-.31-1.9-2.53-1.9-4.826 0-2.296 1.166-3.424 1.636-3.904.386-.394.85-.574 1.34-.574.158 0 .3.008.43.014.386.016.58.038.834.646.316.762 1.086 2.65 1.178 2.84.094.19.188.448.06.758-.12.32-.226.45-.434.692-.21.242-.408.428-.618.688-.19.226-.404.47-.162.886.242.408 1.076 1.772 2.31 2.87 1.592 1.418 2.916 1.87 3.376 2.062.342.142.75.108 1-.16.318-.342.71-.91 1.108-1.47.282-.402.638-.452 1.012-.31.382.134 2.422 1.142 2.838 1.35.416.21.692.31.794.484.1.176.1 1.01-.286 2.1Z" />
      </svg>
    </a>
  )
}
