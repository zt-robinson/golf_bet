import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SportsDataIO API Configuration
    SPORTSDATA_API_KEY = os.getenv('SPORTSDATA_API_KEY')
    # CORRECTED v2 Base URL
    SPORTSDATA_BASE_URL = 'https://api.sportsdata.io/golf/v2/json/'
    
    # App Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DATABASE_PATH = 'golf_betting.db'
    
    # Virtual Betting Configuration
    INITIAL_VIRTUAL_BALANCE = 10000  # $10,000 starting balance
    MIN_BET_AMOUNT = 10  # Minimum bet $10
    MAX_BET_AMOUNT = 1000  # Maximum bet $1,000