import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from db.supabase_client import get_supabase_client

logger = logging.getLogger("db.repository")

LOCAL_ANALYSIS_DB = os.path.join("results", "analysis_jobs.json")
LOCAL_TESTBED_DB = os.path.join("results", "testbed_jobs.json")

def _load_json_db(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_json_db(path: str, data: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


class AnalysisJobRepository:
    """Repository for storing and querying PCAP analysis execution results."""

    @staticmethod
    def save_analysis(job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves an analysis result to Supabase and/or local JSON database."""
        if "id" not in job_data or not job_data["id"]:
            job_data["id"] = str(uuid.uuid4())
        if "created_at" not in job_data or not job_data["created_at"]:
            job_data["created_at"] = datetime.now(timezone.utc).isoformat()

        # 1. Save to local fallback JSON
        records = _load_json_db(LOCAL_ANALYSIS_DB)
        records = [r for r in records if r.get("id") != job_data["id"]]
        records.insert(0, job_data)
        _save_json_db(LOCAL_ANALYSIS_DB, records[:100])  # keep recent 100

        # 2. Persist to Supabase if connected
        client = get_supabase_client()
        if client:
            try:
                # Prepare payload matching table schema
                db_record = {
                    "id": job_data.get("id"),
                    "filename": job_data.get("filename", "unknown.pcap"),
                    "filesize": job_data.get("filesize", 0),
                    "status": job_data.get("status", "COMPLETED"),
                    "protocol_detected": "IPsec" if job_data.get("ipsec_detected") else "Non-IPsec",
                    "ike_version": job_data.get("ike_version"),
                    "compliance_score": job_data.get("compliance_score"),
                    "traffic_classification": job_data.get("traffic_classification"),
                    "security_assessment": job_data.get("security_assessment"),
                    "findings_count": len(job_data.get("security_assessment", {}).get("findings", [])),
                    "result_json": job_data,
                    "html_report_url": job_data.get("html_report_url") or job_data.get("report_html"),
                    "pcap_storage_path": job_data.get("pcap_storage_path"),
                    "error_message": job_data.get("error_message")
                }
                client.table("analysis_jobs").upsert(db_record).execute()
                logger.info(f"[DB] Saved analysis job {job_data['id']} to Supabase")
            except Exception as e:
                logger.warning(f"[DB] Failed to insert to Supabase analysis_jobs table: {e}")

        return job_data

    @staticmethod
    def list_analyses(limit: int = 50) -> List[Dict[str, Any]]:
        """Lists recent analysis jobs."""
        client = get_supabase_client()
        if client:
            try:
                response = client.table("analysis_jobs").select("*").order("created_at", desc=True).limit(limit).execute()
                if response.data:
                    return response.data
            except Exception as e:
                logger.warning(f"[DB] Supabase query failed: {e}. Falling back to local storage.")

        return _load_json_db(LOCAL_ANALYSIS_DB)[:limit]

    @staticmethod
    def get_analysis(job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific analysis job by ID."""
        client = get_supabase_client()
        if client:
            try:
                res = client.table("analysis_jobs").select("*").eq("id", job_id).single().execute()
                if res.data:
                    return res.data
            except Exception:
                pass

        records = _load_json_db(LOCAL_ANALYSIS_DB)
        for r in records:
            if r.get("id") == job_id:
                return r
        return None


class TestbedJobRepository:
    """Repository for strongSwan testbed scenario executions & captures."""

    @staticmethod
    def create_job(scenario_name: str, config_json: Dict[str, Any]) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        job = {
            "id": job_id,
            "created_at": now,
            "updated_at": now,
            "scenario_name": scenario_name,
            "ike_version": config_json.get("ike_version", "IKEv2"),
            "cipher_suite": config_json.get("cipher_suite", "AES-256-GCM"),
            "auth_method": config_json.get("auth_method", "PSK"),
            "state": "QUEUED",
            "config_json": config_json,
            "result_json": None,
            "pcap_storage_path": None,
            "pcap_download_url": None,
            "error_message": None,
            "logs": [f"[{now}] Job initialized."]
        }

        # Local save
        records = _load_json_db(LOCAL_TESTBED_DB)
        records.insert(0, job)
        _save_json_db(LOCAL_TESTBED_DB, records[:100])

        # Supabase save
        client = get_supabase_client()
        if client:
            try:
                db_record = {
                    "id": job["id"],
                    "scenario_name": job["scenario_name"],
                    "ike_version": job["ike_version"],
                    "cipher_suite": job["cipher_suite"],
                    "auth_method": job["auth_method"],
                    "state": job["state"],
                    "progress_pct": 0,
                    "config_json": job["config_json"],
                    "logs": job.get("logs", [])
                }
                client.table("testbed_jobs").insert(db_record).execute()
            except Exception as e:
                logger.warning(f"[DB] Failed to insert testbed job to Supabase: {e}")

        return job

    @staticmethod
    def update_job(job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now

        # Update local
        records = _load_json_db(LOCAL_TESTBED_DB)
        updated_job = None
        for r in records:
            if r.get("id") == job_id:
                r.update(updates)
                if "log" in updates:
                    r.setdefault("logs", []).append(f"[{now}] {updates['log']}")
                updated_job = r
                break
        _save_json_db(LOCAL_TESTBED_DB, records)

        # Update Supabase
        client = get_supabase_client()
        if client:
            try:
                db_updates = {k: v for k, v in updates.items() if k != "log"}
                if updated_job and "logs" in updated_job:
                    db_updates["logs"] = updated_job["logs"]
                client.table("testbed_jobs").update(db_updates).eq("id", job_id).execute()
            except Exception as e:
                logger.warning(f"[DB] Failed to update testbed job in Supabase: {e}")

        return updated_job

    @staticmethod
    def list_jobs(limit: int = 50) -> List[Dict[str, Any]]:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("testbed_jobs").select("*").order("created_at", desc=True).limit(limit).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return _load_json_db(LOCAL_TESTBED_DB)[:limit]

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("testbed_jobs").select("*").eq("id", job_id).single().execute()
                if res.data:
                    return res.data
            except Exception:
                pass

        records = _load_json_db(LOCAL_TESTBED_DB)
        for r in records:
            if r.get("id") == job_id:
                return r
        return None
