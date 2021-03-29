import json

d = {'take_profit' : 76000, 'stop_loss' : 40000}
with open('./src/Backend/params.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=4)
    print ('done')