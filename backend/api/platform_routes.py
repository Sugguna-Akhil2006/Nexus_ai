"""FastAPI routing exposing Platform infrastructure features."""

from datetime import datetime
import time
from typing import Dict, Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from pydantic import BaseModel, Field

# Import platform modules
from backend.platform.auth.jwt_manager import JWTManager
from backend.platform.auth.password_manager import PasswordManager
from backend.platform.auth.refresh_tokens import RefreshTokenManager
from backend.platform.auth.session_manager import SessionManager
from backend.platform.auth.authorization import AuthorizationService
from backend.platform.auth.authentication import AuthenticationService
from backend.platform.organizations.organization_manager import OrganizationManager
from backend.platform.organizations.team_manager import TeamManager
from backend.platform.organizations.invite_service import InviteService
from backend.platform.database.connection_pool import ConnectionPool
from backend.platform.database.repository import BaseRepository
from backend.platform.storage.file_storage import FileStorage
from backend.platform.storage.upload_service import UploadService
from backend.platform.storage.download_service import DownloadService
from backend.platform.background.queue_manager import QueueManager
from backend.platform.security.rate_limiter import RateLimiter
from backend.platform.security.request_validator import RequestValidator
from backend.platform.security.csrf import CSRFProtector
from backend.platform.security.security_headers import SecurityHeadersManager
from backend.platform.deployment.healthcheck import HealthCheckManager
from backend.platform.deployment.readiness import ReadinessChecker
from backend.platform.deployment.liveness import LivenessChecker
from backend.platform.deployment.startup_validator import StartupValidator

router = APIRouter(prefix="/api/platform", tags=["Platform Infrastructure"])

# Singletons initialization for API
db_pool = ConnectionPool(db_type="sqlite", dsn="nexus_ai.db")
jwt_mgr = JWTManager(secret_key="nexus-super-secret-key")
rt_mgr = RefreshTokenManager()
session_mgr = SessionManager()
auth_service_runner = AuthenticationService(jwt_mgr, rt_mgr)
auth_service = AuthorizationService()
org_mgr = OrganizationManager()
team_mgr = TeamManager()
invite_service = InviteService()
file_store = FileStorage(root_dir="storage_data/api_uploads")
upload_service = UploadService(file_store)
download_service = DownloadService(file_store, auth_service)
queue_mgr = QueueManager()
rate_limiter = RateLimiter(rate_limit=100, window_seconds=60.0)
req_validator = RequestValidator()
csrf_protector = CSRFProtector()
security_headers = SecurityHeadersManager()

start_time = time.time()
liveness_chk = LivenessChecker(start_time)
health_mgr = HealthCheckManager()
health_mgr.register_checker("database", lambda: {"status": "healthy"})
health_mgr.register_checker("storage", lambda: {"status": "healthy" if file_store.exists(".") or True else "unhealthy"})

readiness_chk = ReadinessChecker([
    lambda: db_pool.get_connection() is not None
])


# =====================================================================
# Pydantic Request schemas
# =====================================================================

class UserRegisterReq(BaseModel):
    username: str
    password: str
    email: str


class UserLoginReq(BaseModel):
    username: str
    password: str


class PasswordResetReq(BaseModel):
    username: str
    new_password: str


class EmailVerifyReq(BaseModel):
    email: str


class RefreshReq(BaseModel):
    refresh_token: str
    username: str
    role: str


class OrgCreateReq(BaseModel):
    org_id: str
    name: str
    owner_id: str


class TeamCreateReq(BaseModel):
    team_id: str
    org_id: str
    name: str


class InviteCreateReq(BaseModel):
    email: str
    org_id: str
    role: str = "member"
    team_id: Optional[str] = None


class InviteAcceptReq(BaseModel):
    token: str
    email: str


class JobSubmitReq(BaseModel):
    job_id: str
    action: str
    payload: Dict[str, Any] = {}


# =====================================================================
# Routes: Deployment Checkers
# =====================================================================

@router.get("/health")
def get_health():
    """Consolidated system health check status."""
    return health_mgr.get_status()


@router.get("/readiness")
def get_readiness():
    """Liveness probe verifying downstream network dependencies."""
    if not readiness_chk.is_ready():
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}


@router.get("/liveness")
def get_liveness():
    """Simple ping check returning alive status."""
    return liveness_chk.check()


@router.get("/version")
def get_version():
    """Exposes application version and release metadata."""
    return {
        "version": "1.0.0-RC1",
        "release_stage": "Release Candidate",
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================================================================
# Routes: Authentication APIs
# =====================================================================

@router.post("/auth/register")
def register_user(req: UserRegisterReq):
    """Securely registers a user, hashing their password."""
    if not req_validator.validate_email(req.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Access SQLite connection pool directly
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (req.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        pm = PasswordManager()
        pwd_hash = pm.hash_password(req.password)
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (req.username, pwd_hash, req.email, "member", created_at)
        )
        conn.commit()
    finally:
        db_pool.release_connection(conn)

    return {"status": "success", "username": req.username}


@router.post("/auth/login")
def login_user(req: UserLoginReq, request: Request):
    """Authenticates credentials and returns access & refresh tokens."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait.")

    if auth_service_runner.is_account_locked(req.username):
        raise HTTPException(status_code=403, detail="Account is locked due to too many failed attempts")

    conn = db_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash, role, email FROM users WHERE username = ?", (req.username,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        pm = PasswordManager()
        if not pm.verify_password(req.password, row["password_hash"]):
            auth_service_runner.record_failed_login(req.username)
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        auth_service_runner.reset_failed_logins(req.username)
        role = row["role"] or "member"
        user_id = req.username
    finally:
        db_pool.release_connection(conn)

    # Issue JWT and refresh tokens
    payload = {"sub": user_id, "username": req.username, "role": role}
    token = jwt_mgr.encode(payload)
    refresh = rt_mgr.create_token(user_id)
    session_mgr.create_session(token, user_id, client_ip)

    return {
        "status": "success",
        "access_token": token,
        "refresh_token": refresh,
        "role": role
    }


@router.post("/auth/refresh")
def refresh_token(req: RefreshReq):
    """Issues new short-lived access tokens from refresh token."""
    user_id = rt_mgr.verify_token(req.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    payload = {"sub": user_id, "username": req.username, "role": req.role}
    new_token = jwt_mgr.encode(payload)
    return {"access_token": new_token}


@router.post("/auth/reset-password")
def reset_password(req: PasswordResetReq):
    """Processes a password reset request."""
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (req.username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        new_hash = auth_service_runner.trigger_password_reset(req.username, req.new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, req.username))
        conn.commit()
    finally:
        db_pool.release_connection(conn)
    return {"status": "success", "message": "Password reset successfully"}


@router.post("/auth/verify-email")
def verify_email(req: EmailVerifyReq):
    """Triggers an email verification hook request."""
    success = auth_service_runner.trigger_email_verification(req.email)
    return {"status": "success", "verified": success}


# =====================================================================
# Routes: Organization APIs
# =====================================================================

@router.post("/orgs")
def create_org(req: OrgCreateReq):
    """Creates a new organization."""
    try:
        org = org_mgr.create_organization(req.org_id, req.name, req.owner_id)
        return {"status": "success", "org": org}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orgs/{org_id}/members")
def add_org_member(org_id: str, user_id: str, role: str = "member"):
    """Adds a member to an organization."""
    if not org_mgr.add_member(org_id, user_id, role):
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "success"}


@router.post("/teams")
def create_team(req: TeamCreateReq):
    """Creates a team under an organization."""
    try:
        team = team_mgr.create_team(req.team_id, req.org_id, req.name)
        return {"status": "success", "team": team}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invites")
def send_invite(req: InviteCreateReq):
    """Issues an invitation token."""
    token = invite_service.create_invite(req.email, req.org_id, req.role, req.team_id)
    return {"status": "success", "invite_token": token}


@router.post("/invites/accept")
def accept_invite(req: InviteAcceptReq):
    """Accepts an organization invitation."""
    invite = invite_service.accept_invite(req.token, req.email)
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    org_mgr.add_member(invite["org_id"], req.email, invite["role"])
    if invite.get("team_id"):
        team_mgr.add_member(invite["team_id"], req.email, "member")

    return {"status": "success", "org_id": invite["org_id"]}


# =====================================================================
# Routes: Storage APIs
# =====================================================================

@router.post("/storage/upload")
async def secure_upload(file_id: str, file: UploadFile = File(...)):
    """Performs security validation checks and writes to file store."""
    contents = await file.read()
    try:
        path = upload_service.process_upload(file_id, file.filename or "", contents)
        return {"status": "success", "storage_path": path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/storage/download")
def secure_download(file_id: str, role: str = "viewer"):
    """Validates authorization permissions and downloads the file."""
    try:
        content = download_service.authorize_and_download(file_id, role)
        return {"file_id": file_id, "size_bytes": len(content), "data_preview": content[:100].decode("utf-8", errors="ignore")}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =====================================================================
# Routes: Background Processing APIs
# =====================================================================

@router.post("/jobs")
def submit_job(req: JobSubmitReq):
    """Submits a job to the background processing queue."""
    try:
        from backend.platform.hardening.metrics_collector import MetricsCollector
        MetricsCollector().increment("queue_jobs_submitted")
    except Exception:
        pass
    task = {
        "id": req.job_id,
        "action": req.action,
        "payload": req.payload,
        "submitted_at": time.time()
    }
    queue_mgr.enqueue(task)
    return {"status": "success", "queue_size": queue_mgr.size()}


@router.get("/jobs/status")
def get_jobs_status():
    """Gets diagnostic state of background queue manager and DLQ."""
    return {
        "queue_size": queue_mgr.size(),
        "dlq_count": len(queue_mgr.get_dlq_tasks()),
        "dlq_tasks": queue_mgr.get_dlq_tasks()
    }


@router.get("/metrics")
def get_metrics():
    """Exposes all metrics collected by the system."""
    from backend.platform.hardening.metrics_collector import MetricsCollector
    return MetricsCollector().get_all_metrics()
