from app.db.database import SessionLocal
from app.models.db.agent_command import AgentCommand

db = SessionLocal()
print("=== veeam server rows ===")
from sqlalchemy import text

rows = db.execute(text("SELECT id, name, agent_id, target_id, rest_url, ssh_host, ssh_port, ssh_username, enabled FROM veeam_backup_servers")).fetchall()
for r in rows: print(r)
print()
print("=== recent agent commands (last 15) ===")
for c in db.query(AgentCommand).order_by(AgentCommand.id.desc()).limit(15).all():
    print(c.id, "agent", c.agent_id, c.command_type, c.status, "exit", c.exit_code, (c.stderr or "")[:90])
db.close()