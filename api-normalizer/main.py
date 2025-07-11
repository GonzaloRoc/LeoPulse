# main.py
import os
import time
import sqlite3
import logging
from datetime import datetime
from logging import Handler, LogRecord
from typing import List, Union

import numpy as np
from sklearn.ensemble import IsolationForest
from fastapi import (
    FastAPI, HTTPException, Query, Form, File, UploadFile, Request
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from pydantic import BaseModel
from stdnum import iban as std_iban
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# --- CONFIGURATION ---
DB_FILE = "/data/api_usage.db"
ALLOWED_ORIGINS = [
    "https://explorer.snelapi.nl",
    "https://www.snelapi.nl",
    "http://localhost:8000",
]

# --- DATABASE INIT ---
def init_db():
    # check_same_thread=False is important for SQLite with FastAPI
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            user_id TEXT,
            client_host TEXT,
            endpoint TEXT NOT NULL,
            status_code INTEGER,
            message TEXT,
            process_time FLOAT
        )
    """)
    conn.commit()
    conn.close()

# --- CUSTOM LOG HANDLER ---
class DatabaseLogHandler(Handler):
    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file

    def emit(self, record: LogRecord):
        if not getattr(record, 'db_log', False):
            return
        try:
            conn = sqlite3.connect(self.db_file, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO api_logs 
                   (timestamp, user_id, client_host, endpoint, status_code, message, process_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.utcnow(),
                    getattr(record, 'user_id', 'anonymous'),
                    getattr(record, 'client_host', 'unknown'),
                    getattr(record, 'endpoint', 'unknown'),
                    getattr(record, 'status_code', None),
                    record.getMessage(),
                    getattr(record, 'process_time', 0)
                )
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Logging error: {e}")

# --- LOGGER CONFIG ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(DatabaseLogHandler(DB_FILE))

# --- APP SETUP ---
app = FastAPI(title="LeoPulse API Normalizer", version="1.0.0", openapi_prefix="/v1")

@app.on_event("startup")
async def on_startup():
    logger.info("Starting application, initializing database...")
    init_db()
    logger.info("Database initialized.")

# --- MIDDLEWARE ---
# CORS Middleware MUST be first to handle preflight OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error(f"Unhandled exception in request: {e}", exc_info=True)
        response = Response(status_code=500, content="Internal Server Error")
        status_code = 500

    process_time = (time.time() - start_time) * 1000
    log_extra = {
        "user_id": "anonymous", # TODO: Replace with actual user identification
        "client_host": request.client.host,
        "endpoint": request.url.path,
        "status_code": status_code,
        "process_time": round(process_time, 2),
        "db_log": True
    }
    logger.info(f"{request.method} {request.url.path} -> {status_code}", extra=log_extra)
    return response

# --- API MODELS ---
class MetricRequest(BaseModel):
    value1: float
    value2: float

class AnomalyRequest(BaseModel):
    values: List[float]
    contamination: Union[float, str] = "auto"

# --- ROUTES ---
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.post("/normalizer/addmetrics")
def add_metrics(data: MetricRequest):
    return {"result": data.value1 + data.value2}

@app.get("/iban/validate")
def validate_iban(code: str = Query(..., description="IBAN to validate")):
    try:
        compacted = std_iban.compact(code)
        valid = std_iban.is_valid(compacted)
        return {
            "iban": code,
            "formatted": std_iban.format(compacted),
            "valid": valid
        }
    except Exception as e:
        logger.error(f"IBAN validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid IBAN: {e}")

@app.get("/kvk/validate")
def validate_kvk(number: str = Query(..., description="KvK number")):
    try:
        num = number.replace(" ", "").strip()
        if len(num) == 8 and num.isdigit():
            return {"kvk": number, "formatted": num, "valid": True}
        raise ValueError("KvK number must be exactly 8 digits.")
    except Exception as e:
        logger.error(f"KvK validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid KvK number: {e}")

@app.post("/contact")
async def contact_form(
    name: str = Form(...),
    company: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    message: str = Form(...),
    plan: str = Form(...),
    contract: UploadFile = File(None)
):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        logger.critical("Missing email configuration")
        raise HTTPException(status_code=500, detail="Email service not configured.")

    try:
        smtp_port = int(smtp_port)
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = smtp_user
        msg['Subject'] = f"Contact Request from {name}"

        body = f"""
        Name: {name}
        Company: {company}
        Email: {email}
        Phone: {phone}
        Plan: {plan}

        Message:
        {message}
        """
        msg.attach(MIMEText(body, 'plain'))

        if contract:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(await contract.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={contract.filename}')
            msg.attach(part)

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send email.")

    return {"status": "success", "detail": "Message sent successfully."}

@app.post("/anomaly/detect")
def detect_anomalies(req: AnomalyRequest):
    if not req.values:
        raise HTTPException(status_code=400, detail="Values cannot be empty.")

    try:
        X = np.array(req.values).reshape(-1, 1)
        model = IsolationForest(contamination=req.contamination, random_state=42)
        preds = model.fit_predict(X)
        anomalies = [req.values[i] for i, p in enumerate(preds) if p == -1]
        return {"original_values": req.values, "anomalies_detected": anomalies}
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Anomaly detection failed.")

@app.get("/account/logs")
def get_user_logs():
    user_id = "anonymous" # TODO: Add real authentication
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, endpoint, status_code, message, process_time
            FROM api_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT 100
        """, (user_id,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Log retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve logs.")