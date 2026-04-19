DPDP_CONTROLS = {

    "consent_collection": {
        "description": "User consent must be obtained before collecting personal data.",
        "risk_weight": 20,
        "recommendation": "Implement explicit consent checkbox and store consent logs."
    },

    "data_encryption": {
        "description": "Personal data must be encrypted both at rest and during transmission.",
        "risk_weight": 20,
        "recommendation": "Use AES-256 encryption for storage and HTTPS/TLS for transmission."
    },

    "data_retention_policy": {
        "description": "Data retention period must be defined and justified.",
        "risk_weight": 20,
        "recommendation": "Define retention timeline and document it in the privacy policy."
    },

    "breach_reporting": {
        "description": "A data breach reporting mechanism must exist.",
        "risk_weight": 20,
        "recommendation": "Establish incident response and breach notification procedures."
    },

    "access_control": {
        "description": "Access to personal data must be restricted.",
        "risk_weight": 20,
        "recommendation": "Implement role-based access control (RBAC)."
    }

}