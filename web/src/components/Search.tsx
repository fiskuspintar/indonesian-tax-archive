'use client'

import { useState, useMemo } from 'react'
import { Search as SearchIcon, X, FileText } from 'lucide-react'
import { Regulation, searchRegulations } from '@/lib/data'
import Link from 'next/link'

export function Search() {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  const results = useMemo(() => {
    if (query.length < 2) return []
    return searchRegulations(query).slice(0, 10)
  }, [query])

  const handleSearch = (value: string) => {
    setQuery(value)
    setIsOpen(value.length >= 2)
  }

  const clearSearch = () => {
    setQuery('')
    setIsOpen(false)
  }

  return (
    <div className="relative w-full max-w-2xl">
      <div className="relative">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Cari peraturan perpajakan..."
          className="w-full pl-12 pr-12 py-4 rounded-xl border border-gray-200 bg-white shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg transition-all"
        />
        
        {query && (
          <button
            onClick={clearSearch}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        )}
      </div>
      
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-2xl border border-gray-100 max-h-96 overflow-y-auto z-50">
          {results.length > 0 ? (
            results.map((reg) => (
              <SearchResult key={reg.id} regulation={reg} onClick={clearSearch} />
            ))
          ) : (
            <div className="p-6 text-center text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>Tidak ditemukan peraturan untuk "{query}"</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SearchResult({ regulation, onClick }: { regulation: Regulation; onClick: () => void }) {
  return (
    <Link
      href={`/regulation/${regulation.id}/`}
      onClick={onClick}
      className="block p-4 hover:bg-blue-50 border-b border-gray-100 last:border-0 transition-colors"
    >
      <div className="flex items-start gap-3">
        <FileText className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
        <div className="min-w-0">
          <div className="text-sm font-medium text-blue-700">
            {regulation.type}
            {regulation.number && ` • Nomor ${regulation.number}`}
            {regulation.year && ` • Tahun ${regulation.year}`}
          </div>
          <div className="text-gray-800 mt-1 line-clamp-2 text-sm">
            {regulation.subject}
          </div>
        </div>
      </div>
    </Link>
  )
}
