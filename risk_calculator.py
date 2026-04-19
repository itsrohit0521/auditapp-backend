def calculate_risk(user_answers, controls):

    total_risk = 0
    risk_details = []

    # Only consider controls that were actually answered
    applicable_controls = {
        key: controls[key]
        for key in user_answers
        if key in controls
    }

    # Total controls asked in questionnaire
    total_controls = len(applicable_controls)
    failed_controls = 0

    # Calculate total possible weight for asked controls
    max_possible_risk = sum(
        control.get("risk_weight", 0)
        for control in applicable_controls.values()
    )

    if max_possible_risk == 0:
        max_possible_risk = 1

    # Evaluate answers
    for control, value in user_answers.items():

        if control not in applicable_controls:
            continue

        if value is False:

            failed_controls += 1

            weight = applicable_controls[control].get("risk_weight", 0)

            total_risk += weight

            risk_details.append({
                "control": control,
                "risk": weight,
                "description": applicable_controls[control].get("description", ""),
                "recommendation": applicable_controls[control].get("recommendation", "")
            })

    # Weighted GRC risk calculation
    risk_percentage = (total_risk / max_possible_risk) * 100

    compliance_score = 100 - risk_percentage

    # Risk classification
    if risk_percentage < 20:
        risk_level = "LOW"
    elif risk_percentage < 50:
        risk_level = "MEDIUM"
    elif risk_percentage < 75:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    metadata = {
        "total_controls": total_controls,
        "failed_controls": failed_controls,
        "passed_controls": total_controls - failed_controls
    }

    return {
        "total_risk": total_risk,
        "risk_percentage": round(risk_percentage, 2),
        "compliance_score": round(compliance_score, 2),
        "risk_level": risk_level,
        "details": risk_details,
        "metadata": metadata
    }