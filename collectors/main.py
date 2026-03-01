import asyncio
from scheduler.scheduler import Scheduler


scheduler = Scheduler()
asyncio.run(scheduler.start())