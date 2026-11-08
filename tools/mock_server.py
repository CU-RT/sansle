"""Serve the app locally against a fake account service, to test sign-in and sync without touching real accounts.

    python tools/mock_server.py            # then open http://localhost:8791

index.html and sw.js are served from the repo root with the Supabase address swapped for this server.
Test helpers (plain GET): /__state shows every saved row, /__confirm?e=<email> confirms an email,
/__offline?on and /__offline?off make the account calls fail like a dropped connection.
"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8791
API = "http://127.0.0.1:%d" % PORT
REAL = "https://mhdliqisvgbqktrztmhf.supabase.co"
TYPES = {".html": "text/html", ".js": "text/javascript", ".webmanifest": "application/json", ".png": "image/png"}
rows, tokens, people, confirmed, offline, n = {}, {}, {}, set(), {"on": False}, {"i": 0}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body=None):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if body is not None: self.wfile.write(json.dumps(body).encode())

    def do_OPTIONS(self): self.send(204)

    def user(self):
        return tokens.get(self.headers.get("Authorization", "").replace("Bearer ", ""))

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/__state": return self.send(200, rows)
        if path == "/__confirm": confirmed.add(self.path.split("=", 1)[1]); return self.send(200, {})
        if path == "/__offline": offline["on"] = self.path.endswith("on"); return self.send(200, offline)
        if path.startswith("/rest/v1/user_state"):
            if offline["on"]: return self.send(503, {})
            u = self.user()
            if not u: return self.send(401, {})
            r = rows.get(u)
            return self.send(200, [r] if r else [])
        f = os.path.join(ROOT, path.lstrip("/") or "index.html")
        if not os.path.isfile(f): return self.send(404, {})
        data = open(f, "rb").read()
        if f.endswith("index.html"): data = data.replace(REAL.encode(), API.encode())
        if f.endswith("sw.js"): data = data.replace(b'.endsWith(".supabase.co")', b' === "127.0.0.1"')
        self.send_response(200)
        self.send_header("Content-Type", TYPES.get(os.path.splitext(f)[1], "text/plain"))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or "{}")
        path = self.path.split("?")[0]
        if offline["on"]: return self.send(503, {})

        def grant(email):
            n["i"] += 1
            tok = "tok-%d" % n["i"]
            tokens[tok] = email
            return self.send(200, {"access_token": tok, "refresh_token": tok, "expires_in": 3600, "user": {"id": email, "email": email}})

        if path == "/auth/v1/signup":
            if body["email"] in confirmed: return self.send(200, {"id": "x", "email": body["email"], "identities": []})
            people[body["email"]] = body["password"]
            return self.send(200, {"id": body["email"], "email": body["email"], "identities": [{}]})
        if path == "/auth/v1/token":
            if "password" in self.path:
                if people.get(body.get("email")) != body.get("password"): return self.send(400, {"error_code": "invalid_credentials"})
                if body["email"] not in confirmed: return self.send(400, {"error_code": "email_not_confirmed"})
                return grant(body["email"])
            if body.get("refresh_token") in tokens: return grant(tokens[body["refresh_token"]])
            return self.send(400, {})
        if path == "/auth/v1/logout": return self.send(204)
        if path == "/rest/v1/rpc/save_state":
            u = self.user()
            if not u: return self.send(401, {})
            r = rows.get(u)
            if r and r["rev"] != body["p_rev"]: return self.send(200, None)
            rows[u] = {"data": body["p_data"], "rev": (r["rev"] + 1) if r else 1}
            return self.send(200, rows[u]["rev"])
        self.send(404, {})


print("sansle test server on http://localhost:%d" % PORT)
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
