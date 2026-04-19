import requests


def scan_security_headers(url):
    # Ensure URL has protocol
    if not url.startswith("http"):
        url = "https://" + url

    security_checks = {
        "HSTS (HTTPS enforcement)": {"header": "Strict-Transport-Security", "weight": 15},
        "Content Security Policy": {"header": "Content-Security-Policy", "weight": 20},
        "Clickjacking Protection": {"header": "X-Frame-Options", "weight": 15},
        "MIME Sniffing Protection": {"header": "X-Content-Type-Options", "weight": 10},
        "Referrer Policy": {"header": "Referrer-Policy", "weight": 5},
        "Permissions Policy": {"header": "Permissions-Policy", "weight": 5}
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )

        detected = []
        missing = []
        score = 0
        max_score = 100

        # Base check 1: HTTPS enforced
        if response.url.startswith("https://"):
            detected.append("HTTPS Enforced")
            score += 20
        else:
            missing.append("HTTPS Enforced")

        # HTTP level error
        if response.status_code >= 400:
            for name in security_checks.keys():
                missing.append(name)
            missing.append("Secure Cookies")
            return {
                "detected": detected,
                "missing": missing,
                "score": score,
                "max_score": max_score,
                "error": f"HTTP Error {response.status_code}"
            }

        response_headers = response.headers

        for name, config in security_checks.items():
            if config["header"] in response_headers:
                detected.append(name)
                score += config["weight"]
            else:
                missing.append(name)
                
        # Base check 2: Cookie Security
        set_cookie = response_headers.get("Set-Cookie", "")
        if set_cookie:
            if "Secure" in set_cookie and "HttpOnly" in set_cookie:
                detected.append("Secure Cookies")
                score += 10
            else:
                missing.append("Secure Cookies")
        else:
            # If no cookies are set, give points as it's perfectly secure
            detected.append("Secure Cookies (None set)")
            score += 10

        return {
            "detected": detected,
            "missing": missing,
            "score": score,
            "max_score": max_score,
            "error": None
        }

    except Exception as e:
        return {
            "detected": [],
            "missing": ["HTTPS Enforced", "Secure Cookies"] + list(security_checks.keys()),
            "score": 0,
            "max_score": 100,
            "error": "Connection Failed"
        }