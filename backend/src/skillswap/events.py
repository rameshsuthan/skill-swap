import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

class EventStore:
    """Allowlisted telemetry only: never persist prompts, raw errors, or tool payloads."""
    def __init__(self, path: Path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS events(run_id TEXT, sequence INTEGER, payload TEXT, PRIMARY KEY(run_id,sequence))')
    def connection(self):
        db=sqlite3.connect(self.path,timeout=5)
        db.execute('PRAGMA journal_mode=WAL')
        return db
    def append(self, run_id, *, agent, server, tool, status, duration_ms=0, summary=None):
        safe={k:v for k,v in (summary or {}).items() if k in {'count','code','revision','model_calls'} and isinstance(v,(int,bool))}
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            seq=db.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM events WHERE run_id=?',(run_id,)).fetchone()[0]
            event=dict(sequence=seq,timestamp=datetime.now(timezone.utc).isoformat(),agent=agent,server=server,tool=tool,status=status,duration_ms=round(duration_ms),summary=safe)
            db.execute('INSERT INTO events VALUES(?,?,?)',(run_id,seq,json.dumps(event)))
        return seq
    def list_after(self, run_id, sequence):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT payload FROM events WHERE run_id=? AND sequence>? ORDER BY sequence',(run_id,sequence))]
