import { allRegulations, getRegulationById } from '@/lib/data'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { 
  ArrowLeft, 
  FileText,
  Calendar,
  Hash,
  Scale,
} from 'lucide-react'

// Generate static params for all regulations
export function generateStaticParams() {
  return allRegulations.map((reg) => ({
    id: reg.id.toString(),
  }))
}

export function generateMetadata({ params }: { params: { id: string } }) {
  const regulation = getRegulationById(parseInt(params.id))
  
  if (!regulation) {
    return {
      title: 'Peraturan Tidak Ditemukan',
    }
  }

  return {
    title: `${regulation.type} ${regulation.number || ''} - ${regulation.subject.slice(0, 60)}...`,
    description: regulation.subject,
  }
}

export default function RegulationPage({ params }: { params: { id: string } }) {
  const regulation = getRegulationById(parseInt(params.id))
  
  if (!regulation) {
    notFound()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <Link 
            href={`/type/${encodeURIComponent(regulation.type)}/`}
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4 text-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Kembali ke {regulation.type}
          </Link>
          
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                  {regulation.type}
                </span>
                {regulation.status !== 'active' && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    {regulation.status}
                  </span>
                )}
              </div>
              
              <h1 className="text-xl md:text-2xl font-bold text-gray-900 leading-tight">
                {regulation.number && (
                  <span className="text-blue-600">Nomor {regulation.number} </span>
                )}
                {regulation.year && (
                  <span>Tahun {regulation.year} </span>
                )}
              </h1>
              
              <p className="text-gray-600 mt-2">{regulation.subject}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <article className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Content Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 md:p-8">
              {regulation.content ? (
                <div className="regulation-content prose prose-lg max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-gray-700 bg-gray-50 p-4 rounded-lg overflow-x-auto">
                    {regulation.content}
                  </pre>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                  <FileText className="w-16 h-16 mb-4" />
                  <p className="text-lg">Isi dokumen sedang diproses</p>
                  <p className="text-sm mt-2">Silakan kembali lagi nanti</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Metadata Card */}
          <div className="mt-6 bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h3 className="font-semibold text-gray-800">Informasi Dokumen</h3>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-start gap-3">
                  <Scale className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Jenis Peraturan</span>
                    <span className="font-medium">{regulation.type}</span>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Hash className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Nomor</span>
                    <span className="font-medium">{regulation.number || '-'}</span>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Tahun</span>
                    <span className="font-medium">{regulation.year || '-'}</span>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Jumlah Halaman</span>
                    <span className="font-medium">{regulation.pageCount || '-'}</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-100">
                <span className="block text-sm text-gray-500 mb-2">Nama File</span>
                <code className="text-xs bg-gray-100 px-3 py-2 rounded block overflow-x-auto">
                  {regulation.filename}
                </code>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  )
}
