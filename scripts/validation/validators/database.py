import os

from validators import BaseValidator


class DatabaseValidator(BaseValidator):
    name = "database"

    def run(self, config: dict):
        self._check("postgres_connectivity", lambda: self._check_connectivity(), critical=True)
        self._check("schema_exists", lambda: self._check_schema(), critical=True)
        self._check("alembic_version", lambda: self._check_alembic_version(), critical=False)
        self._check("table_count", lambda: self._check_table_count(), critical=False)
        self._check("required_tables", lambda: self._check_required_tables(), critical=False)
        return self.result()

    def _get_conn_params(self):
        return {
            "host": os.environ.get("POSTGRES_HOST", "localhost"),
            "port": int(os.environ.get("POSTGRES_PORT", 5432)),
            "user": os.environ.get("POSTGRES_USER", "postgres"),
            "password": os.environ.get("POSTGRES_PASSWORD", ""),
            "dbname": os.environ.get("POSTGRES_DB", "missioncontrol"),
        }

    def _connect(self):
        import psycopg
        return psycopg.connect(**self._get_conn_params())

    def _check_connectivity(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                assert cur.fetchone()[0] == 1
        finally:
            conn.close()
        return True

    def _check_schema(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
                )
                exists = cur.fetchone()[0]
                if not exists:
                    raise RuntimeError("users table does not exist")
        finally:
            conn.close()
        return True

    def _check_alembic_version(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("No alembic version found")
                return row[0]
        finally:
            conn.close()

    def _check_table_count(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                count = cur.fetchone()[0]
                if count <= 20:
                    raise RuntimeError(f"Expected >20 tables, found {count}")
                return count
        finally:
            conn.close()

    def _check_required_tables(self):
        required = ["users", "companies", "agents", "agent_commands", "playbooks"]
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                tables = {row[0] for row in cur.fetchall()}
                missing = [t for t in required if t not in tables]
                if missing:
                    raise RuntimeError(f"Missing tables: {', '.join(missing)}")
        finally:
            conn.close()
        return True
