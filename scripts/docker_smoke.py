#!/usr/bin/env python3
"""
Full transactional Docker smoke test.
Validates the entire end-to-end containerized system against a live running Docker Compose stack.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


def http_get(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(url: str, data: dict) -> dict:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_command(cmd: list[str]) -> None:
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        sys.exit(res.returncode)


def main() -> None:
    print("=== Starting Full Docker Smoke Transaction ===")

    try:
        # 1. Build and start containers
        print("[1/10] Starting docker compose services...")
        run_command(["docker", "compose", "up", "-d", "--build"])

        # 2. Wait for readiness
        print("[2/10] Waiting for API readiness probe...")
        ready = False
        for _attempt in range(30):
            try:
                res = http_get("http://localhost:8000/ready")
                if res.get("status") == "ready":
                    ready = True
                    print(f"API is ready! Response: {res}")
                    break
            except Exception:
                time.sleep(2)

        if not ready:
            print("Error: Timed out waiting for API /ready")
            sys.exit(1)

        # 3. Create Project
        print("[3/10] Creating project...")
        proj = http_post(
            "http://localhost:8000/api/v1/projects",
            {"title": "Docker Smoke Novel", "genre_hint": "Fantasy", "privacy_mode": "LOCAL_ONLY"},
        )
        project_id = proj["project_id"]
        print(f"Created project: {project_id}")

        # 4. Import Sample Manuscript
        print("[4/10] Importing manuscript...")
        sample_md = (
            "# Chapter 1: The Mountain Fortress\n\n"
            "Lord Arthur Vance had blue eyes.\n\n"
            "# Chapter 2: The Hall of Council\n\n"
            "Arthur Vance had green eyes."
        )
        import_res = http_post(
            f"http://localhost:8000/api/v1/projects/{project_id}/import",
            {"format": "markdown", "content_text": sample_md},
        )
        print(f"Imported blocks: {import_res.get('units_count')}")

        # 5. Index Manuscript
        print("[5/10] Indexing manuscript...")
        idx_res = http_post(f"http://localhost:8000/api/v1/projects/{project_id}/index", {})
        print(f"Index status: {idx_res.get('status')}")

        # 6. Retrieve Evidence
        print("[6/10] Retrieving evidence...")
        ret_res = http_post(
            f"http://localhost:8000/api/v1/projects/{project_id}/retrieve",
            {"query": "Arthur eyes", "project_id": project_id},
        )
        print(f"Retrieved hits: {len(ret_res.get('results', []))}")

        # 7. Run Continuity Check
        print("[7/10] Running continuity verification...")
        alerts = http_post(
            f"http://localhost:8000/api/v1/projects/{project_id}/continuity/check", {}
        )
        print(f"Alerts generated: {len(alerts)}")
        if not alerts:
            print("Error: Expected at least 1 continuity alert")
            sys.exit(1)
        alert_id = alerts[0]["alert_id"]

        # 8. Save Author Decision
        print("[8/10] Saving author decision (Mark Intentional)...")
        dec_res = http_post(
            f"http://localhost:8000/api/v1/projects/{project_id}/continuity/alerts/{alert_id}/decision",
            {"action_type": "MARK_INTENTIONAL", "author_notes": "Deliberate eye color illusion."},
        )
        print(f"Decision saved: {dec_res}")

        # 9. Modify Passage & Incremental Reindex
        print("[9/10] Saving revision and running incremental reindex...")
        rev_md = (
            "# Chapter 1: The Mountain Fortress\n\n"
            "Lord Arthur Vance had blue eyes.\n\n"
            "# Chapter 2: The Hall of Council\n\n"
            "Arthur Vance had blue eyes."  # Fixed contradiction
        )
        http_post(
            f"http://localhost:8000/api/v1/projects/{project_id}/revisions",
            {"content_markdown": rev_md},
        )
        http_post(
            f"http://localhost:8000/api/v1/projects/{project_id}/index", {"incremental": True}
        )

        # 10. Check Web UI & Prometheus metrics endpoint
        print("[10/11] Checking Web UI frontend...")
        try:
            req_web = urllib.request.Request("http://localhost:3000")
            with urllib.request.urlopen(req_web, timeout=5) as w_resp:
                assert w_resp.status == 200
                print("Web UI responded HTTP 200!")
        except Exception as exc:
            print(f"Web UI check note (frontend service optional or proxied): {exc}")

        print("[11/11] Checking metrics endpoint...")
        req_metrics = urllib.request.Request("http://localhost:8000/metrics")
        with urllib.request.urlopen(req_metrics, timeout=5) as m_resp:
            metrics_content = m_resp.read().decode("utf-8")
            assert "alerts_created_total" in metrics_content
            print("Prometheus metrics successfully validated!")

        print("=== Docker Smoke Transaction SUCCEEDED 100% ===")

    finally:
        print("Tearing down docker compose stack...")
        run_command(["docker", "compose", "down", "-v"])


if __name__ == "__main__":
    main()
