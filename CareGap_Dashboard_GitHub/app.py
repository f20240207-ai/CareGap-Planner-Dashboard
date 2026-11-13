"""CareGap Planner | Georgia preventive-care outreach decision-support dashboard.

Required files beside app.py:
  caregap_data.csv, caregap_allocation.csv, georgia_counties.csv
Optional: georgia_mammography_facilities_with_coordinates.csv (facility overlay)
"""
from pathlib import Path
from html import escape
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="CareGap Planner", page_icon="🔷", layout="wide")
ROOT = Path(__file__).resolve().parent
NAVY, BLUE, LIGHT, CYAN, ORANGE = "#0B2545", "#3B82F6", "#DCE9F8", "#38BDF8", "#F59E0B"
TEXT, MUTED, PANEL = "#E6EEF9", "#8FA8C8", "#0B1220"
GRID = "rgba(255,255,255,.08)"
# Starts at a mid-blue so low values stay visible on the black basemap.
PALETTE = ["#1F4E9C", "#3B82F6", "#38BDF8", "#E6F6FF"]
PAGES = ["Overview", "Screening Gaps", "Resource Allocation", "Access Map"]
STATIC_CONFIG = {"displayModeBar": False}
MAP_CONFIG = {"scrollZoom": True, "displayModeBar": True, "displaylogo": False,
              "modeBarButtonsToRemove": ["lasso2d", "select2d"]}
# name: (latitude, longitude, default zoom)
FOCUS = {"Statewide": (32.7, -83.4, 6.4), "Metro Atlanta": (33.75, -84.39, 9.2),
         "Savannah": (32.08, -81.09, 9.6), "Augusta": (33.47, -81.97, 9.6),
         "Macon": (32.84, -83.63, 9.6), "Columbus": (32.46, -84.99, 9.6),
         "Albany": (31.58, -84.16, 9.6)}


def apply_css():
    st.markdown("""
    <style>
      .stApp {background: radial-gradient(ellipse 700px 460px at 98% 0%,rgba(31,111,235,.22),transparent 72%),#000000;color:#E6EEF9;}
      [data-testid="stHeader"] {background:transparent;}
      .block-container {max-width:1450px;padding-top:1.1rem;padding-bottom:2.8rem;}
      h1,h2,h3,h4 {color:#F1F6FF!important;letter-spacing:-.025em;}
      [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, label {color:#C9D8EE!important;}
      [data-testid="stCaptionContainer"], .stCaption {color:#8FA8C8!important;}
      hr {border-color:rgba(255,255,255,.12)!important;}
      .cg-hero {background:linear-gradient(112deg,#0B2545 4%,#123A70 52%,#1F4E9C 100%);color:#fff;border-radius:18px 18px 26px 26px;padding:28px 36px 30px;box-shadow:0 0 40px rgba(31,111,235,.22);border:1px solid rgba(96,165,250,.25);margin:0 0 20px;position:relative;overflow:hidden;}
      .cg-hero:after {content:'';position:absolute;width:360px;height:360px;right:-90px;top:-240px;background:radial-gradient(circle,rgba(56,189,248,.4),transparent 70%);pointer-events:none;}
      .cg-hero-title {font-size:2.15rem;font-weight:800;letter-spacing:-.045em;line-height:1.12;color:white!important;}
      .cg-hero-sub {font-size:1rem;color:#D9E9FF;margin-top:9px;max-width:900px;}
      .cg-hero-top {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
      .cg-page-pill {background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.32);border-radius:99px;padding:8px 14px;font-size:.75rem;letter-spacing:.09em;font-weight:750;color:white;}
      [data-testid="stVerticalBlockBorderWrapper"] > div:has(> [data-testid="stVerticalBlock"]) {border-radius:14px;}
      [data-testid="stVerticalBlockBorderWrapper"] {background:#0B1220;border:1px solid rgba(59,130,246,.28)!important;border-radius:14px!important;box-shadow:0 0 26px rgba(31,111,235,.10);}
      [data-testid="stMetric"] {background:#0B1220;border:1px solid rgba(59,130,246,.28);border-left:4px solid #3B82F6;border-radius:14px;padding:18px 19px;box-shadow:0 0 26px rgba(31,111,235,.10);min-height:108px;}
      [data-testid="stMetricValue"] {color:#60A5FA!important;font-size:2rem!important;font-weight:800;}
      [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {color:#9DB4D3!important;font-size:.86rem!important;font-weight:600;}
      .stButton>button {background:#2563EB;color:white;border:1px solid #3B82F6;border-radius:11px;font-weight:700;padding:.6rem 1.2rem;}
      .stButton>button:hover {background:#3B82F6;color:white;border-color:#60A5FA;}
      .stButton>button:disabled {background:#111C30;color:#5F7799;border-color:#1B2A44;}
      [data-testid="stProgress"] > div > div {background:#14213A;}
      [data-testid="stProgressBar"]>div>div {background:#3B82F6;}
      div[data-baseweb="select"] > div {background-color:#0B1220!important;border:1px solid rgba(59,130,246,.38)!important;border-radius:10px!important;}
      div[data-baseweb="select"] > div * {background-color:transparent!important;color:#E6EEF9!important;-webkit-text-fill-color:#E6EEF9!important;}
      div[data-baseweb="select"] svg {fill:#9DB4D3!important;}
      div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul, ul[role="listbox"], [data-baseweb="menu"] {background-color:#0B1220!important;color:#E6EEF9!important;}
      li[role="option"], li[role="option"] * {background-color:#0B1220!important;color:#E6EEF9!important;}
      li[role="option"]:hover, li[role="option"]:hover *, li[aria-selected="true"], li[aria-selected="true"] * {background-color:#14284A!important;}
      /* Blue-only focus and active controls, including Streamlit BaseWeb overrides. */
      :root {accent-color:#3B82F6!important;}
      div[data-baseweb="select"] > div,
      div[data-baseweb="select"] > div:hover,
      div[data-baseweb="select"] > div:focus-within,
      div[data-baseweb="select"] > div[data-focused="true"],
      [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border-color:#3B82F6!important;box-shadow:none!important;outline:none!important;
      }
      [data-testid="stSelectbox"]:focus-within div[data-baseweb="select"] > div {
        border-color:#60A5FA!important;box-shadow:0 0 0 2px rgba(59,130,246,.25)!important;
      }
      [data-testid="stSlider"] [role="slider"],
      [data-testid="stSlider"] [role="slider"]:focus,
      [data-testid="stSlider"] [role="slider"]:focus-visible {
        background:#3B82F6!important;border-color:#3B82F6!important;
        outline:2px solid #60A5FA!important;outline-offset:1px!important;
        box-shadow:none!important;
      }
      [data-testid="stSlider"] [data-baseweb="slider"] div[aria-valuenow] {background:#3B82F6!important;}
      [data-testid="stSlider"] [data-baseweb="slider"] > div > div {accent-color:#3B82F6!important;}
      [data-testid="stSlider"] [data-testid="stTickBar"] {color:#9DB4D3!important;}
      [data-testid="stToggleSwitch"] input:checked + div,
      [data-testid="stToggleSwitch"] [aria-checked="true"] {background-color:#3B82F6!important;}
      button:focus-visible, [role="combobox"]:focus-visible {
        outline:2px solid #60A5FA!important;outline-offset:2px!important;
      }
      [data-testid="stTooltipContent"] {background:#0B1220;color:#E6EEF9;}
      .cg-note {background:rgba(31,111,235,.14);border-left:4px solid #3B82F6;padding:13px 17px;border-radius:10px;color:#DCE9F8;margin:12px 0;}
      .cg-table-wrap {overflow-x:auto;border-radius:12px;border:1px solid rgba(59,130,246,.25);}
      table.cg-table {width:100%;border-collapse:collapse;font-size:.89rem;min-width:680px;}
      .cg-table thead th {background:#0B2545;color:white;text-align:left;padding:12px 14px;white-space:nowrap;font-weight:700;}
      .cg-table tbody td {padding:11px 14px;color:#DCE9F8;border-bottom:1px solid #1C2B45;white-space:nowrap;}
      .cg-table tbody tr:nth-child(even) {background:#0F1A2E;}
      .cg-table tbody tr:nth-child(odd) {background:#0B1220;}
      .cg-table tbody tr:hover {background:#14284A;}
      .cg-section-caption {color:#8FA8C8;font-size:.86rem;margin-top:-4px;margin-bottom:12px;}
      [data-testid="stExpander"] {background:#0B1220;border:1px solid rgba(59,130,246,.28);border-radius:14px;}
    </style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data():
    data = pd.read_csv(ROOT / "caregap_data.csv", dtype={"TractFIPS": "string", "GEOID": "string"})
    alloc = pd.read_csv(ROOT / "caregap_allocation.csv", dtype={"TractFIPS": "string"})
    for frame in (data, alloc):
        frame["TractFIPS"] = frame["TractFIPS"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(11)
    counties = pd.read_csv(ROOT / "georgia_counties.csv", dtype={"CountyFIPS": "string"})
    counties["CountyFIPS"] = counties["CountyFIPS"].str.zfill(5)
    names = dict(zip(counties["CountyFIPS"], counties["CountyName"]))
    for frame in (data, alloc):
        frame["CountyFIPS"] = frame["TractFIPS"].str[:5]
        frame["County"] = frame["CountyFIPS"].map(names).fillna("Unknown county")
        frame["TractLabel"] = frame["County"] + " · " + frame["TractFIPS"].str[-6:]
    return data, alloc, len(names)


@st.cache_data(show_spinner=False)
def load_facilities():
    path = ROOT / "georgia_mammography_facilities_with_coordinates.csv"
    if not path.exists():
        return pd.DataFrame()
    facilities = pd.read_csv(path)
    for c in ("Latitude", "Longitude"):
        facilities[c] = pd.to_numeric(facilities[c], errors="coerce")
    return facilities.dropna(subset=["Latitude", "Longitude"])


def num(frame, col):
    if col not in frame:
        return pd.Series(np.nan, index=frame.index)
    return pd.to_numeric(frame[col], errors="coerce")


def plan_concentration(alloc, col="Equity_Allocated_Screenings"):
    """Share of the plan that goes to the most-served vulnerability group (None if it cannot be computed)."""
    if "Vulnerability_Group" not in alloc or col not in alloc:
        return None
    given = num(alloc, col).fillna(0)
    total = float(given.sum())
    if total <= 0:
        return None
    groups = alloc["Vulnerability_Group"].astype(str)
    by_group = given.groupby(groups).sum().sort_values(ascending=False)
    result = {"group": str(by_group.index[0]), "share": float(by_group.iloc[0]) / total,
              "others": total - float(by_group.iloc[0]), "total": total}
    need = num(alloc, "Mammo_Unmet")
    if need.notna().all() and float(need.sum()) > 0:
        result["need_outside"] = float(need[groups != result["group"]].sum()) / float(need.sum())
        result["coverage"] = total / float(need.sum())
    return result


def chart_style(fig, height=470, map_chart=False):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial, sans-serif", color=TEXT, size=12),
                      margin=dict(l=12, r=15, t=22, b=35),
                      hoverlabel=dict(bgcolor=PANEL, font_color=TEXT, bordercolor="#3B82F6"),
                      legend=dict(orientation="h", y=1.06, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)))
    if not map_chart:
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, linecolor="rgba(255,255,255,.18)",
                         title_font_color=TEXT, tickfont_color=TEXT)
        fig.update_yaxes(showgrid=False, zeroline=False, title_font_color=TEXT, tickfont_color=TEXT)
    return fig


def show_chart(fig, config=None, key=None):
    """Render a Plotly chart; falls back gracefully on older Streamlit versions."""
    config = config or STATIC_CONFIG
    try:
        st.plotly_chart(fig, use_container_width=True, config=config, key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=config)


def card(title, description=None):
    container = st.container(border=True)
    with container:
        st.markdown(f"#### {title}")
        if description:
            st.markdown(f'<div class="cg-section-caption">{escape(description)}</div>', unsafe_allow_html=True)
    return container


def show_table(frame, fields, labels=None, n=15):
    labels = labels or {}
    view = frame.loc[:, [c for c in fields if c in frame]].head(n)
    ints = {"Priority_Rank", "Equity_Allocated_Screenings", "Allocated_Screenings", "Tracts", "TotalPopulation", "Mammo_Unmet", "Total_Tracts", "Estimated_Unmet_Need"}
    rows = ['<div class="cg-table-wrap"><table class="cg-table"><thead><tr>']
    rows += [f'<th>{escape(labels.get(c, c.replace("_", " ")))}</th>' for c in view.columns]
    rows += ['</tr></thead><tbody>']
    for _, record in view.iterrows():
        rows.append('<tr>')
        for c, value in record.items():
            if pd.isna(value):
                display = '—'
            elif c in ("TractFIPS", "CountyFIPS"):
                display = str(value)
            elif isinstance(value, (int, float, np.integer, np.floating)):
                display = f'{int(round(value)):,}' if c in ints else f'{value:,.3f}'
            else:
                display = str(value)
            rows.append(f'<td>{escape(display)}</td>')
        rows.append('</tr>')
    rows.append('</tbody></table></div>')
    st.markdown(''.join(rows), unsafe_allow_html=True)


def methodology(data, alloc):
    with st.expander("Methodology and limitations"):
        st.markdown("""
        **Data:** Screening rates from CDC PLACES are modeled prevalence estimates, not verified individual screening records. Estimated unmet need is a planning proxy.

        **Priority model:** Assumed 40% custom vulnerability, 30% mammography gap, 30% colorectal gap. The vulnerability score is a custom Georgia-relative index, **not official CDC SVI**.

        **Access:** Of 311 FDA mammography facilities, 177 were geocoded. Straight-line distances to the geocoded subset are **not driving distances or travel times**.

        **Optimization:** Outreach allocations are hypothetical, not funded deployments. The cap is **50 screenings per tract**, but not every tract receives 50.

        **Vulnerability groups:** The saved vulnerability score is divided into **quartiles**; each group has **696 tracts**. **Very High** denotes the top **25%**, not a score near 1.0. The labels are relative to the saved Georgia data.
        """)
        conc = plan_concentration(alloc)
        if conc:
            text = f"**Equity concentration:** In the saved plan, **{conc['share']:.0%}** of planned screenings go to the **{conc['group']}** vulnerability quartile."
            if "need_outside" in conc:
                text += f" The other quartiles hold **{conc['need_outside']:.0%}** of estimated unmet need" + (" and receive no screenings." if conc["others"] < 0.5 else ".")
                text += f" Overall, the plan covers about **{conc['coverage']:.1%}** of statewide estimated unmet need."
            st.markdown(text)
        if "Vulnerability_Group" in alloc:
            sizes = alloc.groupby("Vulnerability_Group", dropna=False).size()
            if not all(sizes.eq(696)) or len(sizes) != 4:
                st.warning("Current allocation CSV does not have exactly four groups of 696; check its saved grouping rules.")


apply_css()
try:
    df, allocation, county_count = load_data()
except Exception as exc:
    st.error("Missing dashboard data. Keep caregap_data.csv, caregap_allocation.csv, and georgia_counties.csv next to app.py.")
    st.exception(exc)
    st.stop()

if "caregap_page" not in st.session_state:
    st.session_state["caregap_page"] = 0
page = max(0, min(3, int(st.session_state["caregap_page"])))


def change_page(direction):
    st.session_state["caregap_page"] = max(0, min(3, st.session_state["caregap_page"] + direction))


st.markdown(f'''<div class="cg-hero"><div class="cg-hero-top"><div class="cg-hero-title">CareGap Planner</div>
<span class="cg-page-pill">PAGE {page + 1} OF 4</span></div>
<div class="cg-hero-sub">Preventive Healthcare Outreach Decision-Support System &nbsp;·&nbsp; Georgia, USA &nbsp;·&nbsp; {escape(PAGES[page])}</div></div>''', unsafe_allow_html=True)
st.progress((page + 1) / 4)

if page == 0:
    st.markdown("### Georgia preventive-care intelligence")
    st.caption("Identify underserved census tracts and explore an equity-aware hypothetical outreach plan.")
    allocated = num(allocation, "Equity_Allocated_Screenings").fillna(0)
    high_vuln = int(num(df, "Vulnerability_Score").ge(num(df, "Vulnerability_Score").quantile(.9)).sum())
    distant = int(num(df, "Nearest_Mammo_Distance_km").gt(20).sum())
    far10 = int(num(df, "Nearest_Mammo_Distance_km").gt(10).sum())
    stats = [
        ("Census tracts", f"{len(df):,}"),
        ("Average mammography screening", f"{num(df, 'MAMMOUSE_CrudePrev').mean():.1f}%"),
        ("Average colorectal screening", f"{num(df, 'COLON_SCREEN_CrudePrev').mean():.1f}%"),
        ("Planned mammography screenings", f"{allocated.sum():,.0f}"),
        ("High vulnerability · top 10%", f"{high_vuln:,}"),
        ("More than 10 km from facility", f"{far10:,}"),
        ("More than 20 km from facility", f"{distant:,}"),
        ("Tracts receiving resources", f"{int(allocated.gt(0).sum()):,}"),
    ]
    for start in (0, 4):
        cols = st.columns(4)
        for col, (label, value) in zip(cols, stats[start:start + 4]):
            with col:
                st.metric(label, value)
    geo_n = len(load_facilities())
    st.caption("High vulnerability uses the top decile of the custom score. Distances are straight-line to the geocoded subset of FDA mammography facilities"
               + (f" ({geo_n} of 311)." if geo_n else "."))
    st.markdown('<div class="cg-note">CDC PLACES rates are modeled estimates. All outreach allocations are hypothetical planning results, not confirmed healthcare services.</div>', unsafe_allow_html=True)
    with card("Decision-support snapshot", "How to interpret the dashboard"):
        st.markdown(f"**Screening Gaps** ranks tracts using a combined priority score. **Resource Allocation** shows how a capped, equity-aware plan distributes {allocated.sum():,.0f} hypothetical mammography screenings. **Access Map** explores geographic patterns and geocoded facilities.")
    methodology(df, allocation)

elif page == 1:
    st.markdown("### Screening Gap Explorer")
    screening = st.selectbox("Choose screening type", ["Mammography", "Colorectal"])
    gap = "Mammo_Gap_Score" if screening == "Mammography" else "Colorectal_Gap_Score"
    top = df.nlargest(15, "Priority_Score").sort_values("Priority_Score", ascending=False).copy()
    st.caption("The overall Top 15 ranking is fixed: 40% community vulnerability + 30% mammography gap + 30% colorectal gap. Changing the screening type updates the gap comparison and table, not the combined ranking.")
    with card("Top 15 priority census tracts", "Combined priority score · orange highlights the highest-priority tract"):
        plot = top.iloc[::-1]
        colors = [ORANGE if fips == str(top.iloc[0]["TractFIPS"]) else BLUE for fips in plot["TractFIPS"].astype(str)]
        fig = go.Figure(go.Bar(x=num(plot, "Priority_Score"), y=plot["TractLabel"], orientation="h", marker_color=colors,
                               customdata=np.stack([plot["TractFIPS"].astype(str), plot["County"].astype(str)], axis=-1),
                               hovertemplate="%{customdata[1]} · %{customdata[0]}<br>Priority score: %{x:.3f}<extra></extra>"))
        fig.update_layout(xaxis_title="Priority score (unitless)", yaxis_title="County · tract suffix")
        show_chart(chart_style(fig, 570))
    with card(f"{screening} screening gaps among the Top 15", "Screening-specific gap for the same 15 overall priority tracts · higher values mean larger gaps"):
        gap_plot = top.sort_values(gap, ascending=True).copy()
        gap_values = num(gap_plot, gap)
        gap_colors = [ORANGE if str(fips) == str(top.iloc[0]["TractFIPS"]) else CYAN
                      for fips in gap_plot["TractFIPS"].astype(str)]
        gap_fig = go.Figure(go.Bar(
            x=gap_values, y=gap_plot["TractLabel"], orientation="h",
            marker_color=gap_colors,
            customdata=gap_plot["TractFIPS"].astype(str),
            hovertemplate="Tract: %{customdata}<br>" + screening + " gap: %{x:.3f}<extra></extra>"))
        gap_fig.update_layout(xaxis_title=f"{screening} gap (proportion, 0–1)",
                              yaxis_title="County · tract suffix", showlegend=False)
        show_chart(chart_style(gap_fig, 555))
        st.caption("The orange bar identifies the highest-ranked tract overall; it is not necessarily the tract with the largest screening-specific gap.")
    with card("Priority tract details", "15 highest-ranked tracts; scores shown to three decimal places"):
        show_table(top, ["TractFIPS", "County", "Priority_Rank", "Priority_Score", "Vulnerability_Score", gap],
                   {gap: f"{screening} gap", "Priority_Rank": "Priority rank"})
    methodology(df, allocation)

elif page == 2:
    st.markdown("### Resource Allocation Explorer")
    st.caption("Equity-aware hypothetical mammography outreach · no actual services have been deployed")
    col = "Equity_Allocated_Screenings"
    if col not in allocation:
        st.error(f"Missing allocation column: {col}")
    else:
        selected = allocation[num(allocation, col).gt(0)].copy()
        served_n = len(selected)
        total_alloc = float(num(selected, col).sum())
        cap = int(round(float(num(selected, col).max()))) if served_n else 50
        cols = st.columns(3)
        for area, label, value in zip(cols, ["Tracts served", "Total planned screenings", "Per-tract cap"],
                                      [f"{served_n:,}", f"{total_alloc:,.0f}", f"{cap}"]):
            with area:
                st.metric(label, value)
        if served_n and total_alloc < served_n * cap:
            st.markdown(f'<div class="cg-note">{served_n} × {cap} = {served_n * cap:,} is the <b>theoretical maximum</b>, not the allocated total. Some tracts receive fewer than {cap} screenings; their actual allocations sum to {total_alloc:,.0f}.</div>', unsafe_allow_html=True)
        top = selected.sort_values(["Mammo_Unmet", col], ascending=[False, False]).head(15).copy() if "Mammo_Unmet" in selected else selected.nlargest(15, col).copy()
        with card("Unmet need and outreach allocation", f"Top 15 served tracts by estimated unmet need · one count axis; dashed line is the {cap}-screening cap"):
            fig = go.Figure()
            if "Mammo_Unmet" in top:
                fig.add_trace(go.Bar(x=top["TractLabel"], y=num(top, "Mammo_Unmet"), name="Estimated unmet need", marker_color="#8DBDF5"))
            fig.add_trace(go.Bar(x=top["TractLabel"], y=num(top, col), name="Allocated screenings", marker_color=BLUE))
            fig.add_hline(y=cap, line_color=ORANGE, line_dash="dash", line_width=2,
                          annotation_text=f"Cap: {cap} per tract", annotation_position="top left", annotation_font_color=TEXT,
                          annotation_bgcolor="rgba(11,18,32,.9)", annotation_bordercolor=ORANGE)
            fig.update_layout(barmode="group", xaxis_title="County · tract suffix", yaxis_title="People / screenings (count)", xaxis_tickangle=-40)
            show_chart(chart_style(fig, 535))
            st.caption("The cap applies to allocations, not unmet-need estimates. Both series use the same count axis; large unmet-need values may make allocation bars look small.")
        below = selected[num(selected, col).lt(cap)].sort_values(col).copy()
        if "Mammo_Unmet" in below and len(below):
            near_full = int(((num(below, "Mammo_Unmet") - num(below, col)) <= 1).sum())
            below_note = (f"{near_full} of {len(below)} receive about their full estimated unmet need, which is below the cap · "
                          f"this explains why {served_n} served tracts total {total_alloc:,.0f} rather than {served_n * cap:,}")
        else:
            below_note = f"These partial allocations explain why the {served_n} served tracts total {total_alloc:,.0f} rather than {served_n * cap:,}"
        with card(f"Tracts receiving fewer than {cap} screenings · {len(below)}", below_note):
            if below.empty:
                st.info("No partially allocated tracts found in the current file.")
            else:
                fig = go.Figure(go.Bar(x=below["TractLabel"].head(25), y=num(below, col).head(25), marker_color=CYAN,
                                       hovertemplate="%{x}<br>Allocated: %{y:.0f}<extra></extra>"))
                fig.add_hline(y=cap, line_color=ORANGE, line_dash="dash", annotation_text=f"Cap: {cap} per tract", annotation_font_color=TEXT,
                              annotation_bgcolor="rgba(11,18,32,.9)", annotation_bordercolor=ORANGE)
                fig.update_layout(xaxis_title="County · tract suffix", yaxis_title="Allocated screenings (count)", xaxis_tickangle=-40)
                show_chart(chart_style(fig, 355))
                show_table(below, ["TractFIPS", "County", col, "Mammo_Unmet", "Priority_Score"], n=len(below))
                st.caption(f"Tracts below the cap: {len(below)} · total screenings in these tracts: {num(below, col).sum():,.0f} · tracts at the cap: {int(num(selected, col).ge(cap).sum())}.")
        with card("Allocation details", "15 served tracts with the largest estimated unmet need"):
            show_table(top, ["TractFIPS", "County", "Mammo_Unmet", "Priority_Score", col, "Vulnerability_Score", "Vulnerability_Group"])
        if "Vulnerability_Group" in allocation:
            conc = plan_concentration(allocation, col)
            with card("Allocation by vulnerability quartile", "Saved Georgia-relative groups; Very High means the top 25%"):
                if conc:
                    message = f"<b>{conc['share']:.0%}</b> of planned screenings go to the <b>{escape(conc['group'])}</b> vulnerability quartile"
                    message += "; the other quartiles receive none in this plan." if conc["others"] < 0.5 else "."
                    if "need_outside" in conc:
                        message += f" The other quartiles hold {conc['need_outside']:.0%} of estimated unmet need, and the plan covers about {conc['coverage']:.1%} of statewide unmet need overall."
                    st.markdown(f'<div class="cg-note">{message}</div>', unsafe_allow_html=True)
                groups = allocation.groupby("Vulnerability_Group", dropna=False).agg(Tracts=("TractFIPS", "size"), Allocated_Screenings=(col, "sum")).reset_index()
                need = num(allocation, "Mammo_Unmet")
                if need.notna().all():
                    unmet_by_group = need.groupby(allocation["Vulnerability_Group"], dropna=False).sum()
                    groups["Estimated_Unmet_Need"] = groups["Vulnerability_Group"].map(unmet_by_group)
                    groups["Coverage_Percent"] = np.where(groups["Estimated_Unmet_Need"] > 0,
                                                          groups["Allocated_Screenings"] / groups["Estimated_Unmet_Need"] * 100, np.nan)
                order = {"Low": 0, "Moderate": 1, "High": 2, "Very High": 3}
                groups = groups.assign(_order=groups["Vulnerability_Group"].map(order).fillna(9)).sort_values("_order").drop(columns="_order")
                show_table(groups, ["Vulnerability_Group", "Tracts", "Allocated_Screenings", "Estimated_Unmet_Need", "Coverage_Percent"],
                           {"Estimated_Unmet_Need": "Estimated unmet need", "Coverage_Percent": "Coverage of unmet need (%)"}, n=10)
        methodology(df, allocation)

elif page == 3:
    st.markdown("### Georgia Screening Access Map")
    options = {"Mammography Screening Gap": "Mammo_Gap_Score", "Colorectal Screening Gap": "Colorectal_Gap_Score",
               "Community Vulnerability": "Vulnerability_Score", "Distance to Mammography Facility (km)": "Nearest_Mammo_Distance_km"}
    controls = st.columns([2.3, 1.5, 1.5])
    with controls[0]:
        indicator = st.selectbox("Geographic indicator", list(options))
    with controls[1]:
        top_pct = st.slider("Show highest X% of tracts", min_value=5, max_value=100, value=100, step=5)
    with controls[2]:
        show_facilities = st.toggle("Overlay mammography facilities", value=False)
    view_controls = st.columns([2.3, 1.5, 1.5])
    with view_controls[0]:
        focus = st.selectbox("Focus area", list(FOCUS))
    with view_controls[1]:
        # The slider default follows the focus area, so picking a city also zooms to it.
        zoom_level = st.slider("Map zoom", min_value=5.0, max_value=12.0, value=float(FOCUS[focus][2]), step=0.1)
    with view_controls[2]:
        wheel_zoom = st.toggle("Mouse-wheel zoom", value=True,
                               help="On: scrolling over the map zooms it. Off: the page scrolls normally and you zoom with the + / − buttons.")
    metric = options[indicator]
    map_data = df.copy()
    coords = map_data["Geolocation"].astype("string").str.extract(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)")
    map_data["longitude"] = pd.to_numeric(coords[0], errors="coerce")
    map_data["latitude"] = pd.to_numeric(coords[1], errors="coerce")
    map_data[metric] = num(map_data, metric)
    map_data = map_data.dropna(subset=["latitude", "longitude", metric])
    if map_data.empty:
        st.warning("No valid geographic records for this indicator.")
    else:
        full_values = map_data[metric]
        threshold = full_values.quantile(1 - top_pct / 100)
        map_data = map_data[map_data[metric] >= threshold].copy() if top_pct < 100 else map_data
        low, high = full_values.quantile([.05, .95])
        if not np.isfinite(low) or not np.isfinite(high) or low >= high:
            low, high = float(full_values.min()), float(full_values.max())
            if low == high:
                high += 1e-9
        map_data["MapColor"] = num(map_data, metric).clip(low, high)
        population = num(map_data, "TotalPopulation").clip(lower=0).fillna(0)
        pop95 = max(float(population.quantile(.95)), 1.0)
        map_data["MarkerSize"] = (3 + 5 * np.sqrt(population.clip(upper=pop95) / pop95)).clip(3, 8)
        map_data["HoverText"] = (
            "<b>" + map_data["County"].astype(str) + " · " + map_data["TractFIPS"].astype(str) + "</b><br>"
            + "Priority: " + num(map_data, "Priority_Score").map(lambda x: f"{x:.3f}") + "<br>"
            + "Vulnerability: " + num(map_data, "Vulnerability_Score").map(lambda x: f"{x:.3f}") + "<br>"
            + "Mammography gap: " + num(map_data, "Mammo_Gap_Score").map(lambda x: f"{x:.3f}") + "<br>"
            + "Colorectal gap: " + num(map_data, "Colorectal_Gap_Score").map(lambda x: f"{x:.3f}") + "<br>"
            + "Facility distance: " + num(map_data, "Nearest_Mammo_Distance_km").map(lambda x: f"{x:.1f} km")
        )
        with card("Geographic screening intelligence", f"{len(map_data):,} census tracts shown · dark basemap · brighter cyan indicates higher {indicator.lower()}"):
            fig = go.Figure()
            fig.add_trace(go.Scattermapbox(lat=map_data["latitude"], lon=map_data["longitude"], mode="markers",
                marker=dict(size=map_data["MarkerSize"].tolist(), color=map_data["MapColor"],
                            colorscale=PALETTE, cmin=float(low), cmax=float(high), opacity=.85,
                            colorbar=dict(title=dict(text=indicator, side="top", font=dict(color=TEXT)), orientation="h",
                                          x=.5, y=-.09, xanchor="center", yanchor="top", len=.64, thickness=13,
                                          tickfont=dict(color=TEXT), outlinewidth=0)),
                text=map_data["HoverText"], hovertemplate="%{text}<extra></extra>", name="Census tracts", showlegend=False))
            top15 = df.nlargest(15, "Priority_Score")
            rings = map_data[map_data["TractFIPS"].isin(top15["TractFIPS"])]
            if not rings.empty:
                # Orange ring: a larger orange dot with a smaller dot on top that keeps the tract's own indicator color.
                fig.add_trace(go.Scattermapbox(lat=rings["latitude"], lon=rings["longitude"], mode="markers",
                    marker=dict(size=15, color=ORANGE, opacity=.95), text=rings["HoverText"],
                    hovertemplate="TOP 15 PRIORITY<br>%{text}<extra></extra>", name="Top 15 priority"))
                fig.add_trace(go.Scattermapbox(lat=rings["latitude"], lon=rings["longitude"], mode="markers",
                    marker=dict(size=8, color=rings["MapColor"], colorscale=PALETTE, cmin=float(low), cmax=float(high), opacity=1),
                    hoverinfo="skip", showlegend=False))
            if show_facilities:
                facilities = load_facilities()
                if facilities.empty:
                    st.warning("Facility overlay file not found. Add georgia_mammography_facilities_with_coordinates.csv next to app.py.")
                else:
                    fig.add_trace(go.Scattermapbox(lat=facilities["Latitude"], lon=facilities["Longitude"], mode="markers",
                      marker=dict(size=9, color="#00E5FF", opacity=.98),
                        text=facilities.get("Facility_Name", pd.Series(["Mammography facility"] * len(facilities))).astype(str),
                        hovertemplate="Mammography facility<br>%{text}<extra></extra>", name=f"Geocoded facilities ({len(facilities)})"))
                    st.caption(f"Facility overlay: {len(facilities)} geocoded facilities shown; the 311-facility source list is not fully geocoded.")
            chart_style(fig, 790, map_chart=True)
            lat0, lon0, _ = FOCUS[focus]
            fig.update_layout(
                mapbox=dict(style="carto-darkmatter", center=dict(lat=lat0, lon=lon0), zoom=float(zoom_level), bearing=0, pitch=0),
                dragmode="pan",
                # Keeps the user's own pan/zoom when the indicator or filters change; resets when Focus/Zoom change.
                uirevision=f"{focus}|{zoom_level}",
                # Legend clicks would hide layers (looks like the map "shows only one thing"), so they are disabled.
                margin=dict(l=12, r=15, t=48, b=35),
                legend=dict(orientation="h", x=0, y=1.0, yanchor="bottom", bgcolor="rgba(11,18,32,.85)", font=dict(color=TEXT),
                            itemclick=False, itemdoubleclick=False))
            show_chart(fig, config={**MAP_CONFIG, "scrollZoom": bool(wheel_zoom)}, key=f"access_map_{metric}")
            st.caption(f"Colors clipped at the 5th–95th percentiles ({low:.3f} to {high:.3f}); marker size scales with tract population (capped at the 95th percentile). Orange rings identify top-15 priority tracts currently visible under the filter. Zoom with the mouse wheel (see toggle above) or the + / − buttons, drag to pan, and use the home icon to reset. Your manual pan/zoom is kept until you change Focus area or Map zoom.")
            st.caption("Each marker represents a census tract centroid, not its geographic boundary. Screening estimates are modeled, and facility distances are approximate straight-line distances, not driving times.")
    methodology(df, allocation)

st.divider()
left, _, right = st.columns([1, 4, 1])
with left:
    st.button("← Previous", on_click=change_page, args=(-1,), disabled=(page == 0), use_container_width=True)
with right:
    st.button("Next →", on_click=change_page, args=(1,), disabled=(page == 3), use_container_width=True)
