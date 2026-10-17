"""
run_dashboard.py

Single-command launcher for the Bengaluru Traffic Coordination Center Dashboard.
Starts the FastAPI backend and automatically opens the live interactive dashboard
in your default web browser at http://127.0.0.1:8000/.
"""

import sys
import time
import webbrowser
import threading
import uvicorn

HOST = "127.0.0.1"
PORT = 8000
DASHBOARD_URL = f"http://{HOST}:{PORT}/"


def open_browser():
    """Waits for Uvicorn to initialize and opens the browser."""
    time.sleep(1.5)
    print(f"\n[Dashboard Launcher] Opening live dashboard at: {DASHBOARD_URL}\n")
    webbrowser.open(DASHBOARD_URL)


def main():
    print("=" * 72)
    print("  BENGALURU SMART TRAFFIC COORDINATION CENTER")
    print("  Silk Board Multi-Intersection Adaptive Control Platform")
    print("=" * 72)
    print(f"  * Web Dashboard URL : {DASHBOARD_URL}")
    print(f"  * Interactive Docs   : http://{HOST}:{PORT}/docs")
    print(f"  * WebSocket Stream   : ws://{HOST}:{PORT}/ws/traffic")
    print("=" * 72)
    print("  Starting backend server... Press Ctrl+C to exit.\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch Uvicorn
    try:
        uvicorn.run(
            "backend.main:app",
            host=HOST,
            port=PORT,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n[Dashboard Launcher] Shutting down gracefully. Goodbye!")


if __name__ == "__main__":
    main()
