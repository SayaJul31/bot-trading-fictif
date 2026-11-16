
from common import *
st=load("narratifs"); px=prices()
import time as _t
if _t.time()-st.get("last_run",0)<3.5*3600:
    print("trop tot (4h)"); raise SystemExit
st["last_run"]=_t.time()
CG="https://api.coingecko.com/api/v3"
CATS=["artificial-intelligence","decentralized-finance-defi","meme-token","layer-1","layer-2","real-world-assets-rwa","gaming","decentralized-exchange","liquid-staking-tokens","depin"]
import time; score={}; coins={}
for c in CATS:
    try:
        m=requests.get(CG+"/coins/markets",params={"vs_currency":"usd","category":c,"order":"volume_desc","per_page":15,"price_change_percentage":"7d"},timeout=20).json()
        m=[x for x in m if (x.get("total_volume") or 0)>20e6 and x.get("price_change_percentage_7d_in_currency") is not None]
        if len(m)>=3:
            score[c]=sum(x["price_change_percentage_7d_in_currency"] for x in m)/len(m)
            coins[c]=[x["symbol"].upper()+"USDT" for x in m]
    except Exception as e: print(c,e)
    time.sleep(3)
targets=[]
for c in sorted(score,key=score.get,reverse=True)[:2]:
    targets+=[s for s in coins[c] if s in px and s not in targets][:3]
print("secteurs",sorted(score.items(),key=lambda x:-x[1])[:3])
rebalance("narratifs","NARRATIFS",st,targets,px,stop=0.15)
