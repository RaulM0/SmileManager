"""Local daily backups. Run under a user service with Docker access."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--interval-hours', type=float, default=24)
parser.add_argument('--once', action='store_true')
args = parser.parse_args()
if args.interval_hours < 1:
    parser.error('Minimum interval is one hour.')
root = Path(__file__).resolve().parents[1]
while True:
    result = subprocess.run([sys.executable, str(root / 'scripts/dev_backup.py'), 'create'], cwd=root)
    if args.once:
        sys.exit(result.returncode)
    time.sleep(args.interval_hours * 3600 if result.returncode == 0 else 3600)
