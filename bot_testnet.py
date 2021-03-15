from bitmex_websocket import BitMEXWebsocket
import time
import ccxt
import bitmex
import datetime
import pandas as pd
import json
import os
import asyncio
import websockets
import sys

api_key = ""
api_secret = ""
TEST = False

# helper functions
def get_daily_data(exchange):
    global TEST
    if not TEST:
        date_N_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        since = time.mktime(datetime.datetime.strptime(date_N_days_ago, "%Y-%m-%d %H:%M:%S").timetuple())*1000
        df = exchange.fetch_ohlcv('BTC/USD', timeframe = '1d', since=since, limit=500)
    elif TEST:
        date_N_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        since = time.mktime(datetime.datetime.strptime(date_N_days_ago, "%Y-%m-%d %H:%M:%S").timetuple())*1000
        df = exchange.fetch_ohlcv('BTC/USD', timeframe = '1m', since=since, limit=500)
    df = pd.DataFrame(df)
    df.columns = ["Timestamp", "Open", "High", "Low", "tick", "Volume"]
    df.Timestamp = df.Timestamp.apply(lambda x: datetime.datetime.fromtimestamp(x / 1e3))
    print (df)
    return df.High.tolist()[-2], df.Low.tolist()[-2]

def get_orderQty(client, md, high, low):
    global bet_perc
    while True:
        try:
            balance_XBT = client.User.User_getMargin().result()[0]['amount']
            print ('Current balance: ', balance_XBT)
            balance_USD = md*balance_XBT/1e8
            return min(100, max(50, int(balance_USD*bet_perc/max(high-low, 1)*md/10))) #10 is arbitrary
        except:
            time.sleep(5)
            continue  
            
async def capture_data():
    uri = "wss://testnet.bitmex.com/realtime?subscribe=trade:XBTUSD"
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                data = await websocket.recv()
                data = json.loads(data)
                #print (data)
                try:
                    data = data['data'][-1]
                    md = data['price']
                    run_loop(md=md)
                    time.sleep(1)
                except:
                    time.sleep(1)
                    continue
            except:
                print ('Websocket shut down. Reconnecting...')
                websocket = await websockets.connect(uri)
                
def get_position(client):
    sleep_ctr = 1
    while True:
        try:
            p = client.Position.Position_get(filter=json.dumps({'symbol': 'XBTUSD'})).result()[0][0]['currentQty'] 
            return p # need check
        except:
            time.sleep(sleep_ctr)
            sleep_ctr += 1
            continue

def run_loop(md):
    global ctr, high, low, current_day, traded, tped, client, exchange, risk_lvl, bet_perc, take_profit, sl_lvl, TEST
    ctr += 1
    if ctr % 5 == 0:
        print ('{} -- Price: {} | Take Profit: {} | Stop loss: {}'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), md, take_profit if not tped else 'Already taken/ Not exist', sl_lvl if sl_lvl is not None else 'Not exist'))
        
    position = get_position(client)
    if position != 0 and take_profit == None:
        r1 = input('You are holding a position without a take profit. Do you need a take profit? Y/N: ') 
        if r1 in ['y', 'Y', 'Yes', 'yes']:
            r = None
            while r not in ['y', 'Y', 'Yes', 'yes']:
                take_profit = input('What is your desired take profit level? ')
                r = input('Are you sure your take profit is: {}? Y/N: '.format(take_profit))
            take_profit = int(float(take_profit))
            client.Order.Order_new(symbol='XBTUSD', orderQty=-orderQty, price=take_profit, clOrdID='tp1').result()
        elif r1 in ['N', 'n', 'No', 'no']:
            print ('No take profit needed. Position will be exited when reached stop loss.')
            take_profit = 100000 if position > 0 else 0
            tped = True
        else:
            print ('Response not recognized. Bot terminated.')
            sys.exit()
        if len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) > 0:
            print ('Bot started with unknown orders. All orders cancelled!')
            client.Order.Order_cancelAll().result()
        r2 = None
        while r2 not in ['y', 'Y', 'Yes', 'yes']:
            sl_lvl = input('You are holding a position without a stop loss. What is your desired stop loss level? ')
            r2 = input('Are you sure your stop loss is {}? Y/N: '.format(sl_lvl))
        client.Order.Order_new(symbol='XBTUSD', orderQty=-position, stopPx=int(float(sl_lvl)), execInst="LastPrice", clOrdID='stoploss').result()
        print ('Posted stop loss order')
        traded = False
    
    if ctr == 20: 
        if len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) == 0 and position != 0:
            r2 = None
            while r2 not in ['y', 'Y', 'Yes', 'yes']:
                sl_lvl = input('You are holding a position without a stop loss. What is your desired stop loss level? ')
                r2 = input('Are you sure your stop loss is {}? Y/N: '.format(sl_lvl))
            client.Order.Order_new(symbol='XBTUSD', orderQty=-position, stopPx=int(float(sl_lvl)), execInst="LastPrice", clOrdID='stoploss').result()
            print ('Posted stop loss order')
        ctr = 0

            
    cond = (time.gmtime().tm_mday != current_day) if not TEST else (time.gmtime().tm_min != current_day)
    
    if cond:
        current_day = time.gmtime().tm_mday if not TEST else time.gmtime().tm_min
        high, low = get_daily_data(exchange)
        traded = False
        print ('New day. Reposting stop loss orders.')
        if len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) > 0:
            client.Order.Order_cancel(clOrdID='stoploss').result()
            
        
        # change stop loss
        if position > 0: 
            if low + 2 < md:
                price = low + 2 # placeholder for edge case of minute bars (instead of hourly bars)
                sl_lvl = price
            else:
                price = md - 2
                sl_lvl = price
            client.Order.Order_new(symbol='XBTUSD', orderQty=-position, stopPx=price, execInst="LastPrice", clOrdID='stoploss').result() # might change back to MarkPrice.
        elif position < 0:
            if high - 2 > md:
                price = high - 2 # also placeholder, see comment for case "position > 0"
                sl_lvl = price
            else:
                price = md + 2
                sl_lvl = price
            client.Order.Order_new(symbol='XBTUSD', orderQty=-position, stopPx=price, execInst="LastPrice", clOrdID='stoploss').result()
            
    if position == 0:
        if md > high - 2 and not traded and (high-low >= risk_lvl*high):
            orderQty = get_orderQty(client, md, high, low)
            while position == 0:
                try:
                    client.Order.Order_new(symbol='XBTUSD', orderQty=orderQty).result()
                    time.sleep(5)
                except:
                    time.sleep(5)
                    continue
                position = get_position(client)
                if position != 0:
                    break # not really needed
            take_profit = md + (high-low)
            client.Order.Order_new(symbol='XBTUSD', orderQty=-orderQty, price=take_profit, clOrdID='tp1').result()
            print ('Posted long order for {} XBT; Take profit at {}.'.format(orderQty, take_profit))
            client.Order.Order_new(symbol='XBTUSD', orderQty=-position, stopPx=int(md*0.85), execInst="LastPrice", clOrdID='stoploss').result()
            sl_lvl = int(md*0.85)
            print ('Posted stop loss order')
            traded = True
            tped = Falses

        elif md < low + 2 and not traded and (high-low >= risk_lvl*low):
            orderQty = -get_orderQty(client, md, high, low)
            while position == 0:
                try:
                    client.Order.Order_new(symbol='XBTUSD', orderQty=orderQty).result()
                    time.sleep(5)
                except:
                    time.sleep(5)
                    continue
                position = get_position(client)
                print ('New position: {}'.format(position))
                if position != 0:
                    break # not really needed
            take_profit = md - (high-low)
            client.Order.Order_new(symbol='XBTUSD', orderQty=-orderQty, price=take_profit, clOrdID='tp1').result()
            print ('Posted short order for {} XBT; Take profit at {}.'.format(orderQty, take_profit))
            client.Order.Order_new(symbol='XBTUSD', orderQty=-position, stopPx=int(md*1.15), execInst="LastPrice", clOrdID='stoploss').result()
            sl_lvl = int(md*1.15)
            print ('Posted stop loss order')
            traded = True
            tped = False
            
    elif position < 0:
        if md < take_profit and not traded and not tped:
            client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2)).result()
            print ('Took profit at {}'.format(md))
            tped = True
    else:
        if md > take_profit and not traded and not tped:
            client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2)).result() 
            print ('Took profit at {}'.format(md))
            tped = True
        
    time.sleep(1)

# setup
#ws = BitMEXWebsocket(endpoint="https://testnet.bitmex.com/api/v1", symbol="XBTUSD", api_key=api_key, api_secret=api_secret)
client = bitmex.bitmex(test=True, api_key=api_key, api_secret=api_secret)
#ws.get_instrument()
exchange = ccxt.bitmex({'apiKey':api_key, 'secret':api_secret,})
if 'test' in exchange.urls:
    exchange.urls['api'] = exchange.urls['test']
high, low = get_daily_data(exchange)
#print (high, low)
current_day = time.gmtime().tm_mday if not TEST else time.gmtime().tm_min
traded = False
tped = False
risk_lvl = 0.03
bet_perc = 0.1
ctr = 0
take_profit = None
sl_lvl = None
print ('Bot Initiated.')
#print (client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0])
asyncio.get_event_loop().run_until_complete(capture_data())


