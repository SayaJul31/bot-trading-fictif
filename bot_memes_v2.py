
import json, os, time, requests
from common import issue, FEE
name="memes_v2"; f="state_memes_v2.json"
st=json.load(open(f)) if os.path.exists(f) else {"cash":1000.0,"pos":{},"history":[],"trades":[],"seen":{},"reserve":0.0}
st.setdefault("reserve",0.0)
RES=0.5
def bank(out,cost):
    gain=out-cost
    if gain>0:
        st["reserve"]+=gain*RES; return out-gain*RES
    return out
def rug_ok(a):
    try:
        r=requests.get(f"https://api.rugcheck.xyz/v1/tokens/{a}/report/summary",timeout=15).json()
        return not any(x.get("level")=="danger" for x in (r.get("risks") or []))
    except Exception: return False
DS="https://api.dexscreener.com"
now=time.time(); day=time.strftime("%Y-%m-%d %H:%M",time.gmtime())
def pairs_for(addrs):
    out={}
    for i in range(0,len(addrs),30):
        try:
            r=requests.get(DS+"/latest/dex/tokens/"+",".join(addrs[i:i+30]),timeout=20).json().get("pairs") or []
        except Exception: r=[]
        for p in r:
            if p.get("chainId")!="solana": continue
            a=p["baseToken"]["address"]; liq=(p.get("liquidity") or {}).get("usd") or 0
            if a not in out or liq>((out[a].get("liquidity") or {}).get("usd") or 0): out[a]=p
    return out
SLIP=0.03
msgs=[]
# 1) gestion des positions
if st["pos"]:
    cur=pairs_for(list(st["pos"]))
    for a in list(st["pos"]):
        p=st["pos"][a]; q=cur.get(a)
        liq=((q or {}).get("liquidity") or {}).get("usd") or 0
        px=float(q["priceUsd"]) if q and q.get("priceUsd") else 0.0
        if px>0: p["last"]=px; p["peak"]=max(p.get("peak",px),px)
        mult=(p["last"]/p["entry"]) if p["entry"] else 0
        for lvl,frac,key in ((2,1/3,"t1"),(5,0.5,"t2")):
            if q is not None and liq>=5000 and mult>=lvl and not p.get(key):
                part=p["cost"]*frac; out=part*mult*(1-FEE-SLIP); st["cash"]+=bank(out,part)
                p["cost"]-=part; p[key]=True; p["half"]=True
                st["trades"].append(dict(day=day,side="VENTE",sym=p["sym"],pnl=round(out/part-1,4),why=f"prise de gain partielle a x{lvl}"))
                msgs.append((f"[MEMES V2] GAIN PARTIEL {p['sym']} x{mult:.1f}",f"Vente partielle a x{lvl}. 50 % du benefice part en reserve."))
        why=None
        trail=0.3
        if q is None or liq<5000: why="liquidite disparue (rug probable)"; mult=0.0 if liq<1000 else mult
        elif mult<=0.75 and not p.get("half"): why="stop -25 %"
        elif p["peak"]>=p["entry"]*1.5 and p["last"]<=p["peak"]*(1-trail): why=f"stop suiveur (-{int(trail*100)} % du pic, pic x{p['peak']/p['entry']:.1f})"
        elif now-p["t"]>48*3600 and not p.get("half"): why="duree max 48 h sans decoller"
        elif now-p["t"]>14*86400: why="duree max 14 jours"
        if why:
            out=p["cost"]*mult*(1-FEE-SLIP); st["cash"]+=bank(out,p["cost"])
            pnl=out/p["cost"]-1
            st["trades"].append(dict(day=day,side="VENTE",sym=p["sym"],pnl=round(pnl,4),why=why))
            msgs.append((f"[MEMES V2] VENTE {p['sym']} x{mult:.1f}",f"{why}. Resultat sur la part restante {pnl:+.1%}."))
            del st["pos"][a]
# 2) recherche de nouveaux tokens
try:
    prof=requests.get(DS+"/token-profiles/latest/v1",timeout=20).json()
    boost=requests.get(DS+"/token-boosts/latest/v1",timeout=20).json()
except Exception: prof,boost=[],[]
cand=list(dict.fromkeys([x["tokenAddress"] for x in prof+boost if x.get("chainId")=="solana"]))
cand=[a for a in cand if a not in st["pos"] and a not in st["seen"]]
info=pairs_for(cand)
eq=st["cash"]+st["reserve"]+sum(p["cost"]*(p["last"]/p["entry"]) for p in st["pos"].values())
for a,q in sorted(info.items(),key=lambda kv:-((kv[1].get("volume") or {}).get("h1") or 0)):
    st["seen"][a]=now
    if len(st["pos"])>=10: break
    age_h=(now*1000-(q.get("pairCreatedAt") or 0))/3.6e6
    liq=(q.get("liquidity") or {}).get("usd") or 0
    v1=(q.get("volume") or {}).get("h1") or 0
    tx=(q.get("txns") or {}).get("h1") or {}; b,s_=tx.get("buys",0),tx.get("sells",0)
    ch1=(q.get("priceChange") or {}).get("h1") or 0
    fdv=q.get("fdv") or 0
    ok=(1<=age_h<=72 and liq>=30000 and v1>=50000 and s_>=20 and b>=s_*1.1 and 0<ch1<40 and fdv<=50e6 and liq/max(fdv,1)>=0.03)
    if not ok: continue
    if not rug_ok(a): continue
    amt=min((eq-st["reserve"])*0.05,st["cash"])
    if amt<5: break
    px=float(q["priceUsd"])*(1+SLIP)
    st["cash"]-=amt; sym=q["baseToken"]["symbol"]
    st["pos"][a]=dict(sym=sym,entry=px,last=px,peak=px,cost=amt,t=now,url=q.get("url"))
    st["trades"].append(dict(day=day,side="ACHAT",sym=sym,price=px,amount=round(amt,2)))
    msgs.append((f"[MEMES V2] ACHAT {sym}",f"Achat fictif de {sym} pour {amt:.0f} EUR. Age {age_h:.0f} h, liquidite {liq:,.0f} $, volume 1 h {v1:,.0f} $. {q.get('url')}"))
st["seen"]={k:v for k,v in st["seen"].items() if now-v<7*86400}
eq=st["cash"]+st["reserve"]+sum(p["cost"]*(p["last"]/p["entry"]) for p in st["pos"].values())
st["history"].append(dict(day=day,equity=round(eq,2),reserve=round(st["reserve"],2),positions=len(st["pos"])))
st["history"]=st["history"][-500:]
json.dump(st,open(f,"w"),indent=1)
for t,b in msgs: issue(t,b+f"\n\nCapital fictif MEMES V2 : {eq:.2f} EUR dont {st['reserve']:.2f} EUR en reserve (depart 1000 EUR).")
print(day,round(eq,2),[m[0] for m in msgs])
