# ShadowNet Cyber Labs

Made by **Uzan Khan** 

An offline, self-contained, intentionally vulnerable web application built for
hands-on ethical hacking practice — 15 real, working vulnerabilities, no
tutorials, no difficulty labels. Find the flag, submit it, watch the counter
climb.

> ⚠️ **Run this locally only.** Every route in this app is deliberately
> insecure (SQL injection, command injection, XXE, SSRF, etc.). Do **not**
> deploy it to a public server or any shared/untrusted network. Keep it on
> `127.0.0.1`.

## Setup

Requires Python 3.9+.

```bash
git clone https://github.com/uzankhan/ShadowNet-Cyber-Lab
cd shadownet
pip install -r requirements.txt
python3 app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The app rebuilds its (tiny, file-based) state every time it starts — a fresh
SQLite users table, fresh vault files under `vault/secret/`, and a reset
coupon/balance state. Nothing persists between restarts except what's saved
in your browser's session cookie (which flags you've captured).

## How it works

- **No real database philosophy** — flags live in a plain Python list in
  `app.py`, "users" for the SQLi challenge are in a small local SQLite file
  regenerated on startup, and everything else is in-memory dictionaries or
  small text files under `vault/`.
- **Flag format:** `SHADOWNET{...}`
- **Submitting flags:** every page has a flag-submission bar pinned to the
  bottom. Paste a flag you've found and hit Submit — correct flags trigger
  the green victory popup and update your progress counter (top right nav).
- **Progress:** visit `/progress` any time to see which of the 15 you still
  need.
- **Hidden admin panel:** `/admin` only opens for requests whose
  `User-Agent` header is exactly `AdminBot` — e.g.
  `curl -A "AdminBot" http://127.0.0.1:5000/admin`. It doesn't hand out a
  flag directly; it's there to demonstrate how trivial a User-Agent check is
  to spoof.

## The 15 challenges

| # | Challenge | Route | Core bug |
|---|-----------|-------|----------|
| 1 | Reflected XSS | `/challenges/xss` | `?name=` rendered into HTML unescaped; flag sits in a non-httpOnly cookie only visible via JS |
| 2 | IDOR | `/challenges/idor` | `/api/profile/<id>` never checks the id belongs to the logged-in session |
| 3 | Open Redirect | `/challenges/redirect` | `/redirect?url=` forwards to any host, no allowlist |
| 4 | SQL Injection | `/challenges/sqli` | Login query built with raw string formatting |
| 5 | Command Injection | `/challenges/cmdinj` | Host input concatenated into a shell command (`shell=True`) |
| 6 | Local File Inclusion | `/challenges/lfi` | `?name=` path-joined with no traversal check |
| 7 | SSRF | `/challenges/ssrf` | Server fetches any client-supplied URL, including internal-only routes |
| 8 | Crypto Fail | `/challenges/crypto` | Flag encoded ROT13 → Base64 → XOR; layers ≠ security |
| 9 | XXE | `/challenges/xxe` | XML parser resolves `<!ENTITY ... SYSTEM "file://...">` |
| 10 | Race Condition | `/challenges/race` | Check-then-act coupon redemption with a deliberate delay, no locking |
| 11 | CSRF | `/challenges/csrf` | Fund transfer accepts plain GET, no token, no origin check |
| 12 | SSTI | `/challenges/ssti` | `?name=` rendered *as* a Jinja2 template, not passed as data |
| 13 | Insecure Deserialization | `/challenges/deser` | Cookie-stored prefs unpacked with `eval()` |
| 14 | Hardcoded Secret | `/challenges/secret` | Admin API key shipped in `static/js/app.js` |
| 15 | Business Logic / Price Tamper | `/challenges/logic` | Checkout trusts a client-supplied `price` field |

## Project structure

```
shadownet/
├── app.py                  # Flask app — all 15 vulnerable routes live here
├── requirements.txt
├── static/
│   ├── css/style.css       # dark red/black hacker theme, matrix rain, glassmorphism
│   └── js/app.js           # matrix canvas, flag submission, victory popup
│                            # (also where the hardcoded API key for #14 lives)
├── templates/               # one page per challenge + shared base.html
└── vault/
    ├── public/              # intended file-viewer root (LFI challenge)
    └── secret/              # LFI/XXE/command-injection targets — regenerated on start
```
---

## ⚡ Final Words

> *"The best way to learn security is to break it. The best way to master it is to build it. ShadowNet is my gift to the hacking community — a playground where curiosity meets code, and where every vulnerability is a lesson waiting to be learned."*

**So go ahead. Break it. Earn the flags. And when you're done, come back and break it again — because the real mastery is in the journey, not the destination.**

---

**Happy Hacking!** 🚀  
— **Uzan Khan**

---
