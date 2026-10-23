#!/usr/bin/env python3
"""Merge a #TRADES message (from trade/ page) into data/trades.json.

usage:
  python3 tools/add_trades.py message.txt        # from file
  pbpaste | python3 tools/add_trades.py          # from stdin
  python3 tools/add_trades.py message.txt --dry  # show result, write nothing

Rows are keyed by (date, number): sending the same day again overwrites (corrections).
Strategy column = team name; matched to data/teams.json (case-insensitive / fuzzy).
"""
import sys, os, re, json, difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADES = os.path.join(ROOT, "data", "trades.json")
TEAMS = os.path.join(ROOT, "data", "teams.json")
LEAGUE = os.path.join(ROOT, "data", "league.json")
RES = {"TP", "CLOSE", "RISK", "SL"}
DIRS = {"BUY", "SELL"}
TF = ["1m", "5m", "15m", "30m", "1h"]
FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫−", "01234567890123456789.-")


def load(p, d):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def num(s):
    s = s.translate(FA).replace(",", ".").replace("$", "").replace(" ", "")
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0


def team_of(raw, names, warn):
    s = raw.strip()
    low = {n.lower(): n for n in names}
    if s.lower() in low:
        return low[s.lower()]
    norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    nm = {norm(n): n for n in names}
    if norm(s) in nm:
        return nm[norm(s)]
    m = difflib.get_close_matches(norm(s), list(nm), n=1, cutoff=0.75)
    if m:
        warn.append(f"«{s}» → {nm[m[0]]} (تطبیق تقریبی)")
        return nm[m[0]]
    warn.append(f"«{s}» در teams.json نیست؛ با همین نام ثبت شد")
    return s


def parse(text, names, start, warn):
    date, out = None, []
    for line in text.splitlines():
        line = line.strip().translate(FA)
        if not line:
            continue
        m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
        if line.startswith("تاریخ") and m:
            date = m.group(1)
            continue
        c = [x.strip() for x in line.split("|")]
        if len(c) < 7 or not re.fullmatch(r"\d+", c[0]):
            continue
        if not date:
            warn.append(f"ردیف {c[0]} قبل از خط تاریخ آمده؛ رد شد")
            continue
        if date < start:
            warn.append(f"{date} قبل از شروع لیگ ({start}) است؛ ردیف {c[0]} رد شد")
            continue
        d, r = c[3].upper(), c[4].upper()
        if r not in RES:
            warn.append(f"ردیف {c[0]}: نتیجه‌ی «{c[4]}» نامعتبر؛ رد شد")
            continue
        tr = c[7].split(",") if len(c) > 7 else []
        out.append({
            "date": date, "no": int(c[0]), "team": team_of(c[1], names, warn),
            "time": "" if c[2] in ("-", "") else c[2],
            "dir": d if d in DIRS else "", "res": r,
            "pips": num(c[5]), "usd": num(c[6]),
            "trend": {t: v.strip() for t, v in zip(TF, tr) if v.strip() not in ("-", "")},
            "pincer": len(c) > 8 and c[8] in ("بله", "yes", "Y", "1"),
            "note": "" if len(c) < 10 or c[9] in ("-", "") else " | ".join(c[9:]),
        })
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    dry = "--dry" in sys.argv
    text = open(a[0], encoding="utf-8").read() if a else sys.stdin.read()
    names = [t["name"] for t in load(TEAMS, []) if t.get("name")]
    start = load(LEAGUE, {}).get("start", "2026-10-26")
    warn = []
    new = parse(text, names, start, warn)
    if not new:
        print("هیچ ردیف تریدی پیدا نشد.")
        for w in warn:
            print("⚠", w)
        sys.exit(1)
    db = {(t["date"], t["no"]): t for t in load(TRADES, [])}
    added = sum(1 for t in new if (t["date"], t["no"]) not in db)
    for t in new:
        db[(t["date"], t["no"])] = t
    rows = sorted(db.values(), key=lambda t: (t["date"], t["no"]))
    for w in warn:
        print("⚠", w)
    for t in new:
        print(f'{t["date"]} #{t["no"]:<3} {t["team"]:<16} {t["dir"]:<4} {t["res"]:<5} {t["pips"]:+} pip {t["usd"]:+}$')
    print(f"{added} جدید، {len(new) - added} اصلاح‌شده؛ مجموع {len(rows)} ترید.")
    if dry:
        print("(--dry: چیزی ذخیره نشد)")
        return
    with open(TRADES, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
