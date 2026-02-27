import regulationsData from '../../public/data/regulations.json'
import byTypeData from '../../public/data/regulations-by-type.json'

export type Regulation = {
  id: number
  type: string
  number: string | null
  year: number | null
  title: string
  subject: string
  filename: string
  dateEnacted: string | null
  status: string
  content: string
  pageCount: number | null
}

// Type assertion since we're importing JSON
export const allRegulations: Regulation[] = regulationsData as Regulation[]
export const regulationsByType: Record<string, Regulation[]> = byTypeData as Record<string, Regulation[]>

// Regulation type order for display
export const typeOrder = [
  'UUD 1945',
  'Tap MPR',
  'UU',
  'PERPU',
  'PP',
  'Perpres',
  'Peraturan Menteri Keuangan',
  'Keputusan Menteri Keuangan',
  'Peraturan Direktur Jenderal Pajak',
  'Ketetapan Direktur Jenderal Pajak',
  'Surat Edaran Dirjen Pajak',
]

export function getRegulationTypes(): string[] {
  return typeOrder.filter(type => regulationsByType[type]?.length > 0)
}

export function getRegulationsByType(type: string): Regulation[] {
  return regulationsByType[type] || []
}

export function getRegulationById(id: number): Regulation | undefined {
  return allRegulations.find(r => r.id === id)
}

export function searchRegulations(query: string): Regulation[] {
  const lowerQuery = query.toLowerCase().trim()
  if (!lowerQuery) return []
  
  return allRegulations.filter(reg => 
    reg.title.toLowerCase().includes(lowerQuery) ||
    reg.subject.toLowerCase().includes(lowerQuery) ||
    (reg.number && reg.number.toLowerCase().includes(lowerQuery)) ||
    (reg.year && reg.year.toString().includes(lowerQuery)) ||
    reg.type.toLowerCase().includes(lowerQuery) ||
    reg.content.toLowerCase().includes(lowerQuery)
  )
}

export function getStatistics() {
  const total = allRegulations.length
  const byType = getRegulationTypes().map(type => ({
    type,
    count: regulationsByType[type]?.length || 0
  }))
  
  const years = allRegulations
    .map(r => r.year)
    .filter((y): y is number => y !== null)
  
  const yearRange = years.length > 0 
    ? { min: Math.min(...years), max: Math.max(...years) }
    : { min: null, max: null }
  
  return {
    total,
    byType,
    yearRange,
  }
}
