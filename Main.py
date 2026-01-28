import traceback
from dotenv import load_dotenv
import os
from helper import Bybit
from derivates import Derivatives  
import time
from time import sleep
import math
import datetime
from datetime import timezone
from datetime import date
import random

# Load environment variables from .env file
load_dotenv()

api = os.getenv("api")
secret = os.getenv("secret")
account_type = os.getenv("accountType")

class Main:
    def __init__(self):
        self.session = Bybit(api=api, secret=secret, accounttype=account_type, testing=False)
        self.strategy = Derivatives()  

        # Configurations
        self.mode = 1  # 1 - Isolated, 0 - Cross
        self.leverage = 1
        self.day = 0;
        
