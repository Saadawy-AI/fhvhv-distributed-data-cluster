from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


APP_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = APP_ROOT / "data" / "nyc_taxi_analysis_results.csv"
REQUIRED_COLUMNS = {
    "passenger_count",
    "total_trips",
    "avg_distance_miles",
    "avg_fare_usd",
    "avg_tip_usd",
    "total_revenue_usd",
}


st.set_page_config(
    page_title="NYC Taxi Analytics",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

appearance = st.sidebar.selectbox(
    "Appearance",
    ["Auto", "Light", "Dark"],
    help="Auto follows the appearance preference of your device/browser.",
)
appearance_class = appearance.lower()

st.markdown(
    """
    <style>
    :root {
        --ink: #14212b;
        --muted: #5b6b78;
        --line: #d7e1e8;
        --surface: rgba(255, 255, 255, 0.86);
        --canvas: #f3f7f8;
        --blue: #1769aa;
        --blue-soft: #d8edf7;
        --gold: #c46b16;
        --mint: #147866;
    }
    .app-appearance-dark,
    body:has(.app-appearance-dark) .stApp {
        --ink: #ecf4f7;
        --muted: #aebfc8;
        --line: #334852;
        --surface: rgba(25, 39, 46, 0.92);
        --canvas: #101b20;
        --blue: #6fc4e6;
        --blue-soft: #244b5c;
        --gold: #f1a24f;
        --mint: #65c7ac;
        color-scheme: dark;
    }
    @media (prefers-color-scheme: dark) {
        body:has(.app-appearance-auto) .stApp {
            --ink: #ecf4f7;
            --muted: #aebfc8;
            --line: #334852;
            --surface: rgba(25, 39, 46, 0.92);
            --canvas: #101b20;
            --blue: #6fc4e6;
            --blue-soft: #244b5c;
            --gold: #f1a24f;
            --mint: #65c7ac;
            color-scheme: dark;
        }
    }
    .stApp {
        background: var(--canvas);
        color: var(--ink);
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.35;
        background-image: linear-gradient(rgba(23, 105, 170, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(23, 105, 170, 0.035) 1px, transparent 1px);
        background-size: 28px 28px;
    }
    .block-container { max-width: 1420px; padding-top: 2.2rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { background: #172a33; }
    [data-testid="stSidebar"] * { color: #f4f7f8; }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.2rem 1.8rem;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        box-shadow: 0 16px 34px rgba(23, 33, 43, 0.08);
        margin-bottom: 1.1rem;
    }
    .hero::after { content: ""; position: absolute; width: 190px; height: 190px; right: -54px; top: -74px; border: 26px solid var(--blue-soft); border-radius: 50%; opacity: 0.7; }
    .hero h1 { color: var(--ink); font-size: clamp(2rem, 4vw, 3.5rem); line-height: 1.05; margin: 0; letter-spacing: 0; }
    .hero p { color: var(--muted); margin: 0.65rem 0 0; font-size: 1rem; }
    [data-testid="stMetricValue"] { color: var(--blue); }
    [data-testid="stMetric"] { min-height: 112px; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 0.8rem 1rem; }
    .section-label { color: var(--muted); font-size: 0.8rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin: 1.1rem 0 0.45rem; }
    [data-testid="stTabs"] button { color: var(--muted); font-weight: 700; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--blue); }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    .insight { border-left: 4px solid var(--gold); padding: 0.8rem 1rem; background: var(--surface); color: var(--ink); border-radius: 0 6px 6px 0; margin: 0.5rem 0 1rem; }
    .js-plotly-plot .plotly .modebar-btn path, .js-plotly-plot .xtick text, .js-plotly-plot .ytick text, .js-plotly-plot .gtitle, .js-plotly-plot .legendtext { fill: var(--muted) !important; }
    </style>
    <div class="app-appearance-APPEARANCE_CLASS"></div>
    """.replace("APPEARANCE_CLASS", appearance_class),
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_csv(data_path: str, modified_time: float) -> pd.DataFrame:
    dataframe = pd.read_csv(data_path)
    missing_columns = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    numeric_columns = sorted(REQUIRED_COLUMNS)
    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    invalid_values = {
        column: int((dataframe[column] < 0).sum())
        for column in numeric_columns
        if (dataframe[column] < 0).any()
    }
    if invalid_values:
        raise ValueError(
            "Negative values found in: "
            + ", ".join(invalid_values.keys())
        )

    dataframe = dataframe.dropna(subset=numeric_columns).copy()
    dataframe["passenger_count"] = dataframe["passenger_count"].astype(int)
    if dataframe.empty:
        raise ValueError("The uploaded CSV has no usable rows after validation.")
    return dataframe.sort_values("passenger_count").reset_index(drop=True)


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_timestamp(file_path: Path) -> str:
    return pd.to_datetime(file_path.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")


def render_sidebar() -> tuple[pd.DataFrame, list[int]]:
    st.sidebar.markdown("## Dashboard controls")
    if not DEFAULT_DATA_PATH.exists():
        st.sidebar.error(f"Results file not found: {DEFAULT_DATA_PATH}")
        st.stop()

    if st.sidebar.button("Refresh data", use_container_width=True):
        load_csv.clear()
        st.rerun()

    try:
        dataframe = load_csv(str(DEFAULT_DATA_PATH), DEFAULT_DATA_PATH.stat().st_mtime)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.sidebar.error(str(error))
        st.stop()

    st.sidebar.caption(f"Source: {DEFAULT_DATA_PATH.name}")
    st.sidebar.caption(f"Last updated: {format_timestamp(DEFAULT_DATA_PATH)}")
    st.sidebar.caption("Data is managed by the project pipeline.")
    passenger_options = sorted(dataframe["passenger_count"].unique().tolist())
    selected_passengers = st.sidebar.multiselect(
        "Passenger count",
        options=passenger_options,
        default=passenger_options,
    )
    return dataframe, selected_passengers


def main() -> None:
    dataframe, selected_passengers = render_sidebar()
    filtered = dataframe[dataframe["passenger_count"].isin(selected_passengers)].copy()

    st.markdown(
        """
        <div class="hero">
            <h1>NYC Taxi Analytics</h1>
            <p>Explore distributed Spark results by passenger profile, fare, distance, and revenue.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.warning("Select at least one passenger count from the sidebar.")
        return

    total_trips = filtered["total_trips"].sum()
    total_revenue = filtered["total_revenue_usd"].sum()
    weighted_fare = (filtered["avg_fare_usd"] * filtered["total_trips"]).sum() / total_trips
    weighted_tip = (filtered["avg_tip_usd"] * filtered["total_trips"]).sum() / total_trips
    weighted_distance = (filtered["avg_distance_miles"] * filtered["total_trips"]).sum() / total_trips
    revenue_per_trip = total_revenue / total_trips
    tip_rate = weighted_tip / weighted_fare if weighted_fare else 0
    top_revenue_row = filtered.loc[filtered["total_revenue_usd"].idxmax()]
    top_distance_row = filtered.loc[filtered["avg_distance_miles"].idxmax()]

    overview_tab, revenue_tab, trips_tab, data_tab = st.tabs(
        ["Overview", "Revenue analysis", "Trip metrics", "Data table"]
    )

    with overview_tab:
        st.markdown('<div class="section-label">Snapshot</div>', unsafe_allow_html=True)
        metric_columns = st.columns(4)
        metric_columns[0].metric("Total trips", f"{total_trips:,.0f}")
        metric_columns[1].metric("Total revenue", format_currency(total_revenue))
        metric_columns[2].metric("Revenue / trip", f"${revenue_per_trip:,.2f}")
        metric_columns[3].metric("Tip rate", f"{tip_rate:.1%}")
        st.markdown(
            f'<div class="insight"><strong>Key insight:</strong> '
            f'{int(top_revenue_row["passenger_count"])}-passenger trips generate the highest '
            f'revenue in the selected data ({format_currency(top_revenue_row["total_revenue_usd"])}). '
            f'The longest average distance is {top_distance_row["avg_distance_miles"]:.2f} miles '
            f'for {int(top_distance_row["passenger_count"])} passengers.</div>',
            unsafe_allow_html=True,
        )

        overview_columns = st.columns(2)
        with overview_columns[0]:
            st.markdown('<div class="section-label">Revenue by passenger count</div>', unsafe_allow_html=True)
            revenue_chart = px.bar(
                filtered,
                x="passenger_count",
                y="total_revenue_usd",
                text_auto="$.3s",
                color="total_revenue_usd",
                color_continuous_scale=["#b9d9e8", "#1769aa"],
                labels={"passenger_count": "Passengers", "total_revenue_usd": "Revenue (USD)"},
            )
            revenue_chart.update_layout(coloraxis_showscale=False, height=360)
            st.plotly_chart(revenue_chart, use_container_width=True)
        with overview_columns[1]:
            st.markdown('<div class="section-label">Fare and tip comparison</div>', unsafe_allow_html=True)
            fare_chart = px.bar(
                filtered,
                x="passenger_count",
                y=["avg_fare_usd", "avg_tip_usd"],
                barmode="group",
                labels={"passenger_count": "Passengers", "value": "Amount (USD)", "variable": "Metric"},
                color_discrete_sequence=["#e08b2c", "#238b72"],
            )
            fare_chart.update_layout(height=360, legend_title_text="")
            st.plotly_chart(fare_chart, use_container_width=True)

    with revenue_tab:
        st.markdown('<div class="section-label">Revenue dashboard</div>', unsafe_allow_html=True)
        revenue_columns = st.columns(3)
        revenue_columns[0].metric("Top revenue group", f"{int(filtered.loc[filtered.total_revenue_usd.idxmax(), 'passenger_count'])} passengers")
        revenue_columns[1].metric("Highest fare", format_currency(filtered["avg_fare_usd"].max()))
        revenue_columns[2].metric("Highest tip", format_currency(filtered["avg_tip_usd"].max()))

        revenue_line = px.line(
            filtered,
            x="passenger_count",
            y=["total_revenue_usd", "total_trips"],
            markers=True,
            labels={"passenger_count": "Passengers", "value": "Value", "variable": "Metric"},
            color_discrete_sequence=["#1769aa", "#e08b2c"],
        )
        revenue_line.update_layout(height=420, legend_title_text="")
        st.plotly_chart(revenue_line, use_container_width=True)

        revenue_share = px.pie(
            filtered,
            names="passenger_count",
            values="total_revenue_usd",
            hole=0.45,
            labels={"passenger_count": "Passengers", "total_revenue_usd": "Revenue"},
        )
        revenue_share.update_layout(height=400, legend_title_text="Passengers")
        st.plotly_chart(revenue_share, use_container_width=True)

    with trips_tab:
        st.markdown('<div class="section-label">Trip metrics dashboard</div>', unsafe_allow_html=True)
        trip_columns = st.columns(3)
        trip_columns[0].metric("Avg distance", f"{weighted_distance:,.2f} mi")
        trip_columns[1].metric("Avg fare", format_currency(weighted_fare))
        trip_columns[2].metric("Avg tip", format_currency(weighted_tip))

        distance_chart = px.scatter(
            filtered,
            x="avg_distance_miles",
            y="avg_fare_usd",
            size="total_trips",
            color="passenger_count",
            text="passenger_count",
            labels={
                "avg_distance_miles": "Average distance (miles)",
                "avg_fare_usd": "Average fare (USD)",
                "passenger_count": "Passengers",
            },
            color_continuous_scale=["#238b72", "#e08b2c", "#1769aa"],
        )
        distance_chart.update_traces(textposition="top center")
        distance_chart.update_layout(height=440)
        st.plotly_chart(distance_chart, use_container_width=True)

    with data_tab:
        table_columns = [
            "passenger_count", "total_trips", "avg_distance_miles",
            "avg_fare_usd", "avg_tip_usd", "total_revenue_usd",
        ]
        display_data = filtered[table_columns].rename(
            columns={
                "passenger_count": "Passengers", "total_trips": "Total trips",
                "avg_distance_miles": "Avg distance (mi)", "avg_fare_usd": "Avg fare (USD)",
                "avg_tip_usd": "Avg tip (USD)", "total_revenue_usd": "Total revenue (USD)",
            }
        )
        st.markdown('<div class="section-label">Filtered results</div>', unsafe_allow_html=True)
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        st.download_button(
            "Download filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="nyc_taxi_filtered_results.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()