
import json, os, requests, pandas as pd, numpy as np, datetime as dt
BASE="https://data-api.binance.vision/api/v3"
FEE=0.001; SLOTS=10; STOP=0.10; START=1000.0
EXTRA=["MORPHOUSDT","ASTERUSDT","HYPEUSDT","PENDLEUSDT","RAYUSDT","TAOUSDT"]
STABLE={"USDC","FDUSD","TUSD","DAI","USDP","EUR","BUSD","USDE","PAXG","WBTC","XUSD","USD1","RLUSD","BFUSD","WBETH","AEUR","XAUT","U"}
def zlema(x,n):
    lag=(n-1)//2; return (x+(x-x.shift(lag))).ewm(span=n,adjust=False).mean()
def klines(s):
    k=requests.get(BASE+"/klines",params={"symbol":s,"interval":"4h","limit":400},timeout=20).json()
    if not isinstance(k,list) or len(k)<150: return None
    d=pd.DataFrame(k).iloc[:-1,[0,4,7]]; d.columns=["t","c","qv"]
    d.index=pd.to_datetime(d.t,unit="ms"); return d[["c","qv"]].astype(float)
def issue(title,body):
    tok=os.environ.get("GH_TOKEN"); repo=os.environ.get("GITHUB_REPOSITORY")
    if tok and repo:
        requests.post(f"https://api.github.com/repos/{repo}/issues",headers={"Authorization":f"Bearer {tok}"},json={"title":title,"body":body},timeout=20)
st=json.load(open("state.json")) if os.path.exists("state.json") else {"cash":START,"pos":{},"history":[],"trades":[]}
import time as _t
if _t.time()-st.get("last_run",0)<3.5*3600:
    print("trop tot (4h)"); raise SystemExit
st["last_run"]=_t.time()
t=pd.DataFrame(requests.get(BASE+"/ticker/24hr",timeout=20).json())
t=t[t.symbol.str.endswith("USDT")&~t.symbol.str[:-4].isin(STABLE)&~(t.symbol.str[:-4].str.endswith("B")&(t.symbol!="BNBUSDT"))]; t["qv"]=t.quoteVolume.astype(float)
syms=list(dict.fromkeys(t.sort_values("qv",ascending=False).symbol.head(100).tolist()+[e for e in EXTRA if e in set(t.symbol)]+list(st["pos"].keys())+["BTCUSDT"]))
data={s:d for s in syms if (d:=klines(s)) is not None}
btc=data["BTCUSDT"].c; btc_ok=btc.iloc[-1]>btc.rolling(120).mean().iloc[-1]
day=str(data["BTCUSDT"].index[-1])[:16]
sig={}
for s,d in data.items():
    c,v=d.c,d.qv; m=zlema(c,12)-zlema(c,26); g=m.ewm(span=9,adjust=False).mean(); tr=zlema(c,120)
    sig[s]=dict(price=c.iloc[-1],
      buy=bool(m.iloc[-1]>g.iloc[-1] and m.iloc[-2]<=g.iloc[-2] and v.rolling(30).mean().iloc[-1]>20e6/6 and v.iloc[-1]>v.rolling(20).mean().iloc[-1]*1.2),
      sell=bool((m.iloc[-1]<g.iloc[-1] and m.iloc[-2]>=g.iloc[-2]) or c.iloc[-1]<tr.iloc[-1]))
msgs=[]
for s in list(st["pos"]):
    p=st["pos"][s]; px=sig.get(s,{}).get("price",p["last"]); val=p["qty"]*px; p["last"]=px
    if px<=p["entry"]*(1-STOP) or sig.get(s,{}).get("sell"):
        out=val*(1-FEE); pnl=out/p["cost"]-1; st["cash"]+=out; del st["pos"][s]
        why="stop loss" if px<=p["entry"]*(1-STOP) else "signal de sortie"
        st["trades"].append(dict(day=day,side="VENTE",sym=s,price=px,pnl=round(pnl,4)))
        msgs.append((f"VENTE {s[:-4]} {pnl:+.1%}",f"{day} : vente de {s[:-4]} a {px:g} $ ({why}). Resultat du trade : {pnl:+.2%}."))
equity=st["cash"]+sum(p["qty"]*p["last"] for p in st["pos"].values())
if True:  # filtre Bitcoin retire
    for s in sorted([s for s in sig if sig[s]["buy"] and s not in st["pos"]],key=lambda s:-data[s].qv.iloc[-1]):
        if len(st["pos"])>=SLOTS: break
        a=min(equity/SLOTS,st["cash"])
        if a<1: break
        px=sig[s]["price"]; st["cash"]-=a; st["pos"][s]=dict(qty=a*(1-FEE)/px,entry=px,cost=a,last=px,day=day)
        st["trades"].append(dict(day=day,side="ACHAT",sym=s,price=px,amount=round(a,2)))
        msgs.append((f"ACHAT {s[:-4]}",f"{day} : achat fictif de {s[:-4]} a {px:g} $ pour {a:.2f} EUR."))
equity=st["cash"]+sum(p["qty"]*p["last"] for p in st["pos"].values())
st["history"].append(dict(day=day,equity=round(equity,2),btc=btc.iloc[-1],positions=len(st["pos"])))
json.dump(st,open("state.json","w"),indent=1)
for ti,b in msgs: issue("[ZERO LAG] "+ti,b+f"\n\nCapital fictif total : {equity:.2f} EUR (depart 1000 EUR). Positions ouvertes : {len(st['pos'])}.")
print(day,round(equity,2),msgs)
