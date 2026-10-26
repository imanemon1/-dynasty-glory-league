import json,urllib.request,os,time,datetime,sys
os.makedirs("data",exist_ok=True)
out="data/news.json"
HOSTS=("nfs.faireconomy.media","cdn-nfs.faireconomy.media")

def get(week):
    # try each host, retry with growing waits (the feed answers 429 when asked too often)
    last=None
    for attempt in range(4):
        for h in HOSTS:
            try:
                r=urllib.request.urlopen(urllib.request.Request("https://%s/ff_calendar_%s.json"%(h,week),headers={"User-Agent":"Mozilla/5.0"}),timeout=30)
                return json.load(r)
            except Exception as e:
                last=e
                print(week,h,"failed:",e)
        time.sleep(20*(attempt+1))
    raise last

try:
    rows=get("thisweek")
    try:
        rows+=get("nextweek")
    except Exception as e:
        print("nextweek not available:",e)
    ev=[{"t":x["title"],"d":x["date"],"i":x["impact"],"f":x.get("forecast",""),"p":x.get("previous","")} for x in rows if x.get("country")=="USD"]
    if not ev:
        raise Exception("empty feed")
    ev.sort(key=lambda e:e["d"])
    json.dump({"updated":datetime.datetime.utcnow().isoformat()+"Z","events":ev},open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(len(ev),"USD events")
except Exception as e:
    print("fetch failed, keeping old file:",e)
    sys.exit(0)
