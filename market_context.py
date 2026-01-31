from collections import Counter

def build_market_context(df):
    all_skills = []
    df['skills'].apply(lambda x: all_skills.extend(x))

    top_skills = Counter(all_skills).most_common(10)
    top_companies = df['company'].value_counts().head(5)

    return f"""
MARKET SNAPSHOT:
- Total active jobs: {len(df)}
- Top demanded skills: {', '.join([s for s, _ in top_skills])}
- Top hiring companies: {', '.join(top_companies.index.tolist())}

INSIGHT:
Hiring managers prioritize candidates who match at least 70% of required skills.
Skill combinations matter more than single tools.
"""
