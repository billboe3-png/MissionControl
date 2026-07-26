import os

from validators import BaseValidator


class RedisValidator(BaseValidator):
    name = "redis"

    def run(self, config: dict):
        self._check("redis_connectivity", lambda: self._check_connectivity(), critical=True)
        self._check("redis_ping", lambda: self._check_ping(), critical=True)
        self._check("redis_set_get", lambda: self._check_set_get(), critical=False)
        self._check("redis_memory", lambda: self._check_memory(), critical=False)
        return self.result()

    def _get_client(self):
        import redis as redis_lib
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", 6379))
        return redis_lib.from_url(f"redis://{host}:{port}")

    def _check_connectivity(self):
        r = self._get_client()
        try:
            r.ping()
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Redis: {e}")
        return True

    def _check_ping(self):
        r = self._get_client()
        if not r.ping():
            raise RuntimeError("Redis ping returned False")
        return True

    def _check_set_get(self):
        r = self._get_client()
        key = "mc_validation_test"
        r.set(key, "1", ex=10)
        val = r.get(key)
        r.delete(key)
        if val != b"1":
            raise RuntimeError(f"Set/get mismatch: expected b'1', got {val}")

    def _check_memory(self):
        r = self._get_client()
        info = r.info("memory")
        used = info.get("used_memory_human", "unknown")
        return used
