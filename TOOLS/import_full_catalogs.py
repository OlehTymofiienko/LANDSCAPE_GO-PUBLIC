#!/usr/bin/env python3
"""Offline SHA-pinned import of original M9/M11/M13/M15 GZIP into private SQLite."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from GAME import science_full


def source_filename(n):
    return f"LANDSCAPE_GO_M{n}_01_full_balanced_catalog.json.gz"


def safe_output(path):
    path = Path(path).expanduser().resolve()
    if path == ROOT or path.is_relative_to(ROOT):
        raise ValueError("SQLite and reports must remain outside Git working tree")
    return path


def audit_sources(folder, specs):
    folder = Path(folder).expanduser().resolve()
    files = {n: folder/source_filename(n) for n in sorted(specs)}
    missing = [str(p) for p in files.values() if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing original GZIP: " + "; ".join(missing))
    return {n: {"filename": p.name, **science_full.verify_gzip(p, specs[n])}
            for n, p in files.items()}


def audit_index(db, specs):
    if not Path(db).is_file():
        raise ValueError("SQLite database not found")
    output = {}
    con = sqlite3.connect(db)
    try:
        for n, spec in sorted(specs.items()):
            origin = con.execute(
                "SELECT records,raw_sha256,gzip_sha256 FROM origins WHERE size=?", (n,)
            ).fetchone()
            if origin != (spec["count"], spec["raw"], spec["gzip"]):
                raise ValueError(f"Origin mismatch: {n}x{n}")
            count, first, last = con.execute(
                "SELECT COUNT(*),MIN(seq),MAX(seq) FROM cards WHERE size=?", (n,)
            ).fetchone()
            if (count, first, last) != (spec["count"], 1, spec["count"]):
                raise ValueError(f"SQLite count/range mismatch: {n}x{n}")
            for seq in sorted({1, (count+1)//2, count}):
                card = con.execute(
                    "SELECT id,matrix_json FROM cards WHERE size=? AND seq=?", (n,seq)
                ).fetchone()
                if card is None or card[0] != f"FULL-M{n}-{seq:06d}":
                    raise ValueError(f"Wrong card ID at {n}x{n}/{seq}")
                if not science_full._valid_matrix(json.loads(card[1]), n):
                    raise ValueError(f"Wrong matrix shape at {n}x{n}/{seq}")
            output[str(n)] = {"count": count, "first": f"FULL-M{n}-000001",
                               "last": f"FULL-M{n}-{count:06d}",
                               "raw_sha256": origin[1], "gzip_sha256": origin[2]}
        quick = con.execute("PRAGMA quick_check").fetchone()
        if quick != ("ok",):
            raise ValueError(f"SQLite quick_check error: {quick!r}")
    finally:
        con.close()
    return output


def import_all(folder, db=None, report_path=None, specs=None):
    specs = science_full.SPECS if specs is None else specs
    db = safe_output(science_full.database_path() if db is None else db)
    report_path = None if report_path is None else safe_output(report_path)
    result = {
        "checkpoint": "V4-FULL-CATALOG-IMPORT-01",
        "utc": datetime.now(timezone.utc).isoformat(),
        "result": "FAIL", "expected": sum(s["count"] for s in specs.values()),
        "db": str(db), "sources": {}, "imported": [], "index": {},
        "release": "EXPERIMENTAL_NOT_PUBLISHED",
    }
    try:
        # All original SHA256 digests MUST pass before any database write.
        result["sources"] = {str(n): info for n,info in
                             audit_sources(folder, specs).items()}
        for n in sorted(specs):
            source = Path(folder).expanduser().resolve()/source_filename(n)
            item = science_full.index_full_archive(n, source, db=db, specs=specs)
            result["imported"].append({"size": n, "count": item["records"]})
        result["index"] = audit_index(db, specs)
        result["installed"] = sum(i["count"] for i in result["index"].values())
        if result["installed"] != result["expected"]:
            raise ValueError("Total record mismatch")
        result["result"] = "PASS"
    except (OSError, ValueError, sqlite3.Error, EOFError, json.JSONDecodeError,
            MemoryError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                               encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--report", type=Path)
    options = parser.parse_args(argv)
    r = import_all(options.archive_dir, options.database, options.report)
    print("V4_FULL_CATALOG_IMPORT", r["result"],
          r.get("installed",0), "/", r["expected"], flush=True)
    if "error" in r: print("ERROR:", r["error"], flush=True)
    if options.report: print("REPORT:", options.report, flush=True)
    return 0 if r["result"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
