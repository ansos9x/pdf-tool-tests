import json,subprocess,re
from concurrent.futures import ThreadPoolExecutor
d=json.load(open('test/crawl.json'))
host=[l for l in d['links'] if l.startswith('https://ai4me.cfd')]
def st(u):
    r=subprocess.run(["curl","-s","-o","/dev/null","-m","30","-w","%{http_code} %{redirect_url}",u],capture_output=True,text=True).stdout
    return u,r
cands=set(host)
for l in host:
    m=re.match(r"https://ai4me.cfd/([^/]+)\.html$",l)
    if m: cands.add(f"https://ai4me.cfd/pdf/{m.group(1)}"); cands.add(f"https://ai4me.cfd/pdf/{m.group(1)}.html")
with ThreadPoolExecutor(8) as ex: res=sorted(ex.map(st,cands))
open("test/link_status.txt","w").write("\n".join(f"{r} {u}" for u,r in res))
