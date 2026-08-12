import re

def get_spec(t):
    t = t.lower()
    if re.search(r'\d+(\.\d+)?\s*(%|\bmtco2e\b|\bkl\b|\btons\b|\bkg\b|\bliters\b|\bkwh\b|\bmwh\b|l/)', t): 
        return 3
    if re.search(r'\d+', t): 
        return 2
    if re.search(r'\b(increase|decrease|reduce|grow|improve|mitigate|achieved|invested)\b', t): 
        return 1
    return 0

def get_comm(t):
    t = t.lower()
    if re.search(r'\b(by 20\d{2}|target of|commit to|pledge)\b', t): 
        return 3
    if re.search(r'\b(will|aim to|plan to|strive to)\b', t): 
        return 2
    if re.search(r'\b(explore|consider|evaluating)\b', t): 
        return 1
    return 0

def get_verf(t):
    t = t.lower()
    if re.search(r'\b(bureau veritas|pwc|kpmg|ey|deloitte|assured by|independent third party)\b', t): 
        return 3
    if re.search(r'\b(gri|iso|sasb|tcfd|sebi|brsr|statutory)\b', t): 
        return 2
    if re.search(r'\b(internal audit|committee|policy|mechanism)\b', t): 
        return 1
    return 0

def score(txt):
    if not txt or len(txt.strip()) < 10:
        return {
            "is_claim": False, 
            "specificity": "NA", 
            "commitment": "NA", 
            "verifiability": "NA"
        }
    
    return {
        "is_claim": True,
        "specificity": get_spec(txt),
        "commitment": get_comm(txt),
        "verifiability": get_verf(txt)
    }