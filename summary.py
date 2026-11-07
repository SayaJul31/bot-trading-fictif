
import json, glob, os, datetime as dt
names={"state.json":"Zero Lag (daily)","state_momentum.json":"Momentum (hebdo)","state_narratifs.json":"Narratifs (hebdo)","state_copy.json":"Copy trading Hyperliquid","state_volume.json":"Volume whales (daily)","state_zl4h.json":"Zero Lag 4h","state_zl1h.json":"Zero Lag 1h","state_majors.json":"Majeures BTC/ETH/SOL"}
rows=[]
for f,n in names.items():
    if not os.path.exists(f): rows.append((n,100.0,0,0,0,"pas encore lance")); continue
    s=json.load(open(f)); h=s.get("history",[])
    eq=h[-1]["equity"] if h else 100.0
    sells=[t for t in s.get("trades",[]) if t["side"]=="VENTE"]
    win=sum(1 for t in sells if t.get("pnl",0)>0)
    pos=", ".join(k[:-4] for k in s.get("pos",{})) or "aucune"
    rows.append((n,eq,len(s.get("trades",[])),len(sells),win,pos))
rows.sort(key=lambda r:-r[1])
out=["# Classement des bots (argent fictif, depart 100 EUR chacun)","",f"Mis a jour : {dt.datetime.utcnow():%d/%m/%Y %H:%M} UTC","","| Rang | Bot | Capital | Perf | Trades | Ventes gagnantes | Positions |","|---|---|---|---|---|---|---|"]
for i,(n,eq,nt,ns,w,p) in enumerate(rows,1):
    out.append(f"| {i} | {n} | {eq:.2f} EUR | {eq-100:+.1f} % | {nt} | {w}/{ns} | {p} |")
out+=["","Aucun argent reel. Les trades sont dans l'onglet Issues."]
open("README.md","w").write("\n".join(out))
