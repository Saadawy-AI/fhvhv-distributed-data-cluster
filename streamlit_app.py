from io import BytesIO
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

st.markdown(
    """
    <style>
    :root {
        --ink: #17212b;
        --muted: #66727d;
        --line: #dfe6eb;
        --blue: #1769aa;
        --gold: #e08b2c;
        --mint: #238b72;
    }
    .stApp {
        background: linear-gradient(135deg, #f7fafc 0%, #eef5f4 52%, #fff8ee 100%);
    }
    [data-testid="stSidebar"] {
        background: #17212b;
    }
    [data-testid="stSidebar"] * {
        color: #f4f7f8;
    }
    .hero {
        padding: 1.4rem 1.7rem 1.2rem;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.86);
        box-shadow: 0 10px 28px rgba(23, 33, 43, 0.06);
        margin-bottom: 1.1rem;
    }
    .hero h1 {
        color: var(--ink);
        font-size: clamp(2rem, 4vw, 3.5rem);
        line-height: 1.05;
        margin: 0;
    }
    .hero p {
        color: var(--muted);
        margin: 0.65rem 0 0;
        font-size: 1rem;
    }
    [data-testid="stMetricValue"] {
        color: var(--blue);
    }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.8rem 1rem;
    }
    .section-label {
        color: var(--muted);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 1.1rem 0 0.45rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_csv(source: bytes) -> pd.DataFrame:
    dataframe = pd.read_csv(BytesIO(source))
    missing_columns = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    numeric_columns = sorted(REQUIRED_COLUMNS)
    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe = dataframe.dropna(subset=numeric_columns).copy()
    dataframe["passenger_count"] = dataframe["passenger_count"].astype(int)
    if dataframe.empty:
        raise ValueError("The uploaded CSV has no usable rows after validation.")
    return dataframe.sort_values("passenger_count").reset_index(drop=True)


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def render_sidebar() -> tuple[pd.DataFrame, list[int]]:
    st.sidebar.markdown("## Data source")
    uploaded_file = st.sidebar.file_uploader(
        "Upload an analysis CSV",
        type="csv",
        help="The file must contain the six columns used by the Spark aggregation.",
    )

    source_name = uploaded_file.name if uploaded_file else DEFAULT_DATA_PATH.name
    source_bytes = uploaded_file.getvalue() if uploaded_file else DEFAULT_DATA_PATH.read_bytes()
    try:
        dataframe = load_csv(source_bytes)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.sidebar.error(str(error))
        st.stop()

    st.sidebar.caption(f"Loaded: {source_name}")
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

    st.markdown('<div class="section-label">Snapshot</div>', unsafe_allow_html=True)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Total trips", f"{total_trips:,.0f}")
    metric_columns[1].metric("Total revenue", format_currency(total_revenue))
    metric_columns[2].metric("Weighted avg fare", format_currency(weighted_fare))
    metric_columns[3].metric("Weighted avg tip", format_currency(weighted_tip))

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.markdown('<div class="section-label">Revenue by passenger count</div>', unsafe_allow_html=True)
        revenue_chart = px.bar(
            filtered,
            x="passenger_count",
            y="total_revenue_usd",
            text_auto="$.3s",
            color="total_revenue_usd",
            color_continuous_scale=["#b9d9e8", "#1769aa"],
            labels={
                "passenger_count": "Passengers",
                "total_revenue_usd": "Revenue (USD)",
            },
        )
        revenue_chart.update_layout(coloraxis_showscale=False, height=360)
        st.plotly_chart(revenue_chart, use_container_width=True)

    with chart_columns[1]:
        st.markdown('<div class="section-label">Average fare and tip</div>', unsafe_allow_html=True)
        fare_chart = px.bar(
            filtered,
            x="passenger_count",
            y=["avg_fare_usd", "avg_tip_usd"],
            barmode="group",
            labels={
                "passenger_count": "Passengers",
                "value": "Amount (USD)",
                "variable": "Metric",
            },
            color_discrete_sequence=["#e08b2c", "#238b72"],
        )
        fare_chart.update_layout(height=360, legend_title_text="")
        st.plotly_chart(fare_chart, use_container_width=True)

    table_columns = [
        "passenger_count",
        "total_trips",
        "avg_distance_miles",
        "avg_fare_usd",
        "avg_tip_usd",
        "total_revenue_usd",
    ]
    display_data = filtered[table_columns].rename(
        columns={
            "passenger_count": "Passengers",
            "total_trips": "Total trips",
            "avg_distance_miles": "Avg distance (mi)",
            "avg_fare_usd": "Avg fare (USD)",
            "avg_tip_usd": "Avg tip (USD)",
            "total_revenue_usd": "Total revenue (USD)",
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