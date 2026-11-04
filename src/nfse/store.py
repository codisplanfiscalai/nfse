"""SQLite persistence, source preservation and per-company NSU cursor."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sqlite3
from .settings import ensure_data_dir

SCHEMA = '''
CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'admin', active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 csrf_hash TEXT NOT NULL, expires_at INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS companies (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, identifier TEXT NOT NULL UNIQUE,
 active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS certificates (
 id INTEGER PRIMARY KEY, label TEXT NOT NULL, identity TEXT, serial_number TEXT,
 subject TEXT, expires_at TEXT, encrypted_pfx BLOB NOT NULL,
 encrypted_password BLOB NOT NULL, sha256 TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS company_certificates (
 company_id INTEGER NOT NULL REFERENCES companies(id), certificate_id INTEGER NOT NULL REFERENCES certificates(id),
 PRIMARY KEY(company_id, certificate_id)
);
CREATE TABLE IF NOT EXISTS sync_cursors (
 company_id INTEGER NOT NULL REFERENCES companies(id), certificate_id INTEGER NOT NULL REFERENCES certificates(id),
 last_nsu INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
 PRIMARY KEY(company_id, certificate_id)
);
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(id),
 nsu INTEGER NOT NULL, access_key TEXT NOT NULL, document_type TEXT NOT NULL,
 event_type TEXT, generated_at TEXT, issuer_identifier TEXT, issuer_name TEXT,
 recipient_identifier TEXT, recipient_name TEXT, invoice_number TEXT,
 issued_on TEXT, competence_on TEXT, service_code TEXT, service_description TEXT,
 service_cents INTEGER NOT NULL DEFAULT 0, net_cents INTEGER NOT NULL DEFAULT 0,
 iss_cents INTEGER NOT NULL DEFAULT 0, iss_withheld_cents INTEGER NOT NULL DEFAULT 0,
 irrf_cents INTEGER NOT NULL DEFAULT 0, inss_cents INTEGER NOT NULL DEFAULT 0,
 pcc_cents INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'ATIVA',
 xml_sha256 TEXT NOT NULL, xml_content BLOB NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(company_id, nsu)
);
CREATE INDEX IF NOT EXISTS idx_documents_report ON documents(company_id, document_type, competence_on, issued_on);
CREATE INDEX IF NOT EXISTS idx_documents_key ON documents(company_id, access_key);
CREATE TABLE IF NOT EXISTS sync_runs (
 id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL, certificate_id INTEGER NOT NULL,
 started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL,
 inserted INTEGER NOT NULL DEFAULT 0, fetched INTEGER NOT NULL DEFAULT 0,
 diagnostic TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL,
 target TEXT NOT NULL, at TEXT NOT NULL, metadata TEXT
);
CREATE TABLE IF NOT EXISTS api_tokens (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
 user_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 expires_at INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
'''


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else ensure_data_dir() / 'nfse.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=30000')
        conn.execute('PRAGMA journal_mode=WAL')
        return conn

    def init(self):
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.execute('COMMIT')
        except BaseException:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()

    def row(self, sql, args=()):
        with self.connect() as conn:
            x = conn.execute(sql, args).fetchone()
            return dict(x) if x else None

    def rows(self, sql, args=()):
        with self.connect() as conn:
            return [dict(x) for x in conn.execute(sql, args)]

    def audit(self, actor: str, action: str, target: str, metadata: str = ''):
        with self.transaction() as conn:
            conn.execute('INSERT INTO audit_log(actor,action,target,at,metadata) VALUES(?,?,?,?,?)',
                         (actor, action, target, now(), metadata[:2000]))

    def apply_documents(self, company: int, certificate: int, records: list[dict], *, advance: bool = True):
        """Atomic import: advancing NSU and preserving XML occur in the same transaction."""
        inserted = 0
        with self.transaction() as conn:
            cursor = conn.execute('SELECT last_nsu FROM sync_cursors WHERE company_id=? AND certificate_id=?',
                                  (company, certificate)).fetchone()
            last = int(cursor['last_nsu']) if cursor else 0
            for d in records:
                nsu = int(d['nsu'])
                if nsu < 1:
                    raise ValueError('Invalid NSU')
                fields = ('company_id','nsu','access_key','document_type','event_type','generated_at',
                          'issuer_identifier','issuer_name','recipient_identifier','recipient_name','invoice_number',
                          'issued_on','competence_on','service_code','service_description','service_cents','net_cents',
                          'iss_cents','iss_withheld_cents','irrf_cents','inss_cents','pcc_cents','xml_sha256',
                          'xml_content','created_at')
                vals = {'company_id': company, 'created_at': now(), **d}
                cursor_result = conn.execute(
                    f'INSERT OR IGNORE INTO documents({",".join(fields)}) VALUES({",".join("?" for _ in fields)})',
                    tuple(vals.get(f) for f in fields))
                inserted += cursor_result.rowcount
                last = max(last, nsu)
            if advance:
                conn.execute('INSERT INTO sync_cursors(company_id,certificate_id,last_nsu,updated_at) VALUES(?,?,?,?) '
                             'ON CONFLICT(company_id,certificate_id) DO UPDATE SET '
                             'last_nsu=MAX(last_nsu,excluded.last_nsu),updated_at=excluded.updated_at',
                             (company, certificate, last, now()))
            # Re-evaluate status even when the cancellation event arrives before the invoice.
            conn.execute("""UPDATE documents SET status=CASE
                 WHEN EXISTS(SELECT 1 FROM documents e WHERE e.company_id=documents.company_id
                             AND e.access_key=documents.access_key AND e.document_type='EVENTO'
                             AND e.event_type='CANCELAMENTO_POR_SUBSTITUICAO') THEN 'SUBSTITUIDA'
                 WHEN EXISTS(SELECT 1 FROM documents e WHERE e.company_id=documents.company_id
                             AND e.access_key=documents.access_key AND e.document_type='EVENTO'
                             AND e.event_type IN ('CANCELAMENTO','CANCELAMENTO_DEFERIDO_ANALISE_FISCAL','CANCELAMENTO_POR_OFICIO')) THEN 'CANCELADA'
                 ELSE 'ATIVA' END WHERE company_id=? AND document_type='NFSE'""", (company,))
        return inserted, last
