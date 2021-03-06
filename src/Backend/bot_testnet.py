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
from decouple import config
from os.path import getmtime
from dateutil.tz import tzutc
import pytz
import pymongo
warnings.filterwarnings("ignore")

api_key = config('API_KEY')
api_secret = config('API_SECRET')
mongo_username = config('MONGO_USERNAME')
mongo_password = config('MONGO_PASSWORD')
TEST = False
DRY_RUN = False
MIN_ORDER = 50
MAX_ORDER = 150 if TEST else 500
WATCHED_FILES = './src/Backend/params.json'
watched_files_mtimes = [(WATCHED_FILES, getmtime(WATCHED_FILES))]
data = []
mongo_client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0.we9tx.mongodb.net/crypto_info?retryWrites=true&w=majority".format(mongo_username, mongo_password))
db = mongo_client.get_database('crypto_info')
states = db.bot_states
print('Connection to mongodb Atlas established. Current records: ', states.count_documents({}))

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
   
def record_balance(client, md, data):
    global states
    while True:
        try:
            r = client.User.User_getMargin().result()[0]
            states.insert_one(r)
            data.append(r)
            return data
        except:
            time.sleep(5)
            continue
            
def datetime_handler(x):
    epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)

    if isinstance(x, datetime.datetime):
        return (x - epoch).total_seconds()
    raise TypeError("Unknown type")

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
    with open('./src/Backend/params.json') as f:
        data = json.load(f)
            
    sl_lvl = data['stop_loss']
    return sl_lvl
    
def get_takeprofit():
    with open('./src/Backend/params.json') as f:
        data = json.load(f)
            
    take_profit = data['take_profit']
    return take_profit

def write_takeprofit(take_profit):
    with open('./src/Backend/params.json') as f:
        data = json.load(f)
    data['take_profit'] = take_profit
    with open('./src/Backend/params.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def write_stoploss(stop_loss):
    with open('./src/Backend/params.json') as f:
        data = json.load(f)
    data['stop_loss'] = stop_loss
    with open('./src/Backend/params.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
def check_file_change():
    global watched_files_mtimes
    for f, mtime in watched_files_mtimes:
        #print(f, mtime)
        if getmtime(f) > mtime:
            watched_files_mtimes = [(f, getmtime(f))]
            return True
            
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
            return p
        except:
            time.sleep(sleep_ctr)
            sleep_ctr += 1
            continue

def run_loop(md):
    global ctr, high, low, current_day, traded, tped, client, exchange, risk_lvl, bet_perc, take_profit, sl_lvl, prev_position, sl_id, tp_id, short_cond, long_cond, TEST, data
    ctr += 1
    position = get_position(client)
    data = record_balance(client, md, data)
    if ctr % 5 == 0:
        with open('data.txt', 'w') as outfile:
            json.dump(data, outfile, default=datetime_handler)
    
    if take_profit == 0:
        tped = True
            
    if ctr % 1 == 0:
        print ('{} -- Price: {} | Take Profit: {} | Stop loss: {}'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), md, take_profit if not tped else 'Already taken/ Not exist', sl_lvl if position != 0 else 'Not exist'))
        
    if position != 0 and take_profit == None:
        if len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) > 0:
            print ('Bot started with unknown orders. All orders cancelled!')
            client.Order.Order_cancelAll().result()
            
        take_profit = get_takeprofit()
        sl_lvl = get_stoploss()
        
        print ('Loaded json file -- take profit: {}, stop loss: {}'.format(take_profit, sl_lvl))
        
        while True:
            try:
                client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2), price=take_profit).result()
                print ('Posted take profit at {}'.format(take_profit))
                break
            except Exception as e:
                print (e)
                print ('error posting limit order. Retrying...')
                time.sleep(60)
                    
        if position > 0 and short_cond:
            orderQty = get_orget_orderQty(client, md, high, low) * np.sign(position)
        elif position < 0 and long_cond:
            orderQty = get_orderQty(client, md, high, low) * np.sign(position)
        else:
            orderQty = 0
        client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=int(float(sl_lvl)), execInst="LastPrice").result()
        print ('Posted stop loss order')
        traded = False
    
    if ctr >= 5: 
        print ('Conducting status check...')
        order_types = [ord['ordType'] for ord in client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]]
        if position == 0 and len(client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]) > 0:
            client.Order.Order_cancelAll().result()
            print('Status check -- cancel all orders')
        mismatched_tp_sl = check_file_change() and (take_profit != get_takeprofit() or sl_lvl != get_stoploss())
        if position != 0:
            if 'Stop' not in order_types or mismatched_tp_sl:
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
            if (tped == False) and ('Limit' not in order_types) or mismatched_tp_sl:
                valid_type = (isinstance(take_profit, float) or isinstance(take_profit, int))
                invalid_value_pos = position > 0 and take_profit <= md
                invalid_value_neg = position < 0 and take_profit >= md
                take_profit = get_takeprofit()
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
                print ('cond -- cancel stop loss')
            
        
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
            write_stoploss(sl_lvl)
        elif position < 0:
            if high - 2 > md:
                price = high - 2 # also placeholder, see comment for case "position > 0"
                sl_lvl = price
            else:
                price = md + 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if long_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result()
            write_stoploss(sl_lvl)
    
    trade_cond1 = (position == 0)
    trade_cond2 = (prev_position is not None) and (np.sign(prev_position) != np.sign(position))
    trade_cond3 = (prev_position is not None) and (np.sign(prev_position) == np.sign(position)) and (abs(position) < abs(prev_position))
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
            write_takeprofit(take_profit)
            print ('Posted long order for {} XBT; Take profit at {}.'.format(orderQty, take_profit))
            sl_orderQty = orderQty if short_cond else 0 
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+sl_orderQty), stopPx=int(md*0.85), execInst="LastPrice").result()
            sl_lvl = int(md*0.85)
            write_stoploss(sl_lvl)
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
            write_takeprofit(take_profit)
            print ('Posted short order for {} XBT; Take profit at {}.'.format(orderQty, take_profit))
            sl_orderQty = orderQty if long_cond else 0 
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+sl_orderQty), stopPx=int(md*1.15), execInst="LastPrice").result()
            sl_lvl = int(md*1.15)
            write_stoploss(sl_lvl)
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
            write_stoploss(sl_lvl)
            print ('Posted stop loss order')
        elif position < 0:
            take_profit = md - (high-low)
            client.Order.Order_cancelAll().result()
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position), stopPx=int(md*1.15), execInst="LastPrice").result()
            sl_lvl = int(md*1.15)
            write_stoploss(sl_lvl)
            print ('Posted stop loss order')
        
        client.Order.Order_new(symbol='XBTUSD', orderQty=-int(position/2), price=take_profit).result()
        write_takeprofit(take_profit)
        print ('Posted take profit order at {}'.format(take_profit))
        tped = False
    
    elif trade_cond3:
        #print (prev_position, position)
        tped = True
        print ('Took profit!')
        for ord in client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0]:
            if ord['ordType'] == 'Stop':
                client.Order.Order_cancel(orderID=ord['orderID']).result()
                print ('Cancel StopLoss')
        if position > 0: 
            if low + 2 < md:
                price = low + 2 # placeholder for edge case of minute bars (instead of hourly bars)
                sl_lvl = price
            else:
                price = md - 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if short_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result() # might change back to MarkPrice.
            write_stoploss(price)
            print('stop loss updated')
        elif position < 0:
            if high - 2 > md:
                price = high - 2 # also placeholder, see comment for case "position > 0"
                sl_lvl = price
            else:
                price = md + 2
                sl_lvl = price
            orderQty = get_orderQty(client, md, high, low) * np.sign(position) if long_cond else 0
            client.Order.Order_new(symbol='XBTUSD', orderQty=-(position+orderQty), stopPx=price, execInst="LastPrice").result()
            write_stoploss(price)
            print('stop loss updated')
    
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
take_profit = sl_lvl = None
prev_position = None
#sl_id, tp_id = 'stoploss' + str(np.random.randint(0, 4000)), 'tp1' + str(np.random.randint(0, 4000))
print ('Bot Initiated.')
long_cond = (high-low >= risk_lvl*high)
short_cond = (high-low >= risk_lvl*low)
#print (client.Order.Order_getOrders(filter=json.dumps({"open": True})).result()[0])
asyncio.get_event_loop().run_until_complete(capture_data())

