
import json, glob, os, datetime as dt
names={"state.json":"Zero Lag 4h (top 100)","state_momentum.json":"Momentum (4h)","state_narratifs.json":"Narratifs (4h)","state_copy.json":"Copy trading Hyperliquid (4h)","state_volume.json":"Volume whales (4h)","state_zl4h.json":"Zero Lag 4h (top 60)","state_zl1h.json":"Zero Lag 1h","state_cassure.json":"Cassure de zone (4h)","state_trois.json":"3 indicateurs (4h)","state_memes.json":"Memecoins Solana (Pump Fun)","state_vol4h.json":"Volume 4h (achat des chutes)"}
rows=[]
for f,n in names.items():
    if not os.path.exists(f): rows.append((n,1000.0,0,0,0,"pas encore lance")); continue
    s=json.load(open(f)); h=s.get("history",[])
    eq=h[-1]["equity"] if h else 1000.0
    sells=[t for t in s.get("trades",[]) if t["side"]=="VENTE"]
    win=sum(1 for t in sells if t.get("pnl",0)>0)
    pos=", ".join(k[:-4] for k in s.get("pos",{})) or "aucune"
    rows.append((n,eq,len(s.get("trades",[])),len(sells),win,pos))

def _eq(f):
    if not os.path.exists(f): return 1000.0
    h=json.load(open(f)).get("history",[]); return h[-1]["equity"] if h else 1000.0
for _n,_fs in [("EQUIPE 2 (Zero Lag + Cassure)",["state.json","state_cassure.json"]),("EQUIPE 3 (Zero Lag + Cassure + Volume)",["state.json","state_cassure.json","state_volume.json"])]:
    rows.append((_n,sum(_eq(f) for f in _fs)/len(_fs),0,0,0,"capital partage entre "+str(len(_fs))+" bots"))
rows.sort(key=lambda r:-r[1])
out=["# Classement des bots (argent fictif, depart 1000 EUR chacun)","",f"Mis a jour : {dt.datetime.utcnow():%d/%m/%Y %H:%M} UTC","","| Rang | Bot | Capital | Perf | Trades | Ventes gagnantes | Positions |","|---|---|---|---|---|---|---|"]
for i,(n,eq,nt,ns,w,p) in enumerate(rows,1):
    out.append(f"| {i} | {n} | {eq:.2f} EUR | {(eq/1000-1)*100:+.1f} % | {nt} | {w}/{ns} | {p} |")
out+=["","Aucun argent reel. Les trades sont dans l'onglet Issues."]
open("README.md","w").write("\n".join(out))
