#!/usr/bin/env python3
# ShadowNet Cyber Labs
# Made by Uzan Khan (ID: 468675)
#
# ⚠️  INTENTIONALLY VULNERABLE APPLICATION — FOR AUTHORIZED, OFFLINE, EDUCATIONAL USE ONLY.
# Every bug in this file is on purpose. Do not deploy this on a public server or a
# network you do not fully control. Run it locally (127.0.0.1) for coursework only.

import base64
import hashlib
import os
import pickle
import re
import sqlite3
import subprocess
import threading
import time
import urllib.request
import urllib.parse
from flask import (
    Flask, request, session, redirect, jsonify, render_template,
    render_template_string, make_response, g
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PUBLIC = os.path.join(BASE_DIR, "vault", "public")
VAULT_SECRET = os.path.join(BASE_DIR, "vault", "secret")

app = Flask(__name__)
app.config["SECRET_KEY"] = "shadownet-dev-secret-key-do-not-use-in-prod"
# Deliberately exposed for the SSTI challenge (leaking app.config via {{ config }})
app.config["FLAG_SSTI"] = "SHADOWNET{ssti_c0nfig_l3ak_1s_r3al}"

# Gate very dangerous endpoints behind this env var. Default: OFF
UNSAFE_MODE = os.getenv("UNSAFE_MODE", "0") == "1"

# ---------------------------------------------------------------------------
# "Database" — per the brief: no real DB, just files / sessions / arrays.
# ---------------------------------------------------------------------------

FLAGS = [
    {"id": "xss",       "name": "Reflected XSS",              "value": "SHADOWNET{xss_r3fl3ct3d_c00ki3_th3ft}"},
    {"id": "idor",       "name": "IDOR",                       "value": "SHADOWNET{1d0r_us3r_z3r0_1s_4dm1n}"},
    {"id": "redirect",   "name": "Open Redirect",              "value": "SHADOWNET{0p3n_r3d1r3ct_ph1sh1ng_r3ady}"},
    {"id": "sqli",       "name": "SQL Injection",              "value": "SHADOWNET{sql1_or_1_equ4ls_1_4lw4ys}"},
    {"id": "cmdinj",     "name": "Command Injection",          "value": "SHADOWNET{c0mm4nd_1nj3ct10n_sh3ll_p0wn3d}"},
    {"id": "lfi",        "name": "Local File Inclusion",       "value": "SHADOWNET{lf1_d0t_d0t_sl4sh_tr4v3rs4l}"},
    {"id": "ssrf",       "name": "SSRF",                       "value": "SHADOWNET{ssrf_1nt3rn4l_m3t4d4t4_l34k}"},
    {"id": "crypto",     "name": "Crypto Fail",                "value": "SHADOWNET{l4y3r3d_crypt0_1s_n0t_s3cur1ty}"},
    {"id": "xxe",        "name": "XXE",                        "value": "SHADOWNET{xxe_3xt3rn4l_3nt1ty_r3ad_f1l3}"},
    {"id": "race",       "name": "Race Condition",             "value": "SHADOWNET{r4c3_c0nd1t10n_d0ubl3_r3d33m}"},
    {"id": "csrf",       "name": "CSRF",                       "value": "SHADOWNET{csrf_n0_t0k3n_n0_pr0bl3m}"},
    {"id": "ssti",       "name": "Server-Side Template Injection", "value": app.config["FLAG_SSTI"]},
    {"id": "deser",      "name": "Insecure Deserialization",   "value": "SHADOWNET{3v4l_1s_ev1l_d3s3r14l1z4t10n}"},
    {"id": "secret",     "name": "Hardcoded Secret",           "value": "SHADOWNET{h4rdc0d3d_4p1_k3y_1n_js}"},
    {"id": "logic",      "name": "Business Logic / Price Tamper", "value": "SHADOWNET{pr1c3_t4mp3r1ng_ch3ck0ut_byp4ss}"},
]
FLAG_BY_ID = {f["id"]: f for f in FLAGS}
VALID_FLAG_VALUES = {f["value"]: f["id"] for f in FLAGS}

HINTS = {
    "xss": "The greeting page echoes your name back into the HTML. What else might it echo? A cookie named 'flag_xss' is set but never printed to the page...",
    "idor": "You're logged in as user id=1. The profile API trusts whatever id you send it. What does user 0 look like?",
    "redirect": "The /redirect endpoint sends people wherever ?url= says, no questions asked. Where does it refuse to send you? Nowhere.",
    "sqli": "The login query is built with plain string formatting. Classic quote-and-comment tricks still work in 2026.",
    "cmdinj": "The network-diagnostic tool builds a shell command out of your input. Shells understand ; | && more than one command at a time.",
    "lfi": "The file viewer only ever meant to serve vault/public/*. Path separators are just characters to a naive join().",
    "ssrf": "Something inside the network can only be reached from inside the network... unless you can make the server ask on your behalf.",
    "crypto": "Open devtools. Check the console and the page source. The flag went through ROT13, then Base64, then a single-byte XOR — in that order.",
    "xxe": "The XML importer resolves external entities. DOCTYPE + ENTITY + SYSTEM is a classic combo.",
    "race": "One coupon, one redemption — that's the rule, enforced with a check, a deliberate delay, then a decrement. Fire requests fast enough and the check goes stale.",
    "csrf": "The transfer endpoint changes state on a plain GET/POST with no token, no origin check, and no confirmation.",
    "ssti": "The greeting page renders your name AS a template, not just INTO one. Curly braces might do more than display text.",
    "deser": "Preferences are packed into a cookie and unpacked with a very powerful Python builtin. What else can that builtin evaluate?",
    "secret": "Not every secret lives on the server. Sometimes it ships to the browser in a JS file, 'temporarily', months ago.",
    "logic": "Checkout trusts the price the client sends it instead of looking the price up itself. What happens if you disagree with the price?",
}

# In-memory "users table" — used by the real SQLite DB below (SQLi target)
DB_PATH = os.path.join(BASE_DIR, "shadownet.db")

# Only initialize the embedded DB if it doesn't exist; the seed script will create it.
def init_db():
    if os.path.exists(DB_PATH):
        # DB already exists (created by scripts/seed_db.py or previous run) — keep it
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        role TEXT,
        note TEXT
    )""")
    cur.executemany(
        "INSERT INTO users (id, username, password, role, note) VALUES (?, ?, ?, ?, ?)",
        [
            (0, "admin", "S4dm1n_p@ss_2026!", "admin", FLAG_BY_ID["sqli"]["value"]),
            (1, "uzan", "hacktheplanet", "user", "just a regular user"),
            (2, "guest", "guest123", "user", "welcome to shadownet"),
        ],
    )
    conn.commit()
    conn.close()

init_db()

# DB helper
def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def record_progress(session_id, challenge_id):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO progress (session_id, challenge) VALUES (?, ?)', (str(session_id), challenge_id))
        conn.commit()
        conn.close()
    except Exception:
        # be forgiving in the demo app
        pass

def record_attempt(session_id, route, payload):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO attempts (session_id, route, payload) VALUES (?, ?, ?)', (str(session_id), route, str(payload)))
        conn.commit()
        conn.close()
    except Exception:
        pass

# In-memory IDOR "user profiles"
PROFILES = {
    0: {"id": 0, "username": "admin", "role": "admin", "private_note": FLAG_BY_ID["idor"]["value"]},
    1: {"id": 1, "username": "uzan_dev", "role": "user", "private_note": "nothing to see here"},
}

# Coupon state for the race-condition challenge
coupon_lock_demo = {"uses_left": 1, "redemptions": 0}
race_flag_awarded = {"done": False}

# Secret vault files for LFI / XXE
os.makedirs(VAULT_SECRET, exist_ok=True)
with open(os.path.join(VAULT_SECRET, "flag_lfi.txt"), "w") as fh:
    fh.write(FLAG_BY_ID["lfi"]["value"] + "\n")
with open(os.path.join(VAULT_SECRET, "flag_xxe.txt"), "w") as fh:
    fh.write(FLAG_BY_ID["xxe"]["value"] + "\n")
with open(os.path.join(VAULT_SECRET, "flag_cmdinj.txt"), "w") as fh:
    fh.write(FLAG_BY_ID["cmdinj"]["value"] + "\n")

# Fake "internal metadata" service for the SSRF challenge
INTERNAL_METADATA = {
    "instance": "shadownet-internal-01",
    "role": "service-account",
    "flag": FLAG_BY_ID["ssrf"]["value"],
}

ADMIN_API_KEY = "sk_live_sh4d0wn3t_4dm1n_9f81c2"  # also hardcoded in static/js/app.js on purpose

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def captured():
    return session.get("captured", [])

def mark_captured(flag_id):
    caps = session.get("captured", [])
    if flag_id not in caps:
        caps.append(flag_id)
        session["captured"] = caps

def xor_bytes(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)

def rot13(s: str) -> str:
    return s.encode("rot13").decode() if False else __import__("codecs").encode(s, "rot13")

# ---------------------------------------------------------------------------
# Core pages
# ---------------------------------------------------------------------------

@app.before_request
def setup_session():
    if "captured" not in session:
        session["captured"] = []
    # demo login: everyone browsing the site is auto "logged in" as uzan_dev (id=1)
    if "uid" not in session:
        session["uid"] = 1
    # initialize points for hints/score
    if "points" not in session:
        session["points"] = 100

@app.after_request
def plant_cookies(resp):
    if not request.cookies.get("flag_xss"):
        resp.set_cookie("flag_xss", FLAG_BY_ID["xss"]["value"], httponly=False, samesite="Lax")
    return resp

@app.context_processor
def inject_progress():
    return {"captured": captured(), "flags": FLAGS, "points": session.get("points", 0)}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/challenges")
def challenges():
    admin_unlocked = request.headers.get("User-Agent", "") == "AdminBot"
    return render_template(
        "challenges.html",
        flags=FLAGS,
        captured=captured(),
        admin_unlocked=admin_unlocked,
    )

@app.route("/progress")
def progress():
    caps = captured()
    return render_template("progress.html", flags=FLAGS, captured=caps, total=len(FLAGS))

@app.route("/api/submit", methods=["POST"])
def submit_flag():
    data = request.get_json(silent=True) or request.form
    submitted = (data.get("flag") or "").strip()
    if submitted in VALID_FLAG_VALUES:
        fid = VALID_FLAG_VALUES[submitted]
        already = fid in captured()
        mark_captured(fid)
        # Record progress in the DB for instructor visibility
        try:
            record_progress(session.get("uid", "anon"), fid)
        except Exception:
            pass
        return jsonify({
            "correct": True,
            "already_captured": already,
            "challenge": FLAG_BY_ID[fid]["name"],
            "total_captured": len(captured()),
            "total": len(FLAGS),
        })
    return jsonify({"correct": False})

@app.route("/api/hint/<flag_id>")
def get_hint(flag_id):
    # tier param (1,2,3) increases hint detail and costs points
    try:
        tier = int(request.args.get("tier", "1"))
    except ValueError:
        tier = 1
    costs = {1: 5, 2: 15, 3: 30}
    cost = costs.get(tier, 5)
    available = session.get("points", 0)
    if available < cost:
        return jsonify({"error": "not enough points", "points": available}), 402
    session["points"] = available - cost
    # record hint usage
    try:
        record_attempt(session.get("uid", "anon"), f"/api/hint/{flag_id}", {"tier": tier})
    except Exception:
        pass
    base = HINTS.get(flag_id, "No hint available.")
    # expand hint detail for higher tiers (technical nudges only)
    if tier == 1:
        hint = base
    elif tier == 2:
        hint = base + " [HINT LEVEL 2 — check network logs and server-side behaviors.]"
    else:
        hint = base + " [HINT LEVEL 3 — look at server-side code paths and internal services referenced by the routes.]"
    return jsonify({"hint": hint, "points": session["points"]})

# ---------------------------------------------------------------------------
# 1. Reflected XSS
# ---------------------------------------------------------------------------

@app.route("/challenges/xss")
def chal_xss():
    name = request.args.get("name", "")
    # VULNERABLE: user input rendered directly into HTML, no escaping (|safe)
    return render_template("xss.html", name=name)

# ---------------------------------------------------------------------------
# XSS: stored memo demo — transactions
# ---------------------------------------------------------------------------

@app.route("/challenges/transactions")
def transactions_page():
    # read simple transactions table from SQLite
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, account_id, amount, memo, created_at FROM transactions ORDER BY created_at DESC')
        txs = [dict(r) for r in cur.fetchall()]
    except Exception:
        txs = []
    conn.close()
    return render_template('transactions.html', transactions=txs)

@app.route("/api/tx/create", methods=["POST"])
def api_tx_create():
    data = request.get_json(silent=True) or request.form
    account_id = int(data.get('account_id', 1))
    amount = int(data.get('amount', 0))
    memo = data.get('memo', '')
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO transactions (account_id, amount, memo) VALUES (?, ?, ?)', (account_id, amount, memo))
        conn.commit()
        conn.close()
        # record attempt
        record_attempt(session.get('uid', 'anon'), '/api/tx/create', {'memo': memo})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ---------------------------------------------------------------------------
# 2. IDOR
# ---------------------------------------------------------------------------

@app.route("/challenges/idor")
def chal_idor_page():
    return render_template("idor.html", my_id=session.get("uid", 1))

@app.route("/api/profile/<int:user_id>")
def api_profile(user_id):
    # VULNERABLE: no check that user_id belongs to the logged-in session user
    profile = PROFILES.get(user_id)
    if not profile:
        return jsonify({"error": "not found"}), 404
    return jsonify(profile)

# ---------------------------------------------------------------------------
# 3. Open Redirect
# ---------------------------------------------------------------------------

@app.route("/challenges/redirect")
def chal_redirect_page():
    return render_template("redirect.html")

@app.route("/redirect")
def open_redirect():
    url = request.args.get("url", "/")
    # VULNERABLE: no allowlist / same-origin check on redirect target
    parsed = urllib.parse.urlparse(url)
    is_external = bool(parsed.netloc) and parsed.netloc not in (request.host,)
    body = f"<p>Redirecting you to <code>{url}</code>...</p>"
    if is_external:
        body += f"<!-- unrestricted open redirect confirmed: {FLAG_BY_ID['redirect']['value']} -->"
    resp = make_response(body)
    resp.headers["Location"] = url
    resp.status_code = 302
    return resp

# ---------------------------------------------------------------------------
# 4. SQL Injection
# ---------------------------------------------------------------------------

@app.route("/challenges/sqli")
def chal_sqli_page():
    return render_template("sqli.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form
    username = data.get("username", "")
    password = data.get("password", "")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # VULNERABLE: raw string formatting straight into SQL
    query = f"SELECT id, username, role, note FROM users WHERE username = '{username}' AND password = '{password}'"
    try:
        cur.execute(query)
        row = cur.fetchone()
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"success": False, "error": str(e), "query_used": query}), 400
    conn.close()
    if row:
        return jsonify({
            "success": True,
            "user": {"id": row[0], "username": row[1], "role": row[2], "note": row[3]},
            "query_used": query,
        })
    return jsonify({"success": False, "query_used": query})

@app.route("/api/search", methods=["POST"])
def api_search():
    # Legacy admin search endpoint (vulnerable to SQL injection)
    data = request.get_json(silent=True) or request.form
    q = data.get("q", "")
    conn = get_db_conn()
    cur = conn.cursor()
    # VULNERABLE: constructing SQL with string interpolation; intended for teaching
    query = f"SELECT id, username, role, note FROM users WHERE username LIKE '%{q}%'"
    # record the raw query as an attempt for instructor review
    record_attempt(session.get("uid", "anon"), "/api/search", query)
    try:
        cur.execute(query)
        rows = [dict(r) for r in cur.fetchall()]
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": str(e), "query_used": query}), 400
    conn.close()
    return jsonify({"results": rows, "query_used": query})

# ---------------------------------------------------------------------------
# 5. Command Injection
# ---------------------------------------------------------------------------

@app.route("/challenges/cmdinj")
def chal_cmdinj_page():
    return render_template("cmdinj.html")

@app.route("/api/ping", methods=["POST"])
def api_ping():
    data = request.get_json(silent=True) or request.form
    host = data.get("host", "127.0.0.1")
    # VULNERABLE: user input concatenated into a shell command with shell=True
    cmd = f"echo Checking host: {host}"
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        output = output.decode(errors="replace")
    except subprocess.CalledProcessError as e:
        output = e.output.decode(errors="replace")
    except Exception as e:
        output = str(e)
    # record attempt
    record_attempt(session.get("uid", "anon"), "/api/ping", {"host": host})
    return jsonify({"output": output, "command_used": cmd})

# Add a report generator demonstrating command injection (gated by UNSAFE_MODE)
@app.route("/api/generate_report", methods=["POST"])
def api_generate_report():
    if not UNSAFE_MODE:
        return jsonify({"error": "report generation is disabled (UNSAFE_MODE=0)"}), 403
    data = request.get_json(silent=True) or request.form
    filename = data.get('filename', 'report.txt')
    # VULNERABLE: naive concatenation into shell command
    cmd = f"/bin/echo Generating report for {filename} && /bin/ls -l {filename}"
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        output = output.decode(errors="replace")
    except subprocess.CalledProcessError as e:
        output = e.output.decode(errors="replace")
    except Exception as e:
        output = str(e)
    record_attempt(session.get("uid", "anon"), "/api/generate_report", {"cmd": cmd})
    return jsonify({"output": output, "command_used": cmd})

# ---------------------------------------------------------------------------
# 6. LFI
# ---------------------------------------------------------------------------

@app.route("/challenges/lfi")
def chal_lfi_page():
    return render_template("lfi.html")

@app.route("/api/file")
def api_file():
    name = request.args.get("name", "welcome.txt")
    # VULNERABLE: naive path join, no sanitization of ../
    path = os.path.join(VAULT_PUBLIC, name)
    try:
        with open(path, "r", errors="replace") as fh:
            content = fh.read()
        return jsonify({"path_used": path, "content": content})
    except Exception as e:
        return jsonify({"path_used": path, "error": str(e)}), 404

# ---------------------------------------------------------------------------
# 7. SSRF
# ---------------------------------------------------------------------------

@app.route("/challenges/ssrf")
def chal_ssrf_page():
    return render_template("ssrf.html")

@app.route("/internal/metadata")
def internal_metadata():
    # simulated internal-only service — not linked anywhere in the UI
    return jsonify(INTERNAL_METADATA)

@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    data = request.get_json(silent=True) or request.form
    url = data.get("url", "")
    # VULNERABLE: server fetches ANY url the client supplies, including internal ones
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ShadowNet-Fetcher/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read(4000).decode(errors="replace")
        record_attempt(session.get("uid", "anon"), "/api/fetch", {"url": url})
        return jsonify({"url_fetched": url, "body": body})
    except Exception as e:
        return jsonify({"url_fetched": url, "error": str(e)}), 400

# ---------------------------------------------------------------------------
# 8. Crypto Fail
# ---------------------------------------------------------------------------

@app.route("/challenges/crypto")
def chal_crypto_page():
    raw = FLAG_BY_ID["crypto"]["value"]
    step1 = __import__("codecs").encode(raw, "rot13")          # rot13
    step2 = base64.b64encode(step1.encode()).decode()            # base64
    key = 0x2A
    step3 = xor_bytes(step2.encode(), key).hex()                 # xor -> hex
    return render_template("crypto.html", encoded=step3, xor_key=hex(key))

# ---------------------------------------------------------------------------
# 9. XXE (simulated minimal parser — real XML libs patch this by default)
# ---------------------------------------------------------------------------

@app.route("/challenges/xxe")
def chal_xxe_page():
    return render_template("xxe.html")

@app.route("/api/parsexml", methods=["POST"])
def api_parsexml():
    xml_body = request.get_data(as_text=True) or ""
    # VULNERABLE (simulated): manually resolves <!ENTITY name SYSTEM "file://..."> and &name;
    entities = {}
    for m in re.finditer(r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"([^"]+)"\s*>', xml_body):
        ent_name, uri = m.group(1), m.group(2)
        content = ""
        if uri.startswith("file://"):
            file_path = uri[len("file://"):]
            try:
                with open(file_path, "r", errors="replace") as fh:
                    content = fh.read()
            except Exception as e:
                content = f"[error reading {file_path}: {e}]"
        entities[ent_name] = content

    def replace_entity(match):
        name = match.group(1)
        return entities.get(name, match.group(0))

    resolved = re.sub(r"&(\w+);", replace_entity, xml_body)
    text_match = re.search(r"<data>(.*?)</data>", resolved, re.DOTALL)
    parsed_value = text_match.group(1).strip() if text_match else resolved.strip()
    return jsonify({"parsed": parsed_value})

# ---------------------------------------------------------------------------
# 10. Race Condition
# ---------------------------------------------------------------------------

@app.route("/challenges/race")
def chal_race_page():
    return render_template("race.html", uses_left=coupon_lock_demo["uses_left"])

@app.route("/api/redeem", methods=["POST"])
def api_redeem():
    # VULNERABLE: check-then-act with a deliberate delay, no locking
    if coupon_lock_demo["uses_left"] > 0:
        time.sleep(1.0)  # widens the race window on purpose
        coupon_lock_demo["uses_left"] -= 1
        coupon_lock_demo["redemptions"] += 1
        result = {"redeemed": True, "redemptions_so_far": coupon_lock_demo["redemptions"]}
        if coupon_lock_demo["redemptions"] > 1 and not race_flag_awarded["done"]:
            race_flag_awarded["done"] = True
            result["flag"] = FLAG_BY_ID["race"]["value"]
        record_attempt(session.get("uid", "anon"), "/api/redeem", {"action": "redeem"})
        return jsonify(result)
    return jsonify({"redeemed": False, "redemptions_so_far": coupon_lock_demo["redemptions"]})

@app.route("/api/redeem/reset", methods=["POST"])
def api_redeem_reset():
    coupon_lock_demo["uses_left"] = 1
    coupon_lock_demo["redemptions"] = 0
    race_flag_awarded["done"] = False
    return jsonify({"reset": True})

# ---------------------------------------------------------------------------
# 11. CSRF
# ---------------------------------------------------------------------------

BALANCES = {"uzan_dev": 1000, "flaghunter": 0}

@app.route("/challenges/csrf")
def chal_csrf_page():
    return render_template("csrf.html", balances=BALANCES)

@app.route("/api/transfer", methods=["GET", "POST"])
def api_transfer():
    # VULNERABLE: state-changing action, no CSRF token, no origin check, GET allowed
    to = request.values.get("to", "")
    amount = int(request.values.get("amount", 0) or 0)
    if to in BALANCES and 0 < amount <= BALANCES["uzan_dev"]:
        BALANCES["uzan_dev"] -= amount
        BALANCES[to] += amount
        result = {"success": True, "balances": BALANCES}
        if to == "flaghunter" and BALANCES["flaghunter"] >= 500:
            result["flag"] = FLAG_BY_ID["csrf"]["value"]
        record_attempt(session.get("uid", "anon"), "/api/transfer", {"to": to, "amount": amount})
        return jsonify(result)
    return jsonify({"success": False, "balances": BALANCES})

@app.route("/api/transfer/reset", methods=["POST"])
def api_transfer_reset():
    BALANCES["uzan_dev"] = 1000
    BALANCES["flaghunter"] = 0
    return jsonify({"reset": True})

# ---------------------------------------------------------------------------
# 12. SSTI
# ---------------------------------------------------------------------------

@app.route("/challenges/ssti")
def chal_ssti_page():
    name = request.args.get("name", "")
    if name:
        try:
            # VULNERABLE: user input rendered AS a Jinja2 template, not passed as data
            rendered = render_template_string(f"Hello, {name}!")
        except Exception as e:
            rendered = f"[template error: {e}]"
    else:
        rendered = ""
    return render_template("ssti.html", rendered=rendered, raw_name=name)

# Admin preview page (statement/email preview)
@app.route("/admin/preview")
def admin_preview():
    template = request.values.get('template') or request.args.get('template')
    user = {"full_name": "Uzan Khan", "balance": "$1,234.56", "account": "ACCT10001"}
    rendered = None
    if template:
        try:
            # Intentionally render the template with user context — SSTI demo
            rendered = render_template_string(template, user=user)
            record_attempt(session.get("uid", "anon"), "/admin/preview", {"template": template})
        except Exception as e:
            rendered = f"[template error: {e}]"
    return render_template('preview.html', rendered=rendered)

# ---------------------------------------------------------------------------
# 13. Insecure Deserialization (eval-based, simulating unsafe unpickling)
# ---------------------------------------------------------------------------

@app.route("/challenges/deser")
def chal_deser_page():
    current = request.cookies.get("prefs", "")
    decoded_preview = ""
    if current:
        try:
            decoded_preview = base64.b64decode(current).decode(errors="replace")
        except Exception:
            decoded_preview = "[invalid encoding]"
    return render_template("deser.html", decoded_preview=decoded_preview)

@app.route("/api/setprefs", methods=["POST"])
def api_setprefs():
    data = request.get_json(silent=True) or request.form
    raw = data.get("prefs", "{'theme': 'dark'}")
    encoded = base64.b64encode(raw.encode()).decode()
    resp = jsonify({"stored": True})
    resp.set_cookie("prefs", encoded, samesite="Lax")
    return resp

@app.route("/api/getprefs")
def api_getprefs():
    cookie_val = request.cookies.get("prefs", "")
    output = None
    error = None
    try:
        raw = base64.b64decode(cookie_val).decode()
        # VULNERABLE: eval() on attacker-controlled, "deserialized" data
        output = repr(eval(raw))
    except Exception as e:
        error = str(e)
    record_attempt(session.get("uid", "anon"), "/api/getprefs", {"cookie": cookie_val})
    return jsonify({"output": output, "error": error})

# Admin import endpoint demonstrating insecure operations (gated by UNSAFE_MODE)
@app.route("/api/admin/import", methods=["POST"])
def api_admin_import():
    payload = (request.form.get('payload') or request.data.decode() or '').strip()
    # payload should be base64-encoded
    if not payload:
        return jsonify({"error": "no payload provided"}), 400
    try:
        raw = base64.b64decode(payload).decode(errors='replace')
    except Exception as e:
        return jsonify({"error": f"invalid base64: {e}"}), 400
    record_attempt(session.get("uid", "anon"), "/api/admin/import", {"payload": raw[:200]})
    if not UNSAFE_MODE:
        return jsonify({"status": "unsafe import disabled (UNSAFE_MODE=0)", "preview": raw[:400]})
    # UNSAFE: eval() the payload — intentionally dangerous for demo
    try:
        result = eval(raw)
        return jsonify({"status": "imported", "result": repr(result)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ---------------------------------------------------------------------------
# 14. Hardcoded Secret
# ---------------------------------------------------------------------------

@app.route("/challenges/secret")
def chal_secret_page():
    return render_template("secret.html")

@app.route("/api/admin/panel")
def api_admin_panel():
    key = request.headers.get("X-Api-Key", "")
    # VULNERABLE: the "secret" key is shipped to the client in static/js/app.js
    if key == ADMIN_API_KEY:
        record_attempt(session.get("uid", "anon"), "/api/admin/panel", {"used_key": key[:8]})
        return jsonify({"access": "granted", "flag": FLAG_BY_ID["secret"]["value"]})
    return jsonify({"access": "denied"}), 403

# ---------------------------------------------------------------------------
# 15. Business Logic / Price Manipulation
# ---------------------------------------------------------------------------

CATALOG = {
    "voucher": {"name": "Admin Access Voucher", "server_price": 999.99},
    "sticker": {"name": "ShadowNet Sticker Pack", "server_price": 4.99},
}

@app.route("/challenges/logic")
def chal_logic_page():
    return render_template("logic.html", catalog=CATALOG)

@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    data = request.get_json(silent=True) or request.form
    item_id = data.get("item_id", "")
    client_price = data.get("price", None)
    item = CATALOG.get(item_id)
    if not item:
        return jsonify({"success": False, "error": "unknown item"}), 404
    # VULNERABLE: trusts the client-supplied price instead of item['server_price']
    charged = float(client_price) if client_price is not None else item["server_price"]
    result = {"success": True, "item": item["name"], "charged": charged}
    if item_id == "voucher" and charged < item["server_price"]:
        result["flag"] = FLAG_BY_ID["logic"]["value"]
    record_attempt(session.get("uid", "anon"), "/api/checkout", {"item_id": item_id, "charged": charged})
    return jsonify(result)

# ---------------------------------------------------------------------------
# Hidden admin panel — User-Agent gated, per the original brief
# ---------------------------------------------------------------------------

@app.route("/admin")
def admin_panel():
    if request.headers.get("User-Agent", "") != "AdminBot":
        return render_template("admin_denied.html"), 403
    return render_template("admin.html", flags=FLAGS)

if __name__ == "__main__":
    print("=" * 60)
    print(" ShadowNet Cyber Labs — starting on http://127.0.0.1:5000")
    print(" Made by Uzan Khan | ID 468675")
    print(" For local, offline, educational use only.")
    print("UNSAFE_MODE=", UNSAFE_MODE)
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
