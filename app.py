from fastapi import FastAPI
from pydantic import BaseModel
from scorer import score

app = FastAPI(title="ESG Claim Scorer API")

class ClaimRequest(BaseModel):
    text: str

@app.post("/score")
def score_endpoint(req: ClaimRequest):
    result = score(req.text)
    return result