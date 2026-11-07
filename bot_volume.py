
import pandas as pd
from common import *
STABLE={"USDC","FDUSD","TUSD","DAI","USDP","EUR","BUSD","USDE","PAXG","WBTC","XUSD","USD1","RLUSD","BFUSD","WBETH","AEUR","XAUT","U"}
st=load("volume"); st["slots"]=10; px=prices()
t=pd.DataFrame(requests.get(BASE+"/ticker/24hr",timeout=20).json())
t=t[t.symbol.str.endswith("USDT")&~t.symbol.str[:-4].isin(STABLE)]; t["qv"]=t.quoteVolume.astype(float)
EXTRA=["MORPHOUSDT","ASTERUSDT","HYPEUSDT","PENDLEUSDT","RAYUSDT","TAOUSDT"]
syms=list(dict.fromkeys(t.sort_values("qv",ascending=False).symbol.head(100).tolist()+[e for e in EXTRA if e in set(t.symbol)]+list(st["pos"])+["BTCUSDT"]))
data={}
for s in syms:
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":"1d","limit":200},timeout=20).json()
    if isinstance(k,list) and len(k)>130:
        data[s]=(pd.Series([float(x[4]) for x in k[:-1]]),pd.Series([float(x[7]) for x in k[:-1]]))
b=data["BTCUSDT"][0]; ok=b.iloc[-1]>b.rolling(120).mean().iloc[-1]
targets=[s for s in st["pos"] if s in data and data[s][0].iloc[-1]>=data[s][0].ewm(span=20,adjust=False).mean().iloc[-1]]
if ok:
    for s,(c,v) in data.items():
        if len(targets)>=10: break
        if s in targets: continue
        if v.iloc[-1]>v.iloc[-31:-1].mean()*2 and c.iloc[-1]/c.iloc[-2]-1>0.03 and v.tail(30).mean()>20e6:
            targets.append(s)
rebalance("volume","VOLUME WHALES",st,targets,px,stop=0.10)
