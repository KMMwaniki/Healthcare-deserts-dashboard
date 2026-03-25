import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

st.set_page_config(
    page_title="Healthcare Access Deserts - East Africa",
    page_icon="🏥",
    layout="wide"
)

@st.cache_data
def load_data():
    # Try multiple possible paths
    possible_paths = [
        Path("outputs/vulnerability_scores.csv"),
        Path("../outputs/vulnerability_scores.csv"),
        Path("vulnerability_scores.csv"),
    ]
    
    for path in possible_paths:
        if path.exists():
            df = pd.read_csv(path)
            return df
    
    # If no file found, create sample data for demo
    st.warning("Data file not found. Using sample data for demonstration.")
    countries = ['Kenya', 'Ethiopia', 'Tanzania', 'Uganda', 'Rwanda']
    data = []
    for i, country in enumerate(countries):
        for j in range(50):
            data.append({
                'country': country,
                'vulnerability_score': np.random.uniform(20, 80),
                'vulnerability_level': np.random.choice(['Low', 'Moderate', 'High', 'Critical']),
                'pct_desert': np.random.uniform(10, 90),
                'poverty_rate': np.random.uniform(20, 60),
                'distance_score': np.random.uniform(10, 90),
                'poverty_score': np.random.uniform(20, 70),
                'health_score': np.random.uniform(10, 80),
                'child_mortality': np.random.uniform(30, 90)
            })
    return pd.DataFrame(data)

df = load_data()

st.title("🏥 Healthcare Access Deserts in East Africa")
st.markdown("""
### A Geospatial Analysis of Healthcare Inequality Across 761 Administrative Districts
*Kenya • Ethiopia • Tanzania • Uganda • Rwanda*
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📍 Total Districts", f"{len(df):,}")

with col2:
    critical = len(df[df['vulnerability_level'] == 'Critical']) if 'vulnerability_level' in df.columns else 0
    st.metric("⚠️ Critical Districts", critical)

with col3:
    high = len(df[df['vulnerability_level'] == 'High Vulnerability']) if 'vulnerability_level' in df.columns else 0
    st.metric("🔶 High Vulnerability", high)

with col4:
    avg_score = df['vulnerability_score'].mean() if 'vulnerability_score' in df.columns else 0
    st.metric("📊 Avg Vulnerability Score", f"{avg_score:.1f}/100")

st.sidebar.header("🔍 Filter Data")

countries = df['country'].unique() if 'country' in df.columns else []
selected_countries = st.sidebar.multiselect(
    "🌍 Select Countries",
    options=countries,
    default=countries
)

filtered_df = df
if 'country' in df.columns and selected_countries:
    filtered_df = df[df['country'].isin(selected_countries)]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Showing **{len(filtered_df)}** of **{len(df)}** districts")

csv = filtered_df.to_csv(index=False)
st.sidebar.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv,
    file_name="healthcare_vulnerability_data.csv",
    mime="text/csv"
)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Vulnerability Score Distribution")
    if 'vulnerability_score' in filtered_df.columns and 'country' in filtered_df.columns:
        fig = px.histogram(
            filtered_df,
            x='vulnerability_score',
            nbins=30,
            color='country',
            title="Distribution by Country"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Data loaded successfully!")

with col2:
    st.subheader("📈 Average Vulnerability by Country")
    if 'vulnerability_score' in filtered_df.columns and 'country' in filtered_df.columns:
        country_avg = filtered_df.groupby('country')['vulnerability_score'].mean().sort_values()
        fig = px.bar(
            x=country_avg.values,
            y=country_avg.index,
            orientation='h',
            title="Higher Score = More Vulnerable",
            text=country_avg.values.round(1)
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Data loaded successfully!")

st.markdown("---")
st.markdown("### 📋 District Data")

display_cols = ['country', 'vulnerability_score', 'vulnerability_level', 'pct_desert', 'poverty_rate']
available_cols = [col for col in display_cols if col in filtered_df.columns]

if available_cols:
    st.dataframe(
        filtered_df[available_cols].sort_values('vulnerability_score', ascending=False),
        use_container_width=True,
        height=400
    )

st.markdown("---")
st.markdown("""
**Data Sources:** HDX Health Facilities (98,745 clinics) | World Bank Population & Poverty | WHO Health Outcomes
""")
st.markdown("""
---
**Author**
*Kimberly Muthoni Mwaniki (Membu)*
BSc. Statistics and Data Science

✨ *Leveraging data to unveil patterns of healthcare exclusion* ✨
""")
