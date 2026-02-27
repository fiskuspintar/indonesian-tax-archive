import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Arsip Digital Peraturan Perpajakan Indonesia',
  description: 'Direktorat Jenderal Pajak - Kementerian Keuangan Republik Indonesia',
  keywords: 'perpajakan, pajak, Indonesia, peraturan, UU, PP, PMK, KMK, Dirjen Pajak',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="id">
      <body className="antialiased">{children}</body>
    </html>
  )
}
