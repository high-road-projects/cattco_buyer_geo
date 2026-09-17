# Cattaraugus County Buyer Origins

A Streamlit app showing where buyers of Cattaraugus County, NY homes come
from, and how that mix has shifted year to year. This is a Python/Streamlit
port of an original R/Shiny app built on the same data pipeline.

![Illustrative preview of the main chart -- exact rendering in the app uses Plotly and will look slightly different](docs/preview_main_chart.png)

## What it shows

- **Composition by year** -- a 100%-stacked bar chart of `buyer_geo`
  (buyer origin: in-county, elsewhere upstate NY, NYC/Long Island, out of
  state, out of the US, or unknown) for each sale year. Hover any segment
  for the exact count and share.
- **Detail view** -- pick one `buyer_geo` category from the sidebar dropdown
  to see a dual-axis chart: bars for its raw sale count each year (left
  axis), and a line for its share of *all* sales that year (right axis).

Filters, always applied: one- and two-family residential sales
(`prop_class_last_roll` in `{210, 215}`), sale date on or after 2013-01-01.
All years through 2026 are included; 2026 is a partial year (the source
data run only through July 30, 2026), which is called out in a note under
the title and with an asterisk on the 2026 bar.

## Getting started

```bash
git clone <this-repo-url>
cd <this-repo>
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## About the data

The app expects a `cattco_sales_joined.csv` with (at minimum) these
columns: `sale_year`, `sale_date`, `prop_class_last_roll`, and `buyer_geo`.
This is the file produced by the original R pipeline for this project:

```
join_cattco_sales.R -> add_hasadu_and_school_ratings.R -> add_buyer_geo.R
```

**Two ways to supply it:**

1. Drop it at `data/cattco_sales_joined.csv` and the app loads it
   automatically on startup.
2. Leave `data/` empty and use the file-upload widget that appears in the
   app's sidebar instead.

**A note on privacy:** the source sales data includes buyer and seller
names and mailing addresses. `data/*.csv` is git-ignored by default (see
`.gitignore`) so it's easy to run the app locally without ever committing
that data. If you plan to deploy this publicly (e.g. Streamlit Community
Cloud) and don't want to rely on the upload widget every time, consider
either using a private repo, or committing a version of the CSV with
personally identifying columns removed.

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub (with or without `data/cattco_sales_joined.csv`,
   per the privacy note above).
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo,
   and set the main file path to `app.py`.
3. If you didn't commit the data file, use the sidebar file-uploader after
   the app deploys -- it works the same way on Streamlit Cloud as it does
   locally (per-session; it isn't persisted between visits).

## Repo structure

```
.
├── app.py               # the Streamlit app
├── requirements.txt
├── data/
│   ├── README.md         # what goes here
│   └── cattco_sales_joined.csv   # (you provide this; git-ignored)
├── docs/
│   └── preview_main_chart.png
└── README.md
```
