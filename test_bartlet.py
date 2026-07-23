"""Benchmark cold vs warm cache timing."""
import os, sys, time, asyncio
os.chdir('/app')
sys.path.insert(0, '/app')
from app.core import config
settings = config.get_settings()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
from app.services.veeam_service import veeam_service

async def test():
    db = Session()

    # First call - cold cache (db_type detection + provider creation)
    t0 = time.time()
    result = await veeam_service.get_job_stats_daily(days=7, db=db)
    t1 = time.time()
    print(f"COLD CACHE (first call): {t1-t0:.1f}s  jobs={result['count']}  servers={result['server_names']}")

    # Second call - warm cache (should be fast)
    t0 = time.time()
    result = await veeam_service.get_job_stats_daily(days=7, db=db)
    t1 = time.time()
    print(f"WARM CACHE (second call): {t1-t0:.1f}s  jobs={result['count']}")

    # Third call - sessions
    t0 = time.time()
    result = await veeam_service.get_sessions(db=db)
    t1 = time.time()
    print(f"SESSIONS (warm): {t1-t0:.1f}s  sessions={result['count']}")

    # Fourth call - session stats
    t0 = time.time()
    result = await veeam_service.get_session_stats(db=db)
    t1 = time.time()
    print(f"SESSION STATS (warm): {t1-t0:.1f}s  stats={result['count']}")

    db.close()

asyncio.run(test())
