# promptscribe/db.py
import os
import json
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from promptscribe.config import CONFIG

# --- Step 1: Determine safe DB path ---
try:
    raw_path = CONFIG["paths"].get("database", "")
except Exception:
    raw_path = ""

# Fallback: local project data folder
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

if not raw_path or not os.path.isabs(raw_path):
    DB_PATH = os.path.join(data_dir, "promptscribe.db")
else:
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

def list_entries(limit=50):
    db = SessionLocal()
    try:
        q = db.query(SessionEntry).order_by(SessionEntry.start_ts.desc()).limit(limit)
        rows = q.all()
        if not rows:
            print("No sessions indexed.")
        for r in rows:
            start = r.start_ts if r.start_ts else 0
            print(f"{r.id}\t{r.name}\t{r.file}\t{start}")
    finally:
        db.close()
