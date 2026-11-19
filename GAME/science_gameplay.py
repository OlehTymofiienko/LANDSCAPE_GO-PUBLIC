"""Selected scientific FG-1 landscapes, plus optional verified external full archives.

The 45 candidates are a verified-curation *subset*, not the complete scientific
catalogs. Loading them does not change GAME.engine or the original Mono 3/4.
"""
from __future__ import annotations
import json
from functools import lru_cache
from .engine import data_folder


@lru_cache(maxsize=1)
def science_gameplay_catalog():
    path = data_folder() / "SCIENCE_GAMEPLAY_3_TO_19.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["entries"]
    if data.get("format") != "landscape_go_science_gameplay_v0_1" or data["count"] != len(entries):
        raise ValueError("Unknown science-gameplay catalog format")
    ids = set()
    sizes = set()
    for row in entries:
        n = row["size"]
        if not isinstance(n, int) or not 3 <= n <= 19:
            raise ValueError("Incorrect science board size")
        if not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError("Missing scientific ID")
        if (n, row["id"]) in ids:
            raise ValueError("Duplicate scientific size+ID")
        ids.add((n, row["id"]))
        sizes.add(n)
        matrix = row["matrix"]
        if (len(matrix) != n or any(len(line) != n or
            any(type(v) is not int for v in line) for line in matrix)):
            raise ValueError("Scientific matrix shape")
        V, U = row.get("V"), row.get("U")
        if n >= 5 and (V is not None or U is not None):
            raise ValueError("Scientific N>=5 global minimax is not established")
        if U is not None and (len(U) != 6 or U[0] != V or
                             any(type(v) is not int for v in U)):
            raise ValueError("Inconsistent FG-1 U")
        if set(row.get("groups", ())) - {"atlas", "signed"} or not row["groups"]:
            raise ValueError("Unknown scientific family")
    if len(entries) != 45 or sizes != set(range(3, 20)):
        raise ValueError("Scientific catalog size coverage")
    return entries


def selected_science(n, family=None):
    if n not in range(3, 20):
        raise ValueError("Unsupported scientific size")
    if family not in (None, "atlas", "signed"):
        raise ValueError("Unsupported science family")
    rows = []
    for row in science_gameplay_catalog():
        if row["size"] != n or family and family not in row["groups"]:
            continue
        rows.append(dict(
            id=row["id"], matrix=row["matrix"], V=row["V"], U=row["U"],
            science_V_status=row["global_V_status"],
            science_U_status=row["global_U_status"],
            source_science=row["source"], source_groups=row["groups"],
            global_bounds=row["bounds"], spatial_D=(row["D_num"], row["D_den"]),
            source_local=row["local"], checkpoint=row["source"]["checkpoint"],
            **{"class": "Science-selected", "strict_spatial": False},
        ))
    return rows
