from dotenv import load_dotenv
import os
from pybit.unified_trading import HTTP
import pandas as pd
import ta
import traceback
from time import sleep
load_dotenv()

api = os.getenv("api")
secret = os.getenv("secret")
account_type = os.getenv("accountType")


class Derivatives:
    def __init__(self):
        self.session = HTTP(
            api_key=api,
            api_secret=secret
        )
        acc_info = self.session.get_account_info()
        print("the margin mode is the following " + acc_info["result"]["marginMode"])
        # Configurations
        self.tp = 0.015 # Take Profit +1.5%
        self.sl = 0.05 # Stop Loss -5%
        self.timeframe = 15  # 15 minutes
        self.mode = 1  # 1 - Isolated, 0 - Cross
        self.leverage = 10
        self.qty = 50  # Amount of USDT for one order
        self.max_pos = 50

    def klines(self, symbol):
        """ Fetch historical market data (candlesticks) """
        
        if type(symbol) != str:
            return None

        try:
            resp = self.session.get_kline(
                category='linear',
                symbol=symbol,
                interval=self.timeframe,
                limit=50
            )['result']['list']

            
            resp = pd.DataFrame(resp)
            resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
            resp = resp.set_index('Time')
            resp = resp.astype(float)
            resp = resp[::-1]  # Reverse DataFrame order
            print(f"Klines for {symbol} obtained succsesfully ✅ ")
            return resp
        
        except Exception as err:
            print(f"⚠️ Error fetching klines (derivates): {err}")
            print(f"Error symbol {symbol} that")
            print(f"the symbol type is {type(symbol)}")
            sleep(60)
            traceback.print_exc()

            return None

    def klines_timeframe(self, symbol, timeframe):
        """ Fetch historical market data (candlesticks) """
        
        if type(symbol) != str:
            return None

        try:
            resp = self.session.get_kline(
                category='linear',
                symbol=symbol,
                interval=timeframe,
                limit=50
            )['result']['list']

            
            resp = pd.DataFrame(resp)
            resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
            resp = resp.set_index('Time')
            resp = resp.astype(float)
            resp = resp[::-1]  # Reverse DataFrame order
            print(f"Klines for {symbol} obtained succsesfully ✅ ")
            return resp
        
        except Exception as err:
            print(f"⚠️ Error fetching klines (derivates): {err}")
            print(f"Error symbol {symbol} that")
            print(f"the symbol type is {type(symbol)}")
            sleep(60)
            traceback.print_exc()

            return None

    def rsi_indicator(self, symbol, rsi_length=8):
        """Computes RSI (Relative Strength Index)."""
        kl = self.klines(symbol)

        if kl is None or len(kl) <= rsi_length:
            return None  # Not enough data
        
        price = kl["Close"]
        
        rsi = ta.momentum.RSIIndicator(price, window=rsi_length).rsi()
        
        return rsi
    
    def ma_env(self, symbol,  ma_length=20, envelope_pct=1.5):
        """Computes Moving Average Envelope (Upper & Lower Bands)."""
        kl = self.klines(symbol)

        if kl is None or len(kl) <= ma_length:
            return None, None, None  # Not enough data
        
        price = kl["Close"]
        
        ma = price.ewm(span=ma_length, adjust=False).mean()  # EMA Calculation
        upper_band = ma * (1 + envelope_pct / 100)  # Upper Envelope
        lower_band = ma * (1 - envelope_pct / 100)  # Lower Envelope
        
        return ma, upper_band, lower_band

    def macd_indicator(self, symbol, fast_length=12, slow_length=26, signal_length=9):

        """Computes MACD Line, Signal Line, and Histogram."""
        kl = self.klines(symbol)
        if kl is None or len(kl) <= slow_length:
            return None, None, None  # Not enough data
        
        price = kl["Close"]
        
        macd = ta.trend.MACD(price, window_fast=fast_length, window_slow=slow_length, window_sign=signal_length)
        
        macd_line = macd.macd()  # MACD Line
        signal_line = macd.macd_signal()  # Signal Line
        macd_histogram = macd.macd_diff()  # MACD Histogram
        
        return macd_line, signal_line, macd_histogram
        
    def atr_indicator(self, symbol, atr_length=14):
        """Computes ATR (Average True Range) value."""
        kl = self.klines(symbol)

        if kl is None or len(kl) <= atr_length:
            return None  # Not enough data

        atr = ta.volatility.average_true_range(
            high=kl["High"],
            low=kl["Low"],
            close=kl["Close"],
            window=atr_length
        )

        return atr

    def four_hour_min_max(self, symbol):
        kl = self.klines_timeframe(symbol, 240)
        if kl is None or kl.empty:
            return None
    
        try:
            # Convert index (ms) to UTC datetime
            kl = kl.copy()
            kl.index = pd.to_datetime(kl.index, unit="ms", utc=True)
    
            # First 4H candle of the current UTC day
            today_utc = pd.Timestamp.utcnow().normalize()
    
            first_candle = kl.loc[kl.index == today_utc]
    
            if first_candle.empty:
                return None
    
            high = float(first_candle["High"].iloc[0])
            low = float(first_candle["Low"].iloc[0])
    
            return high, low
    
        except Exception as err:
            print(f"⚠️ Error computing 4H high/low for {symbol}: {err}")
            traceback.print_exc()
            return None

        
        

    def trading_strategy_rsi_macd_flipped(self, symbol):

        kl = self.klines(symbol)
        if kl is None:
            return None
        
        self.over_bought = False
        self.over_sold = False
        rsi = None

        atr = self.atr_indicator(symbol)
        current_atr = atr.iloc[-1]
        avg_atr = atr[-20:].mean()
        
        if current_atr > 1.5 * avg_atr or current_atr < 0.5 * avg_atr:
            return 'none'
            
        macd_line, signal_line, macd_histogram   = self.macd_indicator(symbol)

        if(macd_line is not None and signal_line is not None):
            macd_cross_up = (macd_line.iloc[-2] < signal_line.iloc[-2]) and (macd_line.iloc[-1] > signal_line.iloc[-1])  
            macd_cross_down = (macd_line.iloc[-2] > signal_line.iloc[-2]) and (macd_line.iloc[-1] < signal_line.iloc[-1])  
            
            rsi = self.rsi_indicator(symbol)
            
        if(rsi is not None):    
            for i in range (10):
                if (rsi.iloc[-1*  (i+1)] > 79) :         # use this to check the previous 15 candles for rsi activation
                    self.over_bought = True
                    break
                elif (rsi.iloc[-1*  (i+1)] < 21) :         # use this to check the previous 15 candles for rsi activation
                    self.over_sold = True
                    break
                else:
                    self.over_bought = False
                    self.over_sold = False
       
        #Signal logic
        if self.over_sold and macd_cross_up: #and self.upper_env
            return 'down'
        elif self.over_bought and macd_cross_down: #and self.lower_env
            return 'up'

        return 'none'
        
    def trading_strategy_rsi_macd(self, symbol):

        kl = self.klines(symbol)
        if kl is None:
            return None
        
        self.over_bought = False
        self.over_sold = False
        rsi = None

        atr = self.atr_indicator(symbol)
        current_atr = atr.iloc[-1]
        avg_atr = atr[-20:].mean()
        
        if current_atr > 1.5 * avg_atr or current_atr < 0.5 * avg_atr:
            return 'none'
            
        macd_line, signal_line, macd_histogram   = self.macd_indicator(symbol)

        if(macd_line is not None and signal_line is not None):
            macd_cross_up = (macd_line.iloc[-2] < signal_line.iloc[-2]) and (macd_line.iloc[-1] > signal_line.iloc[-1])  
            macd_cross_down = (macd_line.iloc[-2] > signal_line.iloc[-2]) and (macd_line.iloc[-1] < signal_line.iloc[-1])  
            
            rsi = self.rsi_indicator(symbol)
            
        if(rsi is not None):    
            for i in range (10):
                if (rsi.iloc[-1*  (i+1)] >= 85) :         # use this to check the previous 15 candles for rsi activation
                    self.over_bought = True
                    break
                elif (rsi.iloc[-1*  (i+1)] <= 15) :         # use this to check the previous 15 candles for rsi activation
                    self.over_sold = True
                    break
                else:
                    self.over_bought = False
                    self.over_sold = False
       
        #Signal logic
        if self.over_sold and macd_cross_up: #and self.upper_env
            return 'up'
        elif self.over_bought and macd_cross_down: #and self.lower_env
            return 'down'

        return 'none'


    def trading_strategy_rsi_macd_short(self, symbol):

        kl = self.klines(symbol)
        if kl is None:
            return None
        
        self.over_bought = False
        self.over_sold = False
        rsi = None

        atr = self.atr_indicator(symbol)
        current_atr = atr.iloc[-1]
        avg_atr = atr[-20:].mean()
        
        if current_atr > 1.5 * avg_atr or current_atr < 0.5 * avg_atr:
            return 'none'
            
        macd_line, signal_line, macd_histogram   = self.macd_indicator(symbol)

        if(macd_line is not None and signal_line is not None):
            macd_cross_up = (macd_line.iloc[-2] < signal_line.iloc[-2]) and (macd_line.iloc[-1] > signal_line.iloc[-1])  
            macd_cross_down = (macd_line.iloc[-2] > signal_line.iloc[-2]) and (macd_line.iloc[-1] < signal_line.iloc[-1])  
            
            rsi = self.rsi_indicator(symbol)
            
        if(rsi is not None):    
            for i in range (10):
                if (rsi.iloc[-1*  (i+1)] > 79) :         # use this to check the previous 15 candles for rsi activation
                    self.over_bought = True
                    break
                elif (rsi.iloc[-1*  (i+1)] < 21) :         # use this to check the previous 15 candles for rsi activation
                    self.over_sold = True
                    break
                else:
                    self.over_bought = False
                    self.over_sold = False
       
        #Signal logic
        if self.over_bought and macd_cross_down: #and self.lower_env
            return 'down'

        return 'none'

    def trading_strategy_rsi_macd_long(self, symbol):

        kl = self.klines(symbol)
        if kl is None:
            return None
        
        self.over_bought = False
        self.over_sold = False
        rsi = None

        atr = self.atr_indicator(symbol)
        current_atr = atr.iloc[-1]
        avg_atr = atr[-20:].mean()
        
        if current_atr > 1.5 * avg_atr or current_atr < 0.5 * avg_atr:
            return 'none'
            
        macd_line, signal_line, macd_histogram   = self.macd_indicator(symbol)

        if(macd_line is not None and signal_line is not None):
            macd_cross_up = (macd_line.iloc[-2] < signal_line.iloc[-2]) and (macd_line.iloc[-1] > signal_line.iloc[-1])  
            macd_cross_down = (macd_line.iloc[-2] > signal_line.iloc[-2]) and (macd_line.iloc[-1] < signal_line.iloc[-1])  
            
            rsi = self.rsi_indicator(symbol)
            
        if(rsi is not None):    
            for i in range (10):
                if (rsi.iloc[-1*  (i+1)] > 79) :         # use this to check the previous 15 candles for rsi activation
                    self.over_bought = True
                    break
                elif (rsi.iloc[-1*  (i+1)] < 21) :         # use this to check the previous 15 candles for rsi activation
                    self.over_sold = True
                    break
                else:
                    self.over_bought = False
                    self.over_sold = False
       
        #Signal logic
        if self.over_sold and macd_cross_up: #and self.lower_env
            return 'up'

        return 'none'
    
    def simple_RSI_strat(self, symbol):
        
        kl = self.klines(symbol)
        if kl is None:
            return None

        atr = self.atr_indicator(symbol)
        current_atr = atr.iloc[-1]
        avg_atr = atr[-20:].mean()
        
        if current_atr > 1.5 * avg_atr or current_atr < 0.5 * avg_atr:
            return 'none'
        
        self.over_bought = False
        self.over_sold = False
        self.upper_env = False
        
        rsi = self.rsi_indicator(symbol)

        atr = self.atr_indicator(symbol)
        current_atr = atr.iloc[-1]
        avg_atr = atr[-20:].mean()
        
        if current_atr > 1.5 * avg_atr or current_atr < 0.5 * avg_atr:
            return 'none'
        
        if (rsi.iloc[-1] > 79) :         # use this to check the previous 15 candles for rsi activation
                self.over_bought = True
                
        elif (rsi.iloc[-1] < 21) :         # use this to check the previous 15 candles for rsi activation
                self.over_sold = True
        else:
                self.over_bought = False
                self.over_sold= False
    

        #Signal logic
        if self.over_sold : #and self.upper_env
            return 'up'
        if self.over_bought : #and self.lower_env
            return 'down'

        return 'none'






