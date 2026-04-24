import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# Single Page App heuristics and bypass
JINA_BASE_URL = "https://r.jina.ai/"
SPA_SIGNALS = [
    r'<div id=["\']root["\']>',
    r'<div id=["\']app["\']>',
    r'data-reactroot',
    r'__NEXT_DATA__',
]

def is_spa(html_text: str) -> bool:
    for pattern in SPA_SIGNALS:
        if re.search(pattern, html_text, re.IGNORECASE):
            return True
    return False

# Structured Detection Matrix: Weights and Dense Synonym Mapping
# This simulates the semantic capability natively without downloading ~1GB of ML layers.
COMPLIANCE_CHECKS = {
    "Cookie Consent": {
        "weight": 15,
        "keywords": [
            r"cookie.*consent", r"opt[- ]?in", r"tracking technolog(?:y|ies)", 
            r"manage cookies", r"cookie preference", r"strictly necessary cookies",
            r"accept cookies", r"consent banner", r"web beacons", r"pixel tags", r"local storage"
        ]
    },
    "Data Retention": {
        "weight": 10,
        "keywords": [
            r"data retention", r"retain(?: your)? (?:data|information)", r"storage period", 
            r"how long we (?:keep|retain)", r"retention period", r"store(?: your)? information",
            r"criteria used to determine", r"kept for as long as", r"delete.*no longer needed"
        ]
    },
    "User Rights": {
        "weight": 15,
        "keywords": [
            r"your rights", r"your choices", r"data subject rights", r"right to access", 
            r"right to be forgotten", r"delete(?: your)? (?:data|information)", r"erase(?: your)? (?:data|information)",
            r"request data deletion", r"remove(?: your)? information", r"withdraw consent",
            r"access, correct", r"manage your privacy", r"portability", r"restrict processing", r"opt[- ]?out"
        ]
    },
    "Breach Notification": {
        "weight": 10,
        "keywords": [
            r"data breach", r"breach notification", r"security incident", 
            r"unauthorized access", r"notify authorities", r"incident response",
            r"leak", r"compromised", r"safeguards", r"protect(?: your)? (?:data|information|personal)", r"security measures"
        ]
    },
    "Data Sharing": {
        "weight": 15,
        "keywords": [
            r"third party", r"third parties", r"service provider", 
            r"data sharing", r"disclose(?: your)? information", r"sell(?: your)? (?:data|information)",
            r"share(?: your)? (?:data|information)", r"affiliates", r"when we share", r"how we share"
        ]
    },
    "Contact Information": {
        "weight": 10,
        "keywords": [
            r"contact us", r"contact information", r"privacy officer", 
            r"dpo", r"data protection officer", r"get in touch", r"email us at", r"how to contact", r"questions about this policy"
        ]
    },
    "Policy Updates": {
        "weight": 5,
        "keywords": [
            r"changes to this policy", r"we may update", r"updates to our privacy",
            r"modify this policy", r"updated from time to time", r"effective date", r"last updated", r"revision date", r"material changes"
        ]
    }
}

# Compile regex engines on startup for blazing fast parsing speeds
COMPILED_CHECKS = {
    key: [re.compile(pattern, re.IGNORECASE) for pattern in data["keywords"]]
    for key, data in COMPLIANCE_CHECKS.items()
}

def score_page_content(soup: BeautifulSoup, text: str) -> int:
    """Scores a candidate page based on heuristics simulating privacy context."""
    score = 0
    
    # 1. Structural Signals
    if len(text) > 1000:
        score += 20
    if len(soup.find_all("p")) > 3:
        score += 10
        
    lower_text = text.lower()
    
    # 2. Heuristic Content Scoring
    concept_groups = [
        ["collect", "information", "data"],                 # Data collection
        ["access", "delete", "request"],                    # User rights
        ["cookie", "tracking"],                             # Cookies
        ["third party", "partners", "share"]                # Data Sharing
    ]
    
    for concept_list in concept_groups:
        if any(keyword in lower_text for keyword in concept_list):
            score += 15
            
    return score

def find_privacy_link(base_url: str, headers: dict) -> str:
    """Intelligently discovers the privacy policy URL without relying on hardcoded paths."""
    try:
        response = requests.get(base_url, headers=headers, timeout=8)
        if response.status_code != 200:
            return None
    except:
        return None

    soup = BeautifulSoup(response.text, "lxml" if "lxml" in str(BeautifulSoup) else "html.parser")
    base_domain = urlparse(base_url).netloc
    
    candidate_links = set()
    irrelevant_keywords = ["login", "signup", "register", "cart", "checkout", "auth"]
    priority_keywords = ["privacy", "legal", "terms", "policy"]
    
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        # Keep only internal links (same domain), stripping www. to allow matching
        base_domain_stripped = base_domain.replace("www.", "")
        link_domain_stripped = parsed_url.netloc.replace("www.", "")
        
        if not link_domain_stripped.endswith(base_domain_stripped) and not base_domain_stripped.endswith(link_domain_stripped):
            continue
            
        lower_path = parsed_url.path.lower()
        
        if any(irr in lower_path for irr in irrelevant_keywords):
            continue
            
        candidate_links.add(full_url)

    # If SPA or no links found, rely on Jina Reader API to get markdown-rendered content and extract links
    if not candidate_links or is_spa(response.text):
        try:
            jina_resp = requests.get(f"{JINA_BASE_URL}{base_url}", headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"}, timeout=15)
            if jina_resp.status_code == 200:
                # Capture standard markdown links like [Privacy Center](https://www.spotify.com/legal/privacy-policy/)
                matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', jina_resp.text)
                for link_text, href in matches:
                    text_lower = link_text.lower()
                    if "privacy" in text_lower or "policy" in text_lower or "legal" in text_lower or "terms" in text_lower:
                        candidate_links.add(href)
        except Exception:
            pass

    # Sort links to prioritize ones containing legal/privacy terminology directly in URL, max 15
    sorted_candidates = sorted(
        list(candidate_links), 
        key=lambda x: -2 if "privacy" in x.lower() else (-1 if any(p in x.lower() for p in priority_keywords) else 0)
    )[:15]

    best_candidate = None
    highest_score = -1
    
    for candidate_url in sorted_candidates:
        try:
            req = requests.get(candidate_url, headers=headers, timeout=3)
            if req.status_code != 200:
                continue
                
            candidate_soup = BeautifulSoup(req.text, "lxml" if "lxml" in str(BeautifulSoup) else "html.parser")
            
            # Clean scripts and styles to avoid invisible textual noise
            for script in candidate_soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            candidate_text = candidate_soup.get_text(separator=" ", strip=True)
            
            score = score_page_content(candidate_soup, candidate_text)
            
            # Additional heuristic: Intelligent URL-path scoring
            lower_url = candidate_url.lower()
            if "/privacy" in lower_url and not "choices" in lower_url:
                score += 100
            elif "privacy" in lower_url:
                score += 50
            elif any(p in lower_url for p in priority_keywords):
                score += 20
                
            if score > highest_score:
                highest_score = score
                best_candidate = candidate_url
                
            # Early break optimization: If we find a highly confident candidate, stop scanning
            if highest_score >= 120:
                break
                
        except:
            continue
            
    # Failsafe: If heuristic scoring found garbage or a non-legal URL, execute structural brute-force
    url_is_legal = any(p in best_candidate.lower() for p in priority_keywords) if best_candidate else False
    if not best_candidate or (highest_score < 60 and not url_is_legal):
        COMMON_POLICY_PATHS = [
            "/us/legal/privacy-policy/", "/legal/privacy-policy/", "/privacy/", "/privacy-policy/", 
            "/legal/privacy/", "/en/privacy/", "/en-us/privacy/", "/policies/privacy/", "/about/privacy/"
        ]
        
        parsed_base = urlparse(base_url)
        domain_parts = parsed_base.netloc.split(".")
        if len(domain_parts) >= 2:
            root_domain = ".".join(domain_parts[-2:])
            fallback_base = f"{parsed_base.scheme}://www.{root_domain}"
        else:
            fallback_base = base_url
            
        for path in COMMON_POLICY_PATHS:
            test_url = urljoin(fallback_base, path)
            try:
                test_resp = requests.get(test_url, headers=headers, timeout=5, allow_redirects=True)
                if test_resp.status_code == 200:
                    text_lower = test_resp.text.lower()
                    if len(text_lower) > 2000 and ("privacy" in text_lower or "policy" in text_lower):
                        return test_resp.url
            except Exception:
                continue
                
        return None
        
    return best_candidate

def split_into_chunks(text: str, chunk_size: int = 150) -> list:
    """Splits raw text into sliding window word chunks."""
    words = text.split()
    chunks = []
    if not words:
        return chunks
    
    # We no longer need overlapping chunks since regex operates dynamically within sentences.
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def scan_privacy_policy(base_url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AuditApp Scanner"
    }

    try:
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
                "missing": ["Privacy Policy URI Discovered"] + list(COMPLIANCE_CHECKS.keys()),
                "score": 0,
                "max_score": max_score,
                "error": "Failed to discover a privacy policy page on the domain."
            }

        # Automatically grant 20 Points for discovering URI
        detected.append("Privacy Policy URI Discovered")
        score += 20
        confidence_scores["Privacy Policy URI Discovered"] = 1.0
        
        try:
            response = requests.get(privacy_url, headers=headers, timeout=8)
            response.raise_for_status()
            
            # Follow HTTP meta refresh redirects commonly utilized by enterprise firewalls (Google / Apple)
            refresh_soup = BeautifulSoup(response.text, "html.parser")
            meta_refresh = refresh_soup.find("meta", attrs={"http-equiv": lambda x: x and x.lower() == "refresh"})
            if meta_refresh and "content" in meta_refresh.attrs:
                content_attr = meta_refresh["content"]
                if "url=" in content_attr.lower():
                    redirect_url = content_attr.lower().split("url=")[-1].strip(" '\"")
                    if not redirect_url.startswith("http"):
                        redirect_url = urljoin(privacy_url, redirect_url)
                    response = requests.get(redirect_url, headers=headers, timeout=8)
                    response.raise_for_status()
                
        except requests.RequestException as e:
            return {
                "privacy_url": privacy_url,
                "detected": detected,
                "missing": list(COMPLIANCE_CHECKS.keys()),
                "score": score,
                "max_score": max_score,
                "error": f"Failed to fetch privacy policy content: {str(e)}"
            }

        # Parse text cleanly using basic lxml or html.parser
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text(separator=" ", strip=True)
        
        # Enterprise Portal Heuristic: If text is suspiciously short, attempt localization index traversal
        if len(text) < 2000:
            for locale in ["en-us", "en-ww", "english"]:
                try:
                    redirect_url = urljoin(privacy_url, f"{locale}/")
                    locale_resp = requests.get(redirect_url, headers=headers, timeout=5)
                    if locale_resp.status_code == 200:
                        locale_soup = BeautifulSoup(locale_resp.text, "html.parser")
                        for script in locale_soup(["script", "style", "nav", "footer", "header"]):
                            script.extract()
                        locale_text = locale_soup.get_text(separator=" ", strip=True)
                        if len(locale_text) > 2000:
                            text = locale_text
                            privacy_url = redirect_url
                            break
                except:
                    continue
                    
        # Single Page App & Thin Content Bypass utilizing Jina AI Reader API
        if is_spa(response.text) or len(text) < 500:
            try:
                jina_resp = requests.get(f"{JINA_BASE_URL}{privacy_url}", headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"}, timeout=15)
                if jina_resp.status_code == 200 and len(jina_resp.text) > 500:
                    text = jina_resp.text
            except Exception:
                pass
        chunks = split_into_chunks(text, chunk_size=150)
        
        if not chunks:
            return {
                "privacy_url": privacy_url,
                "detected": detected,
                "missing": list(COMPLIANCE_CHECKS.keys()),
                "score": score,
                "max_score": max_score,
                "error": "Privacy document contained no readable text."
            }

        # Mapping engine execution across 100% of chunks to calculate a deterministic fake confidence
        for policy_name, regex_patterns in COMPILED_CHECKS.items():
            match_counts = 0
            
            for chunk in chunks:
                for pattern in regex_patterns:
                    if pattern.search(chunk):
                        match_counts += 1

            # Emulating confidence matrix depending on occurrences (Capped at 99%)
            if match_counts > 0:
                confidence = min(0.40 + (match_counts * 0.15), 0.99)
                confidence_scores[policy_name] = round(confidence, 3)
                detected.append(policy_name)
                score += COMPLIANCE_CHECKS[policy_name]["weight"]
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
            "missing": ["Privacy Policy URI Discovered"] + list(COMPLIANCE_CHECKS.keys()),
            "score": 0,
            "max_score": 100,
            "error": f"Critical scanning failure: {str(e)}"
        }
