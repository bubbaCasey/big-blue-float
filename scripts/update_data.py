#!/usr/bin/env python3
"""Download the MBARI data file for the Big Blue float (WMO 1902753) and
convert it to data/float.json, which the tracking and data pages read.

Standard library only, so it runs on a plain GitHub Actions runner.
"""
import csv
import datetime as dt
import json
import os
import re
import urllib.request

WMO_ID = "1902753"
SOURCE_URL = f"https://www3.mbari.org/lobo/Data/FloatVizData//{WMO_ID}.txt"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "data", "float.json")

# The file uses -1e10 for missing values.
MISSING_THRESHOLD = -1e9

# Quality flags: 0 = good, 4 = questionable, 8 = bad, 1 = missing or not inspected.
# Values flagged 1 or 8 are dropped. Questionable (4) values are kept.
DROP_FLAGS = {1, 8}

# Column header in the MBARI file -> key used in the JSON output.
VARIABLES = {
    "Pressure[dbar]": "pressure",
    "Depth[m]": "depth",
    "Temperature[°C]": "temperature",
    "Salinity[pss]": "salinity",
    "Oxygen[µmol/kg]": "oxygen",
    "Nitrate[µmol/kg]": "nitrate",
    "Chl_a[mg/m^3]": "chlorophyll",
    "pHinsitu[Total]": "ph",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "big-blue-float-site/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def clean(value, flag):
    """Return a rounded float, or None if the value is missing or flagged bad."""
    try:
        v = float(value)
        f = int(float(flag))
    except ValueError:
        return None
    if v <= MISSING_THRESHOLD or f in DROP_FLAGS:
        return None
    return round(v, 4)


def main():
    text = fetch(SOURCE_URL)

    m = re.search(r"//File updated on (.+)", text)
    source_updated = m.group(1).strip() if m else None

    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("//")]
    reader = csv.reader(lines, delimiter="\t")
    header = next(reader)
    col = {name: i for i, name in enumerate(header)}

    st_i = col["Station"]
    date_i = col["mon/day/yr"]
    time_i = col["hh:mm"]
    lat_i = col["Lat [°N]"]
    lon_i = col["Lon [°E]"]

    # Each measured variable is followed by its quality-flag column ("QF").
    var_cols = {}
    for name, key in VARIABLES.items():
        i = col.get(name)
        if i is not None and i + 1 < len(header) and header[i + 1] == "QF":
            var_cols[key] = i

    groups = {}
    for row in reader:
        if len(row) < len(header):
            continue
        gkey = (row[st_i], row[date_i], row[time_i])
        if gkey not in groups:
            groups[gkey] = {
                "station": int(row[st_i]),
                "ts": dt.datetime.strptime(f"{row[date_i]} {row[time_i]}", "%m/%d/%Y %H:%M"),
                "lat": round(float(row[lat_i]), 4),
                "lon": round(float(row[lon_i]), 4),
                "levels": {k: [] for k in var_cols},
            }
        g = groups[gkey]
        for key, i in var_cols.items():
            g["levels"][key].append(clean(row[i], row[i + 1]))

    profiles = []
    for g in sorted(groups.values(), key=lambda g: g["ts"]):
        profiles.append({
            "station": g["station"],
            "timestamp_utc": g["ts"].strftime("%Y-%m-%dT%H:%MZ"),
            "lat": g["lat"],
            "lon": g["lon"],
            "levels": g["levels"],
        })

    out = {
        "wmo_id": WMO_ID,
        "bgc_id": "UW 23357",
        "project": "GO-BGC",
        "source_url": SOURCE_URL,
        "source_file_updated": source_updated,
        "variables": list(var_cols),
        "profiles": profiles,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)

    print(f"Wrote {len(profiles)} profiles to {OUT_PATH}")


if __name__ == "__main__":
    main()
