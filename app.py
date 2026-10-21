"""BEL Machine Lakehouse Flask application.

Reads the project's local sensor CSV files, provides dashboard APIs,
per-machine reports, CSV exports, and admin-only user management.
Sensor thresholds below are illustrative demo thresholds, not validated
operating limits for real BEL equipment.
"""

from __future__ import annotations

import io
import math
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from auth import auth as auth_blueprint, login_required, role_required

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
app.config["SECRET_KEY"] = os.getenv("BEL_SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "BEL_SECRET_KEY is missing. Add BEL_SECRET_KEY=<your secret> to the .env file in the project root."
    )

# Register the authentication routes, e.g. /login and /logout.
app.register_blueprint(auth_blueprint)

# Prefer Silver cleaned data; fall back to raw sensor data if needed.
SILVER_FILE = BASE_DIR / "data" / "silver" / "machine_sensor_data.csv"
RAW_FILE = BASE_DIR / "data" / "machine_sensor_data.csv"
GOLD_FILE = BASE_DIR / "data" / "gold" / "machine_health_summary.csv"

REQUIRED_COLUMNS = ["timestamp", "machine_id", "temperature", "vibration", "pressure"]


def get_data() -> pd.DataFrame:
    """Load the best available sensor CSV and normalize its columns."""
    source = SILVER_FILE if SILVER_FILE.exists() else RAW_FILE
    if not source.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    try:
        df = pd.read_csv(source)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        app.logger.exception("Could not read sensor data from %s", source)
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Accept common column-name variations from exported CSV files.
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    aliases = {
        "machine": "machine_id",
        "machineid": "machine_id",
        "time": "timestamp",
        "datetime": "timestamp",
        "temp": "temperature",
        "vibration_level": "vibration",
        "pressure_level": "pressure",
    }
    df = df.rename(columns={col: aliases[col] for col in df.columns if col in aliases})

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    for col in ("temperature", "vibration", "pressure"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["machine_id"] = df["machine_id"].astype("string").str.strip()
    df["timestamp"] = df["timestamp"].astype("string")
    df = df.dropna(subset=["machine_id"])
    df = df[df["machine_id"].str.len().fillna(0) > 0]
    return df


def status_for_row(row: pd.Series) -> str:
    """Classify one reading using illustrative demo thresholds."""
    values = []
    for column in ("temperature", "vibration", "pressure"):
        try:
            value = float(row.get(column))
        except (TypeError, ValueError):
            return "CHECK_REQUIRED"
        if not math.isfinite(value):
            return "CHECK_REQUIRED"
        values.append(value)

    temperature, vibration, pressure = values

    # Critical thresholds are demo-only and must be validated by equipment specialists.
    if temperature > 85 or vibration > 7 or pressure < 4 or pressure > 7:
        return "CHECK_REQUIRED"

    # A softer monitoring band avoids flagging every mildly unusual reading as critical.
    if temperature > 75 or temperature < 30 or vibration > 5:
        return "MONITOR"

    return "NORMAL"


def serialize_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to JSON-safe dictionaries."""
    if df.empty:
        return []
    clean = df.astype(object).where(pd.notna(df), None)
    return clean.to_dict(orient="records")


def machine_ids(df: pd.DataFrame) -> list[str]:
    if "machine_id" not in df.columns:
        return []
    return sorted(df["machine_id"].dropna().astype(str).unique().tolist())


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/dashboard")
@login_required
def dashboard_api():
    df = get_data()
    if df.empty:
        return jsonify({
            "ready": False,
            "message": "No sensor data found. Check data/silver/machine_sensor_data.csv or data/machine_sensor_data.csv.",
            "machines": [], "records": [], "summary": [], "alerts": [],
            "metric_series": [], "total_readings": 0, "machines_monitored": 0,
            "alert_count": 0, "normal_count": 0,
        })

    machine_filter = request.args.get("machine", "all").strip()
    metric = request.args.get("metric", "temperature").strip()
    if metric not in {"temperature", "vibration", "pressure"}:
        metric = "temperature"

    machines = machine_ids(df)
    view = df.copy()
    if machine_filter != "all":
        view = view[view["machine_id"].astype(str) == machine_filter].copy()

    if view.empty:
        return jsonify({
            "ready": True, "updated_at": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
            "machines": machines, "selected_machine": machine_filter, "metric": metric,
            "total_readings": 0, "machines_monitored": 0, "alerts": [], "alert_count": 0,
            "normal_count": 0, "summary": [], "records": [], "metric_series": [],
        })

    view["machine_status"] = view.apply(status_for_row, axis=1)
    summary = []
    for machine in machines:
        mdf = df[df["machine_id"].astype(str) == machine].copy()
        statuses = mdf.apply(status_for_row, axis=1)
        critical_count = int((statuses == "CHECK_REQUIRED").sum())
        monitor_count = int((statuses == "MONITOR").sum())
        normal_count = int((statuses == "NORMAL").sum())
        alert_pct = round(critical_count / len(mdf) * 100, 1) if len(mdf) else 0.0
        avg = {}
        for col in ("temperature", "vibration", "pressure"):
            vals = pd.to_numeric(mdf[col], errors="coerce").dropna()
            avg[f"avg_{col}"] = round(float(vals.mean()), 2) if len(vals) else None
        machine_health = "REVIEW REQUIRED" if critical_count else ("MONITOR" if monitor_count else "NORMAL")
        summary.append({
            "machine_id": machine, "readings": int(len(mdf)),
            **avg, "alerts": critical_count, "alert_pct": alert_pct,
            "monitor_count": monitor_count, "normal_count": normal_count, "status": machine_health,
        })

    alert_df = view[view["machine_status"] == "CHECK_REQUIRED"].copy()
    if "timestamp" in alert_df.columns:
        alert_df = alert_df.sort_values("timestamp", ascending=False)
    recent = view.copy()
    if "timestamp" in recent.columns:
        recent = recent.sort_values("timestamp", ascending=False)
    metric_series = []
    for _, row in view.iterrows():
        val = pd.to_numeric(pd.Series([row.get(metric)]), errors="coerce").iloc[0]
        metric_series.append({
            "timestamp": str(row.get("timestamp", "")),
            "machine_id": str(row.get("machine_id", "")),
            "value": float(val) if pd.notna(val) else None,
            "status": row.get("machine_status", "NORMAL"),
        })

    return jsonify({
        "ready": True,
        "updated_at": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
        "machines": machines, "selected_machine": machine_filter, "metric": metric,
        "total_readings": int(len(view)),
        "machines_monitored": int(view["machine_id"].nunique()),
        "alerts": serialize_records(alert_df.tail(100)),
        "alert_count": int((view["machine_status"] == "CHECK_REQUIRED").sum()),
        "monitor_count": int((view["machine_status"] == "MONITOR").sum()),
        "normal_count": int((view["machine_status"] == "NORMAL").sum()),
        "summary": summary,
        "records": serialize_records(recent.tail(500)),
        "metric_series": metric_series,
        "threshold_note": "Illustrative demo thresholds only; confirm real operating limits with equipment specialists.",
    })


@app.route("/api/export.csv")
@role_required("Admin", "Maintenance Engineer")
def export_csv():
    df = get_data()
    if df.empty:
        return jsonify({"error": "No dataset available to export."}), 404
    machine = request.args.get("machine", "all").strip()
    if machine != "all":
        df = df[df["machine_id"].astype(str) == machine]
    df = df.copy()
    df["machine_status"] = df.apply(status_for_row, axis=1)
    return app.response_class(
        df.to_csv(index=False), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=machine_health_data.csv"},
    )


@app.route("/api/report")
@login_required
def machine_report_api():
    machine = request.args.get("machine", "").strip()
    start_date = request.args.get("start", "").strip()
    end_date = request.args.get("end", "").strip()
    df = get_data()
    if df.empty or not machine or machine not in set(df["machine_id"].dropna().astype(str)):
        return jsonify({"error": "Choose a valid machine with available data."}), 400

    view = df[df["machine_id"].astype(str) == machine].copy()
    if "timestamp" in view.columns:
        dates = pd.to_datetime(view["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d")
        if start_date:
            view = view[dates >= start_date]
            dates = pd.to_datetime(view["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d")
        if end_date:
            view = view[dates <= end_date]
    if view.empty:
        return jsonify({"error": "No readings found for this machine/date range."}), 404

    view["machine_status"] = view.apply(status_for_row, axis=1)
    critical = view[view["machine_status"] == "CHECK_REQUIRED"]
    stats = {}
    for col in ("temperature", "vibration", "pressure"):
        vals = pd.to_numeric(view[col], errors="coerce").dropna()
        stats[col] = {
            "average": round(float(vals.mean()), 2) if len(vals) else None,
            "minimum": round(float(vals.min()), 2) if len(vals) else None,
            "maximum": round(float(vals.max()), 2) if len(vals) else None,
            "valid_readings": int(len(vals)),
        }
    alert_pct = round(len(critical) / len(view) * 100, 1)
    latest = view.sort_values("timestamp", ascending=False) if "timestamp" in view.columns else view
    status_counts = view["machine_status"].value_counts().to_dict()
    return jsonify({
        "machine_id": machine, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_from": start_date or "All available dates", "date_to": end_date or "Latest available",
        "total_readings": int(len(view)), "flagged_readings": int(len(critical)),
        "normal_readings": int(status_counts.get("NORMAL", 0)),
        "monitor_readings": int(status_counts.get("MONITOR", 0)),
        "flagged_percentage": alert_pct,
        "status": "REVIEW REQUIRED" if len(critical) else ("MONITOR" if status_counts.get("MONITOR", 0) else "NORMAL"),
        "stats": stats,
        "recent_flagged": serialize_records(latest[latest["machine_status"] == "CHECK_REQUIRED"].head(20)),
        "readings": serialize_records(latest.head(100)),
        "threshold_note": "Illustrative demo rules only; validate thresholds with equipment specialists before real use.",
    })


@app.route("/api/report.csv")
@role_required("Admin", "Maintenance Engineer")
def machine_report_csv():
    machine = request.args.get("machine", "").strip()
    df = get_data()
    if df.empty or not machine:
        return jsonify({"error": "Choose a machine with available data."}), 400
    df = df[df["machine_id"].astype(str) == machine].copy()
    if df.empty:
        return jsonify({"error": "No data found for this machine."}), 404
    df["machine_status"] = df.apply(status_for_row, axis=1)
    for key in ("start", "end"):
        date_value = request.args.get(key, "").strip()
        if date_value and "timestamp" in df.columns:
            dates = pd.to_datetime(df["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df[dates >= date_value] if key == "start" else df[dates <= date_value]
    return app.response_class(
        df.to_csv(index=False), mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{machine}_health_report.csv"'},
    )


@app.route("/api/settings/users", methods=["GET", "POST"])
@role_required("Admin")
def settings_users_api():
    """Admin-only account management; uses the existing auth module database."""
    import sqlite3
    from auth import DATABASE, ROLES, create_user

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))
        role = str(payload.get("role", ""))
        try:
            create_user(username, password, role)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except sqlite3.IntegrityError:
            return jsonify({"error": "That username already exists."}), 409
        return jsonify({"message": f"User {username} created.", "username": username, "role": role}), 201

    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, username, role, active, created_at FROM users ORDER BY id"
        ).fetchall()
    return jsonify({"users": [dict(row) for row in rows], "roles": sorted(ROLES)})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.getenv("PORT", "5000"))
    url = f"http://{host}:{port}/login"

    # Open the browser after the local server has had time to start.
    Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"Starting BEL Machine Lakehouse at {url}", flush=True)
    app.run(host=host, port=port, debug=False, use_reloader=False)
