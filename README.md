# 💼 JobiFy — Tech Job Market Intelligence

JobiFy is an automated **tech job market intelligence dashboard** that collects real-time remote job postings, analyzes skill demand, and provides actionable insights through an interactive Streamlit UI.

It combines **scheduled data ingestion**, **market analytics**, and an optional **local AI career strategist** to help developers understand hiring trends and skill gaps.

---

## 🚀 Features

### 📡 Automated Job Data Collection
- Fetches remote job listings from **WeWorkRemotely RSS feed**
- Filters **tech-only roles** using keyword + category logic
- Runs automatically via **GitHub Actions (daily)**
- Stores data in a versioned CSV dataset

### 📊 Market Intelligence Dashboard
- Total active tech jobs
- Hiring companies & job concentration
- Top in-demand skills by domain
- Skill combinations & co-occurrence analysis
- Job category distribution
- Searchable, sortable job listings

### 🎯 Domain-Based Filtering
Analyze jobs by:
- Frontend Development  
- Backend Development  
- Full Stack  
- DevOps / Cloud  
- Data Science / ML  
- Mobile Development  

### 🤖 Local AI Career Strategist
- Runs **100% locally using Ollama**
- Uses real market data for context
- Answers questions like:
  - “What skills am I missing?”
  - “Which jobs should I apply to?”
  - “What should I learn next?”

> ⚠️ AI assistant is **disabled in cloud deployments** (Streamlit Cloud does not support local LLMs).

---

## 🧱 Architecture Overview
```bash
WeWorkRemotely RSS
      ↓
GitHub Actions (daily cron)
      ↓
Filtered Tech Jobs CSV
      ↓
Streamlit Dashboard
      ↓
Local Ollama LLM
```


---

## 🛠️ Tech Stack

- **Python**
- **Streamlit**
- **Pandas**
- **Plotly**
- **Feedparser**
- **BeautifulSoup**
- **GitHub Actions**
- **Ollama (local only)**

---

## 📁 Project Structure
```bash
JobiFy/
│
├── app.py # Streamlit dashboard
├── collect_jobs.py # RSS scraper & tech filter
├── market_context.py # Market summary for AI
├── local_llm.py # Ollama integration (local)
├── wwr_tech_jobs.csv # Auto-updated dataset
├── requirements.txt
└── .github/
└── workflows/
└── daily_scraper.yml
```

---

## 📸 Screenshots:
<img width="1913" height="866" alt="image" src="https://github.com/user-attachments/assets/ababb25d-a986-433e-b394-845529495498" />
<img width="1918" height="867" alt="image" src="https://github.com/user-attachments/assets/a454b24c-1dc8-401c-9caa-fe21755ff000" />
<img width="1919" height="865" alt="image" src="https://github.com/user-attachments/assets/a5e12317-7a0c-4f68-8b74-f25b4f38da4b" />
<img width="1919" height="873" alt="image" src="https://github.com/user-attachments/assets/34e0d15e-712f-4a0f-82c2-884cc1b0a95a" />

---

## 🔴 Live Demo

🚀 **Live App:** https://jobify-jrlagj6idnel5epvrrkftx.streamlit.app/  
📊 **Auto-updated daily via GitHub Actions**

---









