import json,re,sys
from urllib.parse import urlparse,urljoin
from playwright.sync_api import sync_playwright
B="https://ai4me.cfd/pdf/"
reqs={}  # url -> (status,type,page)
pages_seen=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
    ctx=b.new_context(); pg=ctx.new_page()
    cur=[""]
    pg.on("response",lambda r:reqs.setdefault(r.url,[r.status,r.request.resource_type,set()])[2].add(cur[0]))
    pg.on("requestfailed",lambda r:reqs.setdefault(r.url,["FAILED "+str(r.failure),r.resource_type,set()])[2].add(cur[0]))
    def load(u):
        cur[0]=u; pg.goto(u,wait_until="load",timeout=60000); pg.wait_for_timeout(2500)
    load(B)
    links=pg.eval_on_selector_all("a[href]","e=>e.map(a=>a.href)")
    hl=sorted({l.split('#')[0] for l in links})
    inpdf=[l for l in hl if urlparse(l).netloc=="ai4me.cfd" and urlparse(l).path.startswith("/pdf")]
    out=[l for l in hl if l not in inpdf]
    root=[l for l in out if urlparse(l).netloc=="ai4me.cfd"]
    pagestat={}
    for l in inpdf:
        if l==B: pagestat[l]=200; continue
        try:
            r=pg.goto(l,wait_until="load",timeout=60000); pg.wait_for_timeout(2500); cur[0]=l; pagestat[l]=r.status
        except Exception as e: pagestat[l]="ERR "+str(e)[:80]
    b.close()
json.dump({"links":hl,"inpdf":inpdf,"out":out,"pagestat":pagestat,"reqs":{k:[v[0],v[1],sorted(v[2])[:3],len(v[2])] for k,v in reqs.items()}},open("test/crawl.json","w"),indent=1)
print(len(hl),len(inpdf),len(reqs))
