import { regulationsByType, typeOrder, Regulation } from '@/lib/data'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { 
  ArrowLeft, 
  FileText, 
  Calendar,
  Hash,
  Scale,
  ChevronRight
} from 'lucide-react'

// Generate static params for all regulation types
export function generateStaticParams() {
  return typeOrder.map((type) => ({
    type: encodeURIComponent(type),
  }))
}

export function generateMetadata({ params }: { params: { type: string } }) {
  const type = decodeURIComponent(params.type)
  return {
    title: `${type} - Arsip Digital Peraturan Perpajakan`,
    description: `Daftar lengkap ${type} dari Direktorat Jenderal Pajak`,
  }
}

export default function TypePage({ params }: { params: { type: string } }) {
  const type = decodeURIComponent(params.type)
  const regulations = regulationsByType[type]
  
  if (!regulations) {
    notFound()
  }

  // Group by year
  const byYear: Record<number, Regulation[]> = {}
  regulations.forEach((reg) => {
    const year = reg.year || 0
    if (!byYear[year]) byYear[year] = []
    byYear[year].push(reg)
  })

  const years = Object.keys(byYear)
    .map(Number)
    .sort((a, b) => b - a)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <Link 
            href="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4 text-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Kembali ke Beranda
          </Link>
          
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Scale className="w-6 h-6 text-blue-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{type}</h1>
              <p className="text-gray-500">{regulations.length} peraturan</p>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {years.map((year) => (
            <div key={year} className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="w-5 h-5 text-gray-400" />
                <h2 className="text-lg font-semibold text-gray-800">
                  {year === 0 ? 'Tahun Tidak Diketahui' : `Tahun ${year}`}
                </h2>
                <span className="text-sm text-gray-500">({byYear[year].length})</span>
              </div>
              
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {byYear[year].map((reg, idx) => (
                  <Link
                    key={reg.id}
                    href={`/regulation/${reg.id}/`}
                    className={`block p-4 hover:bg-blue-50 transition-colors ${
                      idx !== byYear[year].length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg flex-shrink-0">
                        <Hash className="w-4 h-4 text-gray-500" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-blue-600">
                            {reg.number ? `Nomor ${reg.number}` : 'Tanpa Nomor'}
                          </span>
                          {reg.status !== 'active' && (
                            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                              {reg.status}
                            </span>
                          )}
                        </div>
                        
                        <p className="text-gray-800 line-clamp-2">
                          {reg.subject}
                        </p>
                        
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                          {reg.pageCount && (
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {reg.pageCount} halaman
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <ChevronRight className="w-5 h-5 text-gray-300 flex-shrink-0" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
