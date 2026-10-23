"""Stable, opt-in random streams; legacy mode preserves existing draw order."""

import hashlib
import json
from numbers import Integral
from pathlib import Path

import numpy as np


STREAM_SCHEME = "sha256-name/SeedSequence/PCG64-v1"


def stream_mode(parameters):
    mode = parameters.get("random_stream_mode")
    mode = "legacy" if mode is None else mode
    if mode not in ("legacy", "independent"):
        raise ValueError("random_stream_mode must be 'legacy' or 'independent'")
    return mode


def derive_rng(master_seed, name):
    """Derive a fresh generator independently of call order and Python hash salt."""
    if isinstance(master_seed, bool) or not isinstance(master_seed, Integral) or master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    if not isinstance(name, str) or not name:
        raise ValueError("A random stream needs a nonempty stable name")
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    words = [int.from_bytes(digest[i:i + 4], "little") for i in range(0, len(digest), 4)]
    sequence = np.random.SeedSequence([int(master_seed), *words])
    return np.random.Generator(np.random.PCG64(sequence))


def component_rng(parameters, name):
    """Return None for legacy callers so their global draws remain untouched."""
    if stream_mode(parameters) == "legacy":
        return None
    return derive_rng(parameters["random_seed"], name)


def canonical_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def demand_fingerprint(requests, source_path):
    """Fingerprint loaded exogenous inputs before any offer or policy decision."""
    rows = []
    for request in requests:
        rows.append({
            "id": str(request.get_rid_struct()), "type": request.type,
            "request_time": float(request.rq_time),
            "earliest_start": None if request.earliest_start_time is None else float(request.earliest_start_time),
            "latest_start": None if request.latest_start_time is None else float(request.latest_start_time),
            "latest_decision": float(request.latest_decision_time),
            "max_trip_time": None if request.max_trip_time is None else float(request.max_trip_time),
            "passengers": float(request.nr_pax),
            "origin": str(request.o_pos), "destination": str(request.d_pos),
        })
    rows.sort(key=lambda row: row["id"])
    return {"count": len(rows), "loaded_sha256": canonical_digest(rows),
            "source_sha256": file_digest(source_path)}
