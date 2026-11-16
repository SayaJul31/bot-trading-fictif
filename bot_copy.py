
from common import *
st=load("copy"); px=prices()
import time as _t
if _t.time()-st.get("last_run",0)<3.5*3600:
    print("trop tot (4h)"); raise SystemExit
st["last_run"]=_t.time()
HL="https://api.hyperliquid.xyz/info"
lb=requests.get("https://stats-data.hyperliquid.xyz/Mainnet/leaderboard",timeout=60).json()["leaderboardRows"]
def perf(r,w):
    d=dict(r["windowPerformances"]).get(w,{}); return float(d.get("pnl",0)),float(d.get("roi",0))
cand=[r for r in lb if float(r["accountValue"])>1e6 and perf(r,"month")[0]>0 and perf(r,"allTime")[0]>0]
cand=sorted(cand,key=lambda r:perf(r,"month")[1],reverse=True)[:20]
net={}
for r in cand:
    try:
        cs=requests.post(HL,json={"type":"clearinghouseState","user":r["ethAddress"]},timeout=20).json()
        av=float(cs["marginSummary"]["accountValue"]) or 1
        for p in cs["assetPositions"]:
            q=p["position"]; s=q["coin"]+"USDT"; n=float(q["szi"])*float(q.get("entryPx") or 0)/av
            net[s]=net.get(s,0)+n
    except Exception as e: print(e)
targets=[s for s in sorted(net,key=net.get,reverse=True) if net[s]>0 and s in px][:5]
print("top longs",[(s,round(net[s],2)) for s in targets])
rebalance("copy","COPY",st,targets,px,stop=0.15)
