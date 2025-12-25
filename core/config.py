import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # JIRA
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")
    
    # X-Ray
    XRAY_CLIENT_ID = os.getenv("XRAY_CLIENT_ID")
    XRAY_CLIENT_SECRET = os.getenv("XRAY_CLIENT_SECRET")
    
    # App
    BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api")
    
    @classmethod
    def validate(cls):
        """Validates that essential config is present."""
        missing = [k for k, v in cls.__dict__.items() if not k.startswith("__") and v is None]
        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")
