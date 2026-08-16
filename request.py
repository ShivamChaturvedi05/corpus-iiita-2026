import requests

def fetch_local_score(claim_text):
    url = "http://127.0.0.1:8000/score"
    payload = {"text": claim_text}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
        
    return {"is_claim": False, "specificity": "NA", "commitment": "NA", "verifiability": "NA"}