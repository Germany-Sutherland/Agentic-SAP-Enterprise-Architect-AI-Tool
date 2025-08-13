import re
import json
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="SAP AI Enterprise Architect — Free MVP", layout="wide")
st.title("🏛️ SAP AI Enterprise Architect — Agentic (Free MVP)")
st.caption("Dropdown examples • NLP-lite • 10 agents • Architecture • FMEA • Mitigation (all free/local)")

# ---------------------------------------
# Predefined example requirement packs
# ---------------------------------------
EXAMPLES = {
    "Finance (Default)": """- Implement SAP S/4HANA for finance, logistics, and procurement modules
- Integrate with existing Salesforce CRM and legacy Oracle database
- Enable real-time analytics through SAP BW/4HANA
- Ensure GDPR compliance and role-based access control
- Deploy on AWS Cloud with disaster recovery in a different region
- Enable Fiori-based mobile access for employees
- Automate purchase order approvals using workflow automation
- Ensure API-based integration with third-party logistics providers""",

    "Manufacturing": """- S/4HANA with PP, QM, PM and EWM for factory + DC
- Integrate shop-floor IoT (sensors / PLCs) via gateway; OEE dashboards
- Predictive maintenance data flows to data lake
- ISO 9001 and OSHA compliance; role-based access
- Hybrid: on-prem shop-floor, cloud S/4 core; DR cross-region
- Fiori apps for supervisors and operators
- Automated quality hold/release workflow""",

    "Retail": """- S/4HANA for Retail with inventory and pricing
- Integrate POS + e-commerce (Shopify/Magento)
- Real-time sales analytics; demand forecasting
- PCI-DSS compliance; tokenized payments
- Deploy on Azure; multi-region failover
- Click-and-collect and 3PL shipping APIs
- Fiori apps for store managers""",

    "Healthcare": """- S/4HANA for patient billing and supply chain
- Integrate with EHR; HL7/FHIR interoperability
- Real-time medical inventory and cold-chain tracking
- HIPAA compliance and auditing
- AWS deployment with strong encryption + DR
- Mobile Fiori for clinicians
- Automated approvals for high-value purchases"""
}

# ---------------------------------------
# Lightweight NLP to extract structure
# ---------------------------------------
MODULE_KEYWORDS = {
    "FI": ["finance", "ledger", "invoice", "tax", "closing"],
    "MM": ["procure", "procurement", "purchase", "supplier", "inventory"],
    "SD": ["sales", "order", "customer", "delivery", "billing"],
    "PP": ["production", "shop", "mrp", "bom", "routing"],
    "QM": ["quality", "inspection", "defect"],
    "PM": ["maintenance", "asset", "breakdown"],
    "EWM": ["warehouse", "wms", "picking", "putaway"],
    "BW/4HANA": ["analytics", "bi", "report", "kpi", "bw/4hana"],
    "Fiori": ["fiori", "mobile", "ui"],
    "IBP": ["forecast", "planning", "ibp"],
    "TM": ["freight", "carrier", "transport"],
    "MDG": ["master data", "governance", "mdg"],
    "S/4HANA": ["s/4hana"]
}

EXT_SYSTEMS = {
    "Salesforce CRM": ["salesforce"],
    "Oracle DB (Legacy)": ["oracle"],
    "3PL / Logistics": ["3pl", "logistics provider"],
    "E-commerce": ["shopify", "magento", "e-commerce", "ecommerce"],
    "IoT Gateway": ["iot", "sensor", "plc"],
    "POS": ["pos"],
    "EHR": ["ehr", "hl7", "fhir"]
}

def extract(text: str):
    t = (text or "").lower()
    modules = set()
    for mod, kws in MODULE_KEYWORDS.items():
        if any(kw in t for kw in kws):
            modules.add(mod)
    # Always include core if business modules present
    if modules:
        modules.add("S/4HANA")
        modules.add("Fiori")
    else:
        modules.update(["S/4HANA", "Fiori"])
    externals = [name for name, kws in EXT_SYSTEMS.items() if any(kw in t for kw in kws)]

    hosting = "S/4HANA Cloud"
    if "on-prem" in t or "on prem" in t:
        hosting = "On-Prem"
    if "azure" in t:
        hosting = "Azure Cloud"
    if "aws" in t:
        hosting = "AWS Cloud"
    if "hybrid" in t:
        hosting = "Hybrid"

    compliance = []
    for word in ["gdpr", "hipaa", "pci-dss", "iso"]:
        if word in t:
            compliance.append(word.upper())

    # Users hint (very rough)
    nums = re.findall(r"\b(\d{3,6})\b", t)
    users = int(nums[0]) if nums else 1000

    return {
        "modules": sorted(modules),
        "external": externals,
        "hosting": hosting,
        "compliance": compliance,
        "users": users
    }

# ---------------------------------------
# 10 rule-based “agents”
# ---------------------------------------
AGENTS = [
    ("Requirements Analyst",   lambda a: "Scope confirmed; clarify volumes, SLAs, and localization packs."),
    ("Process Mapper",         lambda a: "Map O2C (SD), P2P (MM/Ariba), RtR (FI), Mfg (PP/QM/PM) as applicable."),
    ("Module Recommender",     lambda a: "Active modules: " + ", ".join(a["modules"])),
    ("Integration Planner",    lambda a: "Integrations: " + (", ".join(a["external"]) if a["external"] else "Standard SAP APIs only")),
    ("Security Architect",     lambda a: "RBAC, SoD, encryption in transit/at rest; audit trails for " + ", ".join(a["compliance"]) if a["compliance"] else "RBAC, SoD, encryption; enable audit trails."),
    ("Performance Engineer",   lambda a: f"Design for ~{a['users']} users; cache OData; batch heavy jobs."),
    ("Data Architect",         lambda a: "Use BW/4HANA for KPIs; MDG for golden records if multiple sources."),
    ("DR & Resilience",        lambda a: "Cross-region DR; RPO ≤ 15m, RTO ≤ 2h; frequent backups."),
    ("Testing Lead",           lambda a: "Automate regression for O2C/P2P/RtR + smoke performance tests."),
    ("Change Manager",         lambda a: "Fit-to-Standard; phased releases; training & hypercare.")
]

def run_agents(analysis):
    return [{"agent": name, "finding": rule(analysis)} for name, rule in AGENTS]

# ---------------------------------------
# Architecture diagram (DOT for st.graphviz_chart)
# ---------------------------------------
def build_dot(analysis):
    edges = []
    edges.append(("Users", "Fiori"))
    edges.append(("Fiori", "S/4HANA"))
    edges.append(("S/4HANA", analysis["hosting"]))
    for m in analysis["modules"]:
        if m not in ("S/4HANA", "Fiori"):
            edges.append((m, "S/4HANA"))
    for ext in analysis["external"]:
        edges.append((ext, "S/4HANA"))

    nodes = {n for a, b in edges for n in (a, b)}
    dot = ["digraph G {", 'rankdir=LR;', 'node [shape=box, style=rounded];']
    for n in sorted(nodes):
        dot.append(f'"{n}";')
    for a, b in edges:
        dot.append(f'"{a}" -> "{b}";')
    dot.append("}")
    return "\n".join(dot)

# ---------------------------------------
# FMEA + Mitigation strategies (rule-based)
# ---------------------------------------
def make_fmea(analysis):
    items = []

    def add(mode, effect, sev, occ, det, actions):
        rpn = sev * occ * det
        items.append({
            "Failure Mode": mode, "Effect": effect,
            "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": rpn,
            "Mitigations": actions
        })

    # Heuristics
    many_integrations = len(analysis["external"]) >= 2
    cloud = "Cloud" in analysis["hosting"] or analysis["hosting"] in ("AWS Cloud", "Azure Cloud")
    hybrid = analysis["hosting"] == "Hybrid"
    users = analysis["users"]

    add("Integration failure",
        "Orders/shipments stuck; revenue impact",
        9, 5 + (1 if many_integrations else 0), 5,
        [
            "Use standard IDoc/OData where possible",
            "Contract SLAs with external systems",
            "Retry & dead-letter queues; circuit breakers",
            "Observability on interfaces (alerts, traces)"
        ])

    add("Data migration error",
        "Inaccurate financials or inventory",
        8, 4, 6,
        [
            "Reconciliation runs & parity reports",
            "Master-data validation rules (MDG-style)",
            "Dry runs + cutover checklists"
        ])

    add("Security breach",
        "PII loss / compliance fines",
        10, 3, 4,
        [
            "RBAC & SoD; MFA/SSO",
            "Field-level encryption & masking",
            "Centralized audit logs; log retention"
        ])

    add("Performance degradation",
        "Slow UI and batch overruns",
        7, 4 + (1 if users > 2000 else 0), 5,
        [
            "OData caching & CDS view tuning",
            "Archive/cold-store aged data",
            "Background jobs leveled; capacity tests"
        ])

    add("Availability / DR gap",
        "Extended outage",
        9, 3 + (1 if (cloud or hybrid) else 0), 4,
        [
            "Automated backups; tested restore",
            "Cross-region replicas; failover drills",
            "RPO/RTO in runbooks"
        ])

    add("Master data quality issues",
        "Downstream errors across modules",
        8, 5, 6,
        [
            "Data ownership & stewardship",
            "Duplicate prevention, validations",
            "Golden-record governance"
        ])

    # Sort by RPN descending
    items.sort(key=lambda x: x["RPN"], reverse=True)
    return items

def mitigation_narrative(fmea_items, analysis):
    """
    Free, rule-based 'GenAI/NLP' summary of mitigations using SAP + open-source tooling.
    """
    bullets = []
    # Pick top 4 risks
    for row in fmea_items[:4]:
        mode = row["Failure Mode"]
        if mode == "Integration failure":
            bullets.append(
                "- **Integration failure:** Prefer *standard SAP APIs* (OData/IDoc), stabilize with message queues "
                "(retry + DLQ). Monitor flows with **open-source Prometheus/Grafana**; contract SLAs with 3rd parties."
            )
        elif mode == "Data migration error":
            bullets.append(
                "- **Data migration error:** Use reconciliation reports and trial cutovers; apply **data quality rules** "
                "and duplicate checks (MDG principles). Validate with **Great Expectations** (open-source)."
            )
        elif mode == "Security breach":
            bullets.append(
                "- **Security breach:** Enforce **RBAC/SoD** and SSO/MFA; encrypt in transit/at rest; enable field masking; "
                "centralize audit logs; periodic access reviews."
            )
        elif mode == "Availability / DR gap":
            bullets.append(
                "- **Availability/DR:** Automate backups, test restore, configure cross-region replicas and run **failover drills**; "
                "document RPO/RTO and escalation runbooks."
            )
        elif mode == "Performance degradation":
            bullets.append(
                "- **Performance:** Tune CDS views, cache OData, level background jobs; run load tests; archive historical data."
            )
        elif mode == "Master data quality issues":
            bullets.append(
                "- **Master data quality:** Define data owners/stewards; validations and duplicate prevention; "
                "golden-record governance and change workflows."
            )

    extra = []
    if "GDPR" in analysis.get("compliance", []):
        extra.append("- **GDPR:** Minimize PII, masking/pseudonymization, consent tracking, and retention schedules.")
    if "HIPAA" in analysis.get("compliance", []):
        extra.append("- **HIPAA:** End-to-end encryption, BAA with vendors, and strict audit logging.")
    text = "\n".join(bullets + extra)
    return text or "- No high risks detected beyond standard good practices."

# ---------------------------------------
# UI — input controls
# ---------------------------------------
left, right = st.columns([2, 3])

with left:
    choice = st.selectbox(
        "Choose SAP Enterprise Architecture example (or select **Custom** to write your own):",
        list(EXAMPLES.keys()) + ["Custom"],
        index=0
    )

    if choice == "Custom":
        req_text = st.text_area(
            "Enter your SAP Enterprise Architecture Requirements",
            height=220,
            placeholder="Describe scope, modules, integrations, hosting, compliance, scale…"
        )
    else:
        req_text = EXAMPLES[choice]
        st.text_area("Selected example (editable):", value=req_text, height=220, key="editable_example")

    run = st.button("🚀 Run Agentic Analysis")

with right:
    st.markdown("### Tips")
    st.write("- Mention modules (FI/MM/SD/PP/QM/PM/EWM…), integrations (Salesforce, 3PL, POS, IoT), hosting (AWS/Azure/On-Prem/Hybrid), compliance (GDPR/HIPAA), and scale (users).")

# ---------------------------------------
# Pipeline
# ---------------------------------------
if run:
    requirements = req_text if choice == "Custom" else st.session_state.get("editable_example", req_text)
    analysis = extract(requirements)
    findings = run_agents(analysis)
    dot = build_dot(analysis)
    fmea = make_fmea(analysis)

    st.success("Analysis completed. See results below.")

    T1, T2, T3, T4 = st.tabs(["Parsed & Agents", "Architecture", "FMEA", "Mitigation"])

    with T1:
        st.subheader("Parsed Requirements (NLP-lite)")
        st.json(analysis)
        st.subheader("Agent Findings (10 specialists)")
        for f in findings:
            st.markdown(f"- **{f['agent']}**: {f['finding']}")

    with T2:
        st.subheader("Proposed SAP Enterprise Architecture")
        st.graphviz_chart(dot, use_container_width=True)

    with T3:
        st.subheader("FMEA — Failure Mode & Effects Analysis")
        st.dataframe(fmea, use_container_width=True)
        bundle = {
            "generated_at": datetime.utcnow().isoformat(),
            "input": requirements,
            "analysis": analysis,
            "agents": findings,
            "fmea": fmea
        }
        st.download_button(
            "⬇️ Download JSON bundle",
            data=json.dumps(bundle, indent=2),
            file_name="sap_architecture_fmea_bundle.json",
            mime="application/json"
        )

    with T4:
        st.subheader("Mitigation Strategies (SAP + Open-Source, free-tier friendly generation)")
        st.markdown(mitigation_narrative(fmea, analysis))
