import os
import json
import uuid
import threading
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from dotenv import load_dotenv

from bac_v2.scanner import run_scan

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
SCAN_DIR = DATA_DIR / "scans"

LOG_DIR.mkdir(exist_ok=True)
SCAN_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    filename=LOG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "blind-access-checker-v4-2"
app.config["SCAN_SECONDS"] = int(os.getenv("SCAN_SECONDS", "60"))

JOBS = {}
LOCK = threading.Lock()


def save_job(job_id: str):
    path = SCAN_DIR / f"{job_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(JOBS[job_id], f, indent=2, ensure_ascii=False)


def update_job(job_id: str, **kwargs):
    with LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(kwargs)
            save_job(job_id)


def create_job(url: str):
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "url": url,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "started_at": None,
        "finished_at": None,
        "scan_seconds": app.config["SCAN_SECONDS"],
        "progress_message": "Waiting to start.",
        "result": None,
        "error": None,
    }
    with LOCK:
        JOBS[job_id] = job
        save_job(job_id)
    return job_id


def progress(job_id: str, message: str):
    update_job(job_id, progress_message=message)


def worker(job_id: str):
    job = JOBS[job_id]
    update_job(
        job_id,
        status="running",
        started_at=datetime.utcnow().isoformat() + "Z",
        progress_message="Launching V4.2 spider scan...",
    )
    try:
        result = run_scan(
            url=job["url"],
            max_seconds=app.config["SCAN_SECONDS"],
            base_dir=str(BASE_DIR),
            progress=lambda msg: progress(job_id, msg),
        )
        update_job(
            job_id,
            status="done",
            finished_at=datetime.utcnow().isoformat() + "Z",
            progress_message="Spider commentary complete.",
            result=result,
        )
    except Exception as e:
        logging.exception("Scan failed for %s", job["url"])
        update_job(
            job_id,
            status="error",
            finished_at=datetime.utcnow().isoformat() + "Z",
            progress_message="Scan failed.",
            error=str(e),
        )


@app.route("/", methods=["GET"])
def index():
    recent = sorted(JOBS.values(), key=lambda x: x["created_at"], reverse=True)[:10]
    return render_template("index.html", recent_jobs=recent, scan_seconds=app.config["SCAN_SECONDS"])


@app.route("/start", methods=["POST"])
def start_scan():
    url = (request.form.get("url") or "").strip()
    if not url:
        return redirect(url_for("index"))
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    job_id = create_job(url)
    threading.Thread(target=worker, args=(job_id,), daemon=True).start()
    return redirect(url_for("scan_status", job_id=job_id))


@app.route("/scan/<job_id>", methods=["GET"])
def scan_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return render_template("error.html", message="Scan job not found."), 404
    return render_template("status.html", job=job)


@app.route("/scan/<job_id>/status", methods=["GET"])
def scan_status_json(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify(
        {
            "ok": True,
            "status": job["status"],
            "progress_message": job.get("progress_message", ""),
            "error": job.get("error"),
            "report_url": url_for("scan_report", job_id=job_id) if job["status"] == "done" else None,
        }
    )


@app.route("/report/<job_id>", methods=["GET"])
def scan_report(job_id):
    job = JOBS.get(job_id)
    if not job:
        return render_template("error.html", message="Scan job not found."), 404
    if job["status"] != "done":
        return redirect(url_for("scan_status", job_id=job_id))
    return render_template("report.html", job=job, result=job["result"])


@app.route("/media/<scan_folder>/<path:filename>", methods=["GET"])
def media(scan_folder, filename):
    folder = SCAN_DIR / scan_folder
    return send_from_directory(folder, filename)


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"Blind Access Checker V4.2 running at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
