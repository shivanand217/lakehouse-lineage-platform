#!/usr/bin/env python3
"""Generates the streaming telemetry this project runs on.

Makes Disney+/ESPN-style playback sessions as Avro files, plus a small title dimension as JSON.
This is what keeps the project self-contained: nothing external has to exist for the lakehouse
to have data.

Usage
-----
  # write Avro + dims to the local filesystem (default)
  python generate_events.py --sessions 500 --out ./out

  # land directly into MinIO (requires `make up`); writes to the `raw` bucket
  python generate_events.py --sessions 500 --sink s3 \
      --s3-endpoint http://localhost:9000 --s3-bucket raw

Output layout (local or S3 key prefix):
  <out>/playback_events/event_date=YYYY-MM-DD/part-<n>.avro
  <out>/dim_title/dim_title.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from fastavro import writer, parse_schema

from schemas import PLAYBACK_EVENT_SCHEMA, TITLE_DIM

COUNTRIES = ["US", "US", "US", "UK", "CA", "IN", "BR", "DE", "AU"]  # weighted toward US
DEVICES = ["web", "ios", "android", "tv", "roku"]
TITLE_IDS = [t["title_id"] for t in TITLE_DIM]


def _session_events(user_id: str, day: datetime, rng: random.Random) -> list[dict]:
    """Generate a plausible event sequence for one viewing session."""
    title_id = rng.choice(TITLE_IDS)
    device = rng.choice(DEVICES)
    country = rng.choice(COUNTRIES)
    session_id = f"s_{uuid.uuid4().hex[:12]}"

    # session starts at a random second within the given day
    start = day.replace(
        hour=rng.randint(0, 23), minute=rng.randint(0, 59), second=rng.randint(0, 59)
    )
    t = start
    events: list[dict] = []

    def emit(event_type: str, ms_watched=None, ad_id=None):
        events.append({
            "event_id": uuid.uuid4().hex,
            "event_type": event_type,
            "user_id": user_id,
            "title_id": title_id,
            "session_id": session_id,
            "device": device,
            "country": country,
            "event_ts": int(t.timestamp() * 1000),
            "ms_watched": ms_watched,
            "ad_id": ad_id,
            "schema_version": 1,
        })

    emit("play")
    # a handful of pause/resume + an occasional ad, then a stop
    n_segments = rng.randint(1, 6)
    for _ in range(n_segments):
        watched = rng.randint(30_000, 600_000)  # 30s–10min
        t += timedelta(milliseconds=watched)
        if rng.random() < 0.25:  # ad break
            emit("ad_impression", ad_id=f"ad_{rng.randint(1000,9999)}")
        emit("pause", ms_watched=watched)
        t += timedelta(seconds=rng.randint(2, 120))
        emit("resume")
    final = rng.randint(30_000, 300_000)
    t += timedelta(milliseconds=final)
    emit("stop", ms_watched=final)
    return events


def generate(sessions: int, days: int, seed: int) -> dict[str, list[dict]]:
    """Return events bucketed by event_date string (YYYY-MM-DD)."""
    rng = random.Random(seed)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    by_date: dict[str, list[dict]] = {}
    for _ in range(sessions):
        day = today - timedelta(days=rng.randint(0, max(0, days - 1)))
        user_id = f"u_{rng.randint(1, max(2, sessions // 3))}"  # some users recur
        for ev in _session_events(user_id, day, rng):
            date_str = datetime.fromtimestamp(ev["event_ts"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            by_date.setdefault(date_str, []).append(ev)
    return by_date


# --------------------------------------------------------------------------- sinks
def _avro_bytes(parsed_schema, records: list[dict]) -> bytes:
    buf = io.BytesIO()
    writer(buf, parsed_schema, records)
    return buf.getvalue()


def write_local(by_date, out_dir: str) -> None:
    parsed = parse_schema(PLAYBACK_EVENT_SCHEMA)
    for date_str, records in sorted(by_date.items()):
        d = os.path.join(out_dir, "playback_events", f"event_date={date_str}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "part-0.avro"), "wb") as f:
            f.write(_avro_bytes(parsed, records))
    dim_dir = os.path.join(out_dir, "dim_title")
    os.makedirs(dim_dir, exist_ok=True)
    with open(os.path.join(dim_dir, "dim_title.json"), "w") as f:
        for row in TITLE_DIM:
            f.write(json.dumps(row) + "\n")
    _summary(by_date, f"local:{out_dir}")


def write_s3(by_date, endpoint: str, bucket: str, access: str, secret: str) -> None:
    import boto3
    from botocore.client import Config

    s3 = boto3.client(
        "s3", endpoint_url=endpoint,
        aws_access_key_id=access, aws_secret_access_key=secret,
        config=Config(s3={"addressing_style": "path"}), region_name="us-east-1",
    )
    try:
        s3.create_bucket(Bucket=bucket)
    except Exception:
        pass  # already exists

    parsed = parse_schema(PLAYBACK_EVENT_SCHEMA)
    for date_str, records in sorted(by_date.items()):
        key = f"playback_events/event_date={date_str}/part-0.avro"
        s3.put_object(Bucket=bucket, Key=key, Body=_avro_bytes(parsed, records))
    body = "\n".join(json.dumps(r) for r in TITLE_DIM)
    s3.put_object(Bucket=bucket, Key="dim_title/dim_title.json", Body=body.encode())
    _summary(by_date, f"s3:{endpoint}/{bucket}")


def _summary(by_date, where: str) -> None:
    total = sum(len(v) for v in by_date.values())
    print(f"wrote {total} events across {len(by_date)} date partition(s) -> {where}")
    for d, recs in sorted(by_date.items()):
        print(f"  event_date={d}: {len(recs)} events")


# --------------------------------------------------------------------------- cli
def main() -> None:
    p = argparse.ArgumentParser(description="Generate synthetic streaming telemetry.")
    p.add_argument("--sessions", type=int, default=300, help="number of viewing sessions")
    p.add_argument("--days", type=int, default=3, help="spread events across the last N days")
    p.add_argument("--seed", type=int, default=42, help="RNG seed (deterministic output)")
    p.add_argument("--sink", choices=["local", "s3"], default="local")
    p.add_argument("--out", default="./out", help="local output dir (sink=local)")
    p.add_argument("--s3-endpoint", default=os.getenv("S3_ENDPOINT_LOCAL", "http://localhost:9000"))
    p.add_argument("--s3-bucket", default="raw")
    p.add_argument("--s3-access", default=os.getenv("AWS_ACCESS_KEY_ID", "admin"))
    p.add_argument("--s3-secret", default=os.getenv("AWS_SECRET_ACCESS_KEY", "password"))
    args = p.parse_args()

    by_date = generate(args.sessions, args.days, args.seed)
    if args.sink == "local":
        write_local(by_date, args.out)
    else:
        write_s3(by_date, args.s3_endpoint, args.s3_bucket, args.s3_access, args.s3_secret)


if __name__ == "__main__":
    main()
