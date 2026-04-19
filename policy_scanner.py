import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from sentence_transformers import SentenceTransformer, util
import torch
import warnings

warnings.filterwarnings("ignore")

# Initialize model locally (loads into memory once at boot)
print("Loading semantic model... This may take a moment.")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define Semantic Queries and their Weights
COMPLIANCE_QUERIES = {
    "Cookie Consent": {
        "weight": 15,
        "query": "Does the website mention using cookies, managing cookie preferences, or tracking technologies?"
    },
    "Data Retention": {
        "weight": 10,
        "query": "How long does the company retain, keep, or store personal user data?"
    },
    "User Rights": {
        "weight": 15,
        "query": "Does the user have the right to access, delete, erase, or be forgotten regarding their personal data?"
    },
    "Breach Notification": {
        "weight": 10,
        "query": "Will the company notify users or authorities in the event of a security incident or data breach?"
    },
    "Data Sharing": {
        "weight": 15,
        "query": "Does the company share, sell, or disclose personal data to third parties or service providers?"
    },
    "Contact Information": {
        "weight": 10,
        "query": "Is there contact information, an email, or a Data Protection Officer (DPO) listed to reach out about privacy concerns?"
    },
    "Policy Updates": {
        "weight": 5,
        "query": "Will the company notify users about changes, modifications, or updates to this privacy policy?"
    }
}

# Pre-compute query embeddings
QUERY_EMBEDDINGS = {k: model.encode(v["query"], convert_to_tensor=True) for k, v in COMPLIANCE_QUERIES.items()}

def find_privacy_link(base_url: str, headers: dict) -> str:
    """Intelligently explores the homepage to find the true privacy policy URL."""
    common_paths = [
        "/privacy", "/privacy-policy", "/privacy-notice", "/privacy-statement",
        "/legal/privacy", "/policies/privacy", "/privacypolicy", "/legal"
    ]
    
    # 1. Direct path check
    for path in common_paths:
        try:
            url = urljoin(base_url, path)
            req = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            if req.status_code == 200:
                return url
        except:
            continue
            
    # 2. Homepage anchor tag crawling
    try:
        response = requests.get(base_url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"].lower()
                text = link.get_text().lower()
                if "privacy" in href or "privacy" in text or "policy" in href or "legal" in href:
                    return urljoin(base_url, link["href"])
    except:
        pass
        
    return None

def split_into_chunks(text: str, chunk_size: int = 50, overlap: int = 15) -> list:
    """Splits raw text into sliding window word chunks to maintain semantic context."""
    words = text.split()
    chunks = []
    if not words:
        return chunks
        
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def scan_privacy_policy(base_url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AuditApp Scanner"
    }

    try:
        # 1. Discover Privacy URL
        privacy_url = find_privacy_link(base_url, headers)
        score = 0
        max_score = 100
        detected = []
        missing = []
        confidence_scores = {}
        
        if not privacy_url:
            return {
                "privacy_url": None,
                "detected": [],
                "missing": ["Privacy Policy URI Discovered"] + list(COMPLIANCE_QUERIES.keys()),
                "score": 0,
                "max_score": 100,
                "error": "Failed to discover a privacy policy page on the domain."
            }

        detected.append("Privacy Policy URI Discovered")
        score += 20
        confidence_scores["Privacy Policy URI Discovered"] = 1.0 # 100% confidence it exists
        
        # 2. Fetch and clean content
        try:
            response = requests.get(privacy_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return {
                "privacy_url": privacy_url,
                "detected": detected,
                "missing": list(COMPLIANCE_QUERIES.keys()),
                "score": score,
                "max_score": max_score,
                "error": f"Failed to fetch privacy policy content: {str(e)}"
            }

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text(separator=" ", strip=True)
        chunks = split_into_chunks(text, chunk_size=60, overlap=20)
        
        if not chunks:
            return {
                "privacy_url": privacy_url,
                "detected": detected,
                "missing": list(COMPLIANCE_QUERIES.keys()),
                "score": score,
                "max_score": max_score,
                "error": "Privacy document contained no readable text."
            }

        # 3. Vectorize text chunks
        chunk_embeddings = model.encode(chunks, convert_to_tensor=True)
        
        # 4. Semantic Similarity Analysis
        # We need to find the maximum cosine similarity for each query against all chunks
        for policy_name, config in COMPLIANCE_QUERIES.items():
            query_emb = QUERY_EMBEDDINGS[policy_name]
            
            # Compute cosine similarity of this query against all chunks
            cos_scores = util.cos_sim(query_emb, chunk_embeddings)[0]
            max_score_tensor = torch.max(cos_scores)
            highest_sim = max_score_tensor.item()
            
            confidence_scores[policy_name] = round(highest_sim, 3)
            
            # Threshold Check
            if highest_sim >= 0.50:
                detected.append(policy_name)
                score += config["weight"]
            else:
                missing.append(policy_name)

        return {
            "privacy_url": privacy_url,
            "detected": detected,
            "missing": missing,
            "score": score,
            "max_score": max_score,
            "confidence_scores": confidence_scores,
            "error": None
        }

    except Exception as e:
        return {
            "privacy_url": None,
            "detected": [],
            "missing": ["Privacy Policy URI Discovered"] + list(COMPLIANCE_QUERIES.keys()),
            "score": 0,
            "max_score": 100,
            "error": f"Critical semantic analysis failure: {str(e)}"
        }
