# Run locally / Replit


1. Create Replit (Python). Paste tree above.
2. Add `requirements.txt` and install.
3. Add `.env` from `.env.example`.
4. `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Open the webview → you should see live simulated telemetry and controls.