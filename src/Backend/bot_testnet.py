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
import numpy as np
import warnings
<<<<<<< Updated upstream
warnings.filterwarnings("ignore")

api_key = "KWLoDRAqZflf6_8C-oE4hnJc"
api_secret = "Km8gURPFzdgOLYmuTDgr7aCBmizxiDIkLF8quLKfJ89F2s9E"
=======
#from decouple import config
warnings.filterwarnings("ignore")

api_key = "KWLoDRAqZflf6_8C-oE4hnJc" #config('API_KEY')
api_secret = "Km8gURPFzdgOLYmuTDgr7aCBmizxiDIkLF8quLKfJ89F2s9E"#config('API_SECRET')
>>>>>>> Stashed changes
TEST = False
DRY_RUN = False
MIN_ORDER = 50
MAX_ORDER = 150 if TEST else 500

# helper functions
def get_daily_data(exchange):
    global TEST
    if not TEST:
        date_N_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
        since = time.mktime(datetime.datetime.strptime(date_N_days_ago, "%Y-%m-%d %H:%M:%S").timetuple())*1000
        df = exchange.fetch_ohlcv('BTC/USD', timeframe = '1d', since=since, limit=500)
    elif TEST:
        date_N_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        since = time.mktime(datetime.datetime.strptime(date_N_days_ago, "%Y-%m-%d %H:%M:%S").timetuple())*1000
        df = exchange.fetch_ohlcv('BTC/USD', timeframe = '1h', since=since, limit=500)
    df = pd.DataFrame(df)
    df.columns = ["Timestamp", "Open", "High", "Low", "tick", "Volume"]
    df.Timestamp = df.Timestamp.apply(lambda x: datetime.datetime.fromtimestamp(x / 1e3))
    print (df)
    return df.High.tolist()[-2], df.Low.tolist()[-2]

def get_balance(client, md):
    while True:
        try:
            balance_XBT = client.User.User_getMargin().result()[0]['amount']
            print ('Current balance: ', balance_XBT)
            balance_USD = md*balance_XBT/1e8
            return balance_USD
        except:
            time.sleep(5)
            continue

def get_orderQty(client, md, high, low):
    global bet_perc
    balance_USD = get_balance(client, md)
    return min(MAX_ORDER, max(MIN_ORDER, int(balance_USD*bet_perc/max(high-low, 1)*md))) #10 is arbitrary

def gen_id (stoploss):
    if stoploss:
        return 'stoploss' + str(np.random.randint(0, 4000))
    else:
        return 'tp1' + str(np.random.randint(0, 4000))
      
def get_stoploss():
    r2 = None
    while r2 not in ['y', 'Y', 'Yes', 'yes']:
        sl_lvl = input('You are holding a position without a stop loss. What is your desired stop loss level? ')
        r2 = input('Are you sure your stop loss is {}? Y/N: '.format(sl_lvl))
    return sl_lvl
    
def get_takeprofit():
    r = None
    while r not in ['y', 'Y', 'Yes', 'yes']:
        take_profit = input('What is your desired take profit level? ')
        r = input('Are you sure your take profit is: {}? Y/N: '.format(take_profit))
    return take_profit
            
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
    global ctr, high, low, current_day, traded, tped, client, exchange, risk_lvl, bet_perc, take_profit, sl_lvl, prev_position, sl_id, tp_id, short_cond, long_cond, TEST
    ctr += 1
    position = get_position(client)
    if ctr % 1 == 0:
        print ('{} -- Price: {} | Take Profit: {} | Stop loss: {}'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), md, take_profit if not tped else 'Already taken/ Not exist', sl_lvl if position != 0 else 'Not exist'))
        
    if position != 0 and take_profit == None:
        if len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) > 0:
            print ('Bot started with unknown orders. All orders cancelled!')
            client.Order.Order_cancelAll().result()
        
        r1 = None
        while r1 not in ['y', 'Y', 'Yes', 'yes', 'N', 'n', 'No', 'no']:
            if r1 != None:
                print('Response not recognized. Please try again!')
            r1 = input('You are holding a position without a take profit. Do you need a take profit? Y/N: ') 
        if r1 in ['y', 'Y', 'Yes', 'yes']:
            take_profit = get_takeprofit()
            take_profit = int(float(take_profit))
            while True:
                try:
                    client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2), price=take_profit).result()
                    break
                except Exception as e:
                    print (e)
                    print ('error posting limit order. Retrying...')
                    time.sleep(60)
            print ('Posted take profit at {}'.format(take_profit))
        elif r1 in ['N', 'n', 'No', 'no']:
            print ('No take profit needed. Position will be exited when reached stop loss.')
            take_profit = 100000 if position > 0 else 0
            tped = True
        else:
            print ('Response not recognized. Bot terminated.')
            sys.exit()
        
        sl_lvl = get_stoploss()
            
        if position > 0 and short_cond:
            orderQty = get_orderQty(client, md, high, low) * np.sign(position)
        elif position < 0 and long_cond:
            orderQty = get_orderQty(client, md, high, low) * np.sign(position)
        else:
            orderQty = 0
        client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=int(float(sl_lvl)), execInst="LastPrice").result()
        print ('Posted stop loss order')
        traded = False
    
    if ctr >= 20: 
        print ('Conducting status check...')
        order_types = [ord['ordType'] for ord in client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]]
        if position == 0 and len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) > 0:
            client.Order.Order_cancelAll().result()
        if position != 0:
            if 'Stop' not in order_types:
                r2 = None
                sl_lvl = get_stoploss()
                if position > 0 and short_cond:
                    orderQty = get_orderQty(client, md, high, low) * np.sign(position)
                elif position < 0 and long_cond:
                    orderQty = get_orderQty(client, md, high, low) * np.sign(position)
                else:
                    orderQty = 0
                while True:
                    try:
                        client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=int(float(sl_lvl)), execInst="LastPrice").result()
                        break
                    except Exception as e:
                        print (e)
                        time.sleep(5)
                print ('Posted stop loss order')
            if (tped == False) and ('Limit' not in order_types):
                valid_type = (isinstance(take_profit, float) or isinstance(take_profit, int))
                invalid_value_pos = position > 0 and take_profit <= md
                invalid_value_neg = position < 0 and take_profit >= md
                if invalid_value_pos or valid_type == False:
                    take_profit = input('System detected deprecated take profit. Please enter new take profit: ')
                elif invalid_value_neg or valid_type == False:
                    take_profit = input('System detected deprecated take profit. Please enter new take profit: ')
                client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2), price=take_profit).result()
                print ('Posted take profit order at {}'.format(take_profit))
        ctr = 0

            
    cond = (time.gmtime().tm_mday != current_day) if not TEST else (time.gmtime().tm_hour != current_day)
    
    if cond:
        current_day = time.gmtime().tm_mday if not TEST else time.gmtime().tm_hour
        high, low = get_daily_data(exchange)
        traded = False
        print ('New day. Reposting stop loss orders.')
        long_cond = (high-low >= risk_lvl*high)
        short_cond = (high-low >= risk_lvl*low)
        
        for ord in client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]:
            if ord['ordType'] == 'Stop':
                client.Order.Order_cancel(orderID=ord['orderID']).result()
            
        
        # change stop loss
        if position > 0: 
            if low + 2 < md:
                price = low + 2 # placeholder for edge case of minute bars (instead of hourly bars)
                sl_lvl = price
            else:
                price = md - 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if short_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result() # might change back to MarkPrice.
        elif position < 0:
            if high - 2 > md:
                price = high - 2 # also placeholder, see comment for case "position > 0"
                sl_lvl = price
            else:
                price = md + 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if long_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result()
    
    trade_cond1 = (position == 0)
    trade_cond2 = (prev_position is not None) and (np.sign(prev_position) != np.sign(position))
    trade_cond3 = (prev_position is not None) and (np.sign(prev_position) == np.sign(position)) and (position != prev_position)
    if trade_cond1:
        if md > high - 2 and not traded and long_cond:
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
            client.Order.Order_new(symbol='XBTUSD', orderQty=-int(orderQty/2), price=take_profit).result()
            print ('Posted long order for {} XBT; Take profit at {}.'.format(orderQty, take_profit))
            sl_orderQty = orderQty if short_cond else 0 
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+sl_orderQty), stopPx=int(md*0.85), execInst="LastPrice").result()
            sl_lvl = int(md*0.85)
            print ('Posted stop loss order')
            traded = True
            tped = False

        elif md < low + 2 and not traded and short_cond:
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
            client.Order.Order_new(symbol='XBTUSD', orderQty=-int(orderQty/2), price=take_profit).result()
            print ('Posted short order for {} XBT; Take profit at {}.'.format(orderQty, take_profit))
            sl_orderQty = orderQty if long_cond else 0 
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+sl_orderQty), stopPx=int(md*1.15), execInst="LastPrice").result()
            sl_lvl = int(md*1.15)
            print ('Posted stop loss order')
            traded = True
            tped = False
            
    elif trade_cond2:
        #print (prev_position, position)
        if position > 0:
            take_profit = md + (high-low)
            client.Order.Order_cancelAll().result()
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position), stopPx=int(md*0.85), execInst="LastPrice").result()
            sl_lvl = int(md*0.85)
            print ('Posted stop loss order')
        elif position < 0:
            take_profit = md - (high-low)
            client.Order.Order_cancelAll().result()
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position), stopPx=int(md*1.15), execInst="LastPrice").result()
            sl_lvl = int(md*1.15)
            print ('Posted stop loss order')
        
        client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2), price=take_profit).result()
        print ('Posted take profit order at {}'.format(take_profit))
        tped = False
    
    elif trade_cond3:
        print (prev_position, position)
        tped = True
        print ('Took profit!')
        for ord in client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]:
            if ord['ordType'] == 'Stop':
                client.Order.Order_cancel(orderID=ord['orderID']).result()
        if position > 0: 
            if low + 2 < md:
                price = low + 2 # placeholder for edge case of minute bars (instead of hourly bars)
                sl_lvl = price
            else:
                price = md - 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if short_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result() # might change back to MarkPrice.
        elif position < 0:
            if high - 2 > md:
                price = high - 2 # also placeholder, see comment for case "position > 0"
                sl_lvl = price
            else:
                price = md + 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if long_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result()
    
    prev_position = position
    time.sleep(1)

# setup
client = bitmex.bitmex(test=True, api_key=api_key, api_secret=api_secret)
exchange = ccxt.bitmex({'apiKey':api_key, 'secret':api_secret,})
if 'test' in exchange.urls:
    exchange.urls['api'] = exchange.urls['test']
high, low = get_daily_data(exchange)
current_day = time.gmtime().tm_mday if not TEST else time.gmtime().tm_min
traded = False
tped = False
risk_lvl = 0.03
bet_perc = 0.1
ctr = 0
take_profit = None
sl_lvl = None
prev_position = None
#sl_id, tp_id = 'stoploss' + str(np.random.randint(0, 4000)), 'tp1' + str(np.random.randint(0, 4000))
print ('Bot Initiated.')
long_cond = (high-low >= risk_lvl*high)
short_cond = (high-low >= risk_lvl*low)
#print (client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0])
asyncio.get_event_loop().run_until_complete(capture_data())

