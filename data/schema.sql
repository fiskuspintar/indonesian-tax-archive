-- Indonesian Tax Regulations Database Schema
-- SQLite with Full-Text Search support

-- Main regulations table
CREATE TABLE IF NOT EXISTS regulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Core identification
    regulation_type TEXT NOT NULL,
    number TEXT,
    year INTEGER,
    title TEXT NOT NULL,
    subject TEXT,
    filename TEXT UNIQUE NOT NULL,
    
    -- Dates
    date_enacted DATE,
    date_effective DATE,
    date_signed DATE,
    
    -- Status
    status TEXT DEFAULT 'active',  -- active, amended, revoked, pending
    amended_by INTEGER,
    revokes INTEGER,
    
    -- Content
    full_text TEXT,
    summary TEXT,
    content_html TEXT,
    
    -- Source tracking
    source_url TEXT,
    download_url TEXT,
    local_path TEXT,
    file_size INTEGER,
    file_format TEXT,  -- pdf, docx, html
    
    -- Metadata
    extracted_metadata TEXT,  -- JSON string
    page_count INTEGER,
    
    -- Search optimization
    search_vector TEXT,  -- Concatenated fields for simple search
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS regulations_fts USING fts5(
    title,
    subject,
    full_text,
    content='regulations',
    content_rowid='id'
);

-- Triggers to keep FTS index updated
CREATE TRIGGER IF NOT EXISTS regulations_ai AFTER INSERT ON regulations BEGIN
    INSERT INTO regulations_fts(rowid, title, subject, full_text)
    VALUES (new.id, new.title, new.subject, new.full_text);
END;

CREATE TRIGGER IF NOT EXISTS regulations_ad AFTER DELETE ON regulations BEGIN
    INSERT INTO regulations_fts(regulations_fts, rowid, title, subject, full_text)
    VALUES ('delete', old.id, old.title, old.subject, old.full_text);
END;

CREATE TRIGGER IF NOT EXISTS regulations_au AFTER UPDATE ON regulations BEGIN
    INSERT INTO regulations_fts(regulations_fts, rowid, title, subject, full_text)
    VALUES ('delete', old.id, old.title, old.subject, old.full_text);
    INSERT INTO regulations_fts(rowid, title, subject, full_text)
    VALUES (new.id, new.title, new.subject, new.full_text);
END;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_type ON regulations(regulation_type);
CREATE INDEX IF NOT EXISTS idx_year ON regulations(year);
CREATE INDEX IF NOT EXISTS idx_status ON regulations(status);
CREATE INDEX IF NOT EXISTS idx_type_year ON regulations(regulation_type, year);
CREATE INDEX IF NOT EXISTS idx_filename ON regulations(filename);

-- Regulation relationships table (for tracking amendments, revocations)
CREATE TABLE IF NOT EXISTS regulation_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_regulation_id INTEGER NOT NULL,
    target_regulation_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,  -- amends, revokes, references, implements
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_regulation_id) REFERENCES regulations(id),
    FOREIGN KEY (target_regulation_id) REFERENCES regulations(id)
);

CREATE INDEX IF NOT EXISTS idx_rel_source ON regulation_relationships(source_regulation_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON regulation_relationships(target_regulation_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON regulation_relationships(relationship_type);

-- Keywords/tags table for categorization
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regulation_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    relevance_score REAL DEFAULT 1.0,
    FOREIGN KEY (regulation_id) REFERENCES regulations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_keyword_reg ON keywords(regulation_id);

-- Scraping log for tracking data source changes
CREATE TABLE IF NOT EXISTS scraping_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    http_status INTEGER,
    error_message TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scrape_url ON scraping_log(url);
CREATE INDEX IF NOT EXISTS idx_scrape_time ON scraping_log(scraped_at);

-- View for active regulations only
CREATE VIEW IF NOT EXISTS active_regulations AS
SELECT * FROM regulations WHERE status = 'active';

-- View for regulations by type with counts
CREATE VIEW IF NOT EXISTS regulations_by_type AS
SELECT 
    regulation_type,
    COUNT(*) as total_count,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
    MIN(year) as earliest_year,
    MAX(year) as latest_year
FROM regulations
GROUP BY regulation_type
ORDER BY 
    CASE regulation_type
        WHEN 'UUD 1945' THEN 1
        WHEN 'Tap MPR' THEN 2
        WHEN 'UU' THEN 3
        WHEN 'PERPU' THEN 4
        WHEN 'PP' THEN 5
        WHEN 'Perpres' THEN 6
        WHEN 'Peraturan Menteri Keuangan' THEN 7
        WHEN 'Keputusan Menteri Keuangan' THEN 8
        WHEN 'Peraturan Direktur Jenderal Pajak' THEN 9
        WHEN 'Ketetapan Direktur Jenderal Pajak' THEN 10
        WHEN 'Surat Edaran Dirjen Pajak' THEN 11
        ELSE 99
    END;
