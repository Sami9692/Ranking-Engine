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


def compute_semantic_score(career_text):
    career_text = career_text.lower()
    
    # Tokenize by finding all word sequences
    words = re.findall(r'\b\w+\b', career_text)
    doc_len = len(words)
    if doc_len == 0:
        return 0.0
        
    # Clusters of terms and weights based on JD key priorities
    term_clusters = [
        (["embeddings", "dense retrieval", "semantic search", "dense vectors", "bi-encoder", "cross-encoder", "dense search"], 2.0),
        (["sentence-transformers", "sentence transformers", "bge", "e5", "mpnet"], 2.0),
        (["vector db", "vector search", "vector database", "hybrid search", "hybrid retrieval"], 2.0),
        (["pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "pgvector"], 2.0),
        (["ndcg", "mrr", "map", "ranking evaluation", "offline evaluation", "evaluation framework", "ab test", "a/b test", "offline-online correlation"], 2.5),
        (["lora", "qlora", "peft", "fine-tuning", "fine-tuned", "sft"], 1.5),
        (["learning to rank", "learning-to-rank", "ltr", "ranking models", "re-ranking", "re-ranker", "xgboost", "lightgbm"], 2.0),
        (["nlp", "natural language processing", "information retrieval", "ir"], 1.5)
    ]
    
    avg_len = 150.0
    k1 = 1.2
    b = 0.75
    
    total_score = 0.0
    
    for terms, weight in term_clusters:
        freq = 0
        for term in terms:
            freq += career_text.count(term)
            
        if freq > 0:
            tf_factor = (freq * (k1 + 1)) / (freq + k1 * (1.0 - b + b * (doc_len / avg_len)))
            total_score += weight * tf_factor
            
    return total_score


def generate_reasoning(profile, career, signals, score, skills_found):
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "AI/ML Engineer")
    company = profile.get("current_company", "")
    
    # 1. Deterministic opening clause variation based on anonymized name
    company_phrase = f" at {company}" if company else ""
    op_hash = sum(ord(c) for c in profile.get("anonymized_name", "")) % 3
    if op_hash == 0:
        opening = f"Strong product-focused {title} with {yoe:.1f} years of experience{company_phrase}."
    elif op_hash == 1:
        opening = f"{yoe:.1f}-year veteran {title}{company_phrase} with a solid track record of production shipping."
    else:
        opening = f"Experienced {title}{company_phrase} ({yoe:.1f} YoE) with demonstrated capability in applied systems."
        
    # 2. Technical fit description
    skills_map = {
        "embeddings": "embeddings-based retrieval",
        "vectordb": "vector databases/hybrid search",
        "eval": "ranking evaluation (NDCG/MRR)",
        "llm_finetuning": "LLM fine-tuning"
    }
    found_desc = [skills_map[s] for s in skills_found if s in skills_map]
    
    if len(found_desc) >= 3:
        tech_clause = f"Directly matches core JD needs in {', '.join(found_desc[:-1])}, and {found_desc[-1]}."
    elif len(found_desc) == 2:
        tech_clause = f"Brings strong hands-on experience in both {found_desc[0]} and {found_desc[1]}."
    elif len(found_desc) == 1:
        tech_clause = f"Well-versed in {found_desc[0]}, though adjacent areas can be picked up quickly."
    else:
        tech_clause = "Brings general software engineering and ML experience."

    # 3. Location, notice period and honest concern checks
    loc = profile.get("location", "").split(",")[0].strip()
    np_days = signals.get("notice_period_days", 90)
    
    concerns = []
    if np_days > 60:
        concerns.append(f"notice period of {np_days}d is longer than preferred")
    if len(found_desc) < 3:
        missing_skills = [skills_map[s] for s in skills_map if s not in skills_found]
        if missing_skills:
            concerns.append(f"lacks direct experience in {missing_skills[0]}")
            
    loc_phrase = ""
    if loc.lower() in ["noida", "pune"]:
        loc_phrase = f"located in {loc} (ideal office location)"
    else:
        loc_phrase = f"{loc}-based"
        if signals.get("willing_to_relocate"):
            loc_phrase += " and willing to relocate"
            
    if concerns:
        concern_str = f" Note: Candidate {', '.join(concerns)}."
    else:
        concern_str = " Fits candidate availability constraints perfectly."
        
    # Combine clauses to produce natural, dynamic reasonings
    reasoning = f"{opening} {tech_clause} {loc_phrase} with {np_days}d notice.{concern_str}"
    return reasoning


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
            
    # Honeypot Check: Job duration exceeding years of experience
    yoe = profile.get("years_of_experience", 0)
    for job in career:
        if job.get("duration_months", 0) / 12.0 > yoe + 0.1:
            return 0.0, "Anomaly: career history job duration exceeds total years of experience"

    # Honeypot Check: Expert proficiency in skills with 0 years used
    expert_zero_dur_count = sum(1 for s in skills_list if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0)
    if expert_zero_dur_count >= 5:
        return 0.0, "Anomaly: expert proficiency in multiple skills with 0 duration"
            
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
        
    # Pure research exclusion check
    all_research = True
    has_production = False
    prod_kws = ["production", "deploy", "scale", "kubernetes", "docker", "aws", "gcp", "azure", "ci/cd", "pipeline", "infrastructure", "latency", "optimization", "monitoring"]
    for kw in prod_kws:
        if kw in career_text:
            has_production = True
            break
            
    research_keywords = ["academic", "research assistant", "phd", "postdoc", "university", "professor", "fellow", "lab"]
    for job in career:
        title = job.get("title", "").lower()
        company = job.get("company", "").lower()
        is_job_research = any(rk in title or rk in company for rk in research_keywords)
        if not is_job_research:
            all_research = False
            break
            
    if has_career and all_research and not has_production:
        return 0.0, "Excluded: purely academic/research career without production deployment"
        
    # Langchain-only exclusion check
    has_llm_wrappers = any(kw in career_text for kw in ["langchain", "llamaindex", "openai", "gpt"])
    has_classic_ml = any(kw in career_text or kw in skills for kw in ["pytorch", "tensorflow", "scikit-learn", "keras", "xgboost", "lightgbm", "regression", "svm", "random forest", "spacy", "nltk", "fasttext", "bert", "embeddings", "ranking", "retrieval"])
    if has_llm_wrappers and not has_classic_ml:
        return 0.0, "Excluded: LangChain-only experience without underlying ML foundations"
        
    # Title chaser exclusion check
    if len(career) >= 3:
        total_months = sum(job.get("duration_months", 0) for job in career)
        avg_months = total_months / len(career)
        curr_title = profile.get("current_title", "").lower()
        is_high_title = any(t in curr_title for t in ["lead", "staff", "principal", "director", "manager"])
        if avg_months < 18.0 and is_high_title:
            return 0.0, "Excluded: title chaser with short job durations"
        
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
    
    # Hybrid skills score: 40% declared skills + 60% semantic career text matching JD
    sem_score_raw = compute_semantic_score(career_text)
    sem_score = min(100.0, (sem_score_raw / 15.0) * 100.0)
    skills_weighted = (skill_points * 0.4 + sem_score * 0.6)
    
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
    reasoning = generate_reasoning(profile, career, signals, composite_score, skills_found)
    
    return composite_score, reasoning

def current_date_diff(d):
    return CURRENT_DATE - d
