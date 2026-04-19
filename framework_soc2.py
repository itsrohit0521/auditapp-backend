SOC2_CONTROLS = {

    "encryption": {
        "description": "Is sensitive customer data encrypted?",
        "risk_weight": 20,
        "recommendation": "Use strong encryption standards such as AES-256 for data storage and TLS for transmission."
    },

    "breach_response": {
        "description": "Do you have a formal incident response process?",
        "risk_weight": 20,
        "recommendation": "Implement a documented incident response and breach management procedure."
    },

    "backups": {
        "description": "Are secure data backups performed regularly?",
        "risk_weight": 20,
        "recommendation": "Implement automated backups and disaster recovery testing."
    },

    "access_control": {
        "description": "Do you restrict system access using role-based access control?",
        "risk_weight": 20,
        "recommendation": "Enforce RBAC and least-privilege access policies."
    },

    "activity_logging": {
        "description": "Do you log and monitor system activity for security events?",
        "risk_weight": 20,
        "recommendation": "Implement centralized logging and continuous monitoring for suspicious activity."
    }

}