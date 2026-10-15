#!/bin/bash
# Docker entrypoint: seed DB and start the app
set -e

# Run seed script if DB missing or if FORCE_SEED=1
if [ "$FORCE_SEED" == "1" ] || [ ! -f /app/shadownet.db ]; then
  echo "Seeding database and flags..."
  python3 scripts/seed_db.py
fi

# Start the app
echo "Starting ShadowNet app..."
python3 app.py
