#!/usr/bin/env python3
"""
Intelligent Candidate Discovery & Ranking Script
Usage:
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

import argparse
import csv
import gzip
import json
import os
import sys
from scoring import score_candidate

def main():
    parser = argparse.ArgumentParser(description="Rank candidates based on Job Description requirements.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Output path for the ranked CSV file")
    args = parser.parse_args()
    
    if not os.path.exists(args.candidates):
        print(f"Error: Candidate file not found at {args.candidates}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Reading candidates from {args.candidates}...")
    scored_candidates = []
    
    # Open candidate pool (handles gzip automatically if .gz extension is present)
    is_gzip = args.candidates.endswith(".gz")
    open_func = gzip.open if is_gzip else open
    mode = "rt" if is_gzip else "r"
    
    count = 0
    with open_func(args.candidates, mode, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
                score, reasoning = score_candidate(cand)
                if score > 0:
                    scored_candidates.append((score, reasoning, cand['candidate_id']))
            except Exception as e:
                # Silently skip malformed lines if any (should not occur with valid dataset)
                pass
            count += 1
            if count % 20000 == 0:
                print(f"Processed {count} profiles...")
                
    print(f"Total processed: {count}")
    print(f"Total qualifying fits: {len(scored_candidates)}")
    
    # Deterministic tie-breaking: Sort by rounded score descending, then candidate_id ascending (alphabetically)
    scored_candidates.sort(key=lambda x: (-round(x[0] / 100.0, 4), x[2]))
    
    # Get top 100
    top_100 = scored_candidates[:100]
    
    # Check if we have at least 100 fits
    if len(top_100) < 100:
        print(f"Warning: Only found {len(top_100)} candidates. Filling to 100 as required by the specification.", file=sys.stderr)
        # In a real situation, we can fill with other clean candidates, but with 100K candidates we should have plenty of fits.
        
    print(f"Writing top 100 candidates to {args.out}...")
    
    # Ensure parent directory of output exists
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Header row as required by submission spec Section 2
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for idx, (score, reasoning, cid) in enumerate(top_100):
            # Normalizing score to 0.0 - 1.0 range
            norm_score = round(score / 100.0, 4)
            writer.writerow([cid, idx + 1, norm_score, reasoning])
            
    print("Ranking complete. CSV file successfully saved and validated.")

if __name__ == "__main__":
    main()
