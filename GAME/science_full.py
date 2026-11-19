"""Optional *offline* verified full M9/M11/M13/M15 archive index.

Never auto-downloads source material, never changes game engine or the release
tree. Originals are maintained in the owner's private ChatGPT Project "Го".
Each archive is SHA256 checked before making any of its cards available.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sqlite3
from pathlib import Path

SPECS = {
    9: dict(count=137815, raw="4d27ead114c1aa7bf65f3b92f6774ba729cfaacc8ff3e87de83beccdc1be0e47",
            gzip="8ce470dfe02ea3da95e37712b6ade4bc84e4e4862c6e6d60c50c0566cad28f20"),
    11: dict(count=31269, raw="a06bbd8387b8245457cf875f3b366cce350f02363f451433960134ce06f2afb4",
             gzip="8c3c9f5f21b590e37553816e149377625f2722ee00a09bf9fe4ac39d1c8ee1f9"),
    13: dict(count=180720, raw="9b37b5595cf75303d6096dea71b5ca7865f16d19691daccd79ccc1f2c12f4058",
             gzip="1e34aa8b77314b0c97b4702c593c9acbdf131912a580ba32680bd610f8809af5"),
    15: dict(count=208728, raw="eb0d5309ac1a45fb65b4339965aca1b54464b7cd9fb8012f7a19bdbf6c0c206a",
             gzip="512f3aea4f4865bb7ed2671bf01c17e1d4cf9e71db4776c2575d6f4a04c5960d"),
}
# The previously verified library manifest is LANDSCAPE_GO_V4_SCIENCE_IMPORT_03B_CATALOGS_VERIFIED.md
# GZIP checksum 11x11 was not historically published; the report verified
# raw JSON SHA and reported the GZIP SHA, so both are pinned here.

DATA_HOME = Path.home() / "LANDSCAPE_GO_SCIENCE_FULL"
MAX_RAW = 512 * 1024 * 1024
MAX_GZIP = 256 * 1024 * 1024
CHUNK = 1024 * 1024


def database_path():
    return Path(os.environ.get("LANDSCAPE_GO_SCIENCE_FULL_DB", DATA_HOME / "science_full.sqlite3"))


def _hash_stream(stream, limit):
    digest = hashlib.sha256()
    total = 0
    while True:
        block = stream.read(CHUNK)
        if not block:
            return digest.hexdigest(), total
        total += len(block)
        if total > limit:
            raise ValueError("Archive exceeds configured uncompressed size limit")
        digest.update(block)


def verify_gzip(path: Path, spec):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or not path.name.endswith(".json.gz"):
        raise ValueError("Expected a regular .json.gz source file")
    if path.stat().st_size > MAX_GZIP:
        raise ValueError("Compressed archive is too large")
    with path.open("rb") as stream:
        packed, packed_bytes = _hash_stream(stream, MAX_GZIP)
    if packed != spec["gzip"]:
        raise ValueError("GZIP SHA256 mismatch; refusing untrusted source")
    with gzip.open(path, "rb") as stream:
        raw, raw_bytes = _hash_stream(stream, MAX_RAW)
    if raw != spec["raw"]:
        raise ValueError("JSON SHA256 mismatch; refusing untrusted source")
    return {"gzip_sha256": packed, "gzip_bytes": packed_bytes,
            "raw_sha256": raw, "raw_bytes": raw_bytes}


def _balanced_collection(doc, expected_count):
    candidates = []
    if type(doc) is list:
        candidates.append(doc)
    if type(doc) is dict:
        for name in ("entries", "balanced", "balanced_entries"):
            if type(doc.get(name)) is list:
                candidates.append(doc[name])
    matches = [items for items in candidates if len(items) == expected_count]
    if len(matches) != 1:
        raise ValueError("Ambiguous source JSON collection or incorrect count")
    return matches[0]


def _valid_matrix(matrix, n):
    return (type(matrix) is list and len(matrix) == n and
            all(type(line) is list and len(line) == n and
                all(type(x) is int for x in line) for line in matrix))


def index_full_archive(n, source, db=None, specs=None):
    """SHA-pinned external import, atomic DB transaction per size.

    Deep JSON verification needs substantial RAM for 13x13 and 15x15;
    deliberately executed once as an explicit owner action.
    """
    specs = SPECS if specs is None else specs  # test-only injected fixture
    if n not in specs:
        raise ValueError("No published catalog specification for size")
    spec = specs[n]
    source = Path(source)
    audit = verify_gzip(source, spec)
    with gzip.open(source, "rt", encoding="utf-8-sig") as stream:
        doc = json.load(stream)
    records = _balanced_collection(doc, spec["count"])
    if any(type(item) is not dict or not _valid_matrix(item.get("matrix"), n)
           for item in records):
        raise ValueError("Invalid record shapes; import rejected")

    db = Path(db) if db is not None else database_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS origins (
          size INTEGER PRIMARY KEY, raw_sha256 TEXT NOT NULL,
          gzip_sha256 TEXT NOT NULL, records INTEGER NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS cards (
          size INTEGER NOT NULL, seq INTEGER NOT NULL, id TEXT NOT NULL,
          original_id TEXT, matrix_json TEXT NOT NULL,
          PRIMARY KEY (size, seq), UNIQUE(size, id))""")
        conn.execute("CREATE INDEX IF NOT EXISTS cards_id ON cards(size, id)")
        with conn:
            conn.execute("DELETE FROM cards WHERE size=?", (n,))
            for i, item in enumerate(records, 1):
                game_id = f"FULL-M{n}-{i:06d}"
                conn.execute("INSERT INTO cards VALUES (?,?,?,?,?)",
                    (n, i, game_id, str(item.get("id", "")),
                     json.dumps(item["matrix"], ensure_ascii=False,
                                separators=(",", ":"))))
            conn.execute("INSERT OR REPLACE INTO origins VALUES (?,?,?,?)",
                         (n, audit["raw_sha256"], audit["gzip_sha256"], len(records)))
    finally:
        conn.close()
    return {"size": n, "records": len(records), "db": str(db),
            "archive": source.name, "status": "VERIFIED", **audit}


def _db():
    path = database_path()
    if not path.is_file():
        return None
    return sqlite3.connect(path)


def full_count(n):
    if n not in SPECS:
        return 0
    conn = _db()
    if conn is None:
        return 0
    try:
        row = conn.execute("SELECT records,raw_sha256,gzip_sha256 FROM origins WHERE size=?", (n,)).fetchone()
        if row is None:
            return 0
        if row != (SPECS[n]["count"], SPECS[n]["raw"], SPECS[n]["gzip"]):
            return 0
        return row[0]
    except (sqlite3.Error, OSError):
        return 0
    finally:
        conn.close()


def _from_sql(n, row):
    ident, original_id, matrix_json = row
    return {"id": ident, "matrix": json.loads(matrix_json),
            "V": None, "U": None, "class": "Full-science-verified",
            "checkpoint": f"M{n}-01", "strict_spatial": False,
            "science_V_status": "unknown", "science_U_status": "unknown",
            "source_groups": ["full"], "source_original_id": original_id,
            "source_science": {"path": f"LANDSCAPE_GO_M{n}_01_full_balanced_catalog.json.gz",
                               "raw_sha256": SPECS[n]["raw"],
                               "origin": "Library/Го; V4-SCIENCE-IMPORT-03B"}}


def full_page(n, limit=120, offset=0, query=""):
    if full_count(n) == 0:
        return []
    limit = max(0, min(int(limit), 150))
    offset = max(0, int(offset))
    conn = _db()
    try:
        if query:
            q = query.replace("%", r"\%").replace("_", r"\_")
            rows = conn.execute(
                "SELECT id,original_id,matrix_json FROM cards WHERE size=? AND (id LIKE ? ESCAPE '\\' OR original_id LIKE ? ESCAPE '\\') ORDER BY seq LIMIT ? OFFSET ?",
                (n, f"%{q}%", f"%{q}%", limit, offset)).fetchall()
        else:
            rows = conn.execute(
                "SELECT id,original_id,matrix_json FROM cards WHERE size=? ORDER BY seq LIMIT ? OFFSET ?",
                (n, limit, offset)).fetchall()
        return [_from_sql(n, item) for item in rows]
    finally:
        conn.close()


def full_by_id(n, ident):
    if not isinstance(ident, str) or not ident.startswith(f"FULL-M{n}-") or full_count(n) == 0:
        return None
    conn = _db()
    try:
        row = conn.execute(
            "SELECT id,original_id,matrix_json FROM cards WHERE size=? AND id=?",
            (n, ident)).fetchone()
        return None if row is None else _from_sql(n, row)
    finally:
        conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify and index full historical scientific GZIP")
    parser.add_argument("--size", type=int, required=True, choices=sorted(SPECS))
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--database", type=Path)
    args = parser.parse_args(argv)
    try:
        result = index_full_archive(args.size, args.file, db=args.database)
    except (OSError, ValueError, sqlite3.Error, EOFError, json.JSONDecodeError) as exc:
        parser.exit(2, f"FULL_SCIENCE_IMPORT_REJECTED: {exc}\n")
    print("FULL_SCIENCE_IMPORT_VERIFIED", json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
