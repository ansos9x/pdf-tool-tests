import json
d=json.load(open('test/crawl.json'))
print(d['out'][:20]); print([(k,v) for k,v in d['pagestat'].items() if v!=200])
for u,v in d['reqs'].items():
    if v[0]!=200 or 'ai4me.cfd/pdf' not in u: print(v[:3],u)
print(len(d['inpdf']));print(d['inpdf'])
