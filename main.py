import sys
import os
import argparse
import logging
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="scapy.*")
warnings.filterwarnings("ignore", message=".*libpcap.*")
import json
import subprocess
from typing import List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from analyzer.tshark import check_tshark_version, find_tshark_path
from analyzer.pcap_ingestion import ingest_and_parse_pcap
from ml.model_loader import find_model_dir
from ml.xgboost_adapter import predict_traffic_class
from security.policy_engine import evaluate_ipsec_security
from security.recommendations import generate_recommendations
from security.risk import calculate_security_risk
from routers.protocol import router as protocol_router
from routers.testbed import router as testbed_router
from db.supabase_client import get_supabase_client, is_supabase_enabled
from contextlib import asynccontextmanager

load_dotenv()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB connection on server startup
    sb = get_supabase_client()
    if sb:
        logger.info(f"Connected to Supabase cloud storage & database at {os.getenv('SUPABASE_URL')}")
    else:
        logger.info("Supabase not configured or unreachable; operating in local storage fallback mode.")
    yield

# FastAPI App Instance for Privcomm Web Platform
app = FastAPI(
    title="Privcomm — AI-Assisted IPsec VPN Security Intelligence Platform",
    description="Full IPsec VPN protocol dissection, XGBoost traffic classification, and compliance audit engine.",
    version="2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(protocol_router)
app.include_router(testbed_router)

@app.head("/health", tags=["System"])
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "supabase_connected": is_supabase_enabled(),
        "storage_mode": "supabase" if is_supabase_enabled() else "local"
    }

react_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(os.path.join(react_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(react_dist, "assets")), name="assets")

# Serve homepage (index.html), dashboard (dashboard.html), and executive report (report.html)
@app.head("/", include_in_schema=False)
@app.get("/", include_in_schema=False)
async def serve_homepage():
    react_index = os.path.join(react_dist, "index.html")
    if os.path.exists(react_index):
        return FileResponse(react_index)
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "operational", "frontend": "not built"}

@app.get("/dashboard.html", include_in_schema=False)
async def serve_dashboard_page():
    return FileResponse("dashboard.html")

@app.get("/report", include_in_schema=False)
async def serve_report_page():
    return FileResponse("report.html")

# Serve static assets if present
if os.path.exists("style.css"):
    @app.get("/style.css", include_in_schema=False)
    async def serve_css():
        return FileResponse("style.css", media_type="text/css")

if os.path.exists("script.js"):
    @app.get("/script.js", include_in_schema=False)
    async def serve_js():
        return FileResponse("script.js", media_type="application/javascript")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """SPA fallback so client-side routes resolve after a static build."""
    dist_file = os.path.join(react_dist, full_path)
    if os.path.isfile(dist_file):
        return FileResponse(dist_file)
    react_index = os.path.join(react_dist, "index.html")
    if os.path.exists(react_index):
        return FileResponse(react_index)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="Not found")


def run_check_dependencies():
    """Execute startup dependency check per PRD Section 2."""
    print("\n--- AI-Powered IPsec VPN Protocol Analyzer Startup Check ---")

    # 1. Python check
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 10)
    py_mark = "[OK]" if py_ok else "[FAIL]"
    print(f"Python: {py_mark} (v{py_ver})")

    # 2. TShark check
    tshark_info = check_tshark_version()
    if tshark_info["installed"]:
        print(f"TShark: [OK] ({tshark_info['path']})")
        print(f"TShark version: {tshark_info['version']}")
    else:
        print("TShark: [NOT FOUND in PATH or TSHARK_PATH]")
        print("        [Note: System will use built-in Scapy engine as fallback]")

    # 3. Wireshark check
    tshark_path = tshark_info.get("path")
    ws_installed = tshark_path and os.path.exists(tshark_path)
    ws_mark = "[OK]" if ws_installed else "[Not required / Custom path]"
    print(f"Wireshark: {ws_mark}")

    # 4. XGBoost Model check
    try:
        m_dir = find_model_dir()
        print(f"XGBoost model: [OK] (Artifacts found at '{m_dir}')")
    except Exception as e:
        print(f"XGBoost model: [FAIL] (Missing trained model: {e})")

    print("-----------------------------------------------------------\n")

def run_analyze_pcap(pcap_path: str, output_path: str = None, export_html_path: str = None) -> Dict[str, Any]:
    """Analyze a single PCAP/PCAPNG capture file."""
    logger.info(f"Loading PCAP capture: {pcap_path}")

    ingest_res = ingest_and_parse_pcap(pcap_path)
    if ingest_res.get("status") == "error":
        logger.error(f"Analysis failed: {ingest_res.get('message')}")
        return ingest_res

    logger.info("Running XGBoost traffic classifier...")
    flow_feats = ingest_res.get("flow_features", {})
    traffic_res = predict_traffic_class(flow_feats)

    from reports.report_generator import build_unified_analysis_report

    logger.info("Running deterministic security assessment...")
    ipsec_config = ingest_res.get("ipsec", {})
    predicted_type = traffic_res.get("traffic_type") if traffic_res.get("status") == "success" else None
    findings = evaluate_ipsec_security(ipsec_config, traffic_type=predicted_type)

    recommendations = generate_recommendations(findings)
    risk_res = calculate_security_risk(findings)

    report = build_unified_analysis_report(
        ingest_res, traffic_res, findings, recommendations, risk_res
    )

    logger.info("Analysis completed successfully.")

    if output_path:
        from reports.report_generator import save_json_report
        save_json_report(report, output_path)

    if export_html_path:
        from reports.html_report_generator import generate_html_report
        generate_html_report(report, export_html_path)

    return report

def run_batch_analysis(input_dir: str, output_dir: str = "results"):
    """Process an entire directory of PCAP files and generate summary CSV."""
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    pcap_files = [
        os.path.join(input_dir, f) for f in os.listdir(input_dir)
        if f.lower().endswith((".pcap", ".pcapng"))
    ]

    if not pcap_files:
        logger.warning(f"No .pcap or .pcapng files found in '{input_dir}'.")
        return

    logger.info(f"Found {len(pcap_files)} PCAP files in '{input_dir}'. Starting batch processing...")

    from reports.report_generator import generate_batch_summary_csv

    reports = []
    for pcap in pcap_files:
        base_name = os.path.splitext(os.path.basename(pcap))[0]
        out_file = os.path.join(output_dir, f"{base_name}.json")
        out_html = os.path.join(output_dir, f"{base_name}_report.html")
        try:
            report = run_analyze_pcap(pcap, output_path=out_file, export_html_path=out_html)
            reports.append(report)
        except Exception as e:
            logger.error(f"Error analyzing '{pcap}': {e}")

    summary_csv = os.path.join(output_dir, "summary.csv")
    generate_batch_summary_csv(reports, summary_csv)
    logger.info(f"Batch processing completed. Results written to '{output_dir}'.")

def run_dashboard():
    """Launch interactive Streamlit web dashboard."""
    dash_app = os.path.join("dashboard", "app.py")
    if not os.path.exists(dash_app):
        logger.error(f"Dashboard script not found at {dash_app}")
        sys.exit(1)

    logger.info("Launching Interactive Streamlit Dashboard UI...")
    cmd = [sys.executable, "-m", "streamlit", "run", dash_app]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        logger.info("Dashboard stopped.")

def run_server():
    """Launch Privcomm FastAPI Server serving Web App and APIs."""
    import uvicorn
    logger.info("Launching Privcomm Platform Server at http://localhost:8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered IPsec VPN Protocol Analyzer & Security Assessment Framework"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("check-dependencies", help="Check system dependencies, TShark, and ML model status")
    parser.add_argument("--check-dependencies", action="store_true", help="Shortcut for check-dependencies")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single PCAP/PCAPNG file")
    analyze_parser.add_argument("--pcap", type=str, required=True, help="Path to input PCAP or PCAPNG file")
    analyze_parser.add_argument("--output", type=str, help="Optional output path for JSON analysis report")
    analyze_parser.add_argument("--export-html", type=str, help="Optional output path for Executive HTML report")

    batch_parser = subparsers.add_parser("batch", help="Batch analyze a directory of PCAP files")
    batch_parser.add_argument("--input", type=str, required=True, help="Path to directory containing PCAP files")
    batch_parser.add_argument("--output", type=str, default="results", help="Output directory for reports and summary CSV")

    subparsers.add_parser("dashboard", help="Launch Streamlit Web Dashboard UI")
    subparsers.add_parser("server", help="Launch Privcomm FastAPI Platform Server (Web UI + APIs)")

    args = parser.parse_args()

    if args.check_dependencies or args.command == "check-dependencies":
        run_check_dependencies()
        sys.exit(0)

    if args.command == "analyze":
        report = run_analyze_pcap(args.pcap, args.output, args.export_html)
        print("\n--- Unified Analysis Result ---")
        print(json.dumps(report, indent=2))

    elif args.command == "batch":
        run_batch_analysis(args.input, args.output)

    elif args.command == "dashboard":
        run_dashboard()

    elif args.command == "server":
        run_server()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
