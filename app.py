# pyrefly: ignore [missing-import]
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime
from scoring import score_candidate

# Set page config for a premium dark mode recruiting app
st.set_page_config(
    page_title="Redrob Talent Intelligence",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling (glassmorphism headers, modern cards, harmonious color scheme)
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Title and main headers */
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        color: #ffffff;
    }
    
    .main-title-container {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #9ca3af;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Cards and containers */
    .metric-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    
    .stat-number {
        font-size: 2.2rem;
        font-weight: 700;
        color: #3b82f6;
        margin-bottom: 0.2rem;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Verified badges */
    .badge-verified {
        background-color: #065f46;
        color: #34d399;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .badge-unverified {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Career history timeline cards */
    .timeline-card {
        background-color: #1e293b;
        border-left: 4px solid #8b5cf6;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0 8px 8px 0;
    }
    
    .timeline-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #ffffff;
    }
    
    .timeline-meta {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main Title and Header
st.markdown("<div class='main-title-container'>Redrob AI Talent Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Vetting & ranking candidates by real-world capability, behavioral signals, and profile integrity.</div>", unsafe_allow_html=True)

# Sidebar - Configuration and Data Upload
st.sidebar.image("https://static.wixstatic.com/media/2cd43b_55b3eb2b89f84852b7b51d38eb15e5a2~mv2.png/v1/fill/w_320,h_100,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/2cd43b_55b3eb2b89f84852b7b51d38eb15e5a2~mv2.png", width=180)
st.sidebar.markdown("### Vetting Controls")

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload candidates file (JSONL, JSON, or GZ)", type=["jsonl", "json", "gz"])

# Default path check
default_candidates_path = "./[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/sample_candidates.json"

@st.cache_data
def load_candidates_data(file_obj, path=None):
    import gzip
    candidates = []
    if file_obj is not None:
        # Check if the uploaded file is gzipped
        if file_obj.name.endswith(".gz"):
            # Decompress gzipped content directly in-memory
            with gzip.open(file_obj, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        candidates.append(json.loads(line))
        else:
            # Regular uncompressed file
            content = file_obj.read().decode("utf-8")
            if file_obj.name.endswith(".jsonl"):
                for line in content.splitlines():
                    if line.strip():
                        candidates.append(json.loads(line))
            else: # Standard JSON list
                candidates = json.loads(content)
    elif path and os.path.exists(path):
        is_gz = path.endswith(".gz")
        open_f = gzip.open if is_gz else open
        mode = "rt" if is_gz else "r"
        with open_f(path, mode, encoding="utf-8") as f:
            if path.endswith(".jsonl") or path.endswith(".jsonl.gz"):
                for line in f:
                    if line.strip():
                        candidates.append(json.loads(line))
            else:
                candidates = json.load(f)
    return candidates

# Load data
candidates = []
data_source = ""
if uploaded_file is not None:
    candidates = load_candidates_data(uploaded_file)
    data_source = f"Uploaded File ({len(candidates)} candidates)"
elif os.path.exists(default_candidates_path):
    candidates = load_candidates_data(None, default_candidates_path)
    data_source = f"Loaded Sample Pool ({len(candidates)} candidates)"

if not candidates:
    st.info("Please upload a candidates file in the sidebar to begin.")
else:
    # Run the ranker on the candidates
    scored_candidates = []
    skipped_anom = 0
    skipped_yoe = 0
    skipped_title = 0
    skipped_consult = 0
    skipped_cv = 0
    
    for cand in candidates:
        score, reason = score_candidate(cand)
        if score > 0:
            scored_candidates.append({
                "cand": cand,
                "score": score,
                "reasoning": reason
            })
        else:
            if "Anomaly:" in reason:
                skipped_anom += 1
            elif "YoE" in reason:
                skipped_yoe += 1
            elif "title" in reason:
                skipped_title += 1
            elif "consulting" in reason:
                skipped_consult += 1
            elif "CV" in reason:
                skipped_cv += 1
                
    # Sort
    scored_candidates.sort(key=lambda x: (-x['score'], x['cand']['candidate_id']))
    
    # ------------------ TELEMETRY STATS SECTION ------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number'>{len(candidates)}</div>
            <div class='stat-label'>Total Candidates Screened</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number' style='color:#10b981;'>{len(scored_candidates)}</div>
            <div class='stat-label'>Clean Matching Profiles</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number' style='color:#ef4444;'>{skipped_anom}</div>
            <div class='stat-label'>Traps & Anomalies Flagged</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number' style='color:#a855f7;'>{round(sum([c['cand']['profile']['years_of_experience'] for c in scored_candidates]) / max(1, len(scored_candidates)), 1)} yrs</div>
            <div class='stat-label'>Avg Experience (Clean Pool)</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Ranked Shortlist", "🔍 Deep Profile Vetting", "📊 Talent Pool Insights"])
    
    with tab1:
        st.markdown("### Ranked Match Results (Top Fits)")
        
        # Display options
        max_rows = st.slider("Number of top candidates to display", min_value=10, max_value=100, value=25)
        
        # Build DataFrame
        df_list = []
        for idx, item in enumerate(scored_candidates[:max_rows]):
            cand = item['cand']
            profile = cand['profile']
            signals = cand['redrob_signals']
            df_list.append({
                "Rank": idx + 1,
                "ID": cand['candidate_id'],
                "Name": profile['anonymized_name'],
                "Current Title": profile['current_title'],
                "Experience (YoE)": profile['years_of_experience'],
                "Match Score": f"{round(item['score'], 1)}%",
                "Location": profile['location'],
                "Notice (Days)": signals['notice_period_days'],
                "Active": signals['last_active_date'],
                "Vetted Reason": item['reasoning']
            })
            
        df = pd.DataFrame(df_list)
        st.dataframe(
            df,
            column_config={
                "Match Score": st.column_config.ProgressColumn("Match Score", help="Composite match confidence", format="%s", min_value=0, max_value=100),
            },
            use_container_width=True,
            hide_index=True
        )
        
    with tab2:
        st.markdown("### Vetting & Profile Analysis")
        if not scored_candidates:
            st.warning("No clean candidates available for detailed profiling.")
        else:
            # Selectbox to choose candidate
            options = [f"Rank {i+1}: {item['cand']['profile']['anonymized_name']} ({item['cand']['candidate_id']})" for i, item in enumerate(scored_candidates)]
            selected_option = st.selectbox("Select a candidate to deep dive:", options)
            selected_idx = options.index(selected_option)
            item = scored_candidates[selected_idx]
            cand = item['cand']
            profile = cand['profile']
            signals = cand['redrob_signals']
            
            st.markdown("---")
            col_p1, col_p2 = st.columns([2, 1])
            
            with col_p1:
                st.markdown(f"## {profile['anonymized_name']} <span style='font-size:1.2rem; color:#9ca3af;'>({cand['candidate_id']})</span>", unsafe_allow_html=True)
                st.markdown(f"#### **{profile['current_title']}** at **{profile['current_company']}**")
                st.markdown(f"📍 {profile['location']}, {profile['country']} | 💼 {profile['current_industry']} | 🏢 Size: {profile['current_company_size']}")
                
                st.markdown("### Recruiter Summary")
                st.markdown(f"*{profile['summary']}*")
                
                # Verified Status Section
                st.markdown("### Profile Verification Status")
                v_email = "<span class='badge-verified'>✓ Email Verified</span>" if signals['verified_email'] else "<span class='badge-unverified'>✗ Email Unverified</span>"
                v_phone = "<span class='badge-verified'>✓ Phone Verified</span>" if signals['verified_phone'] else "<span class='badge-unverified'>✗ Phone Unverified</span>"
                v_link = "<span class='badge-verified'>✓ LinkedIn Connected</span>" if signals['linkedin_connected'] else "<span class='badge-unverified'>✗ LinkedIn Disconnected</span>"
                
                st.markdown(f"{v_email} {v_phone} {v_link}", unsafe_allow_html=True)
                
                # Career History
                st.markdown("### Career History (Timeline)")
                for job in cand.get("career_history", []):
                    end_str = "Present" if job.get("is_current") else job.get("end_date")
                    st.markdown(f"""
                    <div class='timeline-card'>
                        <div class='timeline-title'>{job.get('title')}</div>
                        <div class='timeline-meta'>{job.get('company')} | {job.get('start_date')} to {end_str} ({job.get('duration_months')} months) | Industry: {job.get('industry')} ({job.get('company_size')} employees)</div>
                        <div style='color:#e2e8f0;'>{job.get('description')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            with col_p2:
                # Ranking score card
                st.markdown(f"""
                <div style='background-color:#1e293b; padding:2rem; border-radius:12px; border:1px solid #3b82f6; text-align:center;'>
                    <div style='font-size:1rem; text-transform:uppercase; color:#9ca3af; letter-spacing:0.1em;'>Recruiter Match Score</div>
                    <div style='font-size:4rem; font-weight:800; color:#3b82f6; margin:0.5rem 0;'>{round(item['score'], 1)}%</div>
                    <div style='color:#e2e8f0; font-size:0.9rem; font-style:italic;'>"{item['reasoning']}"</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Expected Salary and Notice Period
                st.markdown("### Recruitment Signals")
                st.markdown(f"⏰ **Notice Period**: {signals['notice_period_days']} Days")
                st.markdown(f"💰 **Expected Salary**: {signals['expected_salary_range_inr_lpa']['min']} - {signals['expected_salary_range_inr_lpa']['max']} LPA")
                st.markdown(f"💼 **Preferred Mode**: {signals['preferred_work_mode'].title()}")
                st.markdown(f"✈️ **Willing to Relocate**: {'Yes' if signals['willing_to_relocate'] else 'No'}")
                st.markdown(f"🧑‍💻 **GitHub Activity Score**: {signals['github_activity_score'] if signals['github_activity_score'] != -1 else 'N/A'}")
                
                # Skills matching list
                st.markdown("### Candidate Skills Profile")
                for s in cand.get("skills", []):
                    prof_color = "#3b82f6" if s['proficiency'] == "expert" else "#8b5cf6" if s['proficiency'] == "advanced" else "#a855f7" if s['proficiency'] == "intermediate" else "#6b7280"
                    st.markdown(f"""
                    <div style='margin-bottom:0.8rem;'>
                        <div style='display:flex; justify-content:between; font-size:0.85rem; font-weight:600;'>
                            <span style='flex-grow:1;'>{s['name']}</span>
                            <span style='color:{prof_color}; margin-right: 1rem;'>{s['proficiency'].upper()}</span>
                            <span style='color:#9ca3af;'>👍 {s['endorsements']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Education History
                st.markdown("### Education")
                for edu in cand.get("education", []):
                    st.markdown(f"""
                    <div style='background-color:#111827; padding:0.8rem; border-radius:8px; margin-bottom:0.5rem; border:1px solid #1f2937;'>
                        <div style='font-weight:700; color:#fff;'>{edu.get('degree')} in {edu.get('field_of_study')}</div>
                        <div style='font-size:0.8rem; color:#9ca3af;'>{edu.get('institution')} ({edu.get('start_year')} - {edu.get('end_year')})</div>
                        <div style='font-size:0.8rem; color:#3b82f6;'>Prestige: {edu.get('tier').upper().replace('_', ' ')} | Grade: {edu.get('grade')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
    with tab3:
        st.markdown("### Marketplace Vetting Analytics")
        col_c1, col_c2 = st.columns(2)
        
        # Convert dataset variables to DataFrames for charts
        clean_df = pd.DataFrame([
            {
                "YoE": c['cand']['profile']['years_of_experience'],
                "Notice": c['cand']['redrob_signals']['notice_period_days'],
                "ResponseRate": c['cand']['redrob_signals']['recruiter_response_rate'] * 100,
                "WorkMode": c['cand']['redrob_signals']['preferred_work_mode']
            } for c in scored_candidates
        ])
        
        with col_c1:
            st.markdown("#### Excluded Trap & Noise Breakdown")
            trap_data = pd.DataFrame({
                "Category": ["Clean Fits", "Integrity Traps (Honeypots)", "YoE Out of Scope", "Irrelevant Titles", "Consulting Only", "Primary CV/Speech"],
                "Count": [len(scored_candidates), skipped_anom, skipped_yoe, skipped_title, skipped_consult, skipped_cv]
            })
            st.bar_chart(trap_data.set_index("Category"))
            
        with col_c2:
            st.markdown("#### Preferred Work Mode Distribution (Clean Pool)")
            if not clean_df.empty:
                mode_counts = clean_df["WorkMode"].value_counts()
                st.bar_chart(mode_counts)
            else:
                st.write("No clean pool data available.")
                
        st.markdown("---")
        col_c3, col_c4 = st.columns(2)
        with col_c3:
            st.markdown("#### Notice Period Distribution (Clean Pool)")
            if not clean_df.empty:
                st.write("Number of candidates in each notice period bucket:")
                np_counts = clean_df["Notice"].value_counts().sort_index()
                st.bar_chart(np_counts)
        with col_c4:
            st.markdown("#### Recruiter Response Rate Distribution")
            if not clean_df.empty:
                st.write("Recruiter response rate percentages (activity signal):")
                st.line_chart(clean_df["ResponseRate"])
