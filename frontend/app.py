import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="VoiceAgent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = "http://localhost:8000"


def load_json(path: str, fallback: dict) -> dict:
    try:
        response = requests.get(f"{API_URL}{path}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return fallback


def safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def short_count(value: object) -> str:
    number = safe_float(value)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return f"{number:.0f}"


def hourly_chart_spec() -> dict:
    return {
        "height": 320,
        "width": "container",
        "background": "transparent",
        "layer": [
            {
                "mark": {
                    "type": "area",
                    "line": {"color": "#7edcff", "strokeWidth": 3},
                    "color": {
                        "x1": 1,
                        "y1": 1,
                        "x2": 1,
                        "y2": 0,
                        "gradient": "linear",
                        "stops": [
                            {"offset": 0, "color": "rgba(126,220,255,0.02)"},
                            {"offset": 1, "color": "rgba(126,220,255,0.28)"},
                        ],
                    },
                    "interpolate": "monotone",
                },
                "encoding": {
                    "x": {
                        "field": "hour",
                        "type": "ordinal",
                        "axis": {
                            "title": None,
                            "labelColor": "#cdd7f8",
                            "labelPadding": 12,
                            "tickColor": "transparent",
                            "domain": False,
                        },
                    },
                    "y": {
                        "field": "trips",
                        "type": "quantitative",
                        "axis": {
                            "title": None,
                            "labelColor": "#cdd7f8",
                            "labelPadding": 10,
                            "gridColor": "rgba(255,255,255,0.10)",
                            "domain": False,
                            "tickColor": "transparent",
                            "format": ",.0f",
                        },
                    },
                    "tooltip": [
                        {"field": "hour", "type": "ordinal", "title": "Hour"},
                        {"field": "trips", "type": "quantitative", "title": "Trips", "format": ",.0f"},
                    ],
                },
            },
            {
                "transform": [{"filter": "datum.is_peak == true"}],
                "mark": {
                    "type": "point",
                    "filled": True,
                    "size": 180,
                    "color": "#9e7bff",
                    "stroke": "#ffffff",
                    "strokeWidth": 2,
                },
                "encoding": {
                    "x": {"field": "hour", "type": "ordinal"},
                    "y": {"field": "trips", "type": "quantitative"},
                    "tooltip": [
                        {"field": "hour", "type": "ordinal", "title": "Peak hour"},
                        {"field": "trips", "type": "quantitative", "title": "Trips", "format": ",.0f"},
                    ],
                },
            },
            {
                "transform": [{"filter": "datum.is_peak == true"}],
                "mark": {
                    "type": "text",
                    "dy": -18,
                    "fontSize": 12,
                    "fontWeight": 700,
                    "color": "#f5f8ff",
                },
                "encoding": {
                    "x": {"field": "hour", "type": "ordinal"},
                    "y": {"field": "trips", "type": "quantitative"},
                    "text": {"field": "label"},
                },
            },
        ],
        "config": {"view": {"stroke": None}},
    }


def payment_chart_spec() -> dict:
    return {
        "height": 320,
        "width": "container",
        "background": "transparent",
        "layer": [
            {
                "mark": {
                    "type": "bar",
                    "cornerRadiusTopLeft": 12,
                    "cornerRadiusTopRight": 12,
                    "color": "#9e7bff",
                },
                "encoding": {
                    "x": {
                        "field": "label",
                        "type": "nominal",
                        "sort": "-y",
                        "axis": {
                            "title": None,
                            "labelAngle": -90,
                            "labelColor": "#cdd7f8",
                            "labelPadding": 14,
                            "domain": False,
                            "tickColor": "transparent",
                        },
                    },
                    "y": {
                        "field": "value",
                        "type": "quantitative",
                        "axis": {
                            "title": None,
                            "labelColor": "#cdd7f8",
                            "labelPadding": 10,
                            "gridColor": "rgba(255,255,255,0.10)",
                            "domain": False,
                            "tickColor": "transparent",
                            "format": ",.0f",
                        },
                    },
                    "tooltip": [
                        {"field": "label", "type": "nominal", "title": "Payment"},
                        {"field": "value", "type": "quantitative", "title": "Trips", "format": ",.0f"},
                        {"field": "share_label", "type": "nominal", "title": "Share"},
                    ],
                },
            },
            {
                "mark": {
                    "type": "text",
                    "dy": -12,
                    "fontSize": 11,
                    "fontWeight": 700,
                    "color": "#efe9ff",
                },
                "encoding": {
                    "x": {"field": "label", "type": "nominal", "sort": "-y"},
                    "y": {"field": "value", "type": "quantitative"},
                    "text": {"field": "value_label"},
                },
            },
        ],
        "config": {"view": {"stroke": None}},
    }


def vendor_chart_spec() -> dict:
    return {
        "height": 320,
        "width": "container",
        "background": "transparent",
        "layer": [
            {
                "mark": {
                    "type": "bar",
                    "cornerRadiusTopLeft": 12,
                    "cornerRadiusTopRight": 12,
                    "color": "#5fd7ff",
                },
                "encoding": {
                    "x": {
                        "field": "label",
                        "type": "nominal",
                        "axis": {
                            "title": None,
                            "labelAngle": -90,
                            "labelColor": "#cdd7f8",
                            "labelPadding": 14,
                            "domain": False,
                            "tickColor": "transparent",
                        },
                    },
                    "y": {
                        "field": "value",
                        "type": "quantitative",
                        "axis": {
                            "title": None,
                            "labelColor": "#cdd7f8",
                            "labelPadding": 10,
                            "gridColor": "rgba(255,255,255,0.10)",
                            "domain": False,
                            "tickColor": "transparent",
                            "format": ",.0f",
                        },
                    },
                    "tooltip": [
                        {"field": "label", "type": "nominal", "title": "Vendor"},
                        {"field": "value", "type": "quantitative", "title": "Trips", "format": ",.0f"},
                    ],
                },
            },
            {
                "mark": {
                    "type": "rule",
                    "strokeDash": [5, 4],
                    "color": "rgba(255,255,255,0.18)",
                    "strokeWidth": 1.5,
                },
                "encoding": {"y": {"field": "avg_vendor_value", "type": "quantitative"}},
            },
            {
                "mark": {
                    "type": "text",
                    "dy": -12,
                    "fontSize": 12,
                    "fontWeight": 700,
                    "color": "#e9fbff",
                },
                "encoding": {
                    "x": {"field": "label", "type": "nominal"},
                    "y": {"field": "value", "type": "quantitative"},
                    "text": {"field": "value_label"},
                },
            },
        ],
        "config": {"view": {"stroke": None}},
    }


stats = load_json(
    "/stats",
    {"total_trips": 0, "avg_fare": 0, "avg_distance": 0},
)
dashboard = load_json(
    "/dashboard",
    {
        "payment_mix": [],
        "vendor_mix": [],
        "hourly_demand": [],
        "insights": {"avg_card_tip": 0, "airport_trip_count": 0},
    },
)

payment_df = pd.DataFrame(dashboard.get("payment_mix", []))
vendor_df = pd.DataFrame(dashboard.get("vendor_mix", []))
hourly_df = pd.DataFrame(dashboard.get("hourly_demand", []))

insights = dashboard.get("insights", {})

if not hourly_df.empty:
    hourly_df = hourly_df.copy()
    hourly_df["trips"] = hourly_df["trips"].astype(float)
    hourly_df["is_peak"] = False
    peak_idx = hourly_df["trips"].idxmax()
    hourly_df.loc[peak_idx, "is_peak"] = True
    hourly_df["label"] = hourly_df.apply(
        lambda row: f"{safe_int(row['hour']):02d}:00 · {short_count(row['trips'])}" if row["is_peak"] else "",
        axis=1,
    )

if not payment_df.empty:
    payment_df = payment_df.copy()
    payment_df["value"] = payment_df["value"].astype(float)
    payment_total_value = payment_df["value"].sum()
    payment_df["value_label"] = payment_df["value"].apply(short_count)
    payment_df["share_label"] = payment_df["value"].apply(
        lambda value: f"{(value / payment_total_value):.0%}" if payment_total_value else "0%"
    )

if not vendor_df.empty:
    vendor_df = vendor_df.copy()
    vendor_df["value"] = vendor_df["value"].astype(float)
    vendor_df["value_label"] = vendor_df["value"].apply(short_count)
    vendor_df["avg_vendor_value"] = vendor_df["value"].mean()

peak_hour_label = "Unavailable"
if not hourly_df.empty and "trips" in hourly_df.columns:
    peak_row = hourly_df.loc[hourly_df["trips"].astype(float).idxmax()]
    peak_hour_label = f"{safe_int(peak_row.get('hour')):02d}:00"

top_payment_label = "Unavailable"
top_payment_share = 0.0
if not payment_df.empty and "value" in payment_df.columns:
    payment_sorted = payment_df.sort_values("value", ascending=False)
    top_payment_label = str(payment_sorted.iloc[0].get("label", "Unavailable"))
    payment_total = payment_sorted["value"].astype(float).sum()
    if payment_total > 0:
        top_payment_share = float(payment_sorted.iloc[0].get("value", 0)) / payment_total

top_vendor_label = "Unavailable"
top_vendor_count = 0
if not vendor_df.empty and "value" in vendor_df.columns:
    vendor_sorted = vendor_df.sort_values("value", ascending=False)
    top_vendor_label = str(vendor_sorted.iloc[0].get("label", "Unavailable"))
    top_vendor_count = safe_int(vendor_sorted.iloc[0].get("value", 0))

summary_cards = [
    ("Peak Hour", peak_hour_label, "Highest observed pickup volume in the loaded dataset."),
    ("Top Payment", top_payment_label, f"{top_payment_share:.0%} of all trips" if top_payment_share else "Share unavailable"),
    ("Top Vendor", top_vendor_label, f"{top_vendor_count:,} recorded trips" if top_vendor_count else "Trip count unavailable"),
]

st.markdown(
    """
    <style>
    #MainMenu, header, footer, [data-testid="stSidebar"], .stDeployButton {
        display: none !important;
    }

    .stApp {
        background:
            radial-gradient(circle at 18% 10%, rgba(76, 173, 255, 0.10), transparent 24%),
            radial-gradient(circle at 82% 10%, rgba(169, 82, 255, 0.10), transparent 30%),
            linear-gradient(180deg, #09101f 0%, #0b1020 42%, #05070d 100%);
        color: #f7f7ff;
    }

    .block-container {
        max-width: 1440px !important;
        padding-top: 1.2rem !important;
        padding-bottom: 4rem !important;
    }

    .hero {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        background: linear-gradient(180deg, rgba(17, 23, 35, 0.86), rgba(12, 16, 27, 0.82));
        padding: 28px 30px;
        margin-bottom: 18px;
        box-shadow: 0 24px 60px rgba(0,0,0,0.22);
        position: relative;
        overflow: hidden;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
        gap: 22px;
        align-items: stretch;
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 320px;
        height: 320px;
        right: -120px;
        bottom: -160px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(153, 90, 255, 0.20), transparent 70%);
        filter: blur(12px);
    }

    .hero-kicker {
        color: #72d6ff;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-size: 0.76rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .hero-title {
        color: #f8fbff;
        font-size: clamp(2.4rem, 4vw, 4.4rem);
        font-weight: 900;
        margin: 0;
        line-height: 0.96;
    }

    .hero-copy {
        margin-top: 16px;
        max-width: 56rem;
        color: rgba(202, 210, 232, 0.92);
        font-size: 1.02rem;
        line-height: 1.7;
    }

    .status-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        color: #eff4ff;
        font-size: 0.92rem;
    }

    .status-pill-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: linear-gradient(180deg, #7af3ff, #9a6bff);
        box-shadow: 0 0 14px rgba(122,243,255,0.45);
    }

    .hero-side {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        padding: 20px;
        backdrop-filter: blur(16px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
    }

    .hero-side-title {
        color: #f7fbff;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 14px;
    }

    .hero-side-grid {
        display: grid;
        gap: 12px;
    }

    .hero-side-item {
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px;
        background: rgba(255,255,255,0.03);
        padding: 14px 16px;
    }

    .hero-side-label {
        color: rgba(178, 190, 222, 0.84);
        font-size: 0.74rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .hero-side-value {
        color: #ffffff;
        font-size: 1.28rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .hero-side-copy {
        color: rgba(204, 212, 234, 0.78);
        font-size: 0.88rem;
        line-height: 1.5;
    }

    [data-testid="metric-container"] {
        background: linear-gradient(180deg, rgba(17, 23, 35, 0.82), rgba(11, 15, 25, 0.8));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 18px 20px 14px 20px;
        box-shadow: 0 14px 36px rgba(0,0,0,0.18);
        transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    }

    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 18px 42px rgba(0,0,0,0.24);
        border-color: rgba(126, 227, 255, 0.18);
    }

    [data-testid="metric-container"] label {
        color: rgba(184, 193, 218, 0.86) !important;
        font-weight: 500 !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: 800;
    }

    .panel {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        background: linear-gradient(180deg, rgba(17, 23, 35, 0.82), rgba(11, 15, 25, 0.8));
        padding: 20px 22px 12px 22px;
        box-shadow: 0 18px 44px rgba(0,0,0,0.18);
        height: 100%;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }

    .panel:hover {
        transform: translateY(-3px);
        box-shadow: 0 24px 54px rgba(0,0,0,0.22);
        border-color: rgba(126, 227, 255, 0.14);
    }

    .panel-title {
        color: #f7f9ff;
        font-size: 1.18rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .panel-copy {
        color: rgba(185, 194, 219, 0.86);
        font-size: 0.95rem;
        margin-bottom: 14px;
        line-height: 1.55;
    }

    .panel-insight {
        margin-top: 4px;
        margin-bottom: 16px;
        color: #91e6ff;
        font-size: 0.88rem;
        letter-spacing: 0.02em;
    }

    .insight-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        margin-top: 10px;
    }

    .insight-card {
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px;
        padding: 16px;
        background: rgba(255,255,255,0.03);
    }

    .insight-label {
        color: rgba(178, 190, 222, 0.84);
        font-size: 0.84rem;
        margin-bottom: 8px;
    }

    .insight-value {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 800;
    }

    .insight-note {
        color: rgba(198, 205, 227, 0.88);
        font-size: 0.92rem;
        line-height: 1.55;
        margin-top: 16px;
    }

    .summary-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin-top: 10px;
        margin-bottom: 18px;
    }

    .summary-card {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(17, 23, 35, 0.82), rgba(11, 15, 25, 0.8));
        padding: 18px 20px;
        box-shadow: 0 16px 34px rgba(0,0,0,0.18);
    }

    .summary-card-label {
        color: rgba(184, 193, 218, 0.82);
        font-size: 0.75rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .summary-card-value {
        color: #ffffff;
        font-size: 1.38rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .summary-card-copy {
        color: rgba(202, 210, 232, 0.8);
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .section-kicker {
        color: #74ddff;
        font-size: 0.76rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 12px;
    }

    [data-testid="stVegaLiteChart"] > div,
    [data-testid="stDataFrame"] > div {
        background: transparent !important;
    }

    @media (max-width: 980px) {
        .hero-grid,
        .summary-strip {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-grid">
        <div>
          <div class="hero-kicker">Voice + Analytics Workspace</div>
          <h1 class="hero-title">VoiceAgent</h1>
          <div class="hero-copy">
            A premium NYC taxi intelligence console for voice-first analysis. Track demand, fares, payment behavior, and vendor performance while keeping your wake-word assistant ready over the dashboard.
          </div>
          <div class="status-strip">
            <div class="status-pill"><span class="status-pill-dot"></span> Backend connected</div>
            <div class="status-pill"><span class="status-pill-dot"></span> Voice mode ready</div>
            <div class="status-pill"><span class="status-pill-dot"></span> {safe_int(stats.get('total_trips', 0)):,} trip records</div>
          </div>
        </div>
        <div class="hero-side">
          <div class="hero-side-title">AI Snapshot</div>
          <div class="hero-side-grid">
            {''.join([
                f'''<div class="hero-side-item">
                    <div class="hero-side-label">{label}</div>
                    <div class="hero-side-value">{value}</div>
                    <div class="hero-side-copy">{copy}</div>
                  </div>'''
                for label, value, copy in summary_cards
            ])}
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(3, gap="large")
with metric_cols[0]:
    st.metric("Total Trips", f"{int(stats.get('total_trips', 0)):,}")
with metric_cols[1]:
    st.metric("Average Fare", f"${float(stats.get('avg_fare', 0)):.2f}")
with metric_cols[2]:
    st.metric("Average Distance", f"{float(stats.get('avg_distance', 0)):.2f} mi")

st.markdown(
    f"""
    <div class="summary-strip">
      <div class="summary-card">
        <div class="summary-card-label">Quick Insight</div>
        <div class="summary-card-value">{top_payment_label}</div>
        <div class="summary-card-copy">The dominant payment method currently accounts for roughly {top_payment_share:.0%} of observed trips.</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-label">Demand Signal</div>
        <div class="summary-card-value">{peak_hour_label}</div>
        <div class="summary-card-copy">This hour shows the strongest pickup demand in the loaded dataset.</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-label">Operator Lead</div>
        <div class="summary-card-value">{top_vendor_label}</div>
        <div class="summary-card-copy">Leading vendor volume sits at {top_vendor_count:,} trips across the current sample.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([1.3, 0.9], gap="large")

with top_left:
    st.markdown(
        f"""
        <div class="panel">
          <div class="section-kicker">Demand Monitor</div>
          <div class="panel-title">Hourly Trip Demand</div>
          <div class="panel-copy">Pickup activity by hour across the loaded NYC taxi trip dataset.</div>
          <div class="panel-insight">Peak demand is currently concentrated around <strong>{peak_hour_label}</strong>.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not hourly_df.empty:
        st.vega_lite_chart(hourly_df, hourly_chart_spec(), use_container_width=True)
    else:
        st.info("Hourly demand data is unavailable.")

with top_right:
    st.markdown(
        f"""
        <div class="panel">
          <div class="section-kicker">Operations Brief</div>
          <div class="panel-title">Dispatch Snapshot</div>
          <div class="panel-copy">Quick operational signals that stay visible while voice mode floats on top.</div>
          <div class="insight-grid">
            <div class="insight-card">
              <div class="insight-label">Avg Credit Card Tip</div>
              <div class="insight-value">${float(insights.get('avg_card_tip', 0)):.2f}</div>
            </div>
            <div class="insight-card">
              <div class="insight-label">Airport Trips</div>
              <div class="insight-value">{int(insights.get('airport_trip_count', 0)):,}</div>
            </div>
          </div>
          <div class="insight-note">
            Ask follow-ups like “Which payment type is most popular?”, “Which vendor leads by volume?”, or “What happens during peak hour?”
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

bottom_left, bottom_right = st.columns([1, 1], gap="large")

with bottom_left:
    st.markdown(
        f"""
        <div class="panel">
          <div class="section-kicker">Revenue Mix</div>
          <div class="panel-title">Payment Mix</div>
          <div class="panel-copy">Distribution of trips by payment method.</div>
          <div class="panel-insight"><strong>{top_payment_label}</strong> is the strongest payment channel in this dataset.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not payment_df.empty:
        st.vega_lite_chart(payment_df, payment_chart_spec(), use_container_width=True)
    else:
        st.info("Payment mix data is unavailable.")

with bottom_right:
    st.markdown(
        f"""
        <div class="panel">
          <div class="section-kicker">Vendor Watch</div>
          <div class="panel-title">Vendor Performance</div>
          <div class="panel-copy">Trip volume by vendor across the current dataset.</div>
          <div class="panel-insight"><strong>{top_vendor_label}</strong> currently leads recorded vendor volume.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not vendor_df.empty:
        st.vega_lite_chart(vendor_df, vendor_chart_spec(), use_container_width=True)
    else:
        st.info("Vendor distribution data is unavailable.")

from pathlib import Path

voice_dock_markup = Path("frontend/voice_dock_fragment.html").read_text(encoding="utf-8")
st.markdown(voice_dock_markup, unsafe_allow_html=True)
st.markdown(
    f'<div id="va-backend-url" style="display:none">http://localhost:8000</div>',
    unsafe_allow_html=True,
)

voice_overlay_worker = Path("frontend/voice_worker.js").read_text(encoding="utf-8")
components.html(
    f'<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="connect-src *;"></head><body><script>{voice_overlay_worker}</script></body></html>',
    height=1,
)
