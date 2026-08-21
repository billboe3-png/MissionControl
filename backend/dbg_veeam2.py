from app.db.database import SessionLocal
from app.models.db.agent_command import AgentCommand

db = SessionLocal()
print("=== veeam server rows ===")
from sqlalchemy import text

try:
    rows = db.execute(text("SELECT id, name, agent_id, target_id, base_url, legacy_ssh_host, legacy_ssh_username, enabled, last_sync_status, last_sync_error FROM veeam_backup_servers")).fetchall()
    for r in rows: print(r)
except Exception as e:
    print("err", e)
print()
print("=== recent agent commands (last 12) ===")
for c in db.query(AgentCommand).order_by(AgentCommand.id.desc()).limit(12).all():
    print(c.id, c.agent_id, c.command_type, c.status, c.exit_code, (c.stderr or "")[:80])
db.close()