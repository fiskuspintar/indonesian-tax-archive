# Indonesian Tax Regulations Archive

Emergency digitization project for Indonesian tax laws and regulations.

## Project Structure

```
indonesian-tax-archive/
├── scraper/              # Data acquisition scripts
│   ├── spiders/          # Scrapy spiders
│   ├── pipelines.py      # Data processing pipelines
│   └── settings.py       # Scrapy configuration
├── data/                 # Data storage
│   ├── raw/              # Original downloads
│   ├── processed/        # Extracted text
│   └── structured/       # Final JSON/SQLite
├── web/                  # Next.js web application
│   ├── src/
│   ├── public/
│   └── package.json
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## Regulation Types (Scope)

1. UUD 1945 (Undang-Undang Dasar)
2. Tap MPR (Ketetapan MPR)
3. UU / PERPU (Undang-Undang / Peraturan Pemerintah Pengganti UU)
4. PP (Peraturan Pemerintah)
5. Perpres (Peraturan Presiden)
6. Peraturan Menteri Keuangan
7. Keputusan Menteri Keuangan
8. Peraturan Direktur Jenderal Pajak
9. Ketetapan Direktur Jenderal Pajak
10. Surat Edaran Direktur Jenderal Pajak

## Naming Convention

Format: `[Regulation Type]_[Regulation Number]_[Subject]`

Example:
- `Peraturan Menteri Keuangan_Nomor 6 Tahun 2026_pajak penghasilan pasal 21`
- `Surat Edaran Dirjen Pajak_Nomor SE 18 PJ 2025_pedoman pelaksanaan`

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run scraper
cd scraper
scrapy crawl ortax_regulations

# Process downloaded files
python ../scripts/extract_text.py

# Build web app
cd ../web
npm install
npm run build
```

## Data Source

https://datacenter.ortax.org/ortax/aturan/list

## License

Government Mandate - State of Emergency Directive
