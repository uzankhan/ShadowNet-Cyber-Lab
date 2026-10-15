#!/usr/bin/env python3
"""
Seed script for ShadowNet banking persona.
Generates randomized flags in vault/secret/ and creates a simple SQLite DB schema used by the app.
Run this before starting the app to refresh flags and sample data.
"""

import os
import sqlite3
import secrets
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT_SECRET = ROOT / 'vault' / 'secret'
DB_PATH = ROOT / 'shadownet.db'

def rand_flag():
    token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    return f"SHADOWNET{{{token}}}"

def ensure_dirs():
    VAULT_SECRET.mkdir(parents=True, exist_ok=True)

def write_flags():
    # Clear existing secret files except .gitkeep
    for p in VAULT_SECRET.glob('flag_*.txt'):
        try:
            p.unlink()
        except Exception:
            pass

    flags = {
        'flag_sqli.txt': rand_flag(),
        'flag_lfi.txt': rand_flag(),
        'flag_xxe.txt': rand_flag(),
        'flag_cmdinj.txt': rand_flag(),
        'flag_xss.txt': rand_flag(),
        'flag_ssrf.txt': rand_flag(),
    }
    for name, val in flags.items():
        (VAULT_SECRET / name).write_text(val)
    print(f"Wrote {len(flags)} flags to {VAULT_SECRET}")
    return flags

def create_db():
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except Exception:
            pass

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # simple users and accounts
    cur.executescript('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        full_name TEXT
    );

    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        account_number TEXT UNIQUE,
        balance INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        amount INTEGER,
        memo TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    );

    CREATE TABLE progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        challenge TEXT,
        found_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        route TEXT,
        payload TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # seed sample users
    users = [
        ('alice', 'alicepass', 'Alice M.'),
        ('bob', 'bobpass', 'Robert B.'),
        ('eve', 'evepass', 'Evelyn E.')
    ]
    cur.executemany('INSERT INTO users (username,password,full_name) VALUES (?,?,?)', users)
    conn.commit()

    # seed accounts
    cur.execute('SELECT id FROM users WHERE username = "alice"')
    alice_id = cur.fetchone()[0]
    cur.execute('SELECT id FROM users WHERE username = "bob"')
    bob_id = cur.fetchone()[0]

    accounts = [
        (alice_id, 'ACCT10001', 100000),
        (bob_id, 'ACCT10002', 50000)
    ]
    cur.executemany('INSERT INTO accounts (user_id,account_number,balance) VALUES (?,?,?)', accounts)
    conn.commit()

    # sample transactions
    cur.executemany('INSERT INTO transactions (account_id, amount, memo) VALUES (?,?,?)', [
        (1, -5000, 'Rent payment'),
        (1, -200, 'Coffee shop'),
        (2, -1000, 'Transfer to friend'),
    ])
    conn.commit()
    conn.close()
    print(f"Created DB at {DB_PATH}")

if __name__ == '__main__':
    ensure_dirs()
    flags = write_flags()
    create_db()
    print("Seed complete. Start the app with: python3 app.py")
