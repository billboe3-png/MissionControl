from sqlalchemy import text

from app.db.database import SessionLocal

db = SessionLocal()
r = db.execute(text("SELECT id, status, last_error, last_sync_at, version, edition, data_source, last_diagnostic FROM veeam_backup_servers")).fetchall()
print(r[0] if r else "none")
db.close()