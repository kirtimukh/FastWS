import os
from dotenv import load_dotenv


load_dotenv()
APP_ID = os.getenv("APP_ID", f"pid-{os.getpid()}")
