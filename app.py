import streamlit as st

st.set_page_config(page_title="Preop Cardiac App", layout="wide")

# -----------------------------
# Styling helpers
# -----------------------------
def result_card(kind, title, body):
    styles = {
        "green": ("#ECFDF5", "#065F46", "#10B981"),
        "yellow": ("#FFFBEB", "#92400E", "#F59E0B"),
        "red": ("#FEF2F2", "#991B1B", "#EF4444"),
        "blue": ("#EFF6FF", "#1E3A8A", "#3B82F6"),
        "gray": ("#F8FAFC", "#334155", "#CBD5E1"),
    }
    bg, text, border = styles[kind]
    st.markdown(
        f"""
        <div style="
            background:{bg};
            border:1px solid {border};
            border-left:8px solid {border};
            padding:18px;
            border-radius:16px;
            margin-bottom:12px;
            white-space:pre-line;
        ">
            <div style="font-size:0.85rem;color:{text};opacity:0.8;margin-bottom:6px;">Recommendation</div>
            <div style="font-size:1.35rem;font-weight:700;color:{text};margin-bottom:8px;">{title}</div>
            <div style="font-size:1rem;color:{text};line-height:1.5;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def note_card(title, items):
    if not items:
        return
    bullets = "".join([f"<li>{item}</li>" for item in items])
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF;
            border:1px solid #E2E8F0;
            padding:16px;
            border-radius:16px;
            margin-bottom:12px;
        ">
            <div style="font-size:1rem;font-weight:700;color:#0F172A;margin-bottom:8px;">{title}</div>
            <ul style="margin:0 0 0 18px;color:#334155;line-height:1.6;">
                {bullets}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Constants
# -----------------------------
DASI_ITEMS = [
    ("Take care of yourself, that is, eating, dressing, bathing, or using the toilet", 2.75),
    ("Walk indoors, such as around your house", 1.75),
    ("Walk a block or two on level ground", 2.75),
    ("Climb a flight of stairs or walk up a hill", 5.50),
    ("Run a short distance", 8.00),
    ("Do light work around the house like dusting or washing dishes", 2.70),
    ("Do moderate work around the house like vacuuming, sweeping floors, or carrying in groceries", 3.50),
    ("Do heavy work around the house like scrubbing floors or lifting/moving heavy furniture", 8.00),
    ("Do yard work like raking leaves, weeding, or pushing a power mower", 4.50),
    ("Have sexual relations", 5.25),
    ("Take part in moderate recreational activities like golf, bowling, dancing, doubles tennis, or throwing a ball", 6.00),
    ("Take part in strenuous sports like swimming, singles tennis, football, basketball, or skiing", 7.50),
]

RISK_MODIFIER_ITEMS = [
    "Severe valvular heart disease",
    "Pulmonary hypertension",
    "Congenital heart disease",
    "Percutaneous coronary intervention or coronary artery bypass grafting",
    "Recent stroke",
    "Cardiac implantable electronic device",
    "Frailty",
]

RISK_MODIFIER_TEXT = (
    "Consider targeted evaluation/optimization of risk modifiers if present:\n"
    "• Severe valvular heart disease\n"
    "• Pulmonary hypertension\n"
    "• Congenital heart disease\n"
    "• Percutaneous coronary intervention or coronary artery bypass grafting\n"
    "• Recent stroke\n"
    "• Cardiac implantable electronic device\n"
    "• Frailty"
)

# -----------------------------
# Helpers
# -----------------------------
def calc_dasi(answers: dict) -> float:
    return round(sum(weight for label, weight in DASI_ITEMS if answers.get(label, False)), 2)


def dasi_band(score: float) -> str:
    if score > 34:
        return "Good functional capacity by DASI (>34)"
    if 25 <= score <= 34:
        return "Borderline functional capacity by DASI (25–34) — proceed with caution"
    return "Poor/unknown functional capacity by DASI (<25)"


def calc_rcri(high_risk_surgery, history_ihd, history_hf, history_cvd, insulin_dm, creat_gt_2):
    return (
        int(high_risk_surgery)
        + int(history_ihd)
        + int(history_hf)
        + int(history_cvd)
        + int(insulin_dm)
        + int(creat_gt_2)
    )


def infer_mace_from_rcri(rcri_score: int) -> str:
    return "≥1%" if rcri_score >= 1 else "<1%"


# -----------------------------
# Header
# -----------------------------
st.title("🫀 Preoperative Cardiac Evaluation")

with st.expander("⚠️ How to use this tool", expanded=False):
    st.markdown(
        """
**This tool is designed to support — not replace — clinical judgment.**

- It follows a stepwise perioperative cardiac evaluation approach, but it should **not** be used as a rigid rule.
- Always apply **clinical context and common sense**.
- **High-risk patients, high-risk procedures, or unclear situations** should be discussed with senior colleagues or consultants.
- If there is **any doubt**, use multidisciplinary discussion when appropriate.
- Final decisions should always reflect **patient factors, surgical urgency, and available resources**.

**Use this tool as guidance — not as a substitute for professional judgment.**
        """
    )

# -----------------------------
# Default live result
# -----------------------------
result_kind = "gray"
result_title = "Complete the questionnaire"
result_body = "Your recommendation will appear here as you answer the questions."
decision_path = []
extra_notes = []

rcri = None
mace = None
dasi_score = None
risk_modifier_present = False
method = None

# -----------------------------
# Layout
# -----------------------------
left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.markdown("### 1) Immediate red flags — choose whichever applies")
    st.caption("If none apply, continue to Step 2.")

    healthy = st.checkbox("Healthy patient (no CV disease/risk factors/symptoms)")
    emergency = st.checkbox("Emergency surgery")
    active = st.checkbox("ACS / unstable arrhythmia / decompensated heart failure")

    if healthy:
        result_kind = "green"
        result_title = "Proceed to OR"
        result_body = "No further preoperative cardiac assessment is needed."
        decision_path = ["Healthy patient shortcut"]

    elif emergency:
        result_kind = "yellow"
        result_title = "Proceed to OR"
        result_body = (
            "Optimize medical therapy and perioperative planning as time permits.\n\n"
            "Consider postoperative BNP / NT-proBNP or troponin surveillance.\n\n"
            + RISK_MODIFIER_TEXT
        )
        decision_path = ["Emergency surgery"]

    elif active:
        result_kind = "red"
        result_title = "Manage acute condition"
        result_body = "Manage acute condition, multidisciplinary discussion regarding surgery/nonsurgery options."
        decision_path = ["Active cardiac condition present"]

    else:
        st.markdown("---")
        st.markdown("### 2) CAD / ischemic symptoms")

        cad = st.checkbox("Ischemic symptoms / CAD history")

        if cad:
            cad_type = st.radio(
                "Select CAD scenario",
                [
                    "Stable CAD with coronary evaluation in past year",
                    "New or worsening symptoms / not evaluated",
                    "Recent ACS or PCI/CABG",
                ],
            )

            if cad_type == "Stable CAD with coronary evaluation in past year":
                result_kind = "green"
                result_title = "Proceed to OR"
                result_body = "Stable CAD with coronary evaluation in the past year."
                decision_path = ["CAD history", "Stable CAD with recent evaluation"]

            elif cad_type == "New or worsening symptoms / not evaluated":
                result_kind = "blue"
                result_title = "Cardiac evaluation first"
                result_body = "Obtain cardiac evaluation before proceeding."
                decision_path = ["CAD history", "New/worsening symptoms or not evaluated"]

            elif cad_type == "Recent ACS or PCI/CABG":
                event = st.selectbox(
                    "Select the recent event/intervention",
                    [
                        "ACS/MI <60 days",
                        "PCI - BMS (stable CAD)",
                        "PCI - DES (stable CAD)",
                        "CABG",
                    ],
                )

                timing_notes = []

                if event == "ACS/MI <60 days":
                    timing_notes.append("ACS/MI within 60 days – delay surgery")

                elif event == "PCI - BMS (stable CAD)":
                    timing_notes.append("BMS – delay surgery at least 30 days")
                    pci_acs = st.checkbox("PCI was done in ACS setting or with high-risk features")
                    if pci_acs:
                        timing_notes.append(
                            "If PCI in setting of ACS or with high-risk features, consider delay up to 12 months or discuss risks/benefits with cardiologist/anesthesiologist/surgeon"
                        )

                elif event == "PCI - DES (stable CAD)":
                    timing_notes.append("DES – delay surgery optimally for 6 months")
                    timing_notes.append("If time-sensitive surgery, OK after 3 months")
                    timing_notes.append("Avoid surgery within 1 month of PCI")
                    pci_acs = st.checkbox("PCI was done in ACS setting or with high-risk features")
                    if pci_acs:
                        timing_notes.append(
                            "If PCI in setting of ACS or with high-risk features, consider delay up to 12 months or discuss risks/benefits with cardiologist/anesthesiologist/surgeon"
                        )

                elif event == "CABG":
                    timing_notes.append("CABG – delay surgery 30 days if possible")

                result_kind = "blue"
                result_title = "Timing recommendation"
                result_body = "\n".join(timing_notes)
                decision_path = ["CAD history", "Recent ACS/PCI/CABG"]

        else:
            st.markdown("---")
            st.markdown("### 3) Estimate perioperative MACE risk (RCRI)")

            c1, c2, c3 = st.columns(3)

            with c1:
                high_risk_surgery = st.checkbox("High-risk surgery")
                history_ihd = st.checkbox("History of ischemic heart disease")

            with c2:
                history_hf = st.checkbox("History of heart failure")
                history_cvd = st.checkbox("History of cerebrovascular disease")

            with c3:
                insulin_dm = st.checkbox("Diabetes on insulin")
                creat_gt_2 = st.checkbox("Creatinine > 2 mg/dL")

            rcri = calc_rcri(
                high_risk_surgery,
                history_ihd,
                history_hf,
                history_cvd,
                insulin_dm,
                creat_gt_2,
            )
            mace = infer_mace_from_rcri(rcri)

            st.markdown("---")
            st.markdown("### 4) Risk modifiers")

            risk_modifier_answer = st.radio(
                "Are there any risk modifiers present?",
                ["No", "Yes"],
                horizontal=True,
            )
            risk_modifier_present = risk_modifier_answer == "Yes"

            if risk_modifier_present:
                with st.expander("Examples of risk modifiers", expanded=False):
                    for item in RISK_MODIFIER_ITEMS:
                        st.write(f"• {item}")

            if mace == "<1%":
                result_kind = "green"
                result_title = "Proceed to OR"
                result_body = "Low estimated perioperative cardiac risk."
                if risk_modifier_present:
                    result_body += "\n\n" + RISK_MODIFIER_TEXT
                decision_path = [f"RCRI {rcri}", "MACE <1%"]

            else:
                st.markdown("---")
                st.markdown("### 5) Functional capacity")

                method = st.radio("Functional capacity method", ["DASI", "Stair climbing"], horizontal=True)

                poor_capacity = False

                if method == "DASI":
                    st.markdown("#### Full DASI calculator")
                    answers = {}
                    col_a, col_b = st.columns(2)
                    for i, (label, weight) in enumerate(DASI_ITEMS):
                        with (col_a if i % 2 == 0 else col_b):
                            answers[label] = st.checkbox(f"{label} (+{weight})")

                    cannot_assess_dasi = st.checkbox("Cannot assess DASI")
                    dasi_score = calc_dasi(answers)
                    st.write(f"**DASI score:** {dasi_score}")

                    if cannot_assess_dasi:
                        poor_capacity = True
                        extra_notes.append("DASI cannot be assessed — treat as poor/unknown functional capacity.")
                    else:
                        st.write(f"**Interpretation:** {dasi_band(dasi_score)}")

                        if dasi_score > 34:
                            result_kind = "green"
                            result_title = "Proceed to OR"
                            result_body = "Adequate functional capacity by DASI."
                            if risk_modifier_present:
                                result_body += "\n\n" + RISK_MODIFIER_TEXT
                            decision_path = [f"RCRI {rcri}", "MACE ≥1%", "DASI >34"]

                        elif 25 <= dasi_score <= 34:
                            result_kind = "yellow"
                            result_title = "Proceed to OR with caution"
                            result_body = "Borderline functional capacity by DASI (25–34)."
                            if risk_modifier_present:
                                result_body += "\n\n" + RISK_MODIFIER_TEXT
                            decision_path = [f"RCRI {rcri}", "MACE ≥1%", "DASI 25–34"]

                        else:
                            poor_capacity = True

                else:
                    stairs = st.radio(
                        "Can the patient climb 2 flights of stairs?",
                        ["Yes", "No", "Cannot assess"],
                        horizontal=True,
                    )

                    if stairs == "Yes":
                        result_kind = "green"
                        result_title = "Proceed to OR"
                        result_body = "Adequate functional capacity by stair-climbing assessment."
                        if risk_modifier_present:
                            result_body += "\n\n" + RISK_MODIFIER_TEXT
                        decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Stair climbing adequate"]

                    else:
                        poor_capacity = True
                        extra_notes.append("Stair climbing is low or uncertain — treat as poor/unknown functional capacity.")

                if poor_capacity and result_title == "Complete the questionnaire":
                    st.markdown("---")
                    st.markdown("### 6) Time sensitivity")

                    time_sensitive = st.radio(
                        "Is the surgery time-sensitive within 3 months with no nonsurgical option?",
                        ["Yes", "No"],
                        horizontal=True,
                    )

                    if time_sensitive == "Yes":
                        result_kind = "yellow"
                        result_title = "Proceed with optimization as feasible"
                        result_body = "Use multidisciplinary discussion and proceed if delay would be more harmful than the cardiac risk."
                        if risk_modifier_present:
                            result_body += "\n\n" + RISK_MODIFIER_TEXT
                        decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Poor/unknown functional capacity", "Time-sensitive surgery"]

                    else:
                        st.markdown("---")
                        st.markdown("### 7) Will further testing change management?")

                        change = st.radio(
                            "Will further cardiac testing change management?",
                            ["Yes", "No", "Possibly"],
                            horizontal=True,
                        )

                        if change == "No":
                            result_kind = "green"
                            result_title = "Proceed to OR"
                            result_body = "Further cardiac testing will not change management."
                            if risk_modifier_present:
                                result_body += "\n\n" + RISK_MODIFIER_TEXT
                            decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Poor/unknown functional capacity", "Not time-sensitive", "Testing will not change management"]

                        elif change == "Yes":
                            result_kind = "red"
                            result_title = "Further cardiac testing"
                            result_body = "Pharmacologic stress test,\nCCTA, or possibly ICA; + GDMT"
                            if risk_modifier_present:
                                result_body += "\n\n" + RISK_MODIFIER_TEXT
                            decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Poor/unknown functional capacity", "Not time-sensitive", "Testing will change management"]

                        else:
                            st.info(
                                "Examples: starting medication that would improve cardiac function, or clarifying whether additional testing would change the anesthetic plan or monitoring."
                            )

                            st.markdown("### 8) Cardiac biomarkers")
                            bio = st.selectbox("Cardiac biomarkers", ["Not done", "Low/normal", "High/elevated"])

                            if bio == "Not done":
                                result_kind = "yellow"
                                result_title = "Obtain biomarkers"
                                result_body = "Consider BNP / NT-proBNP or troponin."
                                decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Poor/unknown functional capacity", "Not time-sensitive", "Testing may possibly change management", "Biomarkers not done"]

                            elif bio == "Low/normal":
                                result_kind = "green"
                                result_title = "Proceed to OR"
                                result_body = "Low/normal biomarkers."
                                if risk_modifier_present:
                                    result_body += "\n\n" + RISK_MODIFIER_TEXT
                                decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Poor/unknown functional capacity", "Not time-sensitive", "Testing may possibly change management", "Biomarkers low/normal"]

                            else:
                                result_kind = "red"
                                result_title = "Further cardiac testing"
                                result_body = "High/elevated biomarkers — Pharmacologic stress test,\nCCTA, or possibly ICA; + GDMT"
                                if risk_modifier_present:
                                    result_body += "\n\n" + RISK_MODIFIER_TEXT
                                decision_path = [f"RCRI {rcri}", "MACE ≥1%", "Poor/unknown functional capacity", "Not time-sensitive", "Testing may possibly change management", "Biomarkers high/elevated"]

with right:
    st.markdown("### Summary")

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("RCRI", str(rcri) if rcri is not None else "—")
    metric2.metric("MACE", mace if mace is not None else "—")
    metric3.metric("DASI", str(dasi_score) if dasi_score is not None else "—")
    metric4.metric("Modifiers", "Yes" if risk_modifier_present else "No")

    st.markdown("---")
    result_card(result_kind, result_title, result_body)

    if decision_path:
        note_card("Decision path", decision_path)

    if extra_notes:
        note_card("Notes", extra_notes)