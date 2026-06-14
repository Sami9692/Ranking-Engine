import re
from datetime import datetime

CURRENT_DATE = datetime(2026, 6, 14)

def parse_date(d_str):
    if not d_str:
        return None
    try:
        return datetime.strptime(d_str, "%Y-%m-%d")
    except:
        return None

def is_consulting_company(name):
    if not name:
        return False
    name = name.lower()
    consulting_firms = [
        "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", 
        "tata consultancy", "wipro technologies", "infosys technologies", 
        "mphasis", "tech mahindra", "hcl", "deloitte", "pwc", "ey", "kpmg",
        "l&t", "lnt", "mindtree", "ust global", "virtusa", "persistent systems"
    ]
    for firm in consulting_firms:
        if firm in name:
            return True
    return False

def check_mismatched_job(t, d):
    t = t.lower()
    d = d.lower()
    
    # Non-tech titles vs tech descriptions
    is_non_tech_title = any(kw in t for kw in ["accountant", "marketing", "hr", "sales", "support", "graphic", "content writer"])
    is_tech_desc = any(kw in d for kw in [
        "spark", "kafka", "pipeline", "predictive modeling", "nlp pipeline", 
        "recommendation-style", "semantic search", "fine-tuned llama", 
        "ml feature engineering", "deep learning models", "frontend engineering", 
        "android mobile development", "cloud infrastructure", "test automation",
        "pyspark", "airflow", "snowflake", "scikit-learn", "tensorflow", "pytorch",
        "neural", "nlp", "kubernetes", "docker", "gcp", "aws", "vector search", 
        "sentence transformers", "fine-tuning llms", "llama-2-7b", "mistral-7b", 
        "qlora", "lora", "bert", "embeddings", "milvus", "weaviate", "qdrant", 
        "faiss", "opensearch", "elasticsearch", "information retrieval", "ranking models", 
        "xgboost", "lightgbm"
    ])
    
    if is_non_tech_title and is_tech_desc:
        return True
        
    # Tech titles vs non-tech descriptions
    is_tech_title = any(kw in t for kw in ["engineer", "ml", "ai", "developer", "scientist", "analyst"])
    is_non_tech_desc = any(kw in d for kw in [
        "customer support team lead", "mechanical engineering design role", 
        "content writing and seo", "brand design and creative", 
        "senior accounting role", "marketing leadership", 
        "clinical trial data", "legal operations", "compliance officer"
    ])
    
    if is_tech_title and is_non_tech_desc:
        return True
        
    return False

def sk_name_proper(kw):
    mapping = {
        "embeddings": "embeddings",
        "sentence-transformers": "Sentence Transformers",
        "sentence transformers": "Sentence Transformers",
        "bge": "BGE",
        "e5": "E5",
        "vector db": "Vector DBs",
        "vector search": "Vector Search",
        "pinecone": "Pinecone",
        "weaviate": "Weaviate",
        "qdrant": "Qdrant",
        "milvus": "Milvus",
        "opensearch": "OpenSearch",
        "elasticsearch": "Elasticsearch",
        "faiss": "FAISS",
        "ndcg": "NDCG evaluation",
        "mrr": "MRR evaluation",
        "map": "MAP evaluation",
        "evaluation": "ML evaluation",
        "lora": "LoRA",
        "qlora": "QLoRA",
        "peft": "PEFT",
        "fine-tuning": "fine-tuning",
        "fine-tuning llms": "LLM fine-tuning",
        "llm fine-tuning": "LLM fine-tuning"
    }
    return mapping.get(kw.lower(), kw)

def score_candidate(cand):
    profile = cand.get("profile", {})
    career = cand.get("career_history", [])
    signals = cand.get("redrob_signals", {})
    skills_list = cand.get("skills", [])
    skills = {s['name'].lower(): s for s in skills_list}
    
    # 1. HARD FILTER FOR ANOMALIES (HONEYPOTS & TRAPS)
    # Return 0.0, "reason" if any anomaly is found
    signup_dt = parse_date(signals.get("signup_date"))
    last_active_dt = parse_date(signals.get("last_active_date"))
    if signup_dt and last_active_dt and last_active_dt < signup_dt:
        return 0.0, "Anomaly: last active date before signup date"
        
    sal = signals.get("expected_salary_range_inr_lpa", {})
    sal_min = sal.get("min", 0)
    sal_max = sal.get("max", 0)
    if sal_min > sal_max:
        return 0.0, "Anomaly: expected salary min exceeds max"
        
    for job in career:
        start_dt = parse_date(job.get("start_date"))
        end_dt = parse_date(job.get("end_date"))
        if start_dt and end_dt and end_dt < start_dt:
            return 0.0, "Anomaly: career history job start date after end date"
        if job.get("duration_months", 0) < 0:
            return 0.0, "Anomaly: career history job has negative duration"
            
    descriptions = [job.get("description", "") for job in career if job.get("description", "")]
    if len(descriptions) != len(set(descriptions)):
        return 0.0, "Anomaly: duplicate job descriptions in career history"
        
    for job in career:
        if check_mismatched_job(job.get("title", ""), job.get("description", "")):
            return 0.0, "Anomaly: career job title-description mismatch"
            
    # 2. POSITION & EXPERIENCE SCORE
    yoe = profile.get("years_of_experience", 0)
    if yoe < 4.0 or yoe > 15.0:
        return 0.0, "YoE outside valid engineering range"
        
    # Experience scoring: target 5-9 years.
    if 5.0 <= yoe <= 9.0:
        exp_score = 100
    elif 4.0 <= yoe < 5.0:
        exp_score = 70 + (yoe - 4.0) * 30
    elif 9.0 < yoe <= 12.0:
        exp_score = 100 - (yoe - 9.0) * 10
    else: # 12 to 15
        exp_score = 70 - (yoe - 12.0) * 20
        
    # Current Title check
    curr_title = profile.get("current_title", "").lower()
    title_score = 0
    if any(kw in curr_title for kw in ["ai engineer", "ml engineer", "machine learning engineer", "nlp engineer"]):
        title_score = 100
    elif "data scientist" in curr_title or "research engineer" in curr_title:
        title_score = 85
    elif "backend engineer" in curr_title or "software engineer" in curr_title or "developer" in curr_title:
        title_score = 70
    else:
        return 0.0, f"Irrelevant title: {curr_title}"
        
    # 3. TECHNICAL & SKILLS MATCHING
    core_skills = {
        "embeddings": ["embeddings", "sentence-transformers", "sentence transformers", "bge", "e5"],
        "vectordb": ["vector db", "vector search", "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss"],
        "eval": ["ndcg", "mrr", "map", "evaluation"],
        "llm_finetuning": ["lora", "qlora", "peft", "fine-tuning", "fine-tuning llms", "llm fine-tuning"]
    }
    
    skills_found = set()
    skill_points = 0
    
    career_text = " ".join([job.get("description", "").lower() for job in career]) + " " + profile.get("summary", "").lower()
    
    for category, kws in core_skills.items():
        found_in_list = False
        for kw in kws:
            if kw in skills:
                # Skill is in the skills list
                # Verify if it's also in descriptions or summary (to avoid pure keyword stuffers)
                if kw in career_text or any(w in career_text for w in kw.split()):
                    found_in_list = True
                    break
        if found_in_list:
            skills_found.add(category)
            skill_points += 25
        else:
            found_in_desc = False
            for kw in kws:
                if kw in career_text:
                    found_in_desc = True
                    break
            if found_in_desc:
                skills_found.add(category)
                skill_points += 15
                
    # 4. EXCLUSIONS & RESTRICTIONS
    # Consulting check
    all_consulting = True
    has_career = False
    for job in career:
        has_career = True
        if not is_consulting_company(job.get("company", "")):
            all_consulting = False
            break
    if has_career and all_consulting:
        return 0.0, "Excluded: exclusively consulting company background"
        
    # CV/Speech/Robotics Check
    has_nlp_ir = "embeddings" in skills_found or "vectordb" in skills_found or any(kw in career_text for kw in ["nlp", "retrieval", "search", "ranking", "recommendation", "information retrieval"])
    has_cv_speech_robot = any(kw in career_text or kw in skills for kw in ["computer vision", "opencv", "image classification", "object detection", "cnn", "speech recognition", "tts", "robotics", "speech to text", "text to speech"])
    if has_cv_speech_robot and not has_nlp_ir:
        return 0.0, "Excluded: primary CV/speech/robotics without NLP/IR"
        
    # 5. LOCATION SCORE
    country = profile.get("country", "").lower()
    loc = profile.get("location", "").lower()
    
    location_score = 0
    if country == "india":
        if "noida" in loc or "pune" in loc or "delhi" in loc or "gurgaon" in loc or "ncr" in loc:
            location_score = 100
        elif "mumbai" in loc or "hyderabad" in loc or "bangalore" in loc or "bengaluru" in loc:
            location_score = 90
        else:
            location_score = 70
    else:
        if signals.get("willing_to_relocate", False):
            location_score = 30
        else:
            location_score = 10
            
    # 6. BEHAVIORAL SIGNALS & AVAILABILITY
    np_days = signals.get("notice_period_days", 90)
    if np_days <= 30:
        np_score = 100
    elif np_days <= 60:
        np_score = 80
    elif np_days <= 90:
        np_score = 40
    else:
        np_score = 10
        
    rr = signals.get("recruiter_response_rate", 0.0)
    rr_score = rr * 100
    
    last_act = parse_date(signals.get("last_active_date"))
    if last_act:
        days_inactive = (current_date_diff(last_act)).days
        if days_inactive <= 30:
            act_score = 100
        elif days_inactive <= 90:
            act_score = 80
        elif days_inactive <= 180:
            act_score = 50
        else:
            act_score = 10
    else:
        act_score = 0
        
    otw_boost = 1.1 if signals.get("open_to_work_flag", False) else 1.0
    
    skills_weighted = skill_points
    exp_title_weighted = (exp_score * 0.4 + title_score * 0.6)
    loc_weighted = location_score
    behavior_weighted = (np_score * 0.4 + rr_score * 0.3 + act_score * 0.3) * otw_boost
    
    composite_score = (
        skills_weighted * 0.35 +
        exp_title_weighted * 0.25 +
        loc_weighted * 0.15 +
        behavior_weighted * 0.25
    )
    
    # 7. GENERATING SPECIFIC, HONEST REASONING
    title_display = profile.get("current_title", "AI Engineer")
    skills_to_mention = []
    for category, kws in core_skills.items():
        for kw in kws:
            if kw in skills:
                skills_to_mention.append(sk_name_proper(kw))
                break
                
    skills_str = f"proficient in {', '.join(skills_to_mention)}" if skills_to_mention else "strong background in ML/AI systems"
    
    loc_pref = ""
    if "noida" in loc or "pune" in loc:
        loc_pref = f"{loc.split(',')[0].strip().title()}-based (preferred office location)"
    else:
        loc_pref = f"{loc.split(',')[0].strip().title()}-based"
        
    np_str = f"{np_days}d notice"
    
    reasoning = f"{title_display} with {yoe:.1f} yrs experience; {skills_str}; {loc_pref}, {np_str}."
    
    return composite_score, reasoning

def current_date_diff(d):
    return CURRENT_DATE - d
