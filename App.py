import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date, timedelta, datetime
from io import BytesIO

# PDF (ReportLab)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import Color

st.set_page_config(page_title="DSGE Ops Center • Pilot Proposal", layout="wide")

WATERMARK_TEXT = "property of DSGE, Region V fouo"

# ---------------- SAFE DARK STYLE ----------------
st.markdown("""
<style>
html, body { background-color:#0b1020; color:#eaf0ff; }
.block-container { padding-top: 1.2rem; }
h1,h2,h3 { color:#4de1ff; }

.card {
  background:#121a35;
  padding:18px;
  border-radius:14px;
  border:1px solid #1f2b55;
}

.metric-card {
  background:linear-gradient(145deg,#121a35,#0e1429);
  padding:18px;
  border-radius:14px;
  border:1px solid #1f2b55;
  box-shadow:0 0 18px rgba(77,225,255,0.08);
}

.small { color:#aab7e8; font-size: 0.92rem; }
hr { border: none; border-top:1px solid #1f2b55; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ---------------- Helpers ----------------
def currency(x):
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return str(x)

def tons_month(floors, gaylords_per_floor_per_day, workdays_per_month, lbs_per_gaylord):
    return floors * gaylords_per_floor_per_day * workdays_per_month * lbs_per_gaylord / 2000.0

def make_gantt(project_start: date):
    def w(weeks): return project_start + timedelta(weeks=int(weeks))
    rows = [
        ("DEFINE • Charter + CTQs + SIPOC", w(0),  w(2),  "DEFINE",  "Gate: Sponsor approval"),
        ("DEFINE • Safety + Legal boundaries", w(1),  w(3),  "DEFINE",  "Gate: Sign-offs"),
        ("MEASURE • Baseline + Data Plan",     w(2),  w(5),  "MEASURE", "Gate: Baseline report"),
        ("MEASURE • MSA (Measurement System Analysis)", w(3), w(6), "MEASURE", "Gate: Gage R&R acceptable"),
        ("ANALYZE • Capability + Root Cause",  w(5),  w(8),  "ANALYZE", "Gate: Verified drivers"),
        ("IMPROVE • Pilot Solutions + DOE",    w(8),  w(12), "IMPROVE", "Gate: Verified improvement"),
        ("CONTROL • Control Plan + SPC",       w(12), w(13), "CONTROL", "Gate: Sustainment ready"),
    ]
    return pd.DataFrame(rows, columns=["Task","Start","Finish","Phase","Gate"])

def pdf_watermark(c: canvas.Canvas, text: str, page_w: float, page_h: float):
    # light diagonal watermark
    c.saveState()
    c.setFillColor(Color(0.65, 0.75, 0.95, alpha=0.12))
    c.setFont("Helvetica-Bold", 36)
    c.translate(page_w/2, page_h/2)
    c.rotate(30)
    c.drawCentredString(0, 0, text)
    c.restoreState()

def pdf_footer(c: canvas.Canvas, text: str, page_w: float, page_h: float):
    c.saveState()
    c.setFillColor(Color(0.7, 0.75, 0.9, alpha=0.55))
    c.setFont("Helvetica", 9)
    c.drawString(0.7*inch, 0.45*inch, text)
    c.drawRightString(page_w - 0.7*inch, 0.45*inch, datetime.now().strftime("%Y-%m-%d %H:%M"))
    c.restoreState()

def build_pdf_report(title: str, sections: list, watermark_text: str) -> bytes:
    """
    sections = [(heading, [bullets...]), ...]
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    page_w, page_h = letter

    margin_x = 0.7 * inch
    y = page_h - 0.9*inch

    def new_page():
        c.showPage()

    # PAGE 1
    pdf_watermark(c, watermark_text, page_w, page_h)
    c.setFillColor(Color(0.9, 0.95, 1.0, alpha=1))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin_x, y, title)
    y -= 0.35*inch

    c.setFont("Helvetica", 10)
    c.setFillColor(Color(0.8, 0.85, 0.95, alpha=1))
    c.drawString(margin_x, y, "Pilot Proposal • Six Sigma Black Belt format • DMAIC governed")
    y -= 0.30*inch

    c.setFillColor(Color(0.95, 0.98, 1.0, alpha=1))
    for heading, bullets in sections:
        # Heading
        if y < 1.3*inch:
            pdf_footer(c, watermark_text, page_w, page_h)
            new_page()
            y = page_h - 0.9*inch
            pdf_watermark(c, watermark_text, page_w, page_h)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, heading)
        y -= 0.22*inch

        c.setFont("Helvetica", 10)
        for b in bullets:
            if y < 1.1*inch:
                pdf_footer(c, watermark_text, page_w, page_h)
                new_page()
                y = page_h - 0.9*inch
                pdf_watermark(c, watermark_text, page_w, page_h)
                c.setFont("Helvetica", 10)

            # bullet line (wrap simple)
            text = f"• {b}"
            # manual wrapping
            max_chars = 110
            lines = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            for line in lines:
                c.drawString(margin_x, y, line)
                y -= 0.18*inch
        y -= 0.12*inch

    pdf_footer(c, watermark_text, page_w, page_h)
    c.save()
    return buf.getvalue()

# ---------------- Sidebar Inputs (Pilot assumptions) ----------------
st.sidebar.header("⚙ Pilot Inputs (Editable Defaults)")
program_name = st.sidebar.text_input("Program name", "Circular Strap Diversion Pilot")
site_name = st.sidebar.text_input("Site", "4-floor facility (pilot)")
pilot_days = st.sidebar.number_input("Pilot duration (days)", min_value=30, max_value=180, value=90, step=5)

floors = st.sidebar.number_input("Floors", 1, 20, 4)
gaylords = st.sidebar.number_input("Gaylords per floor per day", 1, 200, 20)
workdays = st.sidebar.number_input("Workdays per month", 1, 31, 20)
lbs_per_gaylord = st.sidebar.number_input("Avg lbs per Gaylord", 1, 2000, 100)

density = st.sidebar.number_input("Density (lb/ft³)", 1.0, 60.0, 25.0)
trailer_payload = st.sidebar.number_input("Trailer payload (lb)", 1000.0, 80000.0, 44000.0)

sale_price = st.sidebar.number_input("Sale price ($/ton)", 0.0, 3000.0, 300.0)
proc_cost = st.sidebar.number_input("Processing cost ($/ton)", 0.0, 3000.0, 60.0)
avoid_fee = st.sidebar.number_input("Avoided disposal fee ($/ton)", 0.0, 3000.0, 50.0)

contam_target = st.sidebar.number_input("CTQ target: Contamination ≤ (%)", 1.0, 50.0, 12.0, 0.5)
payload_target = st.sidebar.number_input("CTQ target: Payload util ≥ (%)", 1.0, 100.0, 85.0, 1.0)
weigh_time_target = st.sidebar.number_input("CTQ target: Weigh time ≤ (sec)", 1.0, 120.0, 10.0, 1.0)

project_start = st.sidebar.date_input("Project start", value=date.today())

# ---------------- Compute Snapshot ----------------
t_mo = tons_month(floors, gaylords, workdays, lbs_per_gaylord)
revenue_mo = t_mo * (sale_price + avoid_fee - proc_cost)
payload_util = min(100.0, (density * 3800) / max(trailer_payload, 1e-9) * 100.0)
loads_mo = np.ceil((t_mo * 2000) / max(trailer_payload, 1e-9))

# ---------------- Header ----------------
st.title("🛰 DSGE Ops Center • Pilot Proposal (Six Sigma Black Belt)")
st.caption(f"{program_name} • Site: {site_name} • Watermark: “{WATERMARK_TEXT}”")

# KPI HUD
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Estimated Tons / Month", f"{t_mo:,.1f}")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Net Value / Month (est.)", currency(revenue_mo))
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Payload Utilization", f"{payload_util:,.0f}%")
    st.markdown('</div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Loads / Month (est.)", f"{loads_mo:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

tabs = st.tabs([
    "✅ Pilot Proposal (KISS)",
    "🧱 WBS",
    "📅 Gantt Timeline",
    "🎯 CTQs + Success / Exit Criteria",
    "🧠 Six Sigma Content (BoK)",
    "⬇ Print & PDF"
])

# ---------------- Tab 1: KISS Proposal ----------------
with tabs[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("KISS Narrative (Keep It Simple, Stated Once)")

    st.write(f"""
**What we’re asking for:** approval for a **{pilot_days}-day** controlled pilot.

**What this pilot does:** converts plastic strap waste into a measurable value stream using **DMAIC (Define, Measure, Analyze, Improve, Control)**.

**Why approve it:**  
- **No disruption** to fulfillment flow (defined boundaries + staging)  
- **Safety-positive** (reduces loose strap hazards; cutters-only and PPE controls)  
- **Capped downside** (no long-term commitments; stop rules)  
- **Measurable** (validated weighing method before claims)  
- **Clear decision gate** at the end of the pilot

**What success looks like (CTQs – Critical to Quality):**  
- Contamination ≤ **{contam_target:.1f}%**  
- Payload utilization ≥ **{payload_target:.0f}%**  
- Weigh time ≤ **{weigh_time_target:.0f} sec**  
- Safety incidents = **0**  
- Net value trend ≥ break-even
""")

    st.markdown('<hr>', unsafe_allow_html=True)
    st.write("**Abbreviations (spelled out once, then abbreviated):**")
    st.write("""
- **DMAIC** – Define, Measure, Analyze, Improve, Control  
- **CTQ** – Critical to Quality  
- **MSA** – Measurement System Analysis  
- **SPC** – Statistical Process Control  
- **DOE** – Design of Experiments  
- **FMEA** – Failure Modes and Effects Analysis  
- **ESG** – Environmental, Social, and Governance  
- **Cp / Cpk** – Process Capability (Potential / Actual)
""")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Tab 2: WBS ----------------
with tabs[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Work Breakdown Structure (WBS)")

    wbs = [
        ("1.0 Program Management", [
            "1.1 Sponsor approval + charter sign-off",
            "1.2 Stakeholder alignment (Ops/Safety/Legal/Finance/ESG)",
            "1.3 Governance cadence + decision gates",
            "1.4 Risk register + pilot boundaries"
        ]),
        ("2.0 DEFINE", [
            "2.1 SIPOC (Supplier-Input-Process-Output-Customer)",
            "2.2 CTQs (Critical to Quality) defined + targets",
            "2.3 Operational definitions (unit/defect/opportunity)",
            "2.4 Data plan + reporting cadence"
        ]),
        ("3.0 MEASURE", [
            "3.1 Baseline tons/month + load count",
            "3.2 Baseline contamination sampling",
            "3.3 Baseline cycle time (weigh seconds per bale)",
            "3.4 MSA (Measurement System Analysis) – Gage R&R for weight system"
        ]),
        ("4.0 ANALYZE", [
            "4.1 Capability (Cp/Cpk) for bale weight consistency (if bale data exists)",
            "4.2 Root cause (Pareto + cause-and-effect) for contamination & delays",
            "4.3 Cost/ton sensitivity: density, miles, handling time",
            "4.4 Hypothesis test: before vs after improvement (p-value)"
        ]),
        ("5.0 IMPROVE", [
            "5.1 Standardize strap-only collection points",
            "5.2 Compaction tuning to raise density + reduce air hauling",
            "5.3 Weigh automation (forklift scale or load cells)",
            "5.4 Trailer staging: block & brace SOP to prevent tipping",
            "5.5 DOE (Design of Experiments) for compaction settings and bale targets",
            "5.6 Workforce training (levels 1–4)"
        ]),
        ("6.0 CONTROL", [
            "6.1 Control plan + reaction plan",
            "6.2 SPC (Statistical Process Control) charts if time-series data exists",
            "6.3 Audit-ready reporting + monthly review",
            "6.4 Change management: approvals + versioning",
            "6.5 End-of-pilot executive gate: expand / revise / stop"
        ]),
    ]

    for title, items in wbs:
        st.markdown(f"### {title}")
        for i in items:
            st.write(f"- {i}")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Tab 3: Gantt ----------------
with tabs[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Gantt Timeline (DMAIC)")

    gantt = make_gantt(project_start)

    fig = px.timeline(gantt, x_start="Start", x_end="Finish", y="Task", color="Phase", hover_data=["Gate"])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.add_vline(x=date.today(), line_width=2, line_dash="dash", line_color="#4de1ff")
    st.plotly_chart(fig, use_container_width=True)

    st.write("Decision gates are embedded in each phase to cap downside and keep approvals simple.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Tab 4: CTQs + Success/Exit ----------------
with tabs[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("CTQs (Critical to Quality) + Success / Exit Criteria")

    ctq_df = pd.DataFrame([
        {"CTQ":"Contamination %", "Target":f"≤ {contam_target:.1f}%", "Owner":"Ops Lead", "Reaction":"Retrain + audit + Pareto"},
        {"CTQ":"Payload utilization %", "Target":f"≥ {payload_target:.0f}%", "Owner":"Logistics", "Reaction":"Tune compaction; verify density"},
        {"CTQ":"Weigh time (sec)", "Target":f"≤ {weigh_time_target:.0f}", "Owner":"Supervisor", "Reaction":"Automate weigh; remove queues"},
        {"CTQ":"Safety incidents", "Target":"0", "Owner":"Safety", "Reaction":"Stop & fix; SOP reinforcement"},
        {"CTQ":"Net value trend", "Target":"≥ break-even", "Owner":"Finance", "Reaction":"Renegotiate; reduce handling; hold expansion"},
    ])
    st.dataframe(ctq_df, use_container_width=True)

    st.markdown("### Pilot Success Criteria (Pass)")
    st.write("""
- CTQs meet target thresholds OR show clear trend to target by end of pilot  
- No disruption to fulfillment operations (Ops confirms)  
- Safety incidents remain at zero (Safety confirms)  
- Measurement system validated (MSA – Measurement System Analysis acceptable)  
- End-of-pilot gate recommendation supported with data
""")

    st.markdown("### Pilot Exit Criteria (Stop Rules)")
    st.write("""
- Any recordable safety incident tied to pilot activities  
- Supplier rejection due to preventable contamination  
- Sustained negative economics beyond predefined guardrail (Finance trigger)  
- Verified operational disruption (Ops trigger)
""")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Tab 5: BoK Content ----------------
with tabs[4]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Six Sigma Black Belt Content (ASQ BoK – Body of Knowledge alignment)")

    st.write("""
**Enterprise Planning & Deployment:** sponsor gate, capped downside, measurable outcomes  
**Process Management:** SIPOC + CTQs + metric hierarchy  
**Team Management:** cadence + role clarity  
**DEFINE:** charter + scope + VOC (Voice of Customer) alignment  
**MEASURE:** baseline + MSA (Measurement System Analysis)  
**ANALYZE:** root cause + capability (Cp/Cpk) + hypothesis tests  
**IMPROVE:** DOE (Design of Experiments) + pilot validation  
**CONTROL:** SPC (Statistical Process Control) + control plan + change management
""")

    st.markdown("### Pilot Snapshot (for sponsor brief)")
    st.write(f"- Estimated tons/month (input-based): **{t_mo:,.1f}**")
    st.write(f"- Estimated net value/month: **{currency(revenue_mo)}** (based on editable assumptions)")
    st.write(f"- Estimated payload utilization: **{payload_util:,.0f}%**")
    st.write(f"- Estimated loads/month: **{loads_mo:,.0f}**")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Tab 6: Print & PDF ----------------
with tabs[5]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Print & PDF Export (Watermarked)")

    st.write("### Print")
    st.caption("Uses your browser print dialog. If it opens a blank print preview, refresh once then try again.")
    if st.button("🖨️ Print this page"):
        # Simple JS trigger. Streamlit will execute it via a small HTML component.
        st.components.v1.html(
            """
            <script>
              window.parent.print();
            </script>
            """,
            height=0,
        )
        st.success("Print dialog triggered (check your browser).")

    st.write("### PDF (Watermarked)")
    st.caption(f"Watermark applied to every page: “{WATERMARK_TEXT}”")

    sections = [
        ("Executive Summary", [
            f"Request approval for a {pilot_days}-day controlled pilot under DMAIC (Define, Measure, Analyze, Improve, Control).",
            "No disruption to fulfillment operations; pilot boundaries are defined.",
            "Safety-positive controls: cutters-only, PPE (Personal Protective Equipment), housekeeping, and trailer securement (block & brace).",
            "Measurement credibility: MSA (Measurement System Analysis) before external claims.",
            "Clear exit criteria and end-of-pilot decision gate: expand / revise / stop."
        ]),
        ("Scope", [
            "In scope: straps only; single site pilot; collection → consolidation → compaction → weighing → staging → shipping.",
            "Out of scope: other plastics, capital build-out, long-term contracts, full manufacturing expansion."
        ]),
        ("WBS Summary", [
            "Program Management, DEFINE, MEASURE, ANALYZE, IMPROVE, CONTROL work packages with owners and reaction plans."
        ]),
        ("CTQs (Critical to Quality)", [
            f"Contamination ≤ {contam_target:.1f}%",
            f"Payload utilization ≥ {payload_target:.0f}%",
            f"Weigh time ≤ {weigh_time_target:.0f} sec",
            "Safety incidents = 0",
            "Net value trend ≥ break-even"
        ]),
        ("Pilot Snapshot (Assumption-Based)", [
            f"Estimated tons/month: {t_mo:,.1f}",
            f"Estimated net value/month: {currency(revenue_mo)}",
            f"Estimated payload utilization: {payload_util:,.0f}%",
            f"Estimated loads/month: {loads_mo:,.0f}",
        ]),
        ("Abbreviations", [
            "DMAIC – Define, Measure, Analyze, Improve, Control",
            "CTQ – Critical to Quality",
            "MSA – Measurement System Analysis",
            "SPC – Statistical Process Control",
            "DOE – Design of Experiments",
            "FMEA – Failure Modes and Effects Analysis",
            "ESG – Environmental, Social, and Governance",
            "Cp/Cpk – Process Capability (Potential/Actual)"
        ]),
    ]

    pdf_bytes = build_pdf_report(
        title=f"{program_name} • Pilot Proposal ({site_name})",
        sections=sections,
        watermark_text=WATERMARK_TEXT
    )

    st.download_button(
        "⬇ Download Watermarked PDF",
        data=pdf_bytes,
        file_name="DSGE_Pilot_Proposal_Watermarked.pdf",
        mime="application/pdf"
    )

    st.markdown('</div>', unsafe_allow_html=True)
