import { allRegulations, getRegulationById } from '@/lib/data'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { 
  ArrowLeft, 
  FileText,
  Calendar,
  Hash,
  Scale,
  ExternalLink,
  Tag,
  Clock
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

  // Build Ortax source URL
  const ortaxUrl = `https://datacenter.ortax.org/ortax/aturan/show/${params.id}`

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 to-blue-800 text-white">
        <div className="container mx-auto px-4 py-6">
          <Link 
            href={`/type/${encodeURIComponent(regulation.type)}/`}
            className="inline-flex items-center text-blue-200 hover:text-white mb-4 text-sm transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Kembali ke {regulation.type}
          </Link>
          
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3 py-1 bg-blue-700 text-blue-100 text-sm font-medium rounded-full">
                  {regulation.type}
                </span>
                {regulation.status !== 'active' && (
                  <span className="px-3 py-1 bg-gray-700 text-gray-300 text-sm rounded-full">
                    {regulation.status}
                  </span>
                )}
              </div>
              
              <h1 className="text-2xl md:text-3xl font-bold leading-tight">
                {regulation.number && (
                  <span>Nomor {regulation.number} </span>
                )}
                {regulation.year && (
                  <span className="text-blue-200">Tahun {regulation.year}</span>
                )}
              </h1>
            </div>
            
            <a
              href={ortaxUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-white text-blue-900 rounded-lg hover:bg-blue-50 transition-colors font-medium"
            >
              <ExternalLink className="w-4 h-4" />
              Lihat di Ortax
            </a>
          </div>
        </div>
      </header>

      {/* Content */}
      <article className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          
          {/* Subject/Description Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="font-semibold text-gray-800 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Tentang
              </h2>
            </div>
            <div className="p-6">
              <p className="text-lg text-gray-800 leading-relaxed">
                {regulation.subject}
              </p>
            </div>
          </div>

          {/* Full Content Card (if available) */}
          {regulation.content ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                <h2 className="font-semibold text-gray-800">Isi Dokumen</h2>
              </div>
              <div className="p-6">
                <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-gray-700 bg-gray-50 p-4 rounded-lg overflow-x-auto">
                  {regulation.content}
                </pre>
              </div>
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <FileText className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-amber-900 mb-2">
                    Dokumen Lengkap Tersedia di Ortax
                  </h3>
                  <p className="text-amber-800 mb-4">
                    Untuk melihat isi lengkap dokumen ini, silakan kunjungi halaman aslinya di Ortax Data Center.
                  </p>
                  <a
                    href={ortaxUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Buka di Ortax
                  </a>
                </div>
              </div>
            </div>
          )}
          
          {/* Metadata Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="font-semibold text-gray-800">Informasi Dokumen</h2>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-start gap-3">
                  <Scale className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Jenis Peraturan</span>
                    <span className="font-medium text-gray-900">{regulation.type}</span>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Hash className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Nomor</span>
                    <span className="font-medium text-gray-900">{regulation.number || '-'}</span>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Tahun</span>
                    <span className="font-medium text-gray-900">{regulation.year || '-'}</span>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <span className="block text-sm text-gray-500">Tanggal Diterbitkan</span>
                    <span className="font-medium text-gray-900">{regulation.dateEnacted || '-'}</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-start gap-3">
                  <Tag className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div className="flex-1">
                    <span className="block text-sm text-gray-500 mb-2">Nama File Standar</span>
                    <code className="text-xs bg-gray-100 px-3 py-2 rounded block overflow-x-auto text-gray-700">
                      {regulation.filename}
                    </code>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-start gap-3">
                  <ExternalLink className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div className="flex-1">
                    <span className="block text-sm text-gray-500 mb-2">Sumber</span>
                    <a 
                      href={ortaxUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline break-all"
                    >
                      {ortaxUrl}
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  )
}
