# Big Blue float

Public pages for Swampscott High School's adopted ocean float, Big Blue
(WMO 1902753, BGC UW 23357, GO-BGC / Adopt a Float).

| Page | File | What it shows |
| --- | --- | --- |
| Tracking | `tracking.html` | Map of the float's track and a table of profile positions |
| Data | `data.html` | Interactive depth profiles for each variable, with CSV download |
| About | `about.html` | Project background, float details, data source, and flag notes |

## How it updates

1. `.github/workflows/update-data.yml` runs every 6 hours (and can be run by hand).
2. It runs `scripts/update_data.py`, which downloads the MBARI data file for WMO 1902753
   and writes `data/float.json`.
3. If the data changed, the workflow commits and pushes the new file.
4. The pages read `data/float.json` in the browser, so they always show the latest data
   without any manual edits.

Nothing needs to be edited when new profiles arrive.

## One-time setup

```bash
cd big-blue-float
git init -b main
git add .
git commit -m "Initial site"
git remote add origin https://github.com/<your-username>/big-blue-float.git
git push -u origin main
```

Then, on GitHub:

1. **Turn on GitHub Pages:** Settings → Pages → Build and deployment → Source: *Deploy from a branch*,
   Branch: `main`, folder: `/ (root)`. The site will be at
   `https://<your-username>.github.io/big-blue-float/tracking.html`.
2. **Run the data job once:** Actions → *Update float data* → *Run workflow*.
   After it finishes, `data/float.json` will contain the latest profiles.

## Preview locally

The pages load data with `fetch`, so open them through a local server rather than by double-clicking:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/tracking.html
```

To refresh the data by hand on your computer: `python3 scripts/update_data.py`

## Data source and credit

Float data: MBARI, GO-BGC project. Source file:
https://www3.mbari.org/lobo/Data/FloatVizData//1902753.txt
