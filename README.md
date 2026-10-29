# Big Blue float pages

Live data pages for **Big Blue**, the GO-BGC profiling float (WMO 1902753) adopted by Swampscott High School through the Adopt a Float program.

- **Student page:** https://bubbacasey.github.io/big-blue-float/
- **Google Sites embed (light theme):** https://bubbacasey.github.io/big-blue-float/embed.html

## How it updates

Every morning a GitHub Action (`.github/workflows/update.yml`) downloads the float's data file from MBARI (https://www3.mbari.org/lobo/Data/FloatVizData/1902753.txt), runs `build.py`, and commits new pages to `docs/` only when a new dive has arrived. GitHub Pages serves `docs/`.

To force an update: **Actions → Update Big Blue pages → Run workflow**.

## Files

| File | What it is |
|---|---|
| `template.html` | The page design and charts. Edit this to change wording or layout. |
| `build.py` | Downloads MBARI's file and fills the template (standard-library Python only). |
| `docs/index.html` | Built page (follows light/dark setting). |
| `docs/embed.html` | Built light-only copy for Google Sites. |
| `docs/data.json` | Processed profiles. |

Data: Argo (2000). Argo float data and metadata from Global Data Assembly Centre (Argo GDAC). SEANOE. https://doi.org/10.17882/42182
