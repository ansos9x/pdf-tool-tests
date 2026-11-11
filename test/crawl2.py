import json,re
from playwright.sync_api import sync_playwright
d=json.load(open('test/crawl.json'))
tools=sorted({re.match(r"https://ai4me.cfd/([^/]+)\.html$",l).group(1) for l in d['links'] if re.match(r"https://ai4me.cfd/([^/]+)\.html$",l)})
urls=["https://ai4me.cfd/pdf/vi/"]+[f"https://ai4me.cfd/pdf/{t}" for t in tools]
reqs={};pst={};cons={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_context().new_page(); cur=[""]
    pg.on("response",lambda r:reqs.setdefault(r.url,[r.status,r.request.resource_type,set()])[2].add(cur[0]))
    pg.on("requestfailed",lambda r:reqs.setdefault(r.url,["FAILED "+str(r.failure),r.resource_type,set()])[2].add(cur[0]))
    pg.on("console",lambda m:cons.setdefault(cur[0],[]).append(m.type+": "+m.text[:200]) if m.type in("error","warning") else None)
    pg.on("pageerror",lambda e:cons.setdefault(cur[0],[]).append("pageerror: "+str(e)[:200]))
    for u in urls:
        cur[0]=u
        try: r=pg.goto(u,wait_until="load",timeout=60000); pg.wait_for_timeout(1500); pst[u]=r.status
        except Exception as e: pst[u]="ERR "+str(e)[:80]
    b.close()
json.dump({"pst":pst,"cons":cons,"reqs":{k:[v[0],v[1],sorted(v[2]),len(v[2])] for k,v in reqs.items()}},open("test/crawl2.json","w"),indent=1)
bad=[(v[0],k,len(v[2])) for k,v in reqs.items() if v[0]!=200 or not k.startswith("https://ai4me.cfd/pdf/")]
print(len(urls),len(reqs),[ (u,s) for u,s in pst.items() if s!=200]);
for x in bad: print(x)
print(sum(len(v) for v in cons.values()))
