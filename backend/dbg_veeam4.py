from sqlalchemy import inspect

from app.db.database import engine

i = inspect(engine)
print("=== veeam_backup_servers columns ===")
for c in i.get_columns('veeam_backup_servers'):
    print(c['name'], c['type'])
from sqlalchemy import text

from app.db.database import SessionLocal

db = SessionLocal()
print()
print("=== rows ===")
rows = db.execute(text("SELECT * FROM veeam_backup_servers")).fetchall()
for r in rows: print(r)
db.close()