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
        self.possible_trades = []

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

        if hour > 21 or hour < 12:                #edge hours for trading the last hour of trading, the first hour of trading
           
            print("Sleeping, if traders are not working you shouldnt either")
            sleep(180)
            return False
            
        else:
            print("Market is open, running bot")
            return True


     def run(self):  
        while True:
            
            
            
            try:
                symbols = self.session.get_tickers() 
                random.shuffle(symbols)
                balance = self.session.get_balance()
                prev_balance = balance
                positions = self.session.get_positions()  # Retrieve all open positions
                
                
                
                print(f'💰 Balance: {round(balance, 3)} USDT')
                print(f'📊 Open Positions: {len(positions)}')

                # Convert positions to dictionary for easy lookup

                open_positions = {pos["symbol"]: pos["side"] for pos in positions}  # { "BTCUSDT": "Buy" }
                
                


                for symbol in symbols:

                    if(not self.valid_time(open_positions)): #If time is not valid skip
                        break

                    if len(open_positions) >= self.max_positions: #If max positions are open and the assest is not open then skip
                        if symbol not in open_positions:
                            continue

                    signal = self.strategy.trading_strategy_rsi_macd_short(symbol)  
                    
                    if signal == "none":
                        print(f"⏳ No signal generated")
                        continue
                        
                    if(self.bad_coin(symbol)):
                        print("This is a single day coin, skip")
                        continue

                    # Check if there's an opposite position open
                    prev_balance = balance
                    
                    if symbol in open_positions:
                        current_side = open_positions[symbol]  # "Buy" or "Sell"

                        if signal == "up" and current_side == "Sell":
                            print(f'🚀 Closing short for {symbol}')
                            continue

                        elif signal == "down" and current_side == "Buy":
                            print(f'📉 Closing long for {symbol}')
                            continue
                        
                        

                            

                    positions = self.session.get_positions()  # Retrieve all open positions to check for changes
                    self.evaluate_market(positions)
                    
                    # Stop from opening new trades if at limit or market is not good
                    if len(open_positions) >= self.max_positions or not self.optimal_market:
                        print("The market is not optimal ")
                        continue  
                    else: 
                        print("The market is optimal, checking to buy")

                    # Open new trade only if no position exists

                    if signal == "up":
                        print(f'🚀 BUY: {symbol}')
                        
                    elif signal == "down":
                        print(f'📉 SELL: {symbol}')
                       
                    sleep(1)  

                print("⏳ Waiting 60 sec before next check...")
                sleep(60)  

            except Exception as err:
                print(f"⚠️ Error: {err}")
                traceback.print_exc() 
                sleep(30)  

# 🚀 Start the bot
if __name__ == "__main__":
    bot = Main()
    #print(bot.session.get_tickers()  )
    bot.run()
