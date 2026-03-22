import asyncio
import logging
from scheduler.scheduler import Scheduler
from config.db_config.database import init ; init(url_env="DATABASE_URL")
from utils.logger import setup_logger

# Setup logger for collectors main module
logger = setup_logger('collectors.main', level=20)

# Configure logging to reduce verbose SNMP logs
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and above
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress verbose SNMP library logs - ALL pysnmp related loggers
logging.getLogger('pysnmp').setLevel(logging.ERROR)
logging.getLogger('pyasn1').setLevel(logging.ERROR)
logging.getLogger('pysnmp.hlapi').setLevel(logging.ERROR)
logging.getLogger('pysnmp.carrier').setLevel(logging.ERROR)
logging.getLogger('pysnmp.proto').setLevel(logging.ERROR)
logging.getLogger('pysnmp.smi').setLevel(logging.ERROR)

# Suppress pyasn1 modules
logging.getLogger('pyasn1').setLevel(logging.ERROR)
logging.getLogger('pyasn1.type').setLevel(logging.ERROR)
logging.getLogger('pyasn1.codec').setLevel(logging.ERROR)

# Suppress asyncio debug logs
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Suppress urllib3 and requests
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Create a custom logger for collector health messages
collector_logger = logging.getLogger('nexora.collector')
collector_logger.setLevel(logging.INFO)

logger.info("="*50)
logger.info("NEXORA COLLECTORS STARTING UP")
logger.info("="*50)
logger.info("Database initialized successfully")

scheduler = Scheduler()
logger.info("Scheduler created, starting collection tasks...")

asyncio.run(scheduler.start())
