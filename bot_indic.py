
import sys, pandas as pd, numpy as np
from common import *
mode=sys.argv[1]; name={"cassure":"cassure","trois":"trois"}[mode]
label={"cassure":"CASSURE ZONE","trois":"3 INDICATEURS"}[mode]
STABLE={"USDC","FDUSD","TUSD","DAI","USDP","EUR","BUSD","USDE","PAXG","WBTC","XUSD","USD1","RLUSD","BFUSD","WBETH","AEUR","XAUT","U"}
EXTRA=["MORPHOUSDT","ASTERUSDT","HYPEUSDT","PENDLEUSDT","RAYUSDT","TAOUSDT"]
def zl(x,n):
    lag=(n-1)//2; return (x+(x-x.shift(lag))).ewm(span=n,adjust=False).mean()
st=load(name); st["slots"]=10; px=prices()
t=pd.DataFrame(requests.get(BASE+"/ticker/24hr",timeout=20).json())
t=t[t.symbol.str.endswith("USDT")&~t.symbol.str[:-4].isin(STABLE)]; t["qv"]=t.quoteVolume.astype(float)
syms=list(dict.fromkeys(t.sort_values("qv",ascending=False).symbol.head(100).tolist()+[e for e in EXTRA if e in set(t.symbol)]+list(st["pos"])+["BTCUSDT"]))
sig={}
for s in syms:
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":"1d","limit":400},timeout=20).json()
    if not isinstance(k,list) or len(k)<260: continue
    d=pd.DataFrame(k[:-1]).iloc[:,[2,3,4,7]].astype(float); d.columns=["h","l","c","v"]
    c,h,l,v=d.c,d.h,d.l,d.v
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/70,adjust=False).mean(); basis=zl(c,70); band=atr.rolling(210,min_periods=70).max()*1.2
    stt=pd.Series(np.nan,index=c.index); stt[c>basis+band]=1; stt[c<basis-band]=-1; stt=stt.ffill().fillna(0)
    m=zl(c,12)-zl(c,26); g=m.ewm(span=9,adjust=False).mean()
    cross=(m>g)&(m.shift()<=g.shift())
    liq=v.tail(30).mean()>20e6; volok=v.iloc[-1]>v.rolling(20).mean().iloc[-1]*1.2
    if mode=="cassure":
        hi=c.rolling(50).max().shift(); lo=c.rolling(50).min().shift(); sb=hi-(hi-lo)*0.25
        brk=c.iloc[-1]>sb.iloc[-1] and c.iloc[-2]<=sb.iloc[-2]
        buy=bool(brk and cross.tail(3).any() and stt.iloc[-1]==1 and volok and liq)
    else:
        hi=c.rolling(100).max(); lo=c.rolling(100).min()
        buy=bool(stt.iloc[-1]==1 and cross.iloc[-1] and volok and liq and c.iloc[-1]<=lo.iloc[-1]+(hi.iloc[-1]-lo.iloc[-1])*0.5)
    sell=bool(stt.iloc[-1]==-1 or (m.iloc[-1]<g.iloc[-1] and m.iloc[-2]>=g.iloc[-2] and c.iloc[-1]<basis.iloc[-1]))
    sig[s]=dict(c=c,buy=buy,sell=sell)
b=sig["BTCUSDT"]["c"]; ok=b.iloc[-1]>b.rolling(120).mean().iloc[-1]
targets=[s for s in st["pos"] if not sig.get(s,{}).get("sell")]
if ok:
    for s in [s for s in sig if sig[s]["buy"] and s not in targets]:
        if len(targets)>=10: break
        targets.append(s)
rebalance(name,label,st,targets,px,stop=0.10)
