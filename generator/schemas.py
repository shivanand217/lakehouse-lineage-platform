"""Avro schemas for the generated data.

I land the raw data as Avro because it's row-oriented and carries its schema with it, which
suits append-heavy ingest and a bit of schema drift at the edge. The lakehouse then stores it
as columnar Parquet inside Iceberg (see spark-jobs). Avro in, Parquet out.
"""

# Fact: one row per playback/ad telemetry event.
PLAYBACK_EVENT_SCHEMA = {
    "type": "record",
    "name": "PlaybackEvent",
    "namespace": "lakehouse.raw",
    "fields": [
        {"name": "event_id", "type": "string"},
        {"name": "event_type", "type": {
            "type": "enum", "name": "EventType",
            "symbols": ["play", "pause", "resume", "stop", "ad_impression"],
        }},
        {"name": "user_id", "type": "string"},
        {"name": "title_id", "type": "string"},
        {"name": "session_id", "type": "string"},
        {"name": "device", "type": {
            "type": "enum", "name": "Device",
            "symbols": ["web", "ios", "android", "tv", "roku"],
        }},
        {"name": "country", "type": "string"},
        # event time in epoch milliseconds (logical timestamp-millis)
        {"name": "event_ts", "type": {"type": "long", "logicalType": "timestamp-millis"}},
        # milliseconds watched since the previous event in the session (null for ad_impression)
        {"name": "ms_watched", "type": ["null", "long"], "default": None},
        # populated only for ad_impression events
        {"name": "ad_id", "type": ["null", "string"], "default": None},
        # schema version carried in-band so bronze can observe drift
        {"name": "schema_version", "type": "int", "default": 1},
    ],
}

# Dimension: title catalog. Small, slowly-changing; emitted as JSON for the silver join.
TITLE_DIM = [
    {"title_id": "t_1001", "title": "The Mandalorian",        "content_type": "series", "franchise": "Star Wars"},
    {"title_id": "t_1002", "title": "Loki",                   "content_type": "series", "franchise": "Marvel"},
    {"title_id": "t_1003", "title": "Encanto",                "content_type": "movie",  "franchise": "Animation"},
    {"title_id": "t_1004", "title": "Monday Night Football",  "content_type": "live",   "franchise": "ESPN"},
    {"title_id": "t_1005", "title": "The Bear",               "content_type": "series", "franchise": "Hulu Originals"},
    {"title_id": "t_1006", "title": "Avatar: The Way of Water","content_type": "movie", "franchise": "Avatar"},
    {"title_id": "t_1007", "title": "NBA Finals",             "content_type": "live",   "franchise": "ESPN"},
    {"title_id": "t_1008", "title": "Only Murders in the Building", "content_type": "series", "franchise": "Hulu Originals"},
]
