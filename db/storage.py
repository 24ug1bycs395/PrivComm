import logging
import os
import shutil

from db.supabase_client import get_supabase_client

logger = logging.getLogger("db.storage")

class StorageService:
    """
    Manages storage for executive reports (HTML/JSON) and PCAP capture files.
    Directs assets to Supabase Storage buckets if configured, or saves to local disk.
    """

    @staticmethod
    def upload_report_html(filename: str, content_or_path: str) -> str:
        """
        Uploads or saves an executive HTML report.
        Returns a public URL (if Supabase) or relative local path.
        """
        base_name = os.path.basename(filename)
        if not base_name.endswith(".html"):
            base_name = f"{base_name}.html"

        # 1. Always ensure local backup in results/
        os.makedirs("results", exist_ok=True)
        local_path = os.path.join("results", base_name)
        if os.path.exists(content_or_path) and os.path.isfile(content_or_path):
            if os.path.abspath(content_or_path) != os.path.abspath(local_path):
                shutil.copy2(content_or_path, local_path)
        else:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content_or_path)

        # 2. Upload to Supabase Storage if available
        client = get_supabase_client()
        if client:
            try:
                with open(local_path, "rb") as f:
                    file_bytes = f.read()

                # Upload to 'reports' bucket
                bucket_name = "reports"
                remote_path = f"html/{base_name}"

                # Check / Upsert file
                client.storage.from_(bucket_name).upload(
                    file=file_bytes,
                    path=remote_path,
                    file_options={"content-type": "text/html", "upsert": "true"}
                )
                public_url = client.storage.from_(bucket_name).get_public_url(remote_path)
                logger.info(f"[Storage] Report uploaded to Supabase Storage: {public_url}")
                return public_url
            except Exception as e:
                logger.warning(f"[Storage] Supabase storage upload failed: {e}. Falling back to local URL.")

        return f"/reports/download-html?filename={base_name}"

    @staticmethod
    def upload_pcap_capture(filename: str, local_pcap_path: str) -> str:
        """
        Uploads a generated or analyzed PCAP capture file.
        Returns a download URL or local path.
        """
        base_name = os.path.basename(filename)
        os.makedirs("captures", exist_ok=True)
        dest_path = os.path.join("captures", base_name)

        if os.path.abspath(local_pcap_path) != os.path.abspath(dest_path) and os.path.exists(local_pcap_path):
            shutil.copy2(local_pcap_path, dest_path)

        client = get_supabase_client()
        if client and os.path.exists(dest_path):
            try:
                with open(dest_path, "rb") as f:
                    file_bytes = f.read()

                bucket_name = "captures"
                remote_path = f"pcaps/{base_name}"

                client.storage.from_(bucket_name).upload(
                    file=file_bytes,
                    path=remote_path,
                    file_options={"content-type": "application/vnd.tcpdump.pcap", "upsert": "true"}
                )
                public_url = client.storage.from_(bucket_name).get_public_url(remote_path)
                logger.info(f"[Storage] PCAP uploaded to Supabase Storage: {public_url}")
                return public_url
            except Exception as e:
                logger.warning(f"[Storage] Supabase PCAP upload failed: {e}. Falling back to local.")

        return f"/captures/{base_name}"
