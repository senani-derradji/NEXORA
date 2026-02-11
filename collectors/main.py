import time, asyncio
from collectors.scheduler.scheduler import Scheduler


scheduler = Scheduler()
asyncio.run(scheduler.start())