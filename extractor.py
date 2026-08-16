import csv
import spacy
import re
import fitz
from pathlib import Path
from request import fetch_local_score

PDF_DIR = Path("pdf") 
CSV_OUTPUT = Path("csv_output/Phase_A_All_Reports_Master_v5.csv")
CSV_OUTPUT.parent.mkdir(exist_ok=True)

acts = {'is', 'has', 'will', 'reduce', 'assured', 'energy', 'water', 'implemented', 'adopted', 'mitigate', 'achieved', 'target', 'comply', 'committed', 'invested', 'ensure', 'developed', 'established'}

print("Loading optimized spaCy NLP engine...")
spacy.prefer_gpu()
nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
nlp.max_length = 5000000

def is_tmp(txt: str) -> bool:
    s = txt.strip()
    if not s: return True
    if s.endswith("?"): return True
    
    low = s.lower()
    
    if low.startswith(("businesses should", "businesses, when", "businesses when")): return True
    if "|" in s: return True
    
    pxs = (
        "provide details", "how many", "state the", "whether the",
        "briefly describe", "name of the", "reporting period", "year of",
        "registered office", "corporate address", "web link", "financial year",
        "overview of", "essential indicators", "leadership indicators",
        "contact details", "class of security", "reporting boundary", 
        "safe and responsible", "environmental and social", "recycling and",
        "indicate if", "total (a+b", "whether csr is", "is the entity",
        "describe the strategy", "describe the measures" 
    )
    
    for px in pxs:
        if low.startswith(px): return True
        
    if re.match(r"(?i)^\s*(?:[ivx1-9]+[\.\)]|)\s*whether\s+", s): return True
    if re.match(r"(?i)^\s*(?:[0-9]+)\.\s+provide", s): return True
    
    if re.search(r'(?i)brie.y\s+describe', s): return True 
    if re.search(r'(\d{3,}\s*\|\s*)|(PAGE\s*BREAK)|(Integrated Annual Report)|(BUSINESS RESPONSIBILITY)', s, re.I): return True
    
    return False

def is_val(txt: str) -> bool:
    t = txt.strip().lower()
    if not t: return False
    if t in ("nil", "n.a.", "na", "-", "zero", "none", "not applicable", "n/a"): return True
    if re.search(r"\d", t): return True
    return False

def cvt_row(txs: list) -> str:
    cln = [t.replace("\n", " ").strip() for t in txs if t.strip()]
    if len(cln) < 2: return " ".join(cln)
    return " | ".join(cln)

def get_x0(x): 
    return x["x0"]

def grp_blks(r_blks: list) -> list:
    g_blks = []
    u_idx = set()
    
    for i, b1 in enumerate(r_blks):
        if i in u_idx: continue
        r_grp = [b1]
        u_idx.add(i)
        y0_1, y1_1, h1 = b1["y0"], b1["y1"], b1["h"]
        
        for j, b2 in enumerate(r_blks):
            if j in u_idx: continue
            y0_2, y1_2, h2 = b2["y0"], b2["y1"], b2["h"]
            
            o_min = max(y0_1, y0_2)
            o_max = min(y1_1, y1_2)
            o_h = o_max - o_min
            
            if o_h > 0 and (o_h / min(h1, h2)) > 0.4:
                r_grp.append(b2)
                u_idx.add(j)
                
        r_grp.sort(key=get_x0)
        g_blks.append(r_grp)
        
    f_txs = []
    for g in g_blks:
        if len(g) == 1:
            f_txs.append(g[0]["text"])
        else:
            txs = [b["text"] for b in g]
            f_txs.append(cvt_row(txs))
            
    return f_txs

def proc_pdf(p):
    print(f"\nProcessing {p.name}...")
    pts = p.stem.split('_')
    s, c, y = (pts[0] if len(pts)>0 else "U", pts[1] if len(pts)>1 else "U", pts[2] if len(pts)>2 else "U")
    r = []
    
    try:
        doc = fitz.open(p)
        ct = ""
        for pg in doc:
            t_dct = pg.get_text("dict")
            r_blks = []
            for b in t_dct.get("blocks", []):
                if b.get("type") == 0:
                    bx = b.get("bbox", (0, 0, 0, 0))
                    tx = " ".join([sp.get("text", "") for ln in b.get("lines", []) for sp in ln.get("spans", [])]).strip()
                    if tx:
                        r_blks.append({"x0": bx[0], "y0": bx[1], "x1": bx[2], "y1": bx[3], "h": bx[3]-bx[1], "text": tx})
            
            m_lns = grp_blks(r_blks)
            ct += " ".join(m_lns) + " "
            
        doc.close()
    except Exception as e:
        print(f"Failed to read {p.name}: {e}")
        return []
            
    ct = ct.replace('\n', ' ')
            
    ms = list(re.finditer(r'(SECTION\s*C|PRINCIPLE[\-\s]*WISE)', ct, re.I))
    if not ms: 
        return []
    
    idx = ms[0].end()
    ct = ct[idx:]
    
    em = re.search(r'Independent Assurance Statement', ct, re.I)
    if em: ct = ct[:em.start()]
    
    spl = re.split(r'(Principle\s+[1-9])', ct, flags=re.I)
    cp = "U"
    
    for pt in spl:
        if re.match(r'Principle\s+[1-9]', pt, re.I):
            cp = "P" + re.search(r'\d', pt).group()
            continue
            
        d = nlp(pt)
        for sn in d.sents:
            st = sn.text.strip()
            w = st.split()
            
            if len(w) < 8 or len(w) > 65: continue
            if not any(wd.lower() in acts for wd in w): continue
            if not st[0].isalpha(): continue
            if cp == "U": continue
            if is_tmp(st): continue
            
            r.append({'sector': s, 'company': c, 'year': y, 'principle': cp, 'claim_text': st})
            
    return r

def main():
    if not PDF_DIR.exists(): return

    a_cls = []
    pdfs = list(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs in {PDF_DIR.name}/")
    
    if len(pdfs) == 0: return
        
    for p in pdfs:
        cls = proc_pdf(p)
        for i, cl in enumerate(cls, 1):
            
            score_data = fetch_local_score(cl['claim_text'])
            
            cl.update({
                'claim_id': f"{cl['sector']}_{cl['company']}_{cl['year']}_{cl['principle']}_{i:03d}", 
                'specificity': score_data['specificity'], 
                'commitment': score_data['commitment'], 
                'verifiability': score_data['verifiability'], 
                'annotator': "", 
                'flag_review': "", 
                'note': ""
            })
            a_cls.append(cl)

    if not a_cls: return

    hs = ['claim_id', 'sector', 'company', 'year', 'principle', 'claim_text', 'specificity', 'commitment', 'verifiability', 'annotator', 'flag_review', 'note']
    with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=hs)
        w.writeheader()
        w.writerows(a_cls)
        
    print(f"\nSuccess! Extracted {len(a_cls)} claims.")

if __name__ == "__main__":
    main()