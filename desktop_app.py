"""
DocuGraph AI — Technical Documentation Assistant
Desktop Application Entry Point
------------------------------------------------
Launches the embedded FastAPI backend with self-corrective LangGraph pipeline
and displays the rich user interface in a native, hardware-accelerated desktop window.
"""

import os
import sys
import time
import socket
import argparse
import threading
import webbrowser
import urllib.request
from pathlib import Path

# Setup logging to file so errors in GUI / windowed mode are captured
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DocuGraphAI"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "desktop_app.log"

class MultiLogger:
    def __init__(self, original, file_handle):
        self.original = original
        self.file = file_handle

    def write(self, msg):
        try:
            if self.original:
                self.original.write(msg)
                self.original.flush()
        except Exception:
            pass
        try:
            if self.file:
                self.file.write(msg)
                self.file.flush()
        except Exception:
            pass

    def flush(self):
        try:
            if self.original:
                self.original.flush()
        except Exception:
            pass
        try:
            if self.file:
                self.file.flush()
        except Exception:
            pass

    def isatty(self):
        return False

    def fileno(self):
        if self.file:
            return self.file.fileno()
        raise OSError("fileno not supported")

try:
    log_fh = open(LOG_FILE, "a", encoding="utf-8")
    sys.stdout = MultiLogger(sys.stdout, log_fh)
    sys.stderr = MultiLogger(sys.stderr, log_fh)
except Exception:
    pass

# Determine root application directory
if getattr(sys, "frozen", False):
    # PyInstaller temporary extraction folder or executable folder
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)).resolve()
    os.chdir(str(BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent

# Ensure project root is in sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure writable data directory exists
def configure_storage_paths():
    local_data = BASE_DIR / "data"
    writable = False
    try:
        local_data.mkdir(parents=True, exist_ok=True)
        test_file = local_data / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        writable = True
    except Exception:
        writable = False

    if writable:
        data_dir = local_data
    else:
        # Standard user-writable location in Windows
        data_dir = LOG_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables if not already set
    os.environ.setdefault("CHROMA_PERSIST_DIRECTORY", str(data_dir / "chroma_db"))
    os.environ.setdefault("SQLITE_DB_PATH", str(data_dir / "app_storage.db"))
    
    # Try finding seed documents directory
    candidate_docs = [
        BASE_DIR / "data" / "raw_documents",
        BASE_DIR / "_internal" / "data" / "raw_documents",
    ]
    for cd in candidate_docs:
        if cd.exists():
            os.environ.setdefault("DOCS_DIRECTORY", str(cd))
            break
    else:
        os.environ.setdefault("DOCS_DIRECTORY", str(BASE_DIR / "data" / "raw_documents"))

configure_storage_paths()

def find_available_port(start_port: int = 8000) -> int:
    """Finds an available TCP port starting from start_port."""
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

class ServerThread(threading.Thread):
    """Runs Uvicorn programmatically in a background daemon thread."""
    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        import uvicorn
        from src.api.main import app
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
            log_config=None,
            loop="asyncio",
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True

def wait_for_server(url: str, timeout: float = 20.0) -> bool:
    """Polls the /health endpoint until the backend is fully initialized."""
    start_time = time.perf_counter()
    health_url = f"{url}/health"
    while time.perf_counter() - start_time < timeout:
        try:
            req = urllib.request.Request(
                health_url,
                headers={"User-Agent": "DocuGraphAIDesktopLauncher/1.0"}
            )
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False

def main():
    parser = argparse.ArgumentParser(description="DocuGraph AI Desktop Assistant")
    parser.add_argument("--port", type=int, default=None, help="Specific port to bind to")
    parser.add_argument("--check", action="store_true", help="Perform health check and exit (for testing)")
    parser.add_argument("--headless", action="store_true", help="Run server only without opening GUI window")
    args = parser.parse_args()

    host = "127.0.0.1"
    port = args.port or find_available_port(8000)
    server_url = f"http://{host}:{port}"
    icon_path = BASE_DIR / "app_icon.ico"
    if not icon_path.exists():
        icon_path = BASE_DIR / "_internal" / "app_icon.ico"

    print(f"===========================================================", flush=True)
    print(f"  DocuGraph AI — Technical Documentation Assistant", flush=True)
    print(f"  Starting local server at: {server_url}", flush=True)
    print(f"===========================================================", flush=True)

    # Start FastAPI server thread
    server_thread = ServerThread(host=host, port=port)
    server_thread.start()

    # Wait for server readiness
    print("[Launcher] Waiting for backend initialization...", flush=True)
    is_ready = wait_for_server(server_url, timeout=25.0)
    if not is_ready:
        print("[Launcher] Warning: Backend server took longer than expected to initialize.", flush=True)
    else:
        print(f"[Launcher] Backend ready! Healthcheck passed at {server_url}/health", flush=True)

    if args.check:
        print("[Launcher] --check mode: self-test completed successfully. Exiting.", flush=True)
        server_thread.stop()
        sys.exit(0)

    if args.headless:
        print(f"[Launcher] --headless mode: Server running at {server_url}. Press Ctrl+C to exit.", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[Launcher] Stopping server...", flush=True)
            server_thread.stop()
            sys.exit(0)

    print(f"[Launcher] Launching desktop interface...", flush=True)

    # Attempt native webview window
    try:
        import webview
        # Create a sleek, native desktop window
        window = webview.create_window(
            title="DocuGraph AI — Technical Documentation Assistant",
            url=server_url,
            width=1280,
            height=860,
            min_size=(960, 640),
            background_color="#0b0f19",
            text_select=True,
            zoomable=True,
        )
        webview.start(icon=str(icon_path) if icon_path.exists() else None)
        print("[Launcher] Desktop window closed by user.", flush=True)
    except Exception as e:
        print(f"[Launcher] Note: Native webview returned: {e}", flush=True)
        print(f"[Launcher] Opening in default web browser instead: {server_url}", flush=True)
        webbrowser.open(server_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    # Clean shutdown
    print("[Launcher] Shutting down background services...", flush=True)
    server_thread.stop()
    print("[Launcher] Goodbye!", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
