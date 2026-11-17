
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="Smart Campus Waste Management",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- PROFESSIONAL CSS ----------------
st.markdown("""
<style>
    .stApp {
        background-color: #F5F8FC;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .dashboard-title {
        font-size: 34px;
        font-weight: 750;
        color: #17324D;
        margin-bottom: 0;
    }

    .dashboard-subtitle {
        color: #64748B;
        font-size: 15px;
        margin-bottom: 25px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E2E8F0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
    }

    h2, h3 {
        color: #17324D;
    }

    section[data-testid="stSidebar"] {
        background-color: #EDF3F8;
    }

    .info-card {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- LOAD DATASET ----------------
DATA_FILE = Path(__file__).parent / "data.csv"


@st.cache_data
def load_data(file_path, modified_time):
    df = pd.read_csv(file_path)

    required_columns = [
        "Date", "Location", "Waste_Type", "Waste_Weight_kg"
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(
            f"CSV mein ye columns missing hain: {', '.join(missing)}"
        )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Location"] = df["Location"].astype("string").str.strip()
    df["Waste_Type"] = df["Waste_Type"].astype("string").str.strip()
    df["Waste_Weight_kg"] = pd.to_numeric(
        df["Waste_Weight_kg"], errors="coerce"
    )

    df = df.dropna(
        subset=["Date", "Location", "Waste_Type", "Waste_Weight_kg"]
    )

    df = df[df["Waste_Weight_kg"] >= 0]

    return df


# ---------------- HANDLE DATA ERRORS ----------------
if not DATA_FILE.exists():
    st.error(
        "data.csv file nahi mili. app.py aur data.csv ko "
        "ek hi project folder mein rakho."
    )
    st.stop()

try:
    data = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)
except Exception as error:
    st.error(f"Dataset load nahi hua: {error}")
    st.stop()

if data.empty:
    st.warning("CSV dataset mein valid records nahi hain.")
    st.stop()


# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.markdown("## 🔎 Filter Dashboard")
st.sidebar.caption("Choose filters to analyse campus waste.")

locations = sorted(data["Location"].dropna().unique().tolist())
waste_types = sorted(data["Waste_Type"].dropna().unique().tolist())

selected_locations = st.sidebar.multiselect(
    "Campus Location",
    options=locations,
    default=locations
)

selected_types = st.sidebar.multiselect(
    "Waste Category",
    options=waste_types,
    default=waste_types
)

min_date = data["Date"].min().date()
max_date = data["Date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Tip: Location, waste category aur date filters ko "
    "change karke charts compare karo."
)


# ---------------- APPLY FILTERS ----------------
filtered_data = data[
    data["Location"].isin(selected_locations)
    & data["Waste_Type"].isin(selected_types)
].copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_data = filtered_data[
        (filtered_data["Date"].dt.date >= start_date)
        & (filtered_data["Date"].dt.date <= end_date)
    ]

elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    selected_date = date_range[0]

    filtered_data = filtered_data[
        filtered_data["Date"].dt.date == selected_date
    ]


# ---------------- DASHBOARD HEADER ----------------
st.markdown(
    '<div class="dashboard-title">♻️ Smart Campus Waste Management System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Monitor, analyse and understand waste generation across campus.'
    '</div>',
    unsafe_allow_html=True
)

st.success(
    "Dashboard is running successfully. "
    "Use the sidebar to explore your dataset."
)


# ---------------- KPI CARDS ----------------
st.subheader("📊 Project Overview")

total_waste = filtered_data["Waste_Weight_kg"].sum()
total_records = len(filtered_data)
category_count = filtered_data["Waste_Type"].nunique()
location_count = filtered_data["Location"].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Waste", f"{total_waste:,.1f} kg")
col2.metric("Waste Categories", category_count)
col3.metric("Campus Locations", location_count)
col4.metric("Data Records", total_records)

st.markdown("---")


# ---------------- EMPTY FILTER RESULT ----------------
if filtered_data.empty:
    st.warning(
        "Selected filters ke liye koi data available nahi hai. "
        "Filters change karke dobara check karo."
    )
    st.stop()


# ---------------- CHART DATA ----------------
waste_summary = (
    filtered_data.groupby("Waste_Type", as_index=False)
    ["Waste_Weight_kg"].sum()
    .sort_values("Waste_Weight_kg", ascending=False)
)

location_summary = (
    filtered_data.groupby("Location", as_index=False)
    ["Waste_Weight_kg"].sum()
    .sort_values("Waste_Weight_kg", ascending=False)
)

daily_summary = (
    filtered_data.groupby("Date", as_index=False)
    ["Waste_Weight_kg"].sum()
    .sort_values("Date")
)


# ---------------- CHARTS: WASTE TYPE & LOCATION ----------------
st.subheader("📈 Waste Analysis")

chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("### ♻️ Waste by Type")

    fig_type = px.bar(
        waste_summary,
        x="Waste_Type",
        y="Waste_Weight_kg",
        color="Waste_Type",
        text="Waste_Weight_kg",
        labels={
            "Waste_Type": "Waste Category",
            "Waste_Weight_kg": "Waste Weight (kg)"
        },
        template="plotly_white"
    )

    fig_type.update_traces(
        texttemplate="%{text:.1f} kg",
        textposition="outside"
    )

    fig_type.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=25, b=10),
        xaxis_title="Waste Category",
        yaxis_title="Waste Weight (kg)"
    )

    st.plotly_chart(fig_type, use_container_width=True)


with chart2:
    st.markdown("### 📍 Waste by Location")

    fig_location = px.pie(
        location_summary,
        names="Location",
        values="Waste_Weight_kg",
        hole=0.45,
        template="plotly_white"
    )

    fig_location.update_traces(
        textposition="inside",
        textinfo="label+percent"
    )

    fig_location.update_layout(
        margin=dict(l=10, r=10, t=25, b=10)
    )

    st.plotly_chart(fig_location, use_container_width=True)


# ---------------- DAILY WASTE TREND ----------------
st.markdown("---")
st.subheader("📅 Waste Generation Over Time")

fig_trend = px.line(
    daily_summary,
    x="Date",
    y="Waste_Weight_kg",
    markers=True,
    labels={
        "Date": "Date",
        "Waste_Weight_kg": "Waste Weight (kg)"
    },
    template="plotly_white"
)

fig_trend.update_traces(line_width=3)

fig_trend.update_layout(
    xaxis_title="Date",
    yaxis_title="Waste Weight (kg)",
    hovermode="x unified"
)

st.plotly_chart(fig_trend, use_container_width=True)


# ---------------- DETAILED DATA TABLE ----------------
st.markdown("---")
st.subheader("📋 Waste Records")

display_data = filtered_data.sort_values(
    "Date", ascending=False
).copy()

display_data["Date"] = display_data["Date"].dt.strftime("%Y-%m-%d")

display_data = display_data.rename(columns={
    "Date": "Date",
    "Location": "Campus Location",
    "Waste_Type": "Waste Category",
    "Waste_Weight_kg": "Waste Weight (kg)"
})

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)


# ---------------- DOWNLOAD FILTERED CSV ----------------
csv_data = filtered_data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered Waste Data (CSV)",
    data=csv_data,
    file_name="campus_waste_filtered_data.csv",
    mime="text/csv"
)


# ---------------- RECOMMENDATIONS ----------------
st.markdown("---")
st.subheader("💡 Waste Management Recommendations")

if not waste_summary.empty:
    highest_category = waste_summary.iloc[0]["Waste_Type"]
    highest_weight = waste_summary.iloc[0]["Waste_Weight_kg"]

    highest_location = location_summary.iloc[0]["Location"]

    st.info(
        f"**Highest waste category:** {highest_category} "
        f"({highest_weight:.1f} kg in the selected data). "
        "Consider reviewing segregation, collection and reduction practices."
    )

    st.info(
        f"**Highest waste location:** {highest_location}. "
        "Review waste generation and collection practices at this location."
    )

st.markdown("""
<div class="info-card">
    <b>General Recommendations</b>
    <ul>
        <li>Separate food waste, paper and plastic wherever applicable.</li>
        <li>Encourage recycling and reuse.</li>
        <li>Monitor waste generation regularly.</li>
        <li>Use the dashboard to identify areas that may need improvement.</li>
    </ul>
</div>
""", unsafe_allow_html=True)


# ---------------- FOOTER ----------------
st.caption(
    "Smart Campus Waste Management System | Academic Project Prototype"
)