<a id="top"></a>

<div align="center">
<h1>🕶️ ShadowNet Cyber Labs</h1>
  <p><strong>A local-only, banking-themed web security lab for ethical practice.</strong></p>
  <p>Explore intentionally vulnerable challenge flows, submit flags, and track learning progress in a self-hosted Flask app.</p>
  <p>
    <a href="#quick-start">Get started</a> ·
    <a href="#features">Explore features</a> ·
    <a href="#support">Get support</a>
  </p>
  <p>
    <a href="https://github.com/uzankhan/ShadowNet-Cyber-Lab/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/uzankhan/ShadowNet-Cyber-Lab?style=flat-square"></a>
    <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white">
    <img alt="Flask 3.1.3" src="https://img.shields.io/badge/Flask-3.1.3-000000?style=flat-square&logo=flask&logoColor=white">
  </p>
</div>


[!WARNING]
ShadowNet is intentionally vulnerable. Run it only on your own machine or in an isolated lab. Do not deploy it to the public internet or a shared network. The project includes intentionally unsafe routes and demo secrets/flags. Use synthetic data, never reuse demo values, and do not test systems without authorization.

<a id="quick-navigation"></a>

🧭 Quick Navigation

Start
Learn
Features
Docs
Support
Quick Start
How it works
Features
Docs index


GitHub Issues




<a id="demo"></a>

🎬 Demo

No screenshot or banner asset is included in the repository yet. Add these when you have a safe local instance to capture:

•
docs/assets/shadownet-banner.png — 1600 × 480 px; a dark, cyber-lab themed banner with an abstract banking dashboard. Do not include readable credentials, tokens, or flags.

•
docs/screenshots/shadownet-challenges.png — 1600 × 900 px; the local challenge overview and progress UI, with all secret values hidden or blurred.

<a id="why-this-project"></a>

💡 Why this project?

Practice need
What ShadowNet provides
Security concepts can feel detached from real app flows.
A banking-inspired interface places exercises in account, profile, transaction, and admin-style routes.
Learners need a clear place to begin.
The challenge page lists 15 challenge cards and offers in-app hints.
Progress is easy to lose between exercises.
Flag submission and progress views are wired to per-session tracking after the database is seeded.
A lab should be easy to run without deploying it.
The Python app defaults to loopback; the Compose setup publishes only on host 127.0.0.1.




<a id="features"></a>

✨ Features

Area
What is included
🧩 Challenge catalog
15 listed exercises covering reflected XSS, IDOR, open redirect, SQL injection, command injection, local file inclusion, SSRF, crypto failure, XXE, race conditions, CSRF, SSTI, deserialization, secret exposure, and logic flaws.
🏦 Banking-style flows
Account, profile, transaction, transfer, report, and admin-themed routes provide context for the exercises.
🏁 Flags and hints
Submit discovered flags through the shared flag bar and request challenge hints from the challenge page.
📈 Progress
Session-oriented progress and attempt hooks use SQLite tables created by the seed script.
🗃️ Seed data
scripts/seed_db.py creates the lab database and generates local challenge flag files.
🐳 Local Docker option
Compose keeps the host binding on loopback and creates a fresh disposable database/flag set when the container starts.
🔒 Safe defaults
UNSAFE_MODE defaults to off. Keep it off unless you are deliberately evaluating the gated demo routes in an isolated environment.




<a id="how-it-works"></a>

🧭 How it works

mermaid

Source



A learner opens a page rendered by the Flask routes in app.py. The templates provide the challenge UI, while static/ supplies the shared stylesheet and browser-side JavaScript. API routes accept form or JSON requests and return page data or JSON responses. The seed script prepares SQLite tables and local challenge data before a session begins. In Docker mode, the entrypoint seeds the container and starts the app. The Compose port is exposed only on the host loopback interface.

<a id="quick-start"></a>

🚀 Quick Start

The quickest route is Python 3.11 in a disposable local checkout. Seeding writes a database and generated challenge files into the checkout, so avoid running it in a working copy that contains data you need to keep.

Step 1 — Clone and enter the repository

Bash


git clone --branch main https://github.com/uzankhan/ShadowNet-Cyber-Lab.git
cd ShadowNet-Cyber-Lab



Step 2 — Install dependencies and seed the lab

Bash


python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/seed_db.py



On Windows PowerShell, activate the environment with \.venv\Scripts\Activate.ps1 and use python for the remaining commands.

Step 3 — Start the local server

Bash


python app.py



Verify it works

The terminal should report the local address. Open 

http://127.0.0.1:5000, then visit the challenge list. Stop the server with Ctrl+C.


[!NOTE]
The Python entry point defaults to 127.0.0.1. Do not change that bind address to a public interface for a live or shared deployment.

<a id="detailed-installation"></a>

📦 Detailed installation

Method
Prerequisites
Start command
Data behavior
Local Python
Python 3.11 recommended; requirements.txt pins Flask 3.1.3
Run the three Quick Start steps above.
Seeding updates shadownet.db and generated files under vault/secret/ in that checkout.
Docker Compose
Docker Engine with the Compose plugin; no minimum Compose version is pinned in the repository
docker compose up --build
The container is disposable and force-seeds on each start. The repository is not bind-mounted, so generated data stays inside the container.




To stop and remove the local container:

Bash


docker compose down



The Compose service binds the host port to 127.0.0.1:5000 and uses 0.0.0.0 only inside the container network. Its generated flags and progress are temporary; restarting the service reseeds them.

<a id="configuration"></a>

⚙️ Configuration

There is no .env.example. Local Python mode needs no environment configuration. The following variables are read by the app or Docker entrypoint/configuration:

Variable
Required
Default / Compose value
Purpose
FLASK_HOST
No
127.0.0.1 locally; 0.0.0.0 inside Compose
Selects the Flask listen interface. Compose separately restricts the published host port to loopback.
UNSAFE_MODE
No
0
Gates particularly dangerous demonstration routes. Leave disabled outside a disposable, isolated lab.
FORCE_SEED
No
Seed only if the database is missing; Compose sets 1
Makes the Docker entrypoint regenerate the database and flags on startup. This resets container progress.
FLASK_ENV
No
development in the Docker image/config
Set by the Docker configuration; app.py does not read it directly.




Do not put real credentials or API keys into the lab. Do not copy secret values from the challenge implementation into documentation, screenshots, or issue reports.

<a id="usage-examples"></a>

🧪 Usage examples

Request a hint for a listed challenge:

Bash


curl --fail --silent http://127.0.0.1:5000/api/hint/xss



Submit a flag that you found in your own local lab session. Replace the placeholder with your own discovered value; it is not a project credential:

Bash


curl --fail --silent \
  -X POST http://127.0.0.1:5000/api/submit \
  -H 'Content-Type: application/json' \
  -d '{"flag":"YOUR_DISCOVERED_FLAG"}'



The transaction memo page is available at 

http://127.0.0.1:5000/challenges/transactions after seeding. Use only synthetic account IDs, user IDs, amounts, and memo text.

<a id="project-structure"></a>

🗂️ Project structure

Plain Text


ShadowNet-Cyber-Lab/
├── app.py                    # Flask routes, challenge logic, and local server entry point
├── index.html                # Standalone page; Flask home route uses templates/index.html
├── requirements.txt          # Flask dependency pin
├── shadownet.db              # SQLite database snapshot; reseed before use
├── Dockerfile                # Python 3.11 slim image
├── docker-compose.yml        # Loopback-only disposable local container
├── docker/
│   └── entrypoint.sh         # Seed-if-needed and start the Flask app
├── docs/
│   └── INSTRUCTOR.md         # Instructor notes
├── scripts/
│   └── seed_db.py            # Creates database tables and local flag files
├── static/
│   ├── css/style.css         # Shared interface styles
│   └── js/app.js             # Browser interactions and flag submission
├── templates/                # Flask/Jinja pages for home, challenges, and admin flows
└── vault/
    ├── public/               # Public sample files used by the lab
    └── secret/               # Generated challenge data; do not publish its contents



<a id="tech-stack"></a>

🛠️ Tech stack

Layer
Technology
Server
Python 3.11 runtime in the Docker image
Web framework
Flask 3.1.3
Templates and UI
Jinja templates, HTML, CSS, and browser JavaScript
Database
SQLite via Python's sqlite3 module
Container workflow
Dockerfile and Docker Compose




<a id="api-and-route-reference"></a>

🔌 API and route reference

These are application routes, not a production API contract. They are part of an intentionally vulnerable training lab.

Method
Route
Role
GET
/, /about, /contact, /challenges, /progress, /admin, /admin/preview
Home, information, challenge list, progress, and admin-themed pages.
GET
/challenges/xss, /challenges/idor, /challenges/redirect, /challenges/sqli, /challenges/cmdinj, /challenges/lfi, /challenges/ssrf, /challenges/crypto, /challenges/xxe, /challenges/race, /challenges/csrf, /challenges/ssti, /challenges/deser, /challenges/secret, /challenges/logic
The 15 pages linked by the challenge catalog.
GET
/challenges/transactions
Transaction memo demonstration page.
POST
/api/submit
Submit a discovered challenge flag.
GET
/api/hint/<flag_id>
Request a challenge hint.
POST
/api/tx/create
Create a synthetic transaction entry.
GET
/api/profile/<int:user_id>
Profile demonstration route.
POST
/api/login, /api/search
Login and search challenge flows.
POST
/api/ping, /api/generate_report
Network/report demonstration flows.
GET
/api/file, /internal/metadata
File and internal-metadata demo routes.
POST
/api/fetch, /api/parsexml
Fetch and XML-import demonstrations.
POST
/api/redeem, /api/redeem/reset
Coupon state and reset routes.
GET, POST
/api/transfer
Transfer demonstration route.
POST
/api/transfer/reset
Reset the transfer demonstration state.
POST
/api/setprefs
Set preference demonstration data.
GET
/api/getprefs
Read preference demonstration data.
POST
/api/admin/import
Admin import demonstration route.
GET
/api/admin/panel
Admin API demonstration route.
POST
/api/checkout
Checkout/business-logic demonstration route.
GET
/redirect
Redirect demonstration route.




<a id="testing-and-quality"></a>

✅ Testing and quality

The repository does not include an automated test suite or CI workflow. These commands perform syntax/configuration checks; they do not start the vulnerable application:

Bash


python3 -m py_compile app.py scripts/seed_db.py
docker compose config



The Flask app itself was not started as part of this README update. Test any future runtime changes only in a disposable, isolated environment.

<a id="faq-and-troubleshooting"></a>

❓ FAQ and troubleshooting

<details>
<summary><strong>The home page loads, but challenges or progress look empty.</strong></summary>

Run python scripts/seed_db.py before starting local Python mode. Docker Compose force-seeds its disposable container on each start.

</details> <details>
<summary><strong>Why does Docker recreate flags or reset progress?</strong></summary>

The Compose configuration sets FORCE_SEED=1 so the container has the required database schema. Each container start creates fresh challenge data, and the container is intentionally not backed by a host volume.

</details> <details>
<summary><strong>Can I access the app from another device?</strong></summary>

No. The app is intentionally configured for local-only use. Compose publishes on 127.0.0.1; do not change the binding or forward the port to a shared or public network.

</details> <details>
<summary><strong>What does <code>UNSAFE_MODE</code> do?</strong></summary>

It gates particularly dangerous demo routes and defaults to off. Keep it disabled unless you are deliberately testing the lab in an isolated, disposable environment.

</details> <details>
<summary><strong>Why does seeding modify files in my checkout?</strong></summary>

Local Python seeding writes shadownet.db and generated files under vault/secret/. Use a disposable clone and review git status before committing anything.

</details> <details>
<summary><strong>Port 5000 is already in use. What can I do?</strong></summary>

Stop the other local service before using Python mode. For Docker, change only the host-side port in docker-compose.yml, for example from 127.0.0.1:5000:5000 to 127.0.0.1:5001:5000, then open http://127.0.0.1:5001.

</details> <details>
<summary><strong>Can I deploy this on a public server?</strong></summary>

No. This repository intentionally contains vulnerable code and secret-like training data. Keep it local and use only systems you own or are explicitly authorized to test.

</details>

<a id="roadmap"></a>

🗺️ Roadmap

No official roadmap is published in the repository. The following are suggestions, not committed work:

•
Add a small smoke-test suite for page rendering, seeding, and route availability.

•
Add the redacted local screenshots listed in the Demo section.

•
Add a LICENSE file and expand the instructor notes before inviting broader reuse.

<a id="contributing"></a>

🤝 Contributing

There is no CONTRIBUTING.md yet. A practical contribution flow is:

1.
Fork the repository and create a focused branch.

2.
Keep all testing local and use synthetic values only.

3.
Run the syntax and Compose checks above; note that no automated test suite is currently provided.

4.
Do not commit generated database or secret-flag contents. Open a pull request describing the change and how it was checked.

<a id="docs"></a>

📚 Docs

•
Instructor notes

•
Flask routes and challenge logic

•
Database and flag seeding

•
Docker Compose configuration

•
Container entrypoint

<a id="acknowledgments"></a>

🙏 Acknowledgments

The existing project credits Uzan Khan. This README preserves the project attribution and documents the current default-branch implementation.

<a id="license"></a>

📄 License

No LICENSE file is present in the repository, and GitHub reports no declared license. Reuse terms are therefore unspecified; add the intended license before redistributing the project.

<a id="support"></a>

💬 Support

For questions or project issues, use 

GitHub Issues.

<p align="center"><a href="#top">Back to top</a></p> <div align="center"><sub>ShadowNet Cyber Labs · Local, offline, educational use only</sub></div>

