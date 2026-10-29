"""Rebuild the Big Blue float page from MBARI's FloatViz data file.

Standard library only. Usage:
    python3 build.py TEMPLATE OUT_DIR [OLD_DATA_JSON]

Writes OUT_DIR/index.html, OUT_DIR/embed.html (light-only, for Google Sites)
and OUT_DIR/data.json. Exit code 0 = new data built, 3 = nothing new
(OLD_DATA_JSON matches), anything else = error (pages left alone).
"""
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request

URL = "https://www3.mbari.org/lobo/Data/FloatVizData/1902753.txt"
MISSING = -1e9  # file uses -1e10


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "big-blue-float-page"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", errors="replace")


def num(s):
    try:
        v = float(s)
    except ValueError:
        return None
    return None if v <= MISSING else v


def parse(text):
    lines = text.splitlines()
    file_date = next((l.split("on", 1)[1].strip() for l in lines if l.startswith("//File updated")), "")
    hdr_i = next(i for i, l in enumerate(lines) if l.startswith("Cruise\t"))
    hdr = lines[hdr_i].split("\t")

    def col(prefix):
        return next(i for i, h in enumerate(hdr) if h.startswith(prefix))

    C = {"p": col("Pressure"), "t": col("Temperature"), "s": col("Salinity"), "sig": col("Sigma_theta"),
         "z": col("Depth"), "o2": col("Oxygen["), "o2s": col("OxygenSat"), "no3": col("Nitrate"),
         "chl": col("Chl_a"), "bbp": col("b_bp700"), "ph": col("pHinsitu"), "irr": col("DOWNWELL_PAR")}
    nd = {"z": 1, "t": 4, "s": 4, "sig": 3, "o2": 2, "o2s": 1, "no3": 2, "chl": 4, "bbp": 3, "ph": 4, "irr": 4}

    stations = {}
    for l in lines[hdr_i + 1:]:
        f = l.split("\t")
        if len(f) < len(hdr) - 1 or not f[1].strip().isdigit():
            continue
        st = int(f[1])
        d = stations.setdefault(st, {"cycle": st, "date": f[3], "time": f[4],
                                     "lon": num(f[5]), "lat": num(f[6]), "rows": []})
        row = {}
        for k, i in C.items():
            if k == "p":
                continue
            v = num(f[i])
            qf = f[i + 1].strip() if i + 1 < len(f) else "0"
            if v is not None and qf == "8":  # flagged bad
                v = None
            if v is not None and k == "bbp":
                v *= 1e4
            row[k] = None if v is None else round(v, nd[k])
        if row.get("z") is None or row.get("t") is None or row.get("s") is None:
            continue
        d["rows"].append(row)

    profiles, pending, last = [], [], None
    for st in sorted(stations):
        d = stations[st]
        m, dd, yy = d["date"].split("/")
        p = {"cycle": st, "utc": f"{yy}-{m}-{dd}T{d['time']}", "rows": sorted(d["rows"], key=lambda r: r["z"])}
        complete = (p["rows"] and p["rows"][0]["z"] < 50 and len(p["rows"]) >= 30
                    and sum(r["o2"] is not None for r in p["rows"]) >= 30)
        if not complete:  # float hasn't sent the whole dive yet
            pending.append({"cycle": st, "utc": p["utc"]})
            continue
        if d["lat"] is None or d["lon"] is None:
            if last is None:
                continue
            p.update(lat=last[0], lon=last[1], posEst=True)
        else:
            p.update(lat=round(d["lat"], 4), lon=round(d["lon"], 4))
            last = (p["lat"], p["lon"])
        profiles.append(p)
    return profiles, pending, file_date


def light_only(html):
    html = re.sub(r"/\*DARK-START\*/.*?/\*DARK-END\*/\n", "", html, flags=re.S)
    html = re.sub(r"/\*DARK-JS-START\*/.*?/\*DARK-JS-END\*/\n", "", html, flags=re.S)
    return (html.replace("body{margin:0;background:var(--bg)", "body{margin:0;background:#FFFFFF")
                .replace("--bg:#EAF1F4", "--bg:#F3F7F9")
                .replace("header{padding:32px 0 20px}", "header{padding:16px 0 12px}"))


def main():
    template, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    old = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
    profiles, pending, file_date = parse(fetch())
    if not profiles:
        sys.exit("No profiles with chemistry found; pages left unchanged.")
    data = json.dumps({"profiles": profiles, "pending": pending}, separators=(",", ":"))
    if old and old.exists() and old.read_text().strip() == data:
        print(f"NO_NEW_DATA: {len(profiles)} profiles, latest {profiles[-1]['cycle']}")
        sys.exit(3)
    today = dt.datetime.now(dt.timezone.utc).strftime("%b %d, %Y").replace(" 0", " ")
    try:
        m, d, rest = file_date.split("/")
        fdate = dt.date(int(rest[:4]), int(m), int(d)).strftime("%b %d, %Y").replace(" 0", " ")
    except Exception:
        fdate = file_date or "unknown"
    page = (template.read_text().replace("__DATA__", json.dumps(profiles, separators=(",", ":")))
            .replace("__PENDING__", json.dumps(pending, separators=(",", ":")))
            .replace("__DLDATE__", today).replace("__FILEDATE__", fdate))
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page)
    (out / "embed.html").write_text(light_only(page))
    (out / "data.json").write_text(data)
    print(f"BUILT: {len(profiles)} profiles, latest cycle {profiles[-1]['cycle']} ({profiles[-1]['utc']} UTC); "
          f"{len(pending)} partly received")


if __name__ == "__main__":
    main()
