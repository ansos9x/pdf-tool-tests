import json, re
d = json.load(open("test/crawl2.json"))
reqs = d["reqs"]
rows = []
for u, (st, typ, pages, n) in reqs.items():
    if u.startswith("blob:") or u.startswith("data:"):
        continue
    outside = u.startswith("https://ai4me.cfd/") and not u.startswith("https://ai4me.cfd/pdf/")
    bad = not (st == 200 or st == 304 or st == 301)
    if bad or outside:
        rows.append((st, typ, u, len(pages), pages[:2]))
rows.sort(key=lambda r: r[2])
ok = [u for u, v in reqs.items() if v[0] == 200 and u.startswith("https://ai4me.cfd/pdf/")]
ext = sorted({re.match(r"https?://[^/]+", u).group(0) for u in reqs if not u.startswith(("blob:", "data:", "https://ai4me.cfd"))})
by = {}
for r in rows:
    by.setdefault(str(r[0]), []).append(r)
print("pages crawled", len(d["pst"]), "non200 pages", [x for x in d["pst"].items() if x[1] != 200])
print("total unique requests", len(reqs), "ok in /pdf", len(ok), "external origins", ext)
for k, v in by.items():
    print(k, len(v))
with open("test/asset_defects.tsv", "w") as f:
    f.write("status\ttype\turl\tpages_affected\texample_page\n")
    for r in rows:
        f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4][0] if r[4] else ''}\n")
for r in rows:
    print(r[0], r[1], r[2], r[3])
cons = d["cons"]
c = {}
for p, ms in cons.items():
    for m in ms:
        c[m[:110]] = c.get(m[:110], 0) + 1
print("CONSOLE"); [print(v, k) for k, v in sorted(c.items(), key=lambda x: -x[1])[:15]]
