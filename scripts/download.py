#!/usr/bin/env python3
"""Download UK Meteor Network (UKMON) data into data/.

Uses only the Python standard library.

  python scripts/download.py                          # last 3 days + camera list
  python scripts/download.py --start 2026-01-01 --end 2026-04-30
  python scripts/download.py --parquet 2026           # also the yearly archive file

Outputs:
  data/summary/YYYY/YYYYMMDD.json  matched (multi-camera) meteors for that day,
                                   from api.ukmeteors.co.uk/matches?reqtyp=summary
  data/availability.csv            one row per day fetched: date, matches, stations
  data/cameras/cameraLocs.json     active camera locations from the archive
  data/parquet/                    yearly full-match archives (only with --parquet)
"""

import argparse
import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = 'https://api.ukmeteors.co.uk'
ARCHIVE = 'https://archive.ukmeteors.co.uk'
ROOT = Path(__file__).resolve().parent.parent / 'data'
HEADERS = {'User-Agent': 'uk-meteor-data-downloader (+https://github.com/)'}


def fetch(url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as res:
                return res.read()
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == retries:
                raise
            print(f'  retry {attempt} for {url}: {e}', file=sys.stderr)
            time.sleep(2 ** attempt)


def summary_for_day(day):
    """Returns the list of matched events for a day ([] when there are none)."""
    raw = fetch(f'{API}/matches?reqtyp=summary&reqval={day:%Y%m%d}')
    data = json.loads(raw)
    return data if isinstance(data, list) else []


def update_availability(rows):
    path = ROOT / 'availability.csv'
    existing = {}
    if path.exists():
        with path.open(newline='') as f:
            existing = {r['date']: r for r in csv.DictReader(f)}
    existing.update(rows)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['date', 'matches', 'stations'], lineterminator='\n')
        w.writeheader()
        for date in sorted(existing):
            w.writerow(existing[date])


def download_summaries(start, end):
    rows = {}
    failures = 0
    day = start
    while day <= end:
        try:
            events = summary_for_day(day)
        except Exception as e:  # keep going; report at the end
            print(f'{day:%Y-%m-%d}: FAILED {e}', file=sys.stderr)
            failures += 1
            day += dt.timedelta(days=1)
            continue

        out = ROOT / 'summary' / f'{day:%Y}' / f'{day:%Y%m%d}.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(events, indent=1, sort_keys=True) + '\n')

        stations = set()
        for ev in events:
            stations.update(s for s in re.split(r'[;,\s]+', str(ev.get('stations') or '')) if s)
        rows[f'{day:%Y-%m-%d}'] = {
            'date': f'{day:%Y-%m-%d}',
            'matches': len(events),
            'stations': len(stations),
        }
        print(f'{day:%Y-%m-%d}: {len(events)} matches from {len(stations)} stations')
        day += dt.timedelta(days=1)
        time.sleep(0.5)  # be polite to a volunteer-run service

    update_availability(rows)
    return failures


def download_file(url, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(fetch(url))
    print(f'saved {url} -> {out.relative_to(ROOT.parent)}')


def main():
    today = dt.date.today()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--start', type=dt.date.fromisoformat, default=today - dt.timedelta(days=3))
    p.add_argument('--end', type=dt.date.fromisoformat, default=today)
    p.add_argument('--parquet', type=int, nargs='*', default=[], metavar='YEAR',
                   help='also download the yearly matches-full-YEAR.parquet.snap archive')
    args = p.parse_args()
    if args.start > args.end:
        p.error('--start must not be after --end')

    failures = download_summaries(args.start, args.end)

    try:
        download_file(f'{ARCHIVE}/reports/stations/cameraLocs.json', ROOT / 'cameras' / 'cameraLocs.json')
    except Exception as e:
        print(f'camera list: FAILED {e}', file=sys.stderr)
        failures += 1

    for year in args.parquet:
        name = f'matches-full-{year}.parquet.snap'
        try:
            download_file(f'{ARCHIVE}/browse/parquet/{name}', ROOT / 'parquet' / name)
        except Exception as e:
            print(f'{name}: FAILED {e}', file=sys.stderr)
            failures += 1

    if failures:
        print(f'{failures} download(s) failed', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
