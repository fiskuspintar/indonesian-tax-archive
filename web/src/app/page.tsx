import { Search } from '@/components/Search'
import { getRegulationTypes, regulationsByType, getStatistics } from '@/lib/data'
import Link from 'next/link'
import { 
  Scale, 
  FileText, 
  Building2, 
  Landmark, 
  Scroll,
  BookOpen,
  Gavel,
  ClipboardList,
  FileCheck,
  Mail,
  ChevronRight,
  ExternalLink
} from 'lucide-react'

// Icon mapping for regulation types
const typeIcons: Record<string, React.ReactNode> = {
  'UUD 1945': <Scale className="w-6 h-6" />,
  'Tap MPR': <Landmark className="w-6 h-6" />,
  'UU': <Gavel className="w-6 h-6" />,
  'PERPU': <Scroll className="w-6 h-6" />,
  'PP': <Building2 className="w-6 h-6" />,
  'Perpres': <FileText className="w-6 h-6" />,
  'Peraturan Menteri Keuangan': <BookOpen className="w-6 h-6" />,
  'Keputusan Menteri Keuangan': <ClipboardList className="w-6 h-6" />,
  'Peraturan Direktur Jenderal Pajak': <FileCheck className="w-6 h-6" />,
  'Ketetapan Direktur Jenderal Pajak': <FileCheck className="w-6 h-6" />,
  'Surat Edaran Dirjen Pajak': <Mail className="w-6 h-6" />,
}

// Color mapping for regulation types
const typeColors: Record<string, string> = {
  'UUD 1945': 'bg-red-100 text-red-700 border-red-200',
  'Tap MPR': 'bg-orange-100 text-orange-700 border-orange-200',
  'UU': 'bg-amber-100 text-amber-700 border-amber-200',
  'PERPU': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  'PP': 'bg-green-100 text-green-700 border-green-200',
  'Perpres': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'Peraturan Menteri Keuangan': 'bg-blue-100 text-blue-700 border-blue-200',
  'Keputusan Menteri Keuangan': 'bg-indigo-100 text-indigo-700 border-indigo-200',
  'Peraturan Direktur Jenderal Pajak': 'bg-purple-100 text-purple-700 border-purple-200',
  'Ketetapan Direktur Jenderal Pajak': 'bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200',
  'Surat Edaran Dirjen Pajak': 'bg-pink-100 text-pink-700 border-pink-200',
}

export default function Home() {
  const types = getRegulationTypes()
  const stats = getStatistics()

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white">
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-800/50 rounded-full text-sm mb-6">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              Direktorat Jenderal Pajak - Kementerian Keuangan RI
            </div>
            
            <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
              Arsip Digital
              <br />
              <span className="text-blue-200">Peraturan Perpajakan</span>
            </h1>
            
            <p className="text-blue-100 text-lg mb-8 max-w-xl mx-auto">
              Akses lengkap seluruh hierarki peraturan perpajakan Indonesia dari UUD 1945 hingga Surat Edaran Dirjen Pajak.
            </p>
            
            <div className="max-w-xl mx-auto">
              <Search />
            </div>
            
            {/* Stats */}
            <div className="flex justify-center gap-8 mt-8 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.total.toLocaleString('id-ID')}</div>
                <div className="text-blue-200">Total Peraturan</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{types.length}</div>
                <div className="text-blue-200">Jenis Peraturan</div>
              </div>
              {stats.yearRange.min && (
                <div className="text-center">
                  <div className="text-2xl font-bold">{stats.yearRange.min}-{stats.yearRange.max}</div>
                  <div className="text-blue-200">Rentang Tahun</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Regulation Hierarchy */}
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-800">
              Hierarki Peraturan
            </h2>
            <a 
              href="https://datacenter.ortax.org/ortax/aturan/list" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              Sumber Data
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
          
          <div className="space-y-4">
            {types.map((type) => {
              const regs = regulationsByType[type] || []
              const colorClass = typeColors[type] || 'bg-gray-100 text-gray-700 border-gray-200'
              
              return (
                <Link
                  key={type}
                  href={`/type/${encodeURIComponent(type)}/`}
                  className="group block bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-blue-300 transition-all overflow-hidden"
                >
                  <div className="p-5">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-lg ${colorClass}`}>
                        {typeIcons[type] || <FileText className="w-6 h-6" />}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-gray-800 group-hover:text-blue-700 transition-colors">
                          {type}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {regs.length} peraturan tersedia
                        </p>
                      </div>
                      
                      <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-blue-500 transition-colors" />
                    </div>
                    
                    {/* Preview of recent regulations */}
                    {regs.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-xs text-gray-400 mb-2">Terbaru:</p>
                        <div className="space-y-1">
                          {regs.slice(0, 3).map((reg) => (
                            <div key={reg.id} className="text-sm text-gray-600 truncate">
                              <span className="text-blue-600 font-medium">
                                {reg.number && `Nomor ${reg.number}`} {reg.year && `Tahun ${reg.year}`}
                              </span>
                              {' '}
                              <span className="text-gray-500">{reg.subject.slice(0, 80)}...</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            © {new Date().getFullYear()} Arsip Digital Peraturan Perpajakan Indonesia
          </p>
          <p className="text-xs mt-2">
            Data bersumber dari Ortax Data Center
          </p>
        </div>
      </footer>
    </div>
  )
}
