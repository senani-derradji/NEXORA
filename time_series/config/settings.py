import os
from dotenv import load_dotenv

load_dotenv()

class TSBS_INFO:
    URL = os.getenv("TSBS_URL")
    TOKEN = os.getenv("TSBS_TOKEN")
    ORGANIZATION = os.getenv("TSBS_ORGANIZATION")
    BUCKET = os.getenv("TSBS_BUCKET")

    RAW_RETENTION = os.getenv("TSBS_RAW_RETENTION") or "7d"
    PROCESSED_RETENTION = os.getenv("TSBS_PROCESSED_RETENTION") or "30d"