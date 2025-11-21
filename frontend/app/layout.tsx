import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'QUANTUM_FORGE | Batch Calculations',
  description: 'High-throughput molecular property calculations via xTB',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50">{children}</body>
    </html>
  )
}
