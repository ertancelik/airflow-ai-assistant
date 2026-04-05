import requests
import time
from datetime import datetime

AIRFLOW_BASE_URL = "http://localhost:8080/api/v2"
AIRFLOW_UI_URL = "http://localhost:8080"
USERNAME = "admin"
PASSWORD = "admin"

def get_token() -> str:
    response = requests.post(
        f"{AIRFLOW_UI_URL}/auth/token",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_headers() -> dict:
    return {"Authorization": f"Bearer {get_token()}"}

# ─── DAG İşlemleri ───────────────────────────────────────

def get_dags() -> list:
    response = requests.get(f"{AIRFLOW_BASE_URL}/dags", headers=get_headers())
    response.raise_for_status()
    return response.json().get("dags", [])

def get_dag_details(dag_id: str) -> dict:
    response = requests.get(f"{AIRFLOW_BASE_URL}/dags/{dag_id}", headers=get_headers())
    response.raise_for_status()
    return response.json()

def pause_dag(dag_id: str) -> dict:
    response = requests.patch(
        f"{AIRFLOW_BASE_URL}/dags/{dag_id}",
        headers=get_headers(),
        json={"is_paused": True}
    )
    response.raise_for_status()
    return {"status": "paused", "dag_id": dag_id}

def unpause_dag(dag_id: str) -> dict:
    response = requests.patch(
        f"{AIRFLOW_BASE_URL}/dags/{dag_id}",
        headers=get_headers(),
        json={"is_paused": False}
    )
    response.raise_for_status()
    return {"status": "unpaused", "dag_id": dag_id}

def trigger_dag(dag_id: str, conf: dict = {}) -> dict:
    response = requests.post(
        f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns",
        headers={**get_headers(), "Content-Type": "application/json"},
        json={"dag_run_id": f"manual__{int(time.time())}", "conf": conf}
    )
    response.raise_for_status()
    return {"status": "triggered", "dag_id": dag_id}

# ─── DAG Run İşlemleri ───────────────────────────────────

def get_dag_runs(dag_id: str, limit: int = 5) -> list:
    response = requests.get(
        f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns",
        headers=get_headers(),
        params={"limit": limit, "order_by": "-run_after"}
    )
    response.raise_for_status()
    runs = response.json().get("dag_runs", [])
    result = []
    for r in runs:
        result.append({
            "run_id": r.get("run_id", "unknown"),
            "state": r.get("state", "unknown"),
            "run_after": r.get("run_after", ""),
            "start_date": r.get("start_date", ""),
            "end_date": r.get("end_date", ""),
        })
    return result

def get_system_health() -> dict:
    all_dags = get_dags()
    summary = {
        "total": len(all_dags),
        "active": 0,
        "paused": 0,
        "failed": 0,
        "success": 0,
        "details": []
    }
    for dag in all_dags:
        dag_id = dag["dag_id"]
        if dag["is_paused"]:
            summary["paused"] += 1
        else:
            summary["active"] += 1
        runs = get_dag_runs(dag_id, limit=1)
        last_state = runs[0]["state"] if runs else "no runs"
        if last_state == "failed":
            summary["failed"] += 1
        elif last_state == "success":
            summary["success"] += 1
        summary["details"].append({
            "dag_id": dag_id,
            "last_state": last_state,
            "is_paused": dag["is_paused"]
        })
    return summary

def get_dag_stats() -> list:
    all_dags = get_dags()
    stats = []
    for dag in all_dags:
        dag_id = dag["dag_id"]
        runs = get_dag_runs(dag_id, limit=20)
        if not runs:
            continue
        total_runs = len(runs)
        durations = []
        for r in runs:
            if r.get("start_date") and r.get("end_date"):
                try:
                    start = datetime.fromisoformat(r["start_date"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(r["end_date"].replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    durations.append({
                        "run_id": r["run_id"],
                        "duration_seconds": round(duration, 2),
                        "date": r["start_date"]
                    })
                except:
                    pass
        avg_duration = sum(d["duration_seconds"] for d in durations) / len(durations) if durations else 0
        max_duration = max(durations, key=lambda x: x["duration_seconds"]) if durations else None
        stats.append({
            "dag_id": dag_id,
            "total_runs": total_runs,
            "avg_duration_seconds": round(avg_duration, 2),
            "longest_run": max_duration,
            "success_count": len([r for r in runs if r["state"] == "success"]),
            "failed_count": len([r for r in runs if r["state"] == "failed"]),
        })
    return sorted(stats, key=lambda x: x["total_runs"], reverse=True)

# ─── Task İşlemleri ──────────────────────────────────────

def get_task_instances(dag_id: str, run_id: str) -> list:
    response = requests.get(
        f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json().get("task_instances", [])

def get_failed_tasks(dag_id: str) -> list:
    runs = get_dag_runs(dag_id, limit=1)
    if not runs:
        return []
    tasks = get_task_instances(dag_id, runs[0]["run_id"])
    return [t for t in tasks if t["state"] == "failed"]

def clear_task(dag_id: str, task_id: str, run_id: str) -> dict:
    response = requests.post(
        f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/clear",
        headers={**get_headers(), "Content-Type": "application/json"},
        json={"task_ids": [task_id], "include_downstream": False}
    )
    response.raise_for_status()
    return {"status": "cleared", "task_id": task_id}

def get_task_log(dag_id: str) -> str:
    runs = get_dag_runs(dag_id, limit=5)
    failed_run = next((r for r in runs if r["state"] == "failed"), None)
    if not failed_run:
        return "No failed runs found."
    run_id = failed_run["run_id"]
    tasks = get_task_instances(dag_id, run_id)
    failed_tasks = [t for t in tasks if t["state"] == "failed"]
    if not failed_tasks:
        return "No failed tasks found."
    task_id = failed_tasks[0]["task_id"]
    try:
        log_response = requests.get(
            f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/1",
            headers=get_headers()
        )
        log_response.raise_for_status()
        log_text = log_response.text
        return log_text[-3000:] if len(log_text) > 3000 else log_text
    except Exception as e:
        return f"Could not fetch log: {e}"

# ─── Pool & Variable İşlemleri ───────────────────────────

def get_pools() -> list:
    response = requests.get(f"{AIRFLOW_BASE_URL}/pools", headers=get_headers())
    response.raise_for_status()
    return response.json().get("pools", [])

def get_variables() -> list:
    response = requests.get(f"{AIRFLOW_BASE_URL}/variables", headers=get_headers())
    response.raise_for_status()
    return response.json().get("variables", [])