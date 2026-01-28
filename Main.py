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
        self.tp = 0.03 # Take profit 3.5%
        self.sl = 0.09  # Stop loss 2.5%
        self.sl_multiplier = 2.0 #multiplier for ATR
        self.tp_multiplier =  6 #multiplier for ATR
        self.trail_active = 2.4 #activation multiplier for trailing
        self.trail_dist = 1.2 #distance multipplier for trailing
        self.mode = 1  # 1 - Isolated, 0 - Cross
        self.leverage = 1
        self.qty = 5  # Quantity of USDT to be traded
        self.risk_percentage = 0.03
        self.max_positions =  min(math.floor(1/self.risk_percentage), 25)  # Maximum open trades
        self.percentual_gain = []
        self.optimal_market = True
        self.losing_streak = 0
        self.day = 0;
        
