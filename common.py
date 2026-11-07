
import json, os, requests, datetime as dt
BASE="https://data-api.binance.vision/api/v3"; FEE=0.001
def prices():
    return {x["symbol"]:float(x["price"]) for x in requests.get(BASE+"/ticker/price",timeout=20).json()}
def issue(title,body):
    tok=os.environ.get("GH_TOKEN"); repo=os.environ.get("GITHUB_REPOSITORY")
    if tok and repo: requests.post(f"https://api.github.com/repos/{repo}/issues",headers={"Authorization":f"Bearer {tok}"},json={"title":title,"body":body},timeout=20)
def load(name):
    f=f"state_{name}.json"
    return json.load(open(f)) if os.path.exists(f) else {"cash":1000.0,"pos":{},"history":[],"trades":[]}
def rebalance(name,label,st,targets,px,stop=None):
    day=str(dt.date.today()); msgs=[]
    for s,p in st["pos"].items(): p["last"]=px.get(s,p["last"])
    for s in list(st["pos"]):
        p=st["pos"][s]; hit=stop and p["last"]<=p["entry"]*(1-stop)
        if s not in targets or hit:
            out=p["qty"]*p["last"]*(1-FEE); pnl=out/p["cost"]-1; st["cash"]+=out; del st["pos"][s]
            st["trades"].append(dict(day=day,side="VENTE",sym=s,price=p["last"],pnl=round(pnl,4)))
            msgs.append((f"[{label}] VENTE {s[:-4]} {pnl:+.1%}",f"{day} : vente de {s[:-4]} a {p['last']:g} $. Resultat : {pnl:+.2%}."))
    eq=st["cash"]+sum(p["qty"]*p["last"] for p in st["pos"].values())
    new=[s for s in targets if s not in st["pos"] and s in px]
    for s in new:
        a=min(eq/st.get("slots",max(len(targets),1)),st["cash"])
        if a<1: break
        st["cash"]-=a; st["pos"][s]=dict(qty=a*(1-FEE)/px[s],entry=px[s],cost=a,last=px[s],day=day)
        st["trades"].append(dict(day=day,side="ACHAT",sym=s,price=px[s],amount=round(a,2)))
        msgs.append((f"[{label}] ACHAT {s[:-4]}",f"{day} : achat fictif de {s[:-4]} a {px[s]:g} $ pour {a:.2f} EUR."))
    eq=st["cash"]+sum(p["qty"]*p["last"] for p in st["pos"].values())
    st["history"].append(dict(day=day,equity=round(eq,2),positions=len(st["pos"])))
    json.dump(st,open(f"state_{name}.json","w"),indent=1)
    for t,b in msgs: issue(t,b+f"\n\nCapital fictif {label} : {eq:.2f} EUR (depart 1000 EUR).")
    print(label,day,round(eq,2),[m[0] for m in msgs])
