"""
Where Cattaraugus County home buyers come from
------------------------------------------------
Streamlit translation of the original R/Shiny app. Shows:

  1. A 100%-stacked bar chart of buyer_geo composition by sale year.
  2. A drill-down section: pick one buyer_geo level and see a dual-axis
     chart of its raw sale count (bars, left axis) and its share of all
     sales (line, right axis), by year.

Filters (always applied, matching the Shiny app): prop_class_last_roll in
{210, 215}, and sale date on/after 2013-01-01. All years through 2026 are
included; 2026 is a partial year (data run only through July 30, 2026),
which is called out in a note and with an asterisk on the 2026 bar.

Data: expects a `cattco_sales_joined.csv` with a `buyer_geo` column already
computed (the file produced by the original R pipeline: join_cattco_sales.R
-> add_hasadu_and_school_ratings.R -> add_buyer_geo.R). If data/cattco_sales_joined.csv
isn't present in the repo, the app offers a file-upload widget instead --
see the README for why that's the default (the source data includes buyer
names/addresses, which you may not want committed to a public repo).
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LATEST_2026_DATE = "July 30, 2026"
DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "cattco_sales_joined.csv"

GEO_LEVELS = [
    "In Cattaraugus County, NY",
    "In some other upstate NY county",
    "In New York City or Long Island",
    "Outside of New York State",
    "Outside of the US",
    "Unknown",
]
GEO_COLORS = {
    "In Cattaraugus County, NY":       "#08519C",
    "In some other upstate NY county": "#3182BD",
    "In New York City or Long Island": "#6BAED6",
    "Outside of New York State":       "#BDD7E7",
    "Outside of the US":               "#E6550D",
    "Unknown":                         "#BDBDBD",
}

st.set_page_config(
    page_title="Cattaraugus County Buyer Origins",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and filtering sales data...")
def load_base_data(file) -> pd.DataFrame:
    df = pd.read_csv(file, low_memory=False)

    if "buyer_geo" not in df.columns:
        raise ValueError(
            "buyer_geo column not found. This app expects cattco_sales_joined.csv "
            "as produced by the R pipeline (join_cattco_sales.R -> "
            "add_hasadu_and_school_ratings.R -> add_buyer_geo.R)."
        )

    # Always-on filters: property class 210/215, sale date on/after 2013-01-01.
    df["_sale_date"] = pd.to_datetime(df["sale_date"], format="%m/%d/%Y")
    base = df[
        df["prop_class_last_roll"].isin([210, 215])
        & (df["_sale_date"] >= "2013-01-01")
    ].copy()

    # buyer_geo's missing values are shown here as an explicit "Unknown"
    # category (the source CSV itself is untouched).
    base["buyer_geo"] = pd.Categorical(
        base["buyer_geo"].fillna("Unknown"),
        categories=GEO_LEVELS,
        ordered=True,
    )
    return base


@st.cache_data
def build_summary(base_data: pd.DataFrame) -> pd.DataFrame:
    """One row per (sale_year, buyer_geo) with count, year total, and share."""
    summary = (
        base_data.groupby(["sale_year", "buyer_geo"], observed=False)
        .size()
        .rename("n")
        .reset_index()
    )
    summary["year_total"] = summary.groupby("sale_year")["n"].transform("sum")
    summary["pct"] = summary["n"] / summary["year_total"]
    return summary.sort_values(["sale_year", "buyer_geo"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------
def build_main_chart(summary_data: pd.DataFrame) -> go.Figure:
    year_order = [str(y) for y in sorted(summary_data["sale_year"].unique())]

    fig = go.Figure()
    for level in GEO_LEVELS:
        d = summary_data[summary_data["buyer_geo"] == level].sort_values("sale_year")
        fig.add_trace(go.Bar(
            x=d["sale_year"].astype(str),
            y=d["n"],
            name=level,
            marker_color=GEO_COLORS[level],
            marker_line_color="white",
            marker_line_width=0.6,
            customdata=list(zip(d["pct"] * 100, d["n"], d["year_total"])),
            hovertemplate=(
                "Year: %{x}<br>" + level + "<br>"
                "%{customdata[0]:.1f}% (%{customdata[1]:.0f} of %{customdata[2]:.0f} sales)"
                "<extra></extra>"
            ),
        ))

    # n= labels above each bar (asterisk flags the partial 2026 year)
    year_totals = summary_data.drop_duplicates("sale_year")[["sale_year", "year_total"]]
    bar_annotations = [
        dict(
            x=str(row.sale_year), y=103, xref="x", yref="y",
            text=(f"n={row.year_total}*" if row.sale_year == 2026 else f"n={row.year_total}"),
            showarrow=False, font=dict(size=11, color="grey"),
        )
        for row in year_totals.itertuples()
    ]
    footnote = dict(
        x=0, y=-0.22, xref="paper", yref="paper",
        text=f"* 2026 reflects sales through {LATEST_2026_DATE} only.",
        showarrow=False, font=dict(size=10, color="grey"), align="left",
    )

    fig.update_layout(
        barmode="stack",
        barnorm="percent",
        title_text="<b>Where Cattaraugus County home buyers come from</b>",
        title_x=0,
        title_font=dict(size=20),
        xaxis=dict(title="Sale year", type="category", categoryorder="array", categoryarray=year_order),
        yaxis=dict(title="Share of sales", ticksuffix="%", range=[0, 112]),
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left", yanchor="top"),
        margin=dict(r=220, t=70, b=90),
        annotations=bar_annotations + [footnote],
        height=560,
        template="plotly_white",
    )
    return fig


def build_detail_chart(summary_data: pd.DataFrame, level: str) -> go.Figure:
    d = summary_data[summary_data["buyer_geo"] == level].sort_values("sale_year")
    years = d["sale_year"].astype(str)
    year_order = [str(y) for y in sorted(summary_data["sale_year"].unique())]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=d["n"],
        name="Sales (count)",
        marker_color="#3182BD",
        hovertemplate="Year: %{x}<br>Sales: %{y}<extra></extra>",
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=years, y=d["pct"] * 100,
        name="Share of all sales (%)",
        mode="lines+markers",
        line=dict(color="#E6550D", width=3),
        marker=dict(color="#E6550D", size=8),
        hovertemplate="Year: %{x}<br>Share: %{y:.1f}%<extra></extra>",
        yaxis="y2",
    ))
    fig.update_layout(
        title_text=f"<b>Detail: {level} over time</b>",
        title_x=0,
        xaxis=dict(title="Sale year", type="category", categoryorder="array", categoryarray=year_order),
        yaxis=dict(title="Number of sales", rangemode="tozero"),
        yaxis2=dict(
            title="Share of all sales (%)", overlaying="y", side="right",
            rangemode="tozero", ticksuffix="%", showgrid=False,
        ),
        legend=dict(orientation="h", x=0, y=-0.25),
        hovermode="x unified",
        height=460,
        margin=dict(b=90, r=60, t=60),
        template="plotly_white",
    )
    return fig


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------
st.title("Where Cattaraugus County home buyers come from")

data_source = None
if DEFAULT_DATA_PATH.exists():
    data_source = DEFAULT_DATA_PATH
else:
    st.sidebar.warning("No bundled data found.")
    uploaded = st.sidebar.file_uploader("Upload cattco_sales_joined.csv", type="csv")
    if uploaded is not None:
        data_source = uploaded

if data_source is None:
    st.info(
        "Upload **cattco_sales_joined.csv** using the file uploader in the "
        "sidebar to get started (or add it at `data/cattco_sales_joined.csv` "
        "in this repo -- see the README)."
    )
    st.stop()

try:
    base_data = load_base_data(data_source)
except ValueError as e:
    st.error(str(e))
    st.stop()

summary_data = build_summary(base_data)

st.markdown(
    f"""
    <div style="background-color:#EFF6FC; border-left:4px solid #08519C;
                padding:10px 15px; margin-bottom:18px; font-size:13.5px; color:#333;">
      <strong>Note:</strong> 2026 sales data run only through {LATEST_2026_DATE}.
      Full-year 2026 figures are not yet available, so the 2026 bar below is
      not comparable to a complete year.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        "One- and two-family residential sales (property class 210/215), "
        "on or after January 1, 2013."
    )
    st.divider()
    geo_level = st.selectbox(
        "Detail view: buyer origin",
        GEO_LEVELS,
        index=0,
    )
    st.caption(
        "Choose a category to see its sale count and share of the market "
        "by year in the chart below."
    )

st.plotly_chart(build_main_chart(summary_data), use_container_width=True)

st.divider()
st.subheader(f"Detail: {geo_level} over time")
st.plotly_chart(build_detail_chart(summary_data, geo_level), use_container_width=True)
