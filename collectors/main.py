import asyncio
from scheduler.scheduler import Scheduler
from config.db_config.database import init ; init(url_env="DATABASE_URL")

scheduler = Scheduler()
asyncio.run(scheduler.start())