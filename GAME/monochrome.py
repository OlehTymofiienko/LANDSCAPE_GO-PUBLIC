"""Research catalogs for shared FG-1; original 3x3/4x4 catalogs preserved."""
from copy import deepcopy
from functools import lru_cache
import json
from .engine import data_folder
from .science_gameplay import selected_science
from .science_full import full_page, full_by_id, full_count

MONO_SIZES = tuple(range(3, 20))
MONO_FILTERS = ("all", "v-zero", "u-zero", "strict", "dynamic-exact",
                "dynamic-bound", "dynamic-unresolved")
# Keep historical filter tuple stable for the v4 3x3/4x4 regression suite.
SCIENCE_FILTERS = ("atlas", "signed", "full")


@lru_cache(maxsize=len(MONO_SIZES))
def monochrome_sources(n=3):
    if n not in MONO_SIZES:
        raise ValueError("Монохромный каталог доступен только для 3×3–19×19")
    if n >= 5:
        return selected_science(n)
    doc = json.loads((data_folder()/f"MONOCHROME_{n:02}X{n:02}.json").read_text(encoding="utf8"))
    rows = doc["entries"]
    if doc["size"] != n or doc["count"] != len(rows) or len({x["id"] for x in rows}) != len(rows):
        raise ValueError("Некорректный монохромный каталог")
    return rows


def filtered_monochrome(n=3, category="all"):
    if category not in MONO_FILTERS + SCIENCE_FILTERS:
        raise ValueError(f"Неизвестный фильтр: {category}")
    if category in ("atlas", "signed"):
        return selected_science(n, category)
    if category == "full":
        return full_page(n, limit=120)
    rows = monochrome_sources(n)
    def matches(x):
        u = x["U"]
        d = x.get("dynamic", {})
        if category == "all":
            return True
        if category == "v-zero":
            return x["V"] == 0 and x.get("science_V_status", "exact") != "unknown"
        if category == "u-zero":
            return u is not None and not any(u)
        if category == "strict":
            # Do not reinterpret scientific D as the original M3/M4 'strict' proof.
            return x.get("strict_spatial", n == 3 and n <= 4)
        if category == "dynamic-exact":
            return d.get("status") in ("exact_mixed_sign", "exact_nonpositive_pass")
        if category == "dynamic-bound":
            return d.get("status") == "lower_bound_only"
        return d.get("status") == "unresolved"
    return [x for x in rows if matches(x)]


def make_monochrome(n=3, source_id=None):
    rows = monochrome_sources(n)
    if source_id is None:
        source_id = "M3-B-01" if n == 3 else "M4-Q176" if n == 4 else rows[0]["id"]
    item = next((x for x in rows if x["id"] == source_id), None)
    if item is None:
        item = next((x for x in selected_science(n) if x["id"] == source_id), None)
    if item is None and n in (9, 11, 13, 15):
        item = full_by_id(n, source_id)
    if item is None:
        raise ValueError(f"Неизвестный монохромный ландшафт {n}×{n}: {source_id}")
    flat = [v for line in item["matrix"] for v in line]
    full = deepcopy(item.get("U"))
    exact_V = item.get("V")
    if exact_V is None:
        bound = item.get("global_bounds") or {}
        status = "Глобальные V и U неизвестны; исследовательская карта, minimax не доказан"
        if isinstance(bound.get("lower"), int) and isinstance(bound.get("upper"), int):
            status += f"; границы из источника [{bound['lower']},{bound['upper']}]"
    elif full is None:
        status = f"Точный V={exact_V}; полный U не аттестован в каталоге"
    else:
        u = tuple(full)
        outcome = ("полная ничья" if not any(u) else "белые по R" if
                   u == (0,0,0,-1,0,0) else "чёрные" if
                   u > (0,)*6 else "белые")
        status = f"V={exact_V}; U={u}; {outcome}"
    result = dict(size=n, source_id=source_id, black=flat, white=flat.copy(),
                  game_mode="original_shared", catalog="monochrome", title=source_id,
                  provenance=item.get("checkpoint", "external-verified-full"),
                  status=status, monochrome_class=item.get("class", "Scientific full"),
                  exact_V=exact_V, exact_U=full, rules_version="FG-1 / Scoring v0.2")
    if n == 4 and "window_D" in item:
        result.update(window_D=item["window_D"], strict_spatial=item["strict_spatial"],
                      dynamic=deepcopy(item["dynamic"]))
    for k in ("science_V_status", "science_U_status", "source_science",
              "source_groups", "global_bounds", "spatial_D", "source_local",
              "source_original_id"):
        if k in item:
            result[k] = deepcopy(item[k])
    return result


def dynamic_description(item):
    d = item.get("dynamic")
    if not d:
        return ""
    status = d["status"]
    if status in ("exact_mixed_sign", "exact_nonpositive_pass"):
        return f'Dynamic (исследование): точный V={d["V"]}'
    if status == "lower_bound_only":
        return f'Dynamic (исследование): {d["lower"]}≤V≤{d["upper"]}; точное V неизвестно'
    return f'Dynamic (исследование): точное V неизвестно; V≤{d["upper"]}'
