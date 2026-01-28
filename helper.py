
from pybit.unified_trading import HTTP
import pandas as pd
import traceback
from time import sleep
import requests


class Bybit():

    def __init__(self, api, secret, accounttype, testing = False):
        self.api = api
        self.secret = secret
        self.accountType = accounttype
        self.session = HTTP(api_key=self.api, api_secret=self.secret, testnet = testing )

    def get_balance(self):
        try:
            resp = self.session.get_wallet_balance(accountType=self.accountType, coin="USDT", recv_window=40000)['result']['list'][0]['coin'][0]['walletBalance']
            resp = round(float(resp), 3)
            return resp
        except Exception as err:    	        
            print(err)

    def get_positions(self):
        try:
            resp = self.session.get_positions(
                category='linear',
                settleCoin='USDT',
                recv_window = 40000
            )['result']['list']
            pos = []
            for elem in resp:
                info = {"symbol" : elem['symbol'], "side" :elem['side'], "avgPrice": elem["avgPrice"], "markPrice" : elem["markPrice"]}
                pos.append(info)
            return pos
        except Exception as err:
            print(err)

    def get_last_pnl(self, limit=50):
        try:
            resp = self.session.get_closed_pnl(category="linear", limit=limit, recv_window=40000)['result']['list']
            pnl = 0
            for elem in resp:
                pnl += float(elem['closedPnl'])
            return round(pnl, 4)
        except Exception as err:
            print(err)

    def get_current_pnl(self):
        try:
            resp = self.session.get_positions(
                category="linear",
                settleCoin="USDT",
                recv_window=10000
            )['result']['list']
            pnl = 0
            for elem in resp:
                pnl += float(elem['unrealisedPnl'])
            return round(pnl, 4)
        except Exception as err:
            print(err)

    def get_tickers(self):
        try:
            resp = self.session.get_tickers(category="linear", recv_window=10000)['result']['list']
            symbols = []
            for elem in resp:
                if 'USDT' in elem['symbol'] and not 'USDC' in elem['symbol']:
                    symbols.append(elem['symbol'])
            return symbols
        except Exception as err:
            print(err)

    def klines(self, symbol, timeframe = 15, limit=500):
        
        try:
            resp = self.session.get_kline(
                category='linear',
                symbol=symbol,
                interval=timeframe,
                limit=limit,
                recv_window=7000
            )['result']['list']
            resp = pd.DataFrame(resp)
            resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
            resp = resp.set_index('Time')
            resp = resp.astype(float)
            resp = resp[::-1]


            return resp
        except Exception as err:
            print(f"⚠️ Error fetching klines (Helper): {err}")
            

    def get_price(self, symbol):
        tickers = self.session.get_tickers(category = "linear", symbol = symbol)
        last_price = tickers["result"]["list"][0]["lastPrice"]
        return float(last_price)

    def get_precisions(self, symbol):
        try:
            resp = self.session.get_instruments_info(
                category='linear',
                symbol=symbol,
                recv_window=10000
            )['result']['list'][0]
            price = resp['priceFilter']['tickSize']
            if '.' in price:
                price = len(price.split('.')[1])
            else:
                price = 0
            qty = resp['lotSizeFilter']['qtyStep']
            if '.' in qty:
                qty = len(qty.split('.')[1])
            else:
                qty = 0
            return price, qty
        except Exception as err:
            print(err)

    def get_max_leverage(self, symbol):
        try:
            resp = self.session.get_instruments_info(
                category="linear",
                symbol=symbol,
                recv_window=10000
            )['result']['list'][0]['leverageFilter']['maxLeverage']
            return float(resp)
        except Exception as err:
            print(err)

    def set_mode(self, symbol, mode=1, leverage=10):
        
        try:
            resp = self.session.switch_margin_mode(
                category= 'linear',
                symbol=symbol,
                tradeMode=int(mode),
                buyLeverage=str(leverage),
                sellLeverage=str(leverage),
                recv_window=100000
            )
            if resp['retMsg'] == 'OK':
                if mode == 1:
                    print(f'[{symbol}] Changed margin mode to ISOLATED')
                if mode == 0:
                    print(f'[{symbol}] Changed margin mode to CROSS')
        except Exception as err:
            if '110026' in str(err):
                print(f'[{symbol}] Margin mode is Not changed')
            else:
                print(err)

    def set_leverage(self, symbol, leverage=10):
        try:
            resp = self.session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage),
                recv_window=10000
            )
            if resp['retMsg'] == 'OK':
                print(f'[{symbol}] Changed leverage to {leverage}')
        except Exception as err:
            if '110043' in str(err):
                print(f'[{symbol}] Leverage is Not changed')
            else:
                print(err)

    def place_order_market(self, symbol, side, mode, leverage, qty=10, tp=0.012, sl=0.009):
        #self.set_mode(symbol, mode, leverage)
        sleep(0.5)
        self.set_leverage(symbol, leverage)
        sleep(0.5)
        price_precision = self.get_precisions(symbol)[0]
        qty_precision = self.get_precisions(symbol)[1]
        mark_price = self.session.get_tickers(
            category='linear',
            symbol=symbol, recv_window=10000
        )['result']['list'][0]['markPrice']
        mark_price = float(mark_price)
        print(f'Placing {side} order for {symbol}. Mark price: {mark_price}')
        order_qty = round(qty / mark_price, qty_precision)
        sleep(2)
        if side == 'buy':
            try:
                tp_price = round(mark_price + mark_price * tp, price_precision)
                sl_price = round(mark_price - mark_price * sl, price_precision)
                resp = self.session.place_order(
                    category='linear',
                    symbol=symbol,
                    side='Buy',
                    orderType='Market',
                    qty=order_qty,
                    takeProfit=tp_price,
                    stopLoss=sl_price,
                    tpTriggerBy='MarkPrice',
                    slTriggerBy='MarkPrice', recv_window=10000
                )
                print(resp['retMsg'])
            except Exception as err:
                print(err)

        if side == 'sell':
            try:
                tp_price = round(mark_price - mark_price * tp, price_precision)
                sl_price = round(mark_price + mark_price * sl, price_precision)
                resp = self.session.place_order(
                    category='linear',
                    symbol=symbol,
                    side='Sell',
                    orderType='Market',
                    qty=order_qty,
                    takeProfit=tp_price,
                    stopLoss=sl_price,
                    tpTriggerBy='MarkPrice',
                    slTriggerBy='MarkPrice', recv_window=10000
                )
                print(resp['retMsg'])
            except Exception as err:
                print(err)
                
    def place_order_market_trailing(self, symbol, side, mode, leverage, qty=10, tp=0.012, sl=0.009, trail_percent=0.006, activation_percent=0.005):
    #self.set_mode(symbol, mode, leverage)
        sleep(0.5)
        self.set_leverage(symbol, leverage)
        sleep(0.5)
        price_precision = self.get_precisions(symbol)[0]
        qty_precision = self.get_precisions(symbol)[1]
        mark_price = self.session.get_tickers(
            category='linear',
            symbol=symbol, recv_window=10000
        )['result']['list'][0]['markPrice']
        mark_price = float(mark_price)
        print(f'Placing {side} order for {symbol}. Mark price: {mark_price}')
        order_qty = round(qty / mark_price, qty_precision)
        sleep(2)
        
        # Calculate trailing parameters
        trail_offset = round(mark_price * trail_percent, price_precision)
        
        if side == 'buy':
            try:
                tp_price = round(mark_price + mark_price * tp, price_precision)
                sl_price = round(mark_price - mark_price * sl, price_precision)
                activation_price = round(mark_price + mark_price * activation_percent, price_precision)
                
                resp = self.session.place_order(
                    category='linear',
                    symbol=symbol,
                    side='Buy',
                    orderType='Market',
                    qty=order_qty,
                    takeProfit=tp_price,
                    stopLoss=sl_price,
                    tpTriggerBy='MarkPrice',
                    slTriggerBy='MarkPrice', recv_window=10000
                )
                print(resp['retMsg'])
                
                # Set trailing stop after market order
                if resp['retCode'] == 0:
                    sleep(3)  # Wait for market order to fill
                    trailing_resp = self.session.set_trading_stop(
                        category='linear',
                        symbol=symbol,
                        positionIdx=0,
                        trailingStop=str(trail_offset),
                        activePrice=str(activation_price),
                        tpslMode='Full'
                    )
                    print(f"Trailing stop result: {trailing_resp['retMsg']}")
                    
            except Exception as err:
                print(err)
                
        if side == 'sell':
            try:
                tp_price = round(mark_price - mark_price * tp, price_precision)
                sl_price = round(mark_price + mark_price * sl, price_precision)
                activation_price = round(mark_price - mark_price * activation_percent, price_precision)
                
                resp = self.session.place_order(
                    category='linear',
                    symbol=symbol,
                    side='Sell',
                    orderType='Market',
                    qty=order_qty,
                    takeProfit=tp_price,
                    stopLoss=sl_price,
                    tpTriggerBy='MarkPrice',
                    slTriggerBy='MarkPrice', recv_window=10000
                )
                print(resp['retMsg'])
                
                # Set trailing stop after market order
                if resp['retCode'] == 0:
                    sleep(3)  # Wait for market order to fill
                    trailing_resp = self.session.set_trading_stop(
                        category='linear',
                        symbol=symbol,
                        positionIdx=0,
                        trailingStop=str(trail_offset),
                        activePrice=str(activation_price),
                        tpslMode='Full'
                    )
                    print(f"Trailing stop result: {trailing_resp['retMsg']}")
                    
            except Exception as err:
                print(err)
        

    def place_order_limit(self, symbol, side, mode, leverage, qty=10, tp=0.012, sl=0.009):
        self.set_mode(symbol, mode, leverage)
        sleep(0.5)
        self.set_leverage(symbol, leverage)
        sleep(0.5)
        price_precision = self.get_precisions(symbol)[0]
        qty_precision = self.get_precisions(symbol)[1]
        limit_price = self.session.get_tickers(
            category='linear',
            symbol=symbol
        )['result']['list'][0]['lastPrice']
        limit_price = float(limit_price)
        print(f'Placing {side} order for {symbol}. Limit price: {limit_price}')
        order_qty = round(qty / limit_price, qty_precision)
        self.sleep(2)
        if side == 'buy':
            try:
                tp_price = round(limit_price + limit_price * tp, price_precision)
                sl_price = round(limit_price - limit_price * sl, price_precision)
                resp = self.session.place_order(
                    category='linear',
                    symbol=symbol,
                    side='Buy',
                    orderType='Limit',
                    price= limit_price,
                    qty=order_qty,
                    takeProfit=tp_price,
                    stopLoss=sl_price,
                    tpTriggerBy='MarkPrice',
                    slTriggerBy='MarkPrice'
                )
                print(resp['retMsg'])
            except Exception as err:
                print(err)

        if side == 'sell':
            try:
                tp_price = round(limit_price - limit_price * tp, price_precision)
                sl_price = round(limit_price + limit_price * sl, price_precision)
                resp = self.session.place_order(
                    category='linear',
                    symbol=symbol,
                    side='Sell',
                    orderType='Limit',
                    price=limit_price,
                    qty=order_qty,
                    takeProfit=tp_price,
                    stopLoss=sl_price,
                    tpTriggerBy='MarkPrice',
                    slTriggerBy='MarkPrice'
                )
                print(resp['retMsg'])
            except Exception as err:
                print(err)

    def close_position_market(self, symbol):
        """Closes an open position for the given symbol using a market order."""
        
        # Step 1: Get all open positions
        try:
            positions = self.session.get_positions(
                category='linear',
                settleCoin='USDT',
                recv_window=10000
            )['result']['list']

            # Step 2: Find the position for the given symbol
            position = next((p for p in positions if p["symbol"] == symbol), None)

            if not position:
                print(f'⚠️ No open position found for {symbol}')
                return

            # Step 3: Extract position details
            side = position["side"]  # "Buy" or "Sell"
            qty = float(position["size"])  # Position size
            if qty == 0:
                print(f'⚠️ Position size for {symbol} is 0. No action taken.')
                return

            # Step 4: Get market price & precision values
            price_precision, qty_precision = self.get_precisions(symbol)
            mark_price = float(self.session.get_tickers(
                category='linear',
                symbol=symbol, recv_window=10000
            )['result']['list'][0]['markPrice'])

            # Step 5: Determine opposite order side to close the position
            close_side = "Sell" if side == "Buy" else "Buy"
            
            # Step 6: Round quantity for precision
            order_qty = round(qty, qty_precision)

            # Step 7: Execute market order to close the position
            print(f'🔄 Closing {side} position on {symbol} ({order_qty} contracts) at market price {mark_price}')
            
            resp = self.session.place_order(
                category='linear',
                symbol=symbol,
                side=close_side,
                orderType='Market',
                reduceOnly=True,
                qty=order_qty,
                recv_window=10000
            )

            print(f'✅ {resp["retMsg"]}')
        
        except Exception as err:
            print(f'❌ Error closing position on {symbol}: {err}')

    def send_tg(self, key, tg_id, text):
            try:
                url = f'https://api.telegram.org/bot{key}/sendMessage'
                data = {
                    'chat_id': tg_id,
                    'text': text
                }
                resp = requests.post(url, data=data)
                print(resp)
            except Exception as err:
                print(err)







