import requests
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    url = url.strip()
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    parsed = urlparse(url)
    
    # Lowercase domain
    netloc = parsed.netloc.lower()
    
    # Remove trailing slash from path if it's the only path, or leave it
    path = parsed.path
    if path.endswith('/') and len(path) > 1:
        path = path.rstrip('/')
        
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    return normalized

def validate_and_resolve_url(url: str, timeout: int = 5) -> str:
    """
    Validates the URL by making a lightweight request.
    If it fails, tries fallback variants (e.g., adding www, trying http).
    Returns the resolved URL string that succeeded, or raises Exception.
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    
    variants_to_try = [normalized]
    
    # If no www, try www variant
    if not parsed.netloc.startswith("www."):
        www_url = normalized.replace("://", "://www.", 1)
        variants_to_try.append(www_url)
    # If www, try non-www variant
    else:
        non_www = normalized.replace("://www.", "://", 1)
        variants_to_try.append(non_www)
        
    # Attempt HTTP variants as a last resort
    http_variants = [v.replace("https://", "http://", 1) for v in variants_to_try]
    variants_to_try.extend(http_variants)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AuditAppValidator"
    }

    last_error = None
    for variant in variants_to_try:
        try:
            # We use GET with stream=True to act as a fast HEAD replacement,
            # because some servers block HEAD requests. Always use 'with' to clean up streams and prevent connection leaks.
            with requests.get(variant, headers=headers, timeout=timeout, stream=True, allow_redirects=True) as response:
                if response.status_code < 400 or response.status_code in [401, 403]:
                    # If we get a 200 OK, or even a 401/403 (meaning the server exists and replied), we consider it resolved
                    # Return the final redirected URL (which handles auto-redirects done by the site)
                    final_url = response.url
                    # Clean trailing slash to maintain consistency
                    if final_url.endswith('/'):
                        final_url = final_url[:-1]
                    return final_url
        except Exception as e:
            last_error = e
            continue
            
    raise ValueError(f"Failed to resolve URL. Is the domain correct? Last error: {str(last_error)}")
