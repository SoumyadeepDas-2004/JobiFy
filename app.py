import streamlit as st
import pandas as pd
import re
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations

# --- CONFIGURATION ---
st.set_page_config(page_title="Tech Job Trend Tracker", layout="wide")
DATA_FILE = "wwr_tech_jobs.csv"

# Skill Database (Same as before)
SKILLS_DB = {
    "Languages": ["python", "java", "javascript", "typescript", "golang", "rust", "c++", "ruby", "php", "swift", "kotlin", "sql"],
    "Frameworks": ["react", "node", "django", "flask", "fastapi", "spring", "vue", "angular", "next.js", "rails", "pytorch", "tensorflow"],
    "Cloud/DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "linux", "circleci", "git"],
    "Databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb", "snowflake"]
}
FLAT_SKILLS = [skill for category in SKILLS_DB.values() for skill in category]

# --- HELPER FUNCTIONS ---
@st.cache_data # Caches the data so it doesn't reload on every click
def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['published_date'] = pd.to_datetime(df['published_date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def extract_skills(description):
    found = set()
    if not isinstance(description, str): return []
    text = description.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    for skill in FLAT_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found.add(skill)
    return list(found)

# --- MAIN DASHBOARD ---
def main():
    st.title("🚀 Real-Time Tech Job Market Intelligence")
    st.markdown("Analyzing live job postings from **WeWorkRemotely** to detect emerging tech trends.")

    # 1. LOAD DATA
    df = load_data()
    if df.empty:
        st.error("❌ No data found. Please run 'collect_jobs.py' first.")
        return

    # 2. SIDEBAR FILTERS
    st.sidebar.header("Filters")
    selected_category = st.sidebar.multiselect("Filter by Category", df['category'].unique(), default=df['category'].unique())
    
    # Filter the DataFrame based on selection
    filtered_df = df[df['category'].isin(selected_category)]

    # 3. HIGH-LEVEL METRICS (KPIs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Jobs", len(filtered_df))
    col2.metric("Unique Companies", filtered_df['company'].nunique())
    
    # Find most popular skill dynamically
    all_skills = []
    filtered_df['full_description'].apply(lambda x: all_skills.extend(extract_skills(x)))
    if all_skills:
        most_common_skill = Counter(all_skills).most_common(1)[0][0]
        col3.metric("🔥 Hottest Skill", most_common_skill.upper())

    st.divider()

    # 4. CHART: TOP SKILLS (Interactive Bar Chart)
    st.subheader("📊 Top In-Demand Tech Skills")
    if all_skills:
        skill_counts = pd.DataFrame(Counter(all_skills).most_common(20), columns=['Skill', 'Count'])
        
        fig = px.bar(skill_counts, x='Count', y='Skill', orientation='h', 
                     title="Most Requested Skills", text='Count', color='Count', 
                     color_continuous_scale='viridis')
        fig.update_layout(yaxis=dict(autorange="reversed")) # Top skill at top
        st.plotly_chart(fig, use_container_width=True)
    
    # 5. CHART: SKILL CORRELATION HEATMAP
    st.subheader("🔗 Skill Co-Occurrence Matrix")
    st.markdown("If a job asks for **Skill A**, how likely is it to ask for **Skill B**?")
    
    # Calculate Co-occurrence
    job_skills_list = filtered_df['full_description'].apply(extract_skills).tolist()
    co_occurrence = {skill: {other: 0 for other in FLAT_SKILLS} for skill in FLAT_SKILLS}
    
    for skills in job_skills_list:
        for s1, s2 in combinations(skills, 2):
            co_occurrence[s1][s2] += 1
            co_occurrence[s2][s1] += 1

    matrix_df = pd.DataFrame(co_occurrence)
    # Filter for cleaner view (only top 15 skills from the bar chart)
    top_15_skills = [x[0] for x in Counter(all_skills).most_common(15)]
    matrix_df = matrix_df.loc[top_15_skills, top_15_skills]

    # Plot Heatmap using Plotly
    fig_heatmap = px.imshow(matrix_df, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                            labels=dict(x="Skill", y="Skill", color="Co-occurrences"))
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # 6. RAW DATA INSPECTOR
    with st.expander("🔍 View Raw Job Data"):
        st.dataframe(filtered_df[['published_date', 'company', 'title', 'category', 'link']])

if __name__ == "__main__":
    main()