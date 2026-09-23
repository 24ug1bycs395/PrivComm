import sys
import os
import tempfile
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer.pcap_ingestion import ingest_and_parse_pcap
from ml.xgboost_adapter import predict_traffic_class
from security.policy_engine import evaluate_ipsec_security
from security.recommendations import generate_recommendations
from security.risk import calculate_security_risk
from reports.report_generator import build_unified_analysis_report
from reports.html_report_generator import generate_html_report

# Configure Page
st.set_page_config(
    page_title="AI IPsec VPN Analyzer & Security Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .badge-secure { color: #4ade80; font-weight: bold; }
    .badge-medium { color: #fde047; font-weight: bold; }
    .badge-high { color: #fca5a5; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def analyze_file(file_path: str) -> dict:
    ingest_res = ingest_and_parse_pcap(file_path)
    flow_feats = ingest_res.get("flow_features", {})
    traffic_res = predict_traffic_class(flow_feats)
    ipsec_config = ingest_res.get("ipsec", {})
    predicted_type = traffic_res.get("traffic_type") if traffic_res.get("status") == "success" else None
    findings = evaluate_ipsec_security(ipsec_config, traffic_type=predicted_type)
    recommendations = generate_recommendations(findings)
    risk_res = calculate_security_risk(findings)

    return build_unified_analysis_report(
        ingest_res, traffic_res, findings, recommendations, risk_res
    )


def create_risk_gauge(score: int, level: str):
    colors = {
        "SECURE": "#22c55e",
        "LOW": "#4ade80",
        "MEDIUM": "#eab308",
        "HIGH": "#f97316",
        "CRITICAL": "#ef4444"
    }

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Security Risk Score: {level}", 'font': {'size': 18, 'color': "#f8fafc"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
            'bar': {'color': colors.get(level, "#38bdf8")},
            'bgcolor': "#1e293b",
            'borderwidth': 2,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 25], 'color': 'rgba(34, 197, 94, 0.2)'},
                {'range': [25, 55], 'color': 'rgba(234, 179, 8, 0.2)'},
                {'range': [55, 85], 'color': 'rgba(249, 115, 22, 0.2)'},
                {'range': [85, 100], 'color': 'rgba(239, 68, 68, 0.2)'}
            ]
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def create_threat_matrix_chart():
    # 3x3 Heatmap Grid (Likelihood vs Impact)
    z = [
        [15, 30, 60], # Low Likelihood (Low, Low, Med)
        [30, 45, 75], # Med Likelihood (Low, Med, High)
        [45, 75, 95]  # High Likelihood (Med, High, Critical)
    ]
    x = ['Low Impact', 'Medium Impact', 'High Impact']
    y = ['Low Likelihood', 'Med Likelihood', 'High Likelihood']

    fig = go.Figure(data=go.Heatmap(
        z=z, x=x, y=y,
        colorscale='RdYlGn_r',
        showscale=False
    ))
    fig.update_layout(
        title="3x3 Threat Matrix Grid",
        title_font=dict(color="#f8fafc", size=16),
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def main():
    st.sidebar.title("🛡️ IPsec VPN Analyzer")
    st.sidebar.markdown("AI-Powered Protocol Analysis & Security Assessment Framework")

    # File Source Selection
    source = st.sidebar.radio("Data Source", ["Sample Dataset", "Upload PCAP/PCAPNG"])

    file_path = None
    if source == "Sample Dataset":
        sample_file = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
        if os.path.exists(sample_file):
            file_path = sample_file
            st.sidebar.success(f"Loaded: `{os.path.basename(sample_file)}`")
        else:
            st.sidebar.error("Sample PCAP not found in `samples/` directory.")
    else:
        uploaded_file = st.sidebar.file_uploader("Upload Capture File (.pcap, .pcapng)", type=["pcap", "pcapng"])
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.read())
                file_path = tmp.name

    st.title("🛡️ IPsec VPN Protocol Analyzer & Security Dashboard")
    st.markdown("Automated cryptographic inspection, AI traffic classification, and security baseline compliance auditing.")

    if not file_path:
        st.info("👈 Please select a sample dataset or upload a `.pcap` / `.pcapng` file from the sidebar to begin analysis.")
        return

    # Run Analysis Pipeline
    with st.spinner("Analyzing network capture, protocol proposals, and running AI model..."):
        report = analyze_file(file_path)

    cap = report["capture"]
    ipsec = report["ipsec"]
    tc = report["traffic_classification"]
    sec = report["security_assessment"]

    # Top Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Packets", cap.get("packet_count", 0))
    with m2:
        st.metric("IPsec Protocol", ipsec.get("ike_version", "N/A"))
    with m3:
        st.metric("Encryption Cipher", ipsec.get("encryption", "N/A"))
    with m4:
        st.metric("AI Traffic Class", tc.get("traffic_type", "N/A"))
    with m5:
        conf = tc.get("confidence", 0)
        st.metric("AI Confidence", f"{conf * 100:.1f}%" if isinstance(conf, float) else "N/A")

    st.divider()

    # Column Layout: Charts & Security Matrix
    col1, col2 = st.columns([1, 1])

    with col1:
        st.plotly_chart(create_risk_gauge(sec.get("risk_score", 0), sec.get("risk_level", "SECURE")), use_container_width=True)

    with col2:
        st.plotly_chart(create_threat_matrix_chart(), use_container_width=True)

    st.divider()

    # AI Traffic Probabilities Chart
    st.subheader("🤖 AI Encrypted Traffic Probability Distribution")
    probs = tc.get("probabilities", {})
    if probs:
        df_probs = pd.DataFrame(list(probs.items()), columns=["Traffic Category", "Probability"]).sort_values("Probability", ascending=False)
        fig_bar = px.bar(
            df_probs, x="Traffic Category", y="Probability",
            color="Probability", color_continuous_scale="Blues",
            title="Class Confidence Distribution Across 14 Traffic Categories"
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Cryptographic Configuration & Security Findings
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.subheader("🔑 Cryptographic & SA Parameters")
        spec_data = {
            "Parameter": ["IKE Version", "Exchange Type", "Encryption", "Integrity / Auth", "PRF", "Diffie-Hellman Group", "Mode", "Initiator SPI", "Responder SPI"],
            "Value": [
                ipsec.get("ike_version"),
                ipsec.get("exchange_type"),
                f"{ipsec.get('encryption')} ({ipsec.get('key_length', 256)}-bit)",
                ipsec.get("integrity"),
                ipsec.get("prf"),
                f"Group {ipsec.get('dh_group')}",
                ipsec.get("mode"),
                ipsec.get("initiator_spi") or "N/A",
                ipsec.get("responder_spi") or "N/A"
            ]
        }
        st.table(pd.DataFrame(spec_data))

    with c_right:
        st.subheader("🚨 Security Assessment & Audit Findings")
        findings = sec.get("findings", [])
        if findings:
            for f in findings:
                with st.expander(f"[{f.get('severity')}] {f.get('title')}", expanded=True):
                    st.write(f"**Observed**: `{f.get('observed')}`")
                    st.write(f"**Expected**: `{f.get('expected')}`")
                    st.info(f"**Remediation Action**: {f.get('recommendation')}")
        else:
            st.success("✅ **No Policy Violations Detected**: Configuration complies fully with corporate security baselines.")

    st.divider()

    # One-Click Report Download Buttons
    st.subheader("📥 Export Audit Reports")
    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            label="📄 Download Technical JSON Report",
            data=json.dumps(report, indent=4),
            file_name=f"{os.path.splitext(cap.get('filename', 'report'))[0]}_analysis.json",
            mime="application/json"
        )

    with d2:
        tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html").name
        generate_html_report(report, tmp_html)
        with open(tmp_html, "r", encoding="utf-8") as hf:
            html_content = hf.read()
        st.download_button(
            label="🌐 Download Executive HTML Report",
            data=html_content,
            file_name=f"{os.path.splitext(cap.get('filename', 'report'))[0]}_executive_report.html",
            mime="text/html"
        )


if __name__ == "__main__":
    main()
