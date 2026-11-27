
import json, os, time, requests, numpy as np, pandas as pd
from common import issue, FEE, BASE
f="state_vol4h.json"; L="VOL 4H"
st=json.load(open(f)) if os.path.exists(f) else {"cash":1000.0,"pos":{},"history":[],"trades":[],"last_bar":0}
SLIP=0.002; TP=0.06; SL=0.08; MAXH=96; MAXP=10; SZ=0.10; RSI_MAX=35; VX=1.5
STABLE={"USDC","FDUSD","TUSD","USDP","DAI","EUR","BUSD","USDE","USD1","XUSD","RLUSD","PYUSD","AEUR","EURI","PAXG","WBTC","WBETH","BFUSD","USDS","XAUT","RWUSD","U","KORU"}
now=time.time(); day=time.strftime("%Y-%m-%d %H:%M",time.gmtime()); msgs=[]
def okb(b): return b not in STABLE and not (b.endswith("B") and b!="BNB") and not b.endswith(("UP","DOWN"))
def rsi(c,n=14):
    d=np.diff(c,prepend=c[0]); up=pd.Series(np.clip(d,0,None)).ewm(alpha=1/n).mean(); dn=pd.Series(np.clip(-d,0,None)).ewm(alpha=1/n).mean()
    return (100-100/(1+up/dn.replace(0,1e-9))).values
px={x["symbol"]:float(x["price"]) for x in requests.get(BASE+"/ticker/price",timeout=20).json()}
# 1) sorties (chaque passage)
for s in list(st["pos"]):
    p=st["pos"][s]; last=px.get(s,p["last"]); p["last"]=last; r=last/p["entry"]; why=None
    if r>=1+TP: why=f"objectif +{TP:.0%} atteint"
    elif r<=1-SL: why=f"stop -{SL:.0%}"
    elif now-p["t"]>MAXH*3600: why=f"duree max {MAXH} h"
    if why:
        out=p["cost"]*r*(1-FEE-SLIP); st["cash"]+=out; pnl=out/p["cost"]-1
        st["trades"].append(dict(day=day,side="VENTE",sym=s,price=last,pnl=round(pnl,4),why=why))
        msgs.append((f"[{L}] VENTE {s[:-4]} {pnl:+.1%}",f"{why}. Vente fictive a {last:g} $."))
        del st["pos"][s]
# 2) entrees : seulement sur une nouvelle bougie 4h cloturee
bar=int(now//14400)*14400*1000
if bar>st.get("last_bar",0):
    st["last_bar"]=bar
    t=requests.get(BASE+"/ticker/24hr",timeout=30).json()
    u=[x["symbol"] for x in sorted(t,key=lambda x:-float(x["quoteVolume"])) if x["symbol"].endswith("USDT") and okb(x["symbol"][:-4]) and int(x.get("count",0))>0][:40]
    eq=st["cash"]+sum(p["cost"]*p["last"]/p["entry"] for p in st["pos"].values()); cands=[]
    for s in u:
        if s in st["pos"]: continue
        try:
            k=requests.get(BASE+"/klines",params=dict(symbol=s,interval="4h",limit=60),timeout=20).json()[:-1]
        except Exception: continue
        if len(k)<40: continue
        c=np.array([float(x[4]) for x in k]); v=np.array([float(x[7]) for x in k]); R=rsi(c)
        if R[-1]<RSI_MAX and v[-1]>VX*v[-21:-1].mean() and c[-1]<c[-2]: cands.append((R[-1],s,v[-1]/v[-21:-1].mean()))
    for r_,s,vm in sorted(cands):
        if len(st["pos"])>=MAXP: break
        a=min(eq*SZ,st["cash"])
        if a<5 or s not in px: break
        e=px[s]*(1+SLIP); st["cash"]-=a
        st["pos"][s]=dict(entry=e,last=px[s],cost=a*(1-FEE),t=now)
        st["trades"].append(dict(day=day,side="ACHAT",sym=s,price=e,amount=round(a,2)))
        msgs.append((f"[{L}] ACHAT {s[:-4]}",f"Achat fictif de {s[:-4]} a {px[s]:g} $ pour {a:.0f} EUR. RSI 4h {r_:.0f}, volume x{vm:.1f} la moyenne. Objectif +{TP:.0%}, stop -{SL:.0%}, {MAXH} h max."))
eq=st["cash"]+sum(p["cost"]*p["last"]/p["entry"] for p in st["pos"].values())
st["history"].append(dict(day=day,equity=round(eq,2),positions=len(st["pos"]))); st["history"]=st["history"][-1000:]
json.dump(st,open(f,"w"),indent=1)
for ti,b in msgs: issue(ti,b+f"\n\nCapital fictif {L} : {eq:.2f} EUR (depart 1000 EUR).")
print(L,day,round(eq,2),[m[0] for m in msgs])
