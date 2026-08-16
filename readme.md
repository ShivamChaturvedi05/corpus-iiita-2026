 # ESG Claim Extraction and Scoring Pipeline

This repository contains the end-to-end data pipeline for extracting corporate environmental, social, and governance (ESG) claims from PDF reports and automatically evaluating them based on specific criteria (Specificity, Commitment, Verifiability).

---

## 🏗 Architecture Overview

The system is split into two interconnected micro-components:

1. **The Scoring API (`app.py` & `scorer.py`)** — A local FastAPI backend that receives corporate claims as text and returns 0–3 numerical scores. The root URL redirects to the interactive documentation.
2. **The Extractor (`extractor.py`)** — A processing script that parses raw PDFs, uses spaCy to filter for relevant action-oriented sentences, queries the local Scoring API via `request.py`, and compiles the final structured CSV.

---

## ⚙️ Prerequisites & Installation

Ensure you have Python 3.9+ installed.

1. Clone the repository and navigate to the project directory.
2. Install the required dependencies:

```bash
pip install fastapi uvicorn requests spacy pymupdf pydantic
```

Download the necessary spaCy language model:

```bash
python -m spacy download en_core_web_sm
```

📂 Project Structure

Ensure your working directory matches this structure before running the pipeline:

- `app.py` — The FastAPI server application, routing, and root redirect.
- `scorer.py` — The evaluation logic/models for generating the 0–3 scores.
- `request.py` — The network bridge containing `fetch_local_score()` to handle local HTTP POST requests.
- `extractor.py` — The Phase A PDF processing script.
- `pdf/` — A folder containing all the target corporate PDF reports.
- `csv_output/` — The destination folder where the final generated CSVs will be saved.

🚀 Usage Instructions

To run the extraction pipeline and generate the fully scored dataset:

Step 1 — Start the Local API Server

Open a terminal instance, navigate to the project root, and boot up the FastAPI server (this must be running before the extraction script starts):

```bash
uvicorn app:app --reload
```

The server will start on http://127.0.0.1:8000 and automatically redirect to the `/docs` UI when visited in a browser.

Step 2 — Run the Extraction Engine

Open a second terminal instance, ensure your target PDFs are placed inside the `pdf/` directory, and execute the main pipeline script:

```bash
python extractor.py
```

Step 3 — Access the Output

Once the script terminal displays the "Success!" message, navigate to the `csv_output/` folder and open `Phase_A_All_Reports_Master_v5.csv`. The output will be fully populated, mapping the `claim_id` and `claim_text` to their respective calculated scores for specificity, commitment, and verifiability.

🔌 API Documentation

The scoring engine runs locally on your machine to prevent cloud rate limits and compute costs. Teammates can send requests directly to the localhost URL.

- Interactive UI: http://127.0.0.1:8000/ (Redirects to Swagger `/docs`)
- Endpoint: `POST /score`
- Local URL: http://127.0.0.1:8000/score

Request Payload (JSON):

```json
{
  "text": "Scope 1 emissions for FY2023-24 were 1.2 MtCO2e."
}
```

Response Payload (JSON):

```json
{
  "is_claim": true,
  "specificity": 2,
  "commitment": 0,
  "verifiability": 1
}
```

🔮 Next Steps for the ML Team

The current `scorer.py` serves as a functional placeholder to ensure data flows correctly from the PDFs into the final CSV.

Once the advanced NLP models are fully trained on human-annotated data:

1. Export the trained model weights.
2. Replace the baseline logic inside `scorer.py` with the deep-learning model inference code.
3. Restart the local API server. The extraction pipeline will immediately begin utilizing the production-grade models without requiring any further structural changes.