from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from scorer import score

app = FastAPI(title="ESG Claim Scorer API")

class ClaimRequest(BaseModel):
    text: str

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.post("/score")
def score_endpoint(req: ClaimRequest):
    return score(req.text)