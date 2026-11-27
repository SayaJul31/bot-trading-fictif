
from common import *
import pandas as pd
st=load("momentum"); px=prices()
import time as _t
if _t.time()-st.get("last_run",0)<3.5*3600:
    print("trop tot (4h)"); raise SystemExit
st["last_run"]=_t.time()
STABLE={"USDC","FDUSD","TUSD","DAI","USDP","EUR","BUSD","USDE","PAXG","WBTC","XUSD","USD1","RLUSD","BFUSD","WBETH","AEUR","XAUT","U"}
t=pd.DataFrame(requests.get(BASE+"/ticker/24hr",timeout=20).json())
t=t[t.symbol.str.endswith("USDT")&~t.symbol.str[:-4].isin(STABLE)&~(t.symbol.str[:-4].str.endswith("B")&(t.symbol!="BNBUSDT"))]; t["qv"]=t.quoteVolume.astype(float)
syms=t.sort_values("qv",ascending=False).symbol.head(100).tolist()
def cl(s):
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":"1d","limit":200},timeout=20).json()
    return pd.Series([float(x[4]) for x in k[:-1]]), pd.Series([float(x[7]) for x in k[:-1]])
b,_=cl("BTCUSDT"); targets=[]
if True:  # filtre Bitcoin retire
    sc={}
    for s in syms:
        c,v=cl(s)
        if len(c)<130 or v.tail(30).mean()<20e6: continue
        m=c.iloc[-1]/c.iloc[-8]-1
        sc[s]=m
    targets=sorted(sc,key=sc.get,reverse=True)[:5]
rebalance("momentum","MOMENTUM",st,targets,px,stop=0.08,tp=0.05,trail=0.05)
