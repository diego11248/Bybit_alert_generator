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

    def valid_time(self, open_positions):
        curr = datetime.datetime.now(timezone.utc) # Use UTC instead of local time
        hour = curr.hour 
        minute = curr.minute
        self.day = curr.weekday()
        
        print(f"Current UTC hour: {curr}", flush=True)

        if(self.day == 5 or self.day == 6):
            #self.close_all(open_positions)
            print("Its the weekend")
            return False
            

        if hour > 21 or hour <= 14:                #edge hours for trading the last hour of trading, the first hour of trading

            if( hour == 0 and minute > 1 ):
                self.close_all(open_positions)
                print("Sleeping... Market is not open.")
                sleep(180)
                return False
            
            elif (hour > 21) or (hour < 14):
                #self.close_all(open_positions)
                print("Sleeping... Market is not open.")
                sleep(180)
                return False
                
            elif hour == 21 and minute <= 25:
                #self.close_all(open_positions)
                print("Sleeping... Market is not open.")
                sleep(180)
                return False

            

        if(hour >= 17 and hour < 19):                        #laggy time for trading (closed hours for the strategy)
            if (hour == 17 and minute >= 30):
                #self.close_all(open_positions)
                print("Sleeping... its lunch time")
                sleep(180)
                return False
            elif(hour > 17 and  hour < 19):
                #self.close_all(open_positions)
                print("Sleeping... its lunch time")
                sleep(180)
                return False
                
           
                
              
        else:
            print("Market is open, running bot")
            return True

        
