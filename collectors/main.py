import asyncio
from scheduler.scheduler import Scheduler
from config.db_config.database import init_db ; init_db()

scheduler = Scheduler()
asyncio.run(scheduler.start())