
from common import *
import pandas as pd
st=load("momentum"); px=prices()
if dt.date.today().weekday()!=0 and st["history"]: 
    rebalance("momentum","MOMENTUM",st,list(st["pos"]),px,stop=0.15); raise SystemExit
STABLE={"USDC","FDUSD","TUSD","DAI","USDP","EUR","BUSD","USDE","PAXG","WBTC","XUSD","USD1","RLUSD","BFUSD","WBETH","AEUR","XAUT","U"}
t=pd.DataFrame(requests.get(BASE+"/ticker/24hr",timeout=20).json())
t=t[t.symbol.str.endswith("USDT")&~t.symbol.str[:-4].isin(STABLE)]; t["qv"]=t.quoteVolume.astype(float)
syms=t.sort_values("qv",ascending=False).symbol.head(100).tolist()
def cl(s):
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":"1d","limit":200},timeout=20).json()
    return pd.Series([float(x[4]) for x in k[:-1]]), pd.Series([float(x[7]) for x in k[:-1]])
b,_=cl("BTCUSDT"); targets=[]
if b.iloc[-1]>b.rolling(120).mean().iloc[-1]:
    sc={}
    for s in syms:
        c,v=cl(s)
        if len(c)<130 or v.tail(30).mean()<20e6 or c.iloc[-1]<c.rolling(120).mean().iloc[-1]: continue
        m=c.iloc[-1]/c.iloc[-31]-1
        if m>0: sc[s]=m
    targets=sorted(sc,key=sc.get,reverse=True)[:5]
rebalance("momentum","MOMENTUM",st,targets,px,stop=0.15)
