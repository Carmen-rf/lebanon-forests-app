"""
Lebanon's Forests: From Carbon Source to Carbon Sink (1990-2021)
Streamlit app built on the FAO forest-emissions data used in my Plotly assignment.

Run locally:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page setup and shared styling (same palette as the Plotly assignment)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lebanon's Forests & CO2",
    page_icon="🌲",
    layout="wide",
)
# Softer, more visible expanders: light grey fill, bold dark-green label
st.markdown(
    """
    <style>
    [data-testid="stExpander"] details {
        background-color: #f5f6f6;
        border: 1px solid #e1e5e4;
        border-radius: 0.6rem;
    }
    [data-testid="stExpander"] summary {
        font-weight: 600;
        color: #134e4a;
    }
    [data-testid="stExpander"] summary:hover {
        color: #0f7b6c;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

NAVY = "#0f7b6c"      # Forestland / removals -> forest teal-green
MAROON = "#ee6c2b"    # Forest conversion / emissions -> clearing orange
GREY = "#cfd4d3"      # context (years outside the selection)
INK = "#1f2933"       # net balance line
BREAK_YEAR = 2011

# Look for the CSV in data/ first, then next to app.py (works whichever way it was uploaded)
HERE = Path(__file__).parent
CANDIDATES = [HERE / "data" / "Dataset.csv", HERE / "Dataset.csv"]
DATA_PATH = next((p for p in CANDIDATES if p.exists()), None)
if DATA_PATH is None:
    st.error(
        "Dataset.csv was not found. Upload it to the repository, either at the top level "
        "next to app.py or inside a folder called data/."
    )
    st.stop()

ERAS = {
    "Full record (1990–2021)": (1990, 2021),
    "Loss era (1990–2010)": (1990, 2010),
    "Recovery era (2011–2021)": (2011, 2021),
}


def style(fig, height=420):
    fig.update_layout(
        template="simple_white",
        font=dict(family="Source Sans 3, Source Sans Pro, Helvetica, sans-serif", size=14, color=INK),
        title=dict(font=dict(size=19, color="#134e4a"), x=0.01, xanchor="left"),
        margin=dict(l=60, r=30, t=70, b=50),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(path=DATA_PATH):
    raw = pd.read_csv(path)
    raw.columns = [c.strip() for c in raw.columns]
    df = raw[["Year", "Item", "Element", "Value"]].copy()
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Year"] = df["Year"].astype(int)
    df = df.dropna(subset=["Value"]).drop_duplicates()

    df["Measure"] = df["Element"].map(lambda e: "area" if e == "Area" else "co2")
    wide = df.pivot_table(index="Year", columns=["Item", "Measure"], values="Value")
    wide.columns = [f"{item}|{measure}" for item, measure in wide.columns]
    wide = wide.rename(
        columns={
            "Forestland|area": "forest_area",          # 1000 ha
            "Forestland|co2": "forest_co2",            # kt CO2 (negative = removal)
            "Net Forest conversion|area": "conv_area",  # 1000 ha cleared per year
            "Net Forest conversion|co2": "conv_co2",    # kt CO2 emitted by clearing
        }
    ).reset_index()
    wide["net_co2"] = wide["forest_co2"] + wide["conv_co2"]
    return wide.sort_values("Year").reset_index(drop=True)


def summarise(d):
    """Headline numbers for a slice of years."""
    return {
        "n_years": len(d),
        "area_start": d["forest_area"].iloc[0],
        "area_end": d["forest_area"].iloc[-1],
        "area_change_ha": (d["forest_area"].iloc[-1] - d["forest_area"].iloc[0]) * 1000,
        "removed": -d["forest_co2"].sum(),     # kt, shown as positive
        "emitted": d["conv_co2"].sum(),        # kt
        "net": d["net_co2"].sum(),             # kt, negative = net sink
        "cleared_ha": d["conv_area"].sum() * 1000,
    }


df = load_data()
full = summarise(df)
pre = df[df["Year"] < BREAK_YEAR]
post = df[df["Year"] >= BREAK_YEAR]

# ---------------------------------------------------------------------------
# Header and context
# ---------------------------------------------------------------------------
st.title("Lebanon's Forests: From Carbon Source to Carbon Sink")
st.markdown(
    "#### How much CO2 did Lebanon's forests release or absorb between 1990 and 2021, "
    "and when did things change?"
)

st.markdown(
    """
Forests affect the climate in two directions. **Standing forest (Forestland)** pulls CO2
out of the air as trees grow, which FAO records as a *negative* number (a removal).
**Forest conversion**, meaning forest cleared for other uses, releases CO2, recorded as a
*positive* number (an emission). Adding the two gives the forest sector's **net balance**:
below zero means the forests clean more CO2 than they release, above zero means they add to it.
"""
)

with st.expander("About the data"):
    st.markdown(
        f"""
- **Source:** FAO, FAOSTAT *Emissions from Forests* ([fao.org/faostat](https://www.fao.org/faostat/en/#data/EM)),
  republished for Lebanon by AUB's CODEC linked-data portal.
- **Coverage:** Lebanon, yearly, 1990–2021 ({len(df)} years). Two items (Forestland and Net Forest
  conversion), each with an **area** (thousand hectares) and a **net CO2** value (kilotonnes).
- **Why the lines look like steps:** FAO estimates forest change per reporting period
  (1990–2000, 2001–2010, 2011–2015, 2016–2021) and spreads it evenly across the years
  in that period. So CO2 values are flat inside a period and forest area moves in straight lines.
  Changes *between* periods are real signals, but year-to-year wiggles inside a period are not.
- **A consistency check:** in the 1990s forest area falls by exactly
  {df.loc[df.Year == 1995, 'conv_area'].iloc[0] * 1000:.0f} ha a year, which is the same as the area
  converted each year, so the two items add up.
- 1 kt = 1,000 tonnes of CO2.
"""
    )

# ---------------------------------------------------------------------------
# Headline insights (full record)
# ---------------------------------------------------------------------------
st.subheader("Two things worth knowing")
c1, c2 = st.columns(2)

area_low_year = int(df.loc[df["forest_area"].idxmin(), "Year"])
area_low = df["forest_area"].min()
area_2021 = df["forest_area"].iloc[-1]
sink_before = -pre["forest_co2"].iloc[-1]
sink_after = -post["forest_co2"].iloc[0]

with c1, st.container(border=True):
    st.markdown("**1. The forest turned around in 2011, and its carbon sink grew more than 20 times.**")
    st.markdown(
        f"Forest area shrank for two decades to a low of **{area_low:,.1f} thousand ha in "
        f"{area_low_year}**, then grew every year to **{area_2021:,.1f} thousand ha by 2021** "
        f"(+{(area_2021 - area_low) * 1000:,.0f} ha). Over the same break, the CO2 absorbed by "
        f"standing forest went from about **{sink_before:.1f} kt a year to {sink_after:.1f} kt a year**, "
        f"roughly {sink_after / sink_before:.0f} times more."
    )

conv_total = df["conv_co2"].sum()
conv_1990s = df.loc[df["Year"] < 2000, "conv_co2"].sum()

with c2, st.container(border=True):
    st.markdown("**2. Clearing forest used to outweigh regrowth, so the sector was a net CO2 source until 2010.**")
    st.markdown(
        f"Before 2011, conversion released more CO2 than the forest absorbed, so the sector added "
        f"a net **{pre['net_co2'].sum():,.0f} kt** of CO2 to the atmosphere. "
        f"{conv_1990s / conv_total:.0%} of all clearing emissions happened in the 1990s alone. "
        f"From 2011 on, recorded clearing is zero and the sector became a net **sink** of "
        f"**{-post['net_co2'].sum():,.0f} kt**, more than cancelling out the earlier two decades."
    )

st.divider()

# ---------------------------------------------------------------------------
# Interactive section: two linked widgets
# ---------------------------------------------------------------------------
st.subheader("Explore a period")
st.markdown(
    "Pick an era first, then narrow the years inside it. The slider only offers years "
    "that belong to the era you chose, so you can drill down from the big picture to a "
    "specific stretch of years. All three charts, the numbers and the summary sentence update together."
)

w1, w2 = st.columns([1, 2])

with w1:
    era = st.radio(
        "① Choose an era",
        options=list(ERAS.keys()),
        index=0,
        help="The eras are split at 2011, the year the trend reversed.",
    )
    with st.expander("Why this control?"):
        st.markdown(
            """
**User question:** *Is the story different before and after the 2011 turnaround?*
The dataset has one clear break, so the first step of any question is choosing which side
of it you want to look at.

**Why a radio button:** there are only three options and they are mutually exclusive, so a
radio shows all of them at once with nothing hidden. I considered a dropdown (selectbox),
but it hides the choices behind a click and suits long lists better. I also considered
letting users type any start year, but that would lose the 2011 framing that makes the
data meaningful.

**Course concept, providing context:** the eras come with names ("Loss" and "Recovery")
that frame the data before the user sees a chart. The years outside the selection stay on
the forest-area chart in grey, so the user always sees where their selection sits in the
full 32-year story (overview first, then zoom and filter).
"""
        )

lo, hi = ERAS[era]

with w2:
    # key depends on the era, so the slider resets to the new era's bounds
    # (otherwise a range saved from a previous era can fall outside the new min/max)
    start, end = st.slider(
        "② Narrow the years within that era",
        min_value=lo,
        max_value=hi,
        value=(lo, hi),
        step=1,
        key=f"years_{lo}_{hi}",
    )
    with st.expander("Why this control?"):
        st.markdown(
            """
**User question:** *How much CO2 was absorbed or released over a specific stretch of years,
and how much forest was gained or lost?* For example, the 1990s against the 2000s inside the
loss era, or 2011–2015 against 2016–2021 inside the recovery era.

**Why a range slider:** years are ordered and continuous, and a range slider shows that
visually: one handle for the start, one for the end, and it cannot produce an invalid range
(a start after the end). I considered a multiselect of individual years, but that lets
users pick scattered years with gaps, which makes totals like "CO2 removed over the period"
misleading. Two number inputs would work but show no sense of where you are on the timeline.

**Link to the first control:** the era sets the slider's minimum and maximum, so the
second control only offers valid years for the first choice. That is what makes it a
drill-down rather than two separate filters.

**Course concept, reducing clutter and focusing attention:** narrowing the years removes
bars from the carbon chart, so fewer bars are left to compare. On the area chart and the donut, the
selected years are drawn in strong colour while the rest fade to grey, so colour draws the
eye to the chosen range without hiding the full picture. Colour is also semantic across
the page: green always means CO2 absorbed by the forest and orange always means CO2
released by clearing, so readers can tell the two flows apart without checking a legend.
"""
        )

sel = df[(df["Year"] >= start) & (df["Year"] <= end)]
s = summarise(sel)
span = f"{start}" if start == end else f"{start}–{end}"

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Forest area change",
    f"{s['area_change_ha']:+,.0f} ha",
    help=f"Change in forest area from {start} to {end}.",
)
k2.metric("CO2 absorbed by forest", f"{s['removed']:,.1f} kt", help="Sum of Forestland removals.")
k3.metric("CO2 released by clearing", f"{s['emitted']:,.1f} kt", help="Sum of Net Forest conversion emissions.")
k4.metric(
    "Net balance (" + ("net sink" if s["net"] < 0 else "net source") + ")",
    f"{s['net']:+,.1f} kt",
    help="Absorbed minus released. Negative means the forest sector removed more CO2 than it emitted.",
)

# Plain-language summary of the selection
role = "net **sink**" if s["net"] < 0 else "net **source**"
per_year = abs(s["net"]) / s["n_years"]
if s["n_years"] == 1:
    area_part = f"Lebanon had **{s['area_end']:,.1f} thousand ha** of forest"
elif s["area_change_ha"] > 0:
    area_part = f"Lebanon gained **{s['area_change_ha']:,.0f} ha** of forest"
else:
    area_part = f"Lebanon lost **{-s['area_change_ha']:,.0f} ha** of forest"
summary = (
    f"**In {span}**, {area_part} and the forest sector was a {role} of CO2, "
    f"about **{per_year:,.1f} kt a year**."
)
if s["emitted"] > 0:
    share = s["emitted"] / conv_total
    summary += (
        f" Clearing released {s['emitted']:,.1f} kt here, or {share:.0%} of all clearing "
        f"emissions in the 32-year record."
    )
else:
    summary += " No forest clearing was recorded in these years."
st.success(summary)

# ---------------------------------------------------------------------------
# Chart 1: Forest area (full record for context, selection highlighted)
# ---------------------------------------------------------------------------
fig_area = go.Figure()
fig_area.add_trace(
    go.Scatter(
        x=df["Year"], y=df["forest_area"], mode="lines",
        line=dict(color=GREY, width=2), name="All years",
        hovertemplate="%{y:.2f} thousand ha<extra>All years</extra>",
    )
)
fig_area.add_trace(
    go.Scatter(
        x=sel["Year"], y=sel["forest_area"], mode="lines+markers",
        line=dict(color=NAVY, width=3.5), marker=dict(size=7),
        name="Selected years",
        hovertemplate="%{y:.2f} thousand ha<extra>Selected</extra>",
    )
)
if (start, end) != (1990, 2021):  # only shade when a sub-range is selected
    fig_area.add_vrect(x0=start - 0.5, x1=end + 0.5, fillcolor=NAVY, opacity=0.07,
                       line_width=0, layer="below")
fig_area.add_shape(type="line", x0=BREAK_YEAR - 0.5, x1=BREAK_YEAR - 0.5, y0=0, y1=1,
                   yref="paper", line=dict(color=MAROON, width=1.5, dash="dash"), layer="above")
fig_area.add_annotation(
    x=BREAK_YEAR - 0.5, y=1, yref="paper", text=" 2011 turnaround", showarrow=False,
    xanchor="left", yanchor="top", font=dict(size=12, color=MAROON),
)
fig_area.update_yaxes(title="Forest area (thousand ha)", range=[136.5, 145])
fig_area.update_xaxes(title=None, range=[1989.5, 2021.5], dtick=5)
fig_area.update_layout(title=f"Forest area: decline, then turnaround  ·  selected {span}")
style(fig_area, height=460)

# ---------------------------------------------------------------------------
# Chart 2: Carbon flows for the selected years only
# ---------------------------------------------------------------------------
fig_co2 = go.Figure()
fig_co2.add_trace(
    go.Bar(
        x=sel["Year"], y=sel["forest_co2"], name="Absorbed by forest (Forestland)",
        marker_color=NAVY, hovertemplate="%{y:.1f} kt<extra>Absorbed</extra>",
    )
)
fig_co2.add_trace(
    go.Bar(
        x=sel["Year"], y=sel["conv_co2"], name="Released by clearing (Conversion)",
        marker_color=MAROON, hovertemplate="%{y:.1f} kt<extra>Released</extra>",
    )
)
fig_co2.add_trace(
    go.Scatter(
        x=sel["Year"], y=sel["net_co2"], name="Net balance", mode="lines+markers",
        line=dict(color=INK, width=2, dash="dot"), marker=dict(size=6, symbol="diamond"),
        hovertemplate="%{y:+.1f} kt<extra>Net</extra>",
    )
)
fig_co2.add_hline(y=0, line_color="gray", line_width=1)
fig_co2.add_annotation(
    x=0, xref="paper", y=df["conv_co2"].max() * 1.15, text="↑ adds CO2 (source)",
    showarrow=False, xanchor="left", font=dict(size=11, color=MAROON),
)
fig_co2.add_annotation(
    x=0, xref="paper", y=df["forest_co2"].min() * 1.04, text="↓ removes CO2 (sink)",
    showarrow=False, xanchor="left", yanchor="top", font=dict(size=11, color=NAVY),
)
# keep the y-axis fixed so eras can be compared by eye without the scale shifting
fig_co2.update_yaxes(
    title="Net CO2 (kt; below 0 = removed)",
    range=[df["forest_co2"].min() * 1.2, df["conv_co2"].max() * 1.35],
)
fig_co2.update_xaxes(title=None, range=[start - 0.6, end + 0.6], dtick=1 if end - start <= 12 else 2)
fig_co2.update_layout(barmode="relative", title=f"Where the carbon went, {span}", bargap=0.25)
style(fig_co2)
# legend under the chart so it doesn't collide with the title
fig_co2.update_layout(
    legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0),
    margin=dict(b=110), height=460,
)

ch1, ch2 = st.columns(2)
with ch1:
    st.plotly_chart(fig_area)
    st.caption(
        "Grey shows the full record for context and green shows your selection. The dashed line "
        "marks 2011, where two decades of loss turn into steady regrowth."
    )
with ch2:
    st.plotly_chart(fig_co2)
    st.caption(
        "Green bars below zero are CO2 the forest absorbed and orange bars above zero are CO2 "
        "released by clearing. The dotted line is the net. The y-axis stays fixed across selections "
        "so eras can be compared fairly."
    )

# ---------------------------------------------------------------------------
# Chart 3: Donut - when did clearing emissions happen? (selection highlighted)
# ---------------------------------------------------------------------------
DECADE_COLORS = {"1990s": MAROON, "2000s": "#f4a06b", "2010s": "#f9c9a4"}
OTHER = "#c9c4bf"   # outside the selection: muted, but clearly filled

df["decade"] = (df["Year"] // 10 * 10).astype(str) + "s"
df["selected"] = df["Year"].between(start, end)
labels, values, colors, texts, text_colors = [], [], [], [], []
for dec, color in DECADE_COLORS.items():
    for is_sel in (True, False):
        v = df.loc[(df["decade"] == dec) & (df["selected"] == is_sel), "conv_co2"].sum()
        if v <= 0:
            continue
        labels.append(f"{dec} · {'selected years' if is_sel else 'other years'}")
        values.append(v)
        colors.append(color if is_sel else OTHER)
        share = v / conv_total
        if is_sel:
            texts.append(f"<b>{dec}</b><br>{share:.0%}")
            text_colors.append("white" if dec == "1990s" else INK)  # dark text on the light oranges
        else:
            # label grey slices too, so they read as "other years", not as empty space
            texts.append(f"{dec}<br>not selected<br>{share:.0%}" if share >= 0.08 else "")
            text_colors.append("#4a4540")

sel_share = s["emitted"] / conv_total
center = (
    f"<b>{sel_share:.0%}</b><br>of all clearing CO2<br>in {span}"
    if sel_share > 0 else "<b>0%</b><br>no clearing<br>in these years"
)

fig_donut = go.Figure(
    go.Pie(
        labels=labels, values=values, hole=0.58, sort=False, direction="clockwise",
        rotation=0, marker=dict(colors=colors, line=dict(color="white", width=2)),
        text=texts, textinfo="text", textfont=dict(size=12, color=text_colors), textposition="inside", insidetextorientation="horizontal",
        hovertemplate="%{label}<br>%{value:.1f} kt (%{percent})<extra></extra>",
    )
)
fig_donut.add_annotation(text=center, x=0.5, y=0.5, showarrow=False, font=dict(size=15, color=INK))
fig_donut.update_layout(title="When did clearing emissions happen?", showlegend=False)
style(fig_donut, height=400)
fig_donut.update_layout(hovermode="closest", margin=dict(l=20, r=20, t=60, b=20))

dec_tot = df.groupby("decade")["conv_co2"].sum()
d1, d2 = st.columns([1, 1])
with d1:
    st.plotly_chart(fig_donut)
with d2:
    st.markdown("##### Reading the donut")
    st.markdown(
        f"""
The whole ring is **all {conv_total:,.1f} kt of CO2** released by forest clearing between 1990 and 2021.
**Coloured slices** are the emissions from your selected years. **Grey slices** are emissions from
the other years in the same decade, so they're real emissions that sit outside your selection.
The decades run clockwise from the top.

- **1990s:** {dec_tot.get('1990s', 0):,.1f} kt ({dec_tot.get('1990s', 0) / conv_total:.0%})
- **2000s:** {dec_tot.get('2000s', 0):,.1f} kt ({dec_tot.get('2000s', 0) / conv_total:.0%})
- **2010s:** {dec_tot.get('2010s', 0):,.1f} kt ({dec_tot.get('2010s', 0) / conv_total:.0%}), all of it from 2010
- **2020–2021:** 0 kt

Almost two-thirds of all clearing emissions come from the 1990s, and clearing stops
completely from 2011. Pick the recovery era and the ring turns fully grey.
"""
    )

with st.expander(f"See the numbers for {span}"):
    table = sel.rename(
        columns={
            "forest_area": "Forest area (1000 ha)",
            "forest_co2": "Forestland CO2 (kt)",
            "conv_area": "Area converted (1000 ha)",
            "conv_co2": "Conversion CO2 (kt)",
            "net_co2": "Net CO2 (kt)",
        }
    ).set_index("Year")
    st.dataframe(table.round(3))

st.divider()
st.caption(
    "Built by Carmen Al Fhaili for Data Visualization & Communication (MSBA). "
    "Data: FAO FAOSTAT, Emissions from Forests, Lebanon, via AUB CODEC."
)
