# UK Meteor Network data

A mirror of public data from the [UK Meteor Network](https://ukmeteornetwork.org/)
(UKMON), downloaded by a GitHub Actions workflow and committed to this repository.

## Where the data comes from

| Source | URL | What it gives |
| --- | --- | --- |
| Matches API – summary | `https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval=YYYYMMDD` | Every meteor seen by 2+ cameras on that date, with trajectory, orbit, magnitude, shower and contributing stations |
| Matches API – list | `…/matches?reqtyp=matches&reqval=YYYYMMDD` | Just the event IDs (`orbname`) for a day |
| Matches API – detail | `…/matches?reqtyp=detail&reqval=<orbname>[&points=1]` | Full record for one event, optionally with the measured points |
| Matches API – station | `…/matches?reqtyp=station&statid=UK0006&reqval=YYYYMMDD` | Events a single camera contributed to |
| Summary, part of a day | add `&period=am`, `pm` or `H-H` (e.g. `0-3`, UTC hours) | |
| Single-camera detections | `https://api.ukmeteors.co.uk/detections?d1=<ISO>&d2=<ISO>&opts=t:S` | Raw detections in a time window |
| Trajectory | `https://api.ukmeteors.co.uk/pickle/getpickle?reqval=<orbname>&format=json` | Full WMPL trajectory solution |
| Raw camera data | `https://api.ukmeteors.co.uk/getecsv?stat=<camera>&dt=<ISO time>` | ECSV for a detection |
| Live images | `https://api.ukmeteors.co.uk/liveimages/getlive?pattern=YYYYMMDD_HH` | Last ~month only |
| Camera locations | `https://archive.ukmeteors.co.uk/reports/stations/cameraLocs.json` | |
| Bulk yearly archive | `https://archive.ukmeteors.co.uk/browse/parquet/matches-full-YYYY.parquet.snap` | All matches for a year (Parquet, snappy) |
| Data dictionary | `https://archive.ukmeteors.co.uk/browse/datadictionary.xlsx` | Field definitions |
| Browsable archive | `https://archive.ukmeteors.co.uk/` | Reports, station status, orbit pages |

Endpoint details were taken from UKMON's own code
([markmac99/UKMon-shared](https://github.com/markmac99/UKMon-shared): `api_examples/`,
`tests/apis/test_apis.py` and `archive/lambdas/matchDataApi/`).

## What's in this repo

```
data/availability.csv            date, matches, stations  – one row per day downloaded
data/summary/YYYY/YYYYMMDD.json  full summary records for each day ([] = none that day)
data/cameras/cameraLocs.json     camera locations
data/parquet/                    yearly bulk archives (only when requested)
scripts/download.py              the downloader (Python standard library only)
```

## Updating

- **Automatically:** the workflow runs daily and refreshes the last 3 days
  (recent days can gain matches as more camera data arrives).
- **Backfill a range:** Actions → *Download UKMON data* → *Run workflow*, then
  enter a start and end date (and optionally years for the parquet archives).
- **Locally:** `python scripts/download.py --start 2026-04-01 --end 2026-04-30`

## Licence / attribution

The data belongs to the UK Meteor Network and its volunteer camera operators.
Credit UKMON when you use it, and check their site for terms. The downloader
pauses between requests; please keep it that way.
