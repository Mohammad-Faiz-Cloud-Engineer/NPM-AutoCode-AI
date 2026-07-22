import json
import uuid
import threading
import time
import requests
from pathlib import Path
from typing import Callable, Optional

CONFIG_PATH = Path.home() / ".npmai_agent" / "supabase_config.json"


CONFIG_URL = "https://raw.githubusercontent.com/npmaiecosystem/NPM-AutoCode-AI/refs/heads/main/Desktop_App/app_config.json"

def load_config() -> dict:
    """Fetch latest config from GitHub (primary), fall back to bundled file."""
    bundled = Path(__file__).resolve().parent / "app_config.json"
    if bundled.exists():
        try:
            return json.loads(bundled.read_text())
        except Exception:
            pass
    try:
        response = requests.get(CONFIG_URL, timeout=8)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Failed to fetch remote config: {e}")
    return {}


def save_config(url: str, anon_key: str, mcp_base_url: str = None):
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    cfg = load_config()
    cfg["url"] = url
    cfg["anon_key"] = anon_key
    if mcp_base_url:
        cfg["mcp_base_url"] = mcp_base_url
    CONFIG_PATH.write_text(json.dumps(cfg))


class SupabaseAuthError(Exception):
    pass


class MCPLinkManager:
  
    JOBS_TABLE = "mcp_jobs"
    RESULTS_TABLE = "mcp_job_results"
    LINKS_TABLE = "mcp_links"

    def __init__(self, log_cb: Callable[[str], None] = None):
        self._log = log_cb or print
        self._client = None
        self._session = None
        self._listener_thread = None
        self._stop = threading.Event()
        from npmai_agents import Executor
        self._executor = Executor(log_cb=self._log)
      
    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from supabase import create_client
        except ImportError:
            raise SupabaseAuthError(
                "The 'supabase' package isn't installed. Run: pip install supabase"
            )
        cfg = load_config()
        if not cfg.get("url") or not cfg.get("anon_key"):
            raise SupabaseAuthError(
                "Supabase isn't configured yet. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "env vars, or call mcp_link.save_config(url, anon_key) once from Settings."
            )
        self._client = create_client(cfg["url"], cfg["anon_key"])
        return self._client

    def sign_up(self, email: str, password: str):
        client = self._get_client()
        res = client.auth.sign_up({"email": email, "password": password})
        if res.user is None:
            raise SupabaseAuthError("Sign-up failed — check the email/password and try again.")
        self._session = res.session
        return res.user

    def log_in(self, email: str, password: str):
        client = self._get_client()
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.user is None:
            raise SupabaseAuthError("Login failed — check your credentials.")
        self._session = res.session
        return res.user

    def log_out(self):
        self.stop_listener()
        if self._client:
            try:
                self._client.auth.sign_out()
            except Exception:
                pass
        self._session = None

    @property
    def is_logged_in(self) -> bool:
        return self._session is not None

    @property
    def user_id(self) -> Optional[str]:
        if self._session and getattr(self._session, "user", None):
            return self._session.user.id
        return None

    def get_or_create_link(self) -> str:
        if not self.user_id:
            raise SupabaseAuthError("Log in first — an MCP link can only be issued to a logged-in account.")
        client = self._get_client()
        existing = (
            client.table(self.LINKS_TABLE)
            .select("*")
            .eq("user_id", self.user_id)
            .eq("platform", "desktop")
            .execute()
        )
        if existing.data:
            token = existing.data[0]["token"]
        else:
            token = uuid.uuid4().hex
            client.table(self.LINKS_TABLE).insert({
                "user_id": self.user_id,
                "platform": "desktop",
                "token": token,
            }).execute()
        base = load_config().get("MCP_BASE_URL", "https://YOUR-HF-SPACE.hf.space/mcp")
        return f"{base}/{token}"

    def start_listener(self):
        if self._listener_thread and self._listener_thread.is_alive():
            return
        if not self.user_id:
            raise SupabaseAuthError("Log in first — the job bridge is scoped to a logged-in account.")
        self._stop.clear()
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()

    def stop_listener(self):
        self._stop.set()

    def _listen_loop(self):
        client = self._get_client()
        channel = client.channel(f"jobs-{self.user_id}")

        def _on_insert(payload):
            row = payload.get("record") or payload.get("new") or {}
            if row.get("user_id") != self.user_id:
                return
            self._handle_job(row)

        channel.on_postgres_changes(
            event="INSERT", schema="public", table=self.JOBS_TABLE,
            callback=_on_insert,
        )
        channel.subscribe()
        self._log("MCP link listener connected — waiting for jobs from your connected LLM.")
        try:
            while not self._stop.is_set():
                time.sleep(0.5)
        finally:
            try:
                channel.unsubscribe()
            except Exception:
                pass
            self._log("MCP link listener stopped.")

    def _handle_job(self, row: dict):
        job_id = row.get("id")
        code = row.get("code", "")
        self._log(f"Job {job_id} received — executing locally.")
        success, output = self._executor.run(code)
        client = self._get_client()
        client.table(self.RESULTS_TABLE).insert({
            "job_id": job_id,
            "user_id": self.user_id,
            "success": success,
            "output": output,
        }).execute()
        self._log(f"Job {job_id} {'completed' if success else 'failed'} — result sent back.")
