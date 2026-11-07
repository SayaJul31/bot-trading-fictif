
import pandas as pd
from common import *
def zlema(x,n):
    lag=(n-1)//2; return (x+(x-x.shift(lag))).ewm(span=n,adjust=False).mean()
SY=["BTCUSDT","ETHUSDT","SOLUSDT"]
st=load("majors"); st["slots"]=3; px=prices(); sig={}
for s in SY:
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":"1d","limit":400},timeout=20).json()
    c=pd.Series([float(x[4]) for x in k[:-1]]); v=pd.Series([float(x[7]) for x in k[:-1]])
    m=zlema(c,12)-zlema(c,26); g=m.ewm(span=9,adjust=False).mean(); tr=zlema(c,120)
    sig[s]=dict(c=c,buy=bool(m.iloc[-1]>g.iloc[-1] and m.iloc[-2]<=g.iloc[-2] and c.iloc[-1]>tr.iloc[-1] and v.iloc[-1]>v.rolling(20).mean().iloc[-1]*1.2),
        sell=bool((m.iloc[-1]<g.iloc[-1] and m.iloc[-2]>=g.iloc[-2]) or c.iloc[-1]<tr.iloc[-1]))
b=sig["BTCUSDT"]["c"]; ok=b.iloc[-1]>b.rolling(120).mean().iloc[-1]
targets=[s for s in st["pos"] if not sig[s]["sell"]]
if ok: targets+=[s for s in SY if sig[s]["buy"] and s not in targets]
rebalance("majors","MAJEURES BTC ETH SOL",st,targets,px,stop=0.10)
