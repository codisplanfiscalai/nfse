from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from .settings import DB_PATH

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'admin', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS companies (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, tax_id TEXT NOT NULL UNIQUE, cert_id INTEGER, environment TEXT NOT NULL DEFAULT 'restrita', active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS certificates (
 id INTEGER PRIMARY KEY, label TEXT NOT NULL, filename TEXT NOT NULL, content_enc BLOB NOT NULL, password_enc BLOB NOT NULL, expires_at TEXT, fingerprint TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cursors (
 company_id INTEGER PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
 nsu INTEGER NOT NULL DEFAULT 0, last_sync TEXT, status TEXT NOT NULL DEFAULT 'nunca', last_message TEXT NOT NULL DEFAULT '', query_mode TEXT
);
CREATE TABLE IF NOT EXISTS raw_documents (
 id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 nsu INTEGER, access_key TEXT NOT NULL, doc_type TEXT NOT NULL, event_type TEXT,
 xml_enc BLOB NOT NULL, sha256 TEXT NOT NULL, generated_at TEXT,
 UNIQUE(company_id, nsu), UNIQUE(company_id, doc_type, sha256)
);
CREATE TABLE IF NOT EXISTS invoices (
 id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 access_key TEXT NOT NULL, number TEXT, issued_at TEXT, competence TEXT,
 provider_id TEXT, customer_id TEXT, customer_name TEXT, service_code TEXT, service_desc TEXT,
 amount_cents INTEGER NOT NULL DEFAULT 0, net_cents INTEGER NOT NULL DEFAULT 0,
 iss_cents INTEGER NOT NULL DEFAULT 0, irrf_cents INTEGER NOT NULL DEFAULT 0,
 inss_cents INTEGER NOT NULL DEFAULT 0, pcc_cents INTEGER NOT NULL DEFAULT 0,
 iss_retained INTEGER NOT NULL DEFAULT 0, iss_retention_code TEXT,
 status TEXT NOT NULL DEFAULT 'autorizada', substitute_key TEXT,
 UNIQUE(company_id, access_key)
);
CREATE INDEX IF NOT EXISTS idx_invoice_query ON invoices(company_id, competence, issued_at, status);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 access_key TEXT NOT NULL, event_type TEXT NOT NULL, event_nsu INTEGER, sha256 TEXT NOT NULL,
 processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(company_id, sha256)
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, details TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


def connect():
    c = sqlite3.connect(str(DB_PATH), timeout=30, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=30000')
    return c


def init_db():
    with connect() as c:
        c.executescript(SCHEMA)


@contextmanager
def transaction():
    c = connect()
    try:
        c.execute('BEGIN IMMEDIATE')
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def fetchall(query, args=()):
    with connect() as c:
        return [dict(r) for r in c.execute(query, args).fetchall()]


def fetchone(query, args=()):
    with connect() as c:
        row = c.execute(query, args).fetchone()
        return dict(row) if row else None


def audit(actor, action, details):
    with connect() as c:
        c.execute('INSERT INTO audit(actor,action,details) VALUES (?,?,?)', (actor, action, details))
