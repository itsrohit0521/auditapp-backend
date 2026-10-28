SOC2_CONTROLS = {

    "security": {
        "description": "Are systems protected against unauthorized access (logical and physical)?",
        "risk_weight": 20,
        "recommendation": "Implement firewalls, intrusion detection, MFA, and physical access controls."
    },

    "availability": {
        "description": "Are systems available for operation and use as agreed or committed?",
        "risk_weight": 20,
        "recommendation": "Define and monitor SLAs, implement redundancy and failover mechanisms."
    },

    "processing_integrity": {
        "description": "Is system processing complete, valid, accurate, timely, and authorized?",
        "risk_weight": 20,
        "recommendation": "Implement input validation, error handling, and transaction monitoring."
    },

    "confidentiality": {
        "description": "Is information designated as confidential protected as agreed?",
        "risk_weight": 20,
        "recommendation": "Apply data classification policies and enforce encryption for confidential data."
    },

    "privacy": {
        "description": "Is personal information collected, used, retained, and disclosed in accordance with your privacy notice?",
        "risk_weight": 20,
        "recommendation": "Establish a privacy program aligned with your privacy notice and applicable laws."
    }

}
