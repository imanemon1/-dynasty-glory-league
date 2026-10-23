import json,urllib.request,os
os.makedirs("data",exist_ok=True)
out="data/news.json"
try:
    rows=[]
    for w in ("thisweek","nextweek"):
        try:
            r=urllib.request.urlopen(urllib.request.Request("https://nfs.faireconomy.media/ff_calendar_%s.json"%w,headers={"User-Agent":"Mozilla/5.0"}),timeout=30)
            rows+=json.load(r)
        except Exception as e:
            if w=="thisweek":raise
    ev=[{"t":x["title"],"d":x["date"],"i":x["impact"],"f":x.get("forecast",""),"p":x.get("previous","")} for x in rows if x.get("country")=="USD"]
    ev.sort(key=lambda e:e["d"])
    import datetime
    json.dump({"updated":datetime.datetime.utcnow().isoformat()+"Z","events":ev},open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(len(ev),"USD events")
except Exception as e:
    print("fetch failed, keeping old file:",e)
