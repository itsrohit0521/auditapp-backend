from framework_dpdp import DPDP_CONTROLS
from framework_gdpr import GDPR_CONTROLS
from framework_iso27001 import ISO27001_CONTROLS
from framework_soc2 import SOC2_CONTROLS
from framework_ccpa import CCPA_CONTROLS


# -----------------------------
# Framework registry
# -----------------------------

FRAMEWORKS = {
    "DPDP (India)": DPDP_CONTROLS,
    "GDPR (EU)": GDPR_CONTROLS,
    "ISO 27001": ISO27001_CONTROLS,
    "SOC 2": SOC2_CONTROLS,
    "CCPA (California)": CCPA_CONTROLS
}


# -----------------------------
# Get framework list
# -----------------------------

def get_framework_names():
    """
    Returns list of available compliance frameworks
    """
    return list(FRAMEWORKS.keys())


# -----------------------------
# Get controls for framework
# -----------------------------

def get_framework_controls(framework_name):
    """
    Returns controls dictionary for selected framework
    """

    if framework_name not in FRAMEWORKS:
        return {}

    return FRAMEWORKS[framework_name]


# -----------------------------
# Get control descriptions
# -----------------------------

def get_framework_control_descriptions(framework_name):
    """
    Returns only control descriptions
    Useful for generating questionnaires dynamically
    """

    controls = FRAMEWORKS.get(framework_name, {})

    descriptions = {}

    for key, value in controls.items():
        descriptions[key] = value.get("description")

    return descriptions


# -----------------------------
# Get total control count
# -----------------------------

def get_framework_control_count(framework_name):

    controls = FRAMEWORKS.get(framework_name, {})

    return len(controls)