import json,re,collections,requests
from playwright.sync_api import sync_playwright
B="https://ai4me.cfd"; out={}
def new(b):
    ctx=b.new_context(); pg=ctx.new_page(); L={"fail":[],"cons":[],"reqs":[]}
    pg.on("response",lambda r:(L["reqs"].append((r.status,r.url)),L["fail"].append(f"{r.status} {r.url}") if r.status>=400 else None))
    pg.on("requestfailed",lambda r:L["fail"].append(f"FAILED {r.url}"))
    pg.on("console",lambda m:L["cons"].append(m.type+": "+m.text[:250]) if m.type=="error" else None)
    pg.on("pageerror",lambda e:L["cons"].append("pageerror: "+str(e)[:250]))
    return pg,L
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
    pg,L=new(b); pg.goto(B+"/",wait_until="load"); pg.wait_for_timeout(5000)
    links=pg.eval_on_selector_all("a[href]","e=>e.map(a=>a.href)")
    out["home"]={"status":requests.get(B+"/").status_code,"links":len(links),"fail":L["fail"],"cons":L["cons"]}
    internal=sorted({l.split('#')[0] for l in links if l.startswith(B)})
    st={}
    for u in internal: st[u]=requests.get(u,timeout=30,allow_redirects=False).status_code
    out["internal_links"]=len(internal); out["link_status"]=collections.Counter(st.values())
    out["link_bad"]={u:s for u,s in st.items() if s!=200}
    out["html_links"]=[u for u in internal if u.endswith(".html")][:10]
    out["external"]=sorted({l for l in links if not l.startswith(B)})[:10]
    out["sample_links"]=internal[:8]
    allfail=collections.defaultdict(set)
    pg2,L2=new(b); cur=[""]
    pg2.on("response",lambda r:allfail[f"{r.status} {r.url}"].add(cur[0]) if r.status>=400 else None)
    pg2.on("requestfailed",lambda r:allfail[f"FAILED {r.url}"].add(cur[0]))
    pst={}
    for u in internal:
        cur[0]=u
        try:
            r=pg2.goto(u,wait_until="load",timeout=60000); pg2.wait_for_timeout(1200); pst[u]=r.status
        except Exception as e: pst[u]="ERR "+str(e)[:60]
    out["crawl_status"]=dict(collections.Counter(map(str,pst.values())))
    out["crawl_nonok"]={u:s for u,s in pst.items() if s!=200}
    out["crawl_fail"]={k:sorted(v)[:3] for k,v in allfail.items()}
    out["crawl_cons"]=len(L2["cons"]); out["crawl_cons_sample"]=sorted(set(L2["cons"]))[:10]
    pg,L=new(b); pg.goto(B+"/merge-pdf",wait_until="load"); pg.wait_for_timeout(6000)
    out["merge_cons"]=L["cons"]; out["merge_fail"]=L["fail"]
    out["sw"]=pg.evaluate("""async()=>{const rs=await navigator.serviceWorker.getRegistrations();return {regs:rs.map(r=>({scope:r.scope,script:(r.active||r.installing||r.waiting||{}).scriptURL,state:(r.active||r.installing||r.waiting||{}).state})),controller:!!navigator.serviceWorker.controller}}""")
    pg.reload(wait_until="load"); pg.wait_for_timeout(3000)
    out["sw_after_reload_controller"]=pg.evaluate("!!navigator.serviceWorker.controller")
    out["worker_reqs"]=[r for r in L["reqs"] if re.search(r"worker|\.wasm|config\.json|sw\.js|flexsearch|search",r[1],re.I)]
    pg,L=new(b); pg.goto(B+"/",wait_until="load"); pg.wait_for_timeout(2000)
    try:
        pg.locator("input[type=search],input[placeholder*=earch],#search-input").first.fill("merge"); pg.wait_for_timeout(1500)
        out["search_visible_merge"]=pg.locator("a:visible:has-text('Merge')").count()
    except Exception as e: out["search_err"]=str(e)[:150]
    out["search_cons"]=L["cons"]
    pg,L=new(b); r=pg.goto(B+"/vi/",wait_until="load"); pg.wait_for_timeout(4000)
    out["vi"]={"status":r.status,"lang":pg.evaluate("document.documentElement.lang"),"title":pg.title(),"h1":pg.inner_text("h1")[:120],
      "links":pg.eval_on_selector_all("a[href]","e=>[...new Set(e.map(a=>a.href))]"),"cons":L["cons"],"fail":L["fail"]}
    vl=[l for l in out["vi"]["links"] if l.startswith(B)]
    vs={u:requests.get(u,timeout=30).status_code for u in vl}
    out["vi"]["link_bad"]={u:s for u,s in vs.items() if s!=200}
    out["vi"]["n_internal"]=len(vl); out["vi"]["links"]=vl[:6]
    sw={}
    for path in ["/","/merge-pdf","/vi/"]:
        pg,L=new(b); pg.goto(B+path,wait_until="load"); pg.wait_for_timeout(2500)
        try:
            pg.locator("button:has-text('English'),button:has-text('Tiếng Việt')").first.click(timeout=3000); pg.wait_for_timeout(500)
            tgt="Tiếng Việt" if path!="/vi/" else "English"
            with pg.expect_navigation(timeout=15000): pg.locator(f"button:visible:has-text('{tgt}')").first.click()
            pg.wait_for_timeout(2500)
            sw[path]={"to":pg.url,"lang":pg.evaluate("document.documentElement.lang"),"h1":pg.inner_text("h1")[:80] if pg.locator("h1").count() else "","status":requests.get(pg.url).status_code}
        except Exception as e: sw[path]={"err":str(e)[:150],"url":pg.url}
    out["switch"]=sw
    pg,L=new(b); r=pg.goto(B+"/pdf/merge-pdf",wait_until="load"); pg.wait_for_timeout(2000)
    rr=requests.get(B+"/pdf/merge-pdf",allow_redirects=False)
    out["old"]={"first_hop":[rr.status_code,rr.headers.get("location")],"final":pg.url,"status":r.status,"title":pg.title(),"fail":L["fail"],"cons":L["cons"],"has_input":pg.locator("#file-input").count()}
    b.close()
json.dump(out,open("test/round2.json","w"),indent=1,ensure_ascii=False,default=str)
print(json.dumps(out,indent=1,ensure_ascii=False,default=str)[:9000])
