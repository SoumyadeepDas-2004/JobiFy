import streamlit as st
import pandas as pd
import re
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from local_llm import ask_llm
from market_context import build_market_context

# --- CONFIGURATION ---
st.set_page_config(page_title="Tech Job Market Insights", layout="wide", page_icon="💼")
DATA_FILE = "wwr_tech_jobs.csv"

# Skills Database by Domain
DOMAIN_SKILLS = {
    "All Domains": [],  # Will show all skills
    "Frontend Development": ["react", "vue", "angular", "next.js", "typescript", "javascript", "html", "css", "tailwind"],
    "Backend Development": ["python", "java", "golang", "rust", "node", "django", "flask", "spring", "fastapi"],
    "Full Stack": ["react", "node", "python", "typescript", "django", "next.js", "flask", "vue"],
    "DevOps/Cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "linux", "ansible"],
    "Data Science/ML": ["python", "pytorch", "tensorflow", "pandas", "sql", "spark", "scikit-learn"],
    "Mobile Development": ["react native", "flutter", "swift", "kotlin", "ios", "android"],
}

FLAT_SKILLS = [
    "python", "java", "javascript", "typescript", "golang", "rust", "c++", "ruby", "php", "swift", "kotlin", "sql",
    "react", "node", "django", "flask", "fastapi", "spring", "vue", "angular", "next.js", "rails", "pytorch", "tensorflow",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "linux", "ansible",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb"
]

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['published_date'] = pd.to_datetime(df['published_date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def extract_skills(description):
    found = set()
    if not isinstance(description, str): 
        return []
    text = description.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    for skill in FLAT_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found.add(skill)
    return list(found)

def filter_jobs_by_domain(df, domain, domain_skills):
    """Filter jobs that match the selected domain"""
    if domain == "All Domains" or not domain_skills:
        return df
    
    # Filter jobs that have at least one skill from the domain
    mask = df['full_description'].apply(
        lambda desc: any(skill in desc.lower() for skill in domain_skills)
    )
    return df[mask]

# --- MAIN DASHBOARD ---
def main():
    st.markdown(
    """
    <h1 style="
        text-align: center;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 0;
    ">
        <span style="color:#2E7D32;">JobiFy</span>
        <span style="font-weight: 400;">- Tech Job Market Intelligence</span>
    </h1>
    """,
    unsafe_allow_html=True
)



        # ===============================
    # Session State Initialization
    # ===============================
    if "ai_response" not in st.session_state:
        st.session_state.ai_response = ""

    if "ai_query" not in st.session_state:
        st.session_state.ai_query = ""

    st.markdown(
    "<p style='text-align: center; font-size: 16px;'><b>Real-time insights from WeWorkRemotely</b> | Updated every 6 hours</p>",
    unsafe_allow_html=True
)

    
    # Load Data
    df = load_data()
    
    if df.empty:
        st.error("❌ No data found. Please run 'collect_jobs.py' first.")
        return
    last_updated_str = "Unknown"
    if not df.empty and "dataset_last_updated_utc" in df.columns:
        last_updated = pd.to_datetime(df["dataset_last_updated_utc"].iloc[0])
        last_updated_str = last_updated.strftime("%d %b %Y, %H:%M UTC")
    # Add skills column if not exists
    if 'skills' not in df.columns:
        with st.spinner("Analyzing job descriptions..."):
            df['skills'] = df['full_description'].apply(extract_skills)
    
    # --- DOMAIN SELECTION ---
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    
    left, center, right = st.columns([1, 2, 1])

    with center:
        st.subheader("🎯 Select Domain")
        selected_domain = st.selectbox(
            "Choose your domain:",
            options=list(DOMAIN_SKILLS.keys()),
            index=0,
            help="Filter jobs by technology domain"
        )

        domain_skills = DOMAIN_SKILLS[selected_domain]
            
    
    # Filter data by domain
    filtered_df = filter_jobs_by_domain(df, selected_domain, domain_skills)
    
    st.markdown("---")
    
    # --- MARKET OVERVIEW (KEY METRICS) ---
    st.header(f"📊 {selected_domain} Market Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Active Jobs",
        len(filtered_df),
        delta=f"{(len(filtered_df)/len(df)*100):.1f}% of market"
    )
    
    col2.metric(
        "Hiring Companies",
        filtered_df['company'].nunique(),
        delta=f"Avg {len(filtered_df)/filtered_df['company'].nunique():.1f} jobs/company"
    )
    
    # Extract all skills from filtered jobs
    all_skills = []
    filtered_df['skills'].apply(lambda x: all_skills.extend(x))
    
    col3.metric(
        "Top Skill Demand",
        Counter(all_skills).most_common(1)[0][0].upper() if all_skills else "N/A",
        delta=f"{Counter(all_skills).most_common(1)[0][1]} jobs" if all_skills else ""
    )
    
    col4.metric(
        "Avg Skills/Job",
        f"{filtered_df['skills'].apply(len).mean():.1f}",
        delta="Skill diversity"
    )
    
    st.markdown("---")
    
    # --- DETAILED INSIGHTS (3 COLUMNS) ---
    col1, col2, col3 = st.columns(3)
    
    # COLUMN 1: TOP SKILLS IN DEMAND
    with col1:
        st.subheader("🔥 Most In-Demand Skills")
        
        if all_skills:
            skill_counts = pd.DataFrame(
                Counter(all_skills).most_common(10), 
                columns=['Skill', 'Jobs']
            )
            
            fig = px.bar(
                skill_counts, 
                x='Jobs', 
                y='Skill', 
                orientation='h',
                text='Jobs',
                color='Jobs',
                color_continuous_scale='blues'
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                height=400,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skills data available for this domain")
    
    # COLUMN 2: TOP HIRING COMPANIES
    with col2:
        st.subheader("🏢 Most Active Companies")
        
        company_counts = filtered_df['company'].value_counts().head(10)
        
        fig = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            text=company_counts.values,
            labels={'x': 'Jobs Posted', 'y': 'Company'},
            color=company_counts.values,
            color_continuous_scale='greens'
        )
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # COLUMN 3: JOB CATEGORIES BREAKDOWN
    with col3:
        st.subheader("📁 Job Categories")
        
        category_counts = df['category'].value_counts()
        
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # --- SKILL COMBINATIONS (WHAT SKILLS GO TOGETHER) ---
    st.header("🔗 Skill Combinations Analysis")
    st.markdown("Understanding which skills are commonly required together")
    
    # Build co-occurrence matrix for top 12 skills
    if all_skills:
        top_12_skills = [s for s, _ in Counter(all_skills).most_common(12)]
        
        co_occurrence = {skill: {other: 0 for other in top_12_skills} for skill in top_12_skills}
        
        for skills_list in filtered_df['skills']:
            for i in range(len(skills_list)):
                for j in range(i, len(skills_list)):
                    if skills_list[i] in top_12_skills and skills_list[j] in top_12_skills:
                        co_occurrence[skills_list[i]][skills_list[j]] += 1
        
        matrix_df = pd.DataFrame(co_occurrence)
        
        fig = px.imshow(
            matrix_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Blues",
            labels=dict(x="Skill", y="Skill", color="Co-occurrences")
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("💡 Higher numbers indicate skills frequently required together in job postings")
    
    st.markdown("---")
    
    # --- JOB LISTINGS TABLE ---
    st.header("📋 Recent Job Postings")
    
    # Add search filter
    search_term = st.text_input("🔍 Search jobs by title or company:", "")
    
    display_df = filtered_df.copy()
    if search_term:
        mask = (
            display_df['title'].str.contains(search_term, case=False, na=False) |
            display_df['company'].str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]
    
    # Sort by date
    display_df = display_df.sort_values('published_date', ascending=False)
    
    # Display with expandable rows
    for idx, job in display_df.head(20).iterrows():
        with st.expander(f"**{job['title']}** at {job['company']} | {job['category']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Published:** {job['published_date'].strftime('%Y-%m-%d %H:%M')}")
                
                # Show extracted skills
                if job['skills']:
                    skills_str = ', '.join(sorted(job['skills']))
                    st.success(f"**Skills:** {skills_str}")
                else:
                    st.info("No specific skills detected")
            
            with col2:
                st.link_button("🔗 View Job", job['link'], use_container_width=True)
    
    # Show total count
    st.caption(f"Showing {min(20, len(display_df))} of {len(display_df)} jobs")
    
    # --- FOOTER ---
    st.markdown("---")
    st.markdown(f"""
        **Data Source:** WeWorkRemotely RSS Feed  
        **Auto-updated:** Every 6 hours via GitHub Actions  
        **Last Updated:** {last_updated_str}
        """)
            # ===============================
    # 🤖 LOCAL AI CAREER STRATEGIST (SIDEBAR - ISOLATED)
    # ===============================
    with st.sidebar:
        st.header("🤖 AI Career Strategist")
        st.caption("Runs 100% locally (Ollama)")

        st.markdown("""
        Ask things like:
        - What skills am I missing?
        - Which jobs should I apply to?
        - Create a 30-day learning plan
        """)

        st.session_state.ai_query = st.text_area(
            "💬 Ask the AI",
            value=st.session_state.ai_query,
            placeholder="I know Python and SQL. What should I learn next?",
            height=120
        )

        # Button style (safe)
        st.markdown("""
        <style>
        div.stButton > button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            padding: 0.6em 1.2em;
            font-weight: 600;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #43a047;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.button("Ask AI", key="ask_ai_sidebar"):
            if not st.session_state.ai_query.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Thinking ..."):
                    market_context = build_market_context(filtered_df)
                    st.session_state.ai_response = ask_llm(
                        st.session_state.ai_query,
                        market_context
                    )

        # Persisted AI output
        if st.session_state.ai_response:
            st.success("📌 Strategic Advice")
            st.markdown(st.session_state.ai_response)


if __name__ == "__main__":
    main()



