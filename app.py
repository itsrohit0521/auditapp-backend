import streamlit as st
import requests
from risk_calculator import calculate_risk
from framework_registry import FRAMEWORKS
from report_generator import generate_pdf
from policy_scanner import scan_privacy_policy
from security_scanner import scan_security_headers


st.set_page_config(
    page_title="AuditApp",
    layout="wide"
)

# =========================
# SIDEBAR NAVIGATION
# =========================

st.sidebar.title("AuditApp")

page = st.sidebar.radio(
    "Navigation",
    ["Scanner", "Privacy Policy"]
)


# =========================
# PRIVACY POLICY PAGE
# =========================

if page == "Privacy Policy":

    st.title("AuditApp Privacy Policy")

    with open("privacy_policy.md", "r") as file:
        policy = file.read()

    st.markdown(policy)


# =========================
# MAIN SCANNER PAGE
# =========================

if page == "Scanner":

    st.title("AuditApp — Compliance & Security Scanner")

    st.write(
        "Evaluate regulatory compliance and website security posture using automated scans or self-assessment."
    )

    assessment_mode = st.radio(
        "Choose Assessment Method",
        ["Self Assessment", "Website Scan"]
    )

    framework_choice = st.selectbox(
        "Select Compliance Framework",
        list(FRAMEWORKS.keys())
    )

    selected_controls = FRAMEWORKS[framework_choice]


    # =========================
    # SELF ASSESSMENT MODE
    # =========================

    if assessment_mode == "Self Assessment":

        st.subheader("Compliance Self-Assessment")

        startup_answers = {}

        for control, info in selected_controls.items():

            answer = st.radio(
                info["description"],
                ("Yes", "No"),
                key=control
            )

            startup_answers[control] = True if answer == "Yes" else False

        if st.button("Calculate Compliance Risk"):

            risk_results = calculate_risk(
                startup_answers,
                selected_controls
            )

            st.session_state["results"] = {
                "total_risk": risk_results["total_risk"],
                "risk_percentage": risk_results["risk_percentage"],
                "risk_level": risk_results["risk_level"],
                "details": risk_results["details"],
                "framework": framework_choice
            }


    # =========================
    # WEBSITE SCAN MODE
    # =========================

    if assessment_mode == "Website Scan":

        st.subheader("🌐 Automated Website Compliance Scan")

        website_url = st.text_input("Enter Company Website URL")

        def find_privacy_policy(base_url):

            common_paths = [
                "/privacy",
                "/privacy-policy",
                "/legal/privacy",
                "/privacy-notice"
            ]

            for path in common_paths:

                try:

                    url = base_url.rstrip("/") + path
                    r = requests.get(url, timeout=5)

                    if r.status_code == 200:
                        return url

                except:
                    continue

            return None


        if st.button("Scan Website"):

            if not website_url:

                st.warning("Please enter a website URL.")

            else:

                st.info("Running AuditApp automated scan...")

                privacy_url = find_privacy_policy(website_url)

                if privacy_url:

                    st.success(f"Privacy policy detected: {privacy_url}")

                    privacy_result = scan_privacy_policy(privacy_url)

                    if "error" in privacy_result:
                        st.error(privacy_result["error"])
                        detected_privacy = []
                        missing_privacy = []
                    else:
                        detected_privacy = [k for k, v in privacy_result.items() if v == "Present" and k != "confidenceScore"]
                        missing_privacy = [k for k, v in privacy_result.items() if v == "Missing" and k != "confidenceScore"]

                else:

                    st.warning("Privacy policy could not be automatically detected. Running fallback URL scan...")
                    
                    # New feature: deep crawl starts from the base if privacy page isn't statically guessable
                    privacy_result = scan_privacy_policy(website_url)

                    if "error" in privacy_result:
                        st.error(privacy_result["error"])
                        detected_privacy = []
                        missing_privacy = []
                    else:
                        detected_privacy = [k for k, v in privacy_result.items() if v == "Present" and k != "confidenceScore"]
                        missing_privacy = [k for k, v in privacy_result.items() if v == "Missing" and k != "confidenceScore"]


                security_result = scan_security_headers(website_url)

                if "error" in security_result:

                    st.error(security_result["error"])
                    detected_security = []
                    missing_security = []

                else:

                    detected_security = security_result["detected"]
                    missing_security = security_result["missing"]


                total_privacy = len(detected_privacy) + len(missing_privacy)

                privacy_score = 0
                if total_privacy > 0:
                    privacy_score = int((len(detected_privacy) / total_privacy) * 100)


                total_security = len(detected_security) + len(missing_security)

                security_score = 0
                if total_security > 0:
                    security_score = int((len(detected_security) / total_security) * 100)


                overall_score = int((privacy_score + security_score) / 2)


                st.subheader("📊 Audit Scores")

                st.write(f"Privacy Compliance Score: **{privacy_score}%**")
                st.write(f"Website Security Score: **{security_score}%**")
                st.write(f"Overall Compliance Score: **{overall_score}%**")

                st.progress(overall_score)


                st.subheader("🔎 Privacy Policy Analysis")

                if detected_privacy:

                    st.success("Detected Compliance Sections")

                    for item in detected_privacy:
                        st.write(f"✔ {item}")

                if missing_privacy:

                    st.warning("Missing Compliance Sections")

                    for item in missing_privacy:
                        st.write(f"❌ {item}")


                st.subheader("🔐 Website Security Analysis")

                if detected_security:

                    st.success("Detected Security Protections")

                    for item in detected_security:
                        st.write(f"✔ {item}")

                if missing_security:

                    st.warning("Missing Security Protections")

                    for item in missing_security:
                        st.write(f"❌ {item}")


    # =========================
    # RISK REPORT DISPLAY
    # =========================

    if "results" in st.session_state:

        results = st.session_state["results"]

        total_risk = results["total_risk"]
        risk_percentage = results["risk_percentage"]
        risk_level = results["risk_level"]
        details = results["details"]
        framework_choice = results["framework"]

        st.subheader("📊 Compliance Risk Report")

        st.write(f"Total Risk Score: **{total_risk}**")
        st.write(f"Risk Percentage: **{risk_percentage:.2f}%**")

        st.progress(int(risk_percentage))

        st.write(f"Overall Risk Level: **{risk_level}**")

        if risk_percentage < 30:
            st.success("🟢 Compliance Readiness Status: READY")

        elif risk_percentage < 60:
            st.warning("🟡 Compliance Readiness Status: NEEDS IMPROVEMENT")

        else:
            st.error("🔴 Compliance Readiness Status: HIGH RISK")


        if not details:

            st.success("No major compliance risks detected")

        else:

            st.error("Compliance Issues Detected")

            for item in details:

                st.write(f"**Failed Control:** {item['control']}")
                st.write(f"Risk Impact: {item['risk']}")
                st.write(f"Issue: {item['description']}")
                st.write(f"Recommended Action: {item['recommendation']}")
                st.write("---")


        pdf_buffer = generate_pdf(
            framework_choice,
            total_risk,
            risk_percentage,
            risk_level,
            details
        )

        st.download_button(
            label="📄 Download Compliance Report",
            data=pdf_buffer,
            file_name="AuditApp_Compliance_Report.pdf",
            mime="application/pdf"
        )