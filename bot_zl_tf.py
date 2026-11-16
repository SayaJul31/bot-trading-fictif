
import sys, pandas as pd
from common import *
iv=sys.argv[1]; bpd={"1h":24,"4h":6}[iv]; name="zl"+iv; label="ZERO LAG "+iv.upper()
STABLE={"USDC","FDUSD","TUSD","DAI","USDP","EUR","BUSD","USDE","PAXG","WBTC","XUSD","USD1","RLUSD","BFUSD","WBETH","AEUR","XAUT","U"}
def zlema(x,n):
    lag=(n-1)//2; return (x+(x-x.shift(lag))).ewm(span=n,adjust=False).mean()
st=load(name); px=prices()
import time as _t
if iv=="4h" and _t.time()-st.get("last_run",0)<3.5*3600:
    print("4h: trop tot"); raise SystemExit
st["last_run"]=_t.time()
t=pd.DataFrame(requests.get(BASE+"/ticker/24hr",timeout=20).json())
t=t[t.symbol.str.endswith("USDT")&~t.symbol.str[:-4].isin(STABLE)&~(t.symbol.str[:-4].str.endswith("B")&(t.symbol!="BNBUSDT"))]; t["qv"]=t.quoteVolume.astype(float)
syms=list(dict.fromkeys(t.sort_values("qv",ascending=False).symbol.head(60).tolist()+list(st["pos"])+["BTCUSDT"]))
sig={}
for s in syms:
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":iv,"limit":300},timeout=20).json()
    if not isinstance(k,list) or len(k)<200: continue
    c=pd.Series([float(x[4]) for x in k[:-1]]); v=pd.Series([float(x[7]) for x in k[:-1]])
    m=zlema(c,12)-zlema(c,26); g=m.ewm(span=9,adjust=False).mean(); tr=zlema(c,120)
    sig[s]=dict(c=c,buy=bool(m.iloc[-1]>g.iloc[-1] and m.iloc[-2]<=g.iloc[-2] and v.tail(30*bpd).mean()*bpd>20e6 and v.iloc[-1]>v.rolling(20).mean().iloc[-1]*1.2),
        sell=bool((m.iloc[-1]<g.iloc[-1] and m.iloc[-2]>=g.iloc[-2]) or c.iloc[-1]<tr.iloc[-1]))
b=sig["BTCUSDT"]["c"]; ok=b.iloc[-1]>b.rolling(120).mean().iloc[-1]
targets=[s for s in st["pos"] if not sig.get(s,{}).get("sell")]
if True:  # filtre Bitcoin retire
    for s in [s for s in sig if sig[s]["buy"] and s not in targets]:
        if len(targets)>=10: break
        targets.append(s)
st.setdefault("slots",10)
rebalance(name,label,st,targets,px,stop=0.10)
