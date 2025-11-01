# promptscribe/db.py
import os
import json
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from promptscribe.config import CONFIG

# --- Step 1: Determine safe DB path ---
try:
    raw_path = CONFIG["paths"]["database"]
except Exception:
    raw_path = os.path.expanduser("~/Tools/promptscribe/data/database/vault.db")

DB_PATH = raw_path
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# --- Step 2: Configure SQLAlchemy ---
engine = sa.create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# --- Step 3: Tables ---
class SessionEntry(Base):
    __tablename__ = "sessions"
    id = sa.Column(sa.String, primary_key=True, index=True)
    name = sa.Column(sa.String)
    start_ts = sa.Column(sa.Float)
    end_ts = sa.Column(sa.Float, nullable=True)
    file = sa.Column(sa.String)

class AnalysisEntry(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.String, primary_key=True, index=True)
    session_ids = sa.Column(sa.String)
    summary = sa.Column(sa.Text)
    file = sa.Column(sa.String)

# --- Step 4: Utilities ---
def init_db():
    print(f"Initializing database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)

def insert_session(meta_path):
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    db = SessionLocal()
    try:
        entry = SessionEntry(
            id=meta["session_id"],
            name=meta.get("name"),
            start_ts=meta.get("start_ts"),
            end_ts=meta.get("end_ts"),
            file=meta.get("file"),
        )
        db.merge(entry)
        db.commit()
    finally:
        db.close()

# --- Enhanced listing and cleanup ---
def list_entries(limit=50, show_missing=False):
    """List recent session entries."""
    db = SessionLocal()
    try:
        q = db.query(SessionEntry).order_by(SessionEntry.start_ts.desc()).limit(limit)
        rows = q.all()
        if not rows:
            print("No sessions indexed.")
            return

        for r in rows:
            file_exists = bool(r.file and os.path.exists(r.file))
            marker = "" if file_exists else " [MISSING]"
            if file_exists or show_missing:
                start = r.start_ts if r.start_ts else 0
                print(f"{r.id}\t{r.name or ''}\t{r.file or ''}\t{start}{marker}")
    finally:
        db.close()

def clean_orphans(remove=False):
    """Find DB entries whose log files are missing."""
    db = SessionLocal()
    orphans = []
    try:
        q = db.query(SessionEntry).all()
        for e in q:
            if not e.file or not os.path.exists(e.file):
                orphans.append({
                    "id": e.id,
                    "name": e.name,
                    "file": e.file
                })
                if remove:
                    db.delete(e)
        if remove and orphans:
            db.commit()
    finally:
        db.close()
    return orphans
