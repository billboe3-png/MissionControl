from app.db.database import SessionLocal
from app.models.db.agent import Agent

db = SessionLocal()
print("=== AGENTS ===")
for a in db.query(Agent).all():
    print(a.id, a.name, a.status, "agent_id_type:", type(a.id))
print()
print("=== SSH/remote target related tables ===")
from sqlalchemy import inspect

insp = inspect(db.bind)
tables = insp.get_table_names()
print([t for t in tables if 'remote' in t.lower() or 'target' in t.lower() or 'ssh' in t.lower() or 'integration' in t.lower() or 'profile' in t.lower()])
print()
print("=== IntegrationProfiles / remote targets ===")
for t in tables:
    if any(k in t.lower() for k in ('remote', 'target', 'ssh', 'integration_profile')):
        try:
            from sqlalchemy import text
            cols = [c['name'] for c in insp.get_columns(t)]
            rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
            print(f"[{t}] cols={cols}")
            for r in rows:
                print("   ", r)
        except Exception as e:
            print(f"[{t}] err {e}")
db.close()
