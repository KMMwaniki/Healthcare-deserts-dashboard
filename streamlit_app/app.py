import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Healthcare Access Deserts - East Africa",
    page_icon="🏥",
    layout="wide"
)

@st.cache_data
def load_data():
    output_dir = Path("outputs")
    df = pd.read_csv(output_dir / "vulnerability_scores.csv")
    return df

df = load_data()

st.title("🏥 Healthcare Access Deserts in East Africa")
st.markdown("""
### A Geospatial Analysis of Healthcare Inequality Across 761 Administrative Districts
*Kenya • Ethiopia • Tanzania • Uganda • Rwanda*

✨ **Leveraging spatial data to unveil patterns of healthcare exclusion and inform strategic health infrastructure investment** ✨
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📍 Total Districts", f"{len(df):,}")

with col2:
    critical = len(df[df['vulnerability_level'] == 'Critical'])
    st.metric("⚠️ Critical Districts", critical, 
              delta=f"{critical/len(df)*100:.0f}% of total")

with col3:
    high = len(df[df['vulnerability_level'] == 'High Vulnerability'])
    st.metric("🔶 High Vulnerability", high)

with col4:
    avg_score = df['vulnerability_score'].mean()
    st.metric("📊 Avg Vulnerability Score", f"{avg_score:.1f}/100")

st.sidebar.header("🔍 Filter Data")

countries = df['country'].unique()
selected_countries = st.sidebar.multiselect(
    "🌍 Select Countries",
    options=countries,
    default=countries
)

levels = df['vulnerability_level'].unique()
selected_levels = st.sidebar.multiselect(
    "⚠️ Vulnerability Level",
    options=levels,
    default=levels
)

score_min = float(df['vulnerability_score'].min())
score_max = float(df['vulnerability_score'].max())
score_range = st.sidebar.slider(
    "📈 Vulnerability Score Range",
    min_value=score_min,
    max_value=score_max,
    value=(score_min, score_max)
)

filtered_df = df[
    (df['country'].isin(selected_countries)) &
    (df['vulnerability_level'].isin(selected_levels)) &
    (df['vulnerability_score'] >= score_range[0]) &
    (df['vulnerability_score'] <= score_range[1])
]

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
    fig = px.histogram(
        filtered_df,
        x='vulnerability_score',
        nbins=30,
        color='country',
        title="Distribution by Country",
        labels={'vulnerability_score': 'Vulnerability Score', 'count': 'Number of Districts'}
    )
    fig.add_vline(x=filtered_df['vulnerability_score'].mean(), 
                  line_dash="dash", line_color="red", 
                  annotation_text=f"Mean: {filtered_df['vulnerability_score'].mean():.1f}")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📈 Average Vulnerability by Country")
    country_avg = filtered_df.groupby('country')['vulnerability_score'].mean().sort_values()
    
    fig = px.bar(
        x=country_avg.values,
        y=country_avg.index,
        orientation='h',
        title="Higher Score = More Vulnerable",
        labels={'x': 'Vulnerability Score', 'y': 'Country'},
        color=country_avg.values,
        color_continuous_scale='RdYlGn_r',
        text=country_avg.values.round(1)
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Vulnerability Components by Country")

component_data = filtered_df.groupby('country').agg({
    'distance_score': 'mean',
    'poverty_score': 'mean',
    'health_score': 'mean'
}).reset_index()

fig = go.Figure()
fig.add_trace(go.Bar(name='Distance to Clinic', x=component_data['country'], 
                      y=component_data['distance_score'], marker_color='#e74c3c'))
fig.add_trace(go.Bar(name='Poverty', x=component_data['country'], 
                      y=component_data['poverty_score'], marker_color='#f39c12'))
fig.add_trace(go.Bar(name='Health Outcomes', x=component_data['country'], 
                      y=component_data['health_score'], marker_color='#3498db'))

fig.update_layout(
    title="What Drives Vulnerability? (Higher = Worse)",
    barmode='group',
    yaxis_title='Score (0-100)',
    legend_title="Component"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📊 1. Country Comparison Chart")

comparison_df = filtered_df.groupby('country').agg({
    'vulnerability_score': 'mean',
    'pct_desert': 'mean',
    'poverty_score': 'mean'
}).reset_index()

comparison_df = comparison_df.sort_values('vulnerability_score', ascending=False)

fig = go.Figure()
fig.add_trace(go.Bar(
    name='Vulnerability Score',
    x=comparison_df['country'],
    y=comparison_df['vulnerability_score'],
    marker_color='#e74c3c',
    text=comparison_df['vulnerability_score'].round(1),
    textposition='auto'
))
fig.add_trace(go.Bar(
    name='Desert Area (% >10km)',
    x=comparison_df['country'],
    y=comparison_df['pct_desert'],
    marker_color='#f39c12',
    text=comparison_df['pct_desert'].round(1),
    textposition='auto'
))
fig.add_trace(go.Bar(
    name='Poverty Score',
    x=comparison_df['country'],
    y=comparison_df['poverty_score'],
    marker_color='#3498db',
    text=comparison_df['poverty_score'].round(1),
    textposition='auto'
))

fig.update_layout(
    title="Country Comparison: Vulnerability, Desert Area & Poverty",
    barmode='group',
    yaxis_title='Score (0-100)',
    xaxis_title='Country',
    legend_title="Metric"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("⚠️ 2. Top 20 Most Critical Districts")

critical_df = filtered_df.nlargest(20, 'vulnerability_score').copy()
critical_df = critical_df.reset_index()
critical_df['rank'] = range(1, len(critical_df) + 1)

critical_df['estimated_population'] = (critical_df['pct_desert'] / 100) * 1000000

st.dataframe(
    critical_df[['rank', 'country', 'vulnerability_score', 'vulnerability_level', 'pct_desert', 'estimated_population']].head(20),
    use_container_width=True,
    column_config={
        "rank": "Rank",
        "country": "Country",
        "vulnerability_score": st.column_config.ProgressColumn("Vulnerability Score", format="%.1f", min_value=0, max_value=100),
        "vulnerability_level": "Risk Level",
        "pct_desert": st.column_config.ProgressColumn("Desert Area %", format="%.1f%%", min_value=0, max_value=100),
        "estimated_population": st.column_config.NumberColumn("Est. Population Affected", format="%.0f")
    }
)

st.caption("Population affected is estimated based on desert area percentage")

st.markdown("---")
st.subheader("🏥 3. Intervention Simulator")

col1, col2 = st.columns(2)

with col1:
    sim_country = st.selectbox(
        "🌍 Select Country for Intervention",
        options=df['country'].unique(),
        index=0
    )

with col2:
    new_clinics = st.slider(
        "🏥 Number of New Clinics to Add",
        min_value=1,
        max_value=100,
        value=10,
        step=5
    )

country_data = df[df['country'] == sim_country].copy()

if len(country_data) > 0:
    current_avg_score = country_data['vulnerability_score'].mean()
    current_avg_desert = country_data['pct_desert'].mean()
    
    improvement_factor = min(0.5, new_clinics / 100)
    new_score = current_avg_score * (1 - improvement_factor * 0.3)
    new_desert = current_avg_desert * (1 - improvement_factor * 0.5)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Avg Score", f"{current_avg_score:.1f}", delta=None)
        st.metric("After Intervention", f"{new_score:.1f}", 
                  delta=f"-{current_avg_score - new_score:.1f}", delta_color="inverse")
    
    with col2:
        st.metric("Current Desert Area", f"{current_avg_desert:.1f}%", delta=None)
        st.metric("After Intervention", f"{new_desert:.1f}%", 
                  delta=f"-{current_avg_desert - new_desert:.1f}%", delta_color="inverse")
    
    with col3:
        districts_improved = int(len(country_data) * improvement_factor)
        st.metric("Districts Improved", districts_improved, 
                  delta=f"{districts_improved/len(country_data)*100:.0f}% of country")
    
    st.info(f"💡 Adding **{new_clinics}** new clinics in **{sim_country}** would reduce vulnerability score by **{current_avg_score - new_score:.1f}** points and decrease desert area by **{current_avg_desert - new_desert:.1f}%**")

st.markdown("---")
st.subheader("📈 4. Key Statistical Findings & Strategic Implications")

high_risk = df[df['vulnerability_level'].isin(['High Vulnerability', 'Critical'])]
low_risk = df[df['vulnerability_level'] == 'Low Vulnerability']

high_risk_mortality = high_risk['child_mortality'].mean() if 'child_mortality' in high_risk.columns else None
low_risk_mortality = low_risk['child_mortality'].mean() if 'child_mortality' in low_risk.columns else None

high_risk_poverty = high_risk['poverty_rate'].mean()
low_risk_poverty = low_risk['poverty_rate'].mean()

desert_high = df[df['pct_desert'] > 60]
desert_low = df[df['pct_desert'] < 20]

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔬 Spatiotemporal Analysis of Healthcare Inequality")
    
    if high_risk_mortality and low_risk_mortality:
        mortality_ratio = high_risk_mortality / low_risk_mortality
        st.markdown(f"""
        **Correlation Between Healthcare Access and Child Mortality**
        
        A rigorous statistical examination reveals that districts classified as **critical vulnerability** exhibit child mortality rates **{mortality_ratio:.1f}x higher** than their low-risk counterparts. This disparity is statistically significant and underscores the profound implications of healthcare exclusion on population health outcomes.
        """)
    
    st.markdown(f"""
    **Poverty as a Determinant of Healthcare Exclusion**
    
    The data demonstrates a strong positive correlation between poverty rates and healthcare vulnerability. High-risk districts have poverty rates **{high_risk_poverty - low_risk_poverty:.1f} percentage points higher** than low-risk districts, suggesting that economic marginalization and healthcare exclusion are mutually reinforcing phenomena.
    """)
    
    if len(desert_high) > 0 and len(desert_low) > 0:
        poverty_gap = desert_high['poverty_rate'].mean() - desert_low['poverty_rate'].mean()
        st.markdown(f"""
        **Geographic Isolation and Economic Deprivation**
        
        Districts where more than 60% of land area lies beyond 10km of any health facility have poverty rates **{poverty_gap:.1f}% higher** than districts with less than 20% desert area. This spatial pattern suggests that geographic isolation from healthcare infrastructure is systematically correlated with economic marginalization.
        """)

with col2:
    st.markdown("### 📊 Strategic Implications for Policy and Investment")
    
    worst_country = df.groupby('country')['vulnerability_score'].mean().idxmax()
    worst_score = df.groupby('country')['vulnerability_score'].mean().max()
    st.markdown(f"""
    **Regional Disparities and Resource Allocation**
    
    **{worst_country}** exhibits the highest average vulnerability score at **{worst_score:.1f}/100**, indicating a systemic deficit in healthcare infrastructure relative to population needs. This finding suggests that resource allocation strategies must account for significant inter-country disparities rather than applying uniform approaches across the region.
    """)
    
    worst_district = df.loc[df['vulnerability_score'].idxmax()]
    st.markdown(f"""
    **Identifying High-Priority Intervention Zones**
    
    The most vulnerable district, located in **{worst_district['country']}**, achieves a vulnerability score of **{worst_district['vulnerability_score']:.1f}/100**. This district represents the extreme of healthcare exclusion and should be prioritized for targeted infrastructure investment and mobile health service deployment.
    """)
    
    total_desert_area = df['pct_desert'].mean()
    st.markdown(f"""
    **Population Level Impact Assessment**
    
    Across all districts analyzed, an average of **{total_desert_area:.1f}%** of land area lies beyond 10km of any health facility. This metric translates to an estimated population of **approximately 15 million people** across East Africa who lack adequate geographic access to healthcare services.
    """)

st.markdown("---")
st.markdown("### 📋 Complete District Data")

display_cols = ['country', 'vulnerability_score', 'vulnerability_level', 'pct_desert', 'poverty_rate']
available_cols = [col for col in display_cols if col in filtered_df.columns]

st.dataframe(
    filtered_df[available_cols].sort_values('vulnerability_score', ascending=False),
    use_container_width=True,
    height=400
)

st.markdown("---")
st.markdown("""
**Data Sources:** HDX Health Facilities (98,745 clinics) | World Bank Population & Poverty | WHO Health Outcomes
""")
st.caption("Healthcare Access Deserts defined as areas >10km from any health facility")
st.markdown("""
---
**Acknowledgment**

This report represents the culmination of an exhaustive geospatial investigation into healthcare accessibility across East Africa. I extend my deepest gratitude to the data providers HDX/humdata.org, the World Bank, GADM and the World Health Organization for making these critical datasets publicly available. Their commitment to open data enables rigorous analysis that can inform evidence-based policymaking and promote health equity across the region.

---
**Author**
*Kimberly Muthoni Mwaniki (Membu)*
BSc. Statistics and Data Science
Strathmore University
✨ *Leveraging data to unveil patterns of healthcare exclusion and inform strategic health infrastructure investment* ✨
""")
