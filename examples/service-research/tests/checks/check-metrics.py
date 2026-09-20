"""Trusted python/v1 checker executed by the grading worker after submission.

run(context) returns one private rubric result. The engine constructs
context from verified frozen files; candidates never supply these local paths.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import Path


def run(context: dict) -> dict:
    artifact = context["inputs"]["metrics"]["files"][0]
    answer_path = Path(artifact["path"])
    reference_path = Path(context["references"]["source-data"])
    answer_bytes = answer_path.read_bytes()
    if hashlib.sha256(answer_bytes).hexdigest() != artifact["sha256"]:
        # Storage/integrity failures must not become candidate zero scores.
        raise ValueError("Frozen artifact hash mismatch")

    with reference_path.open(encoding="utf-8-sig", newline="") as source:
        reference = list(csv.DictReader(source))
    totals = {
        key: sum(int(row[key]) for row in reference)
        for key in ("available_slots", "booked_slots", "completed_visits")
    }
    expected = dict(totals)
    expected["booking_rate"] = totals["booked_slots"] / totals["available_slots"]
    expected["completion_rate"] = totals["completed_visits"] / totals["booked_slots"]

    found: dict[str, list[tuple[int, str]]] = {}
    try:
        with io.StringIO(answer_bytes.decode("utf-8-sig"), newline="") as answer:
            reader = csv.DictReader(answer, strict=True)
            if reader.fieldnames != ["metric", "value"]:
                raise ValueError("Expected metric,value headers")
            for row in reader:
                # Extra columns or incomplete rows violate the public CSV contract.
                if None in row or row.get("value") is None:
                    raise ValueError("Malformed CSV row")
                key = row["metric"].strip()
                found.setdefault(key, []).append((reader.line_num, row["value"].strip()))
    except (UnicodeError, csv.Error, ValueError):
        return {
            "status": "completed", "raw_score": 0, "scale_max": 5,
            "reason_code": "invalid_artifact",
            "feedback": "指标表不符合 UTF-8 CSV 的 metric,value 列约定。",
            "evidence": [{"artifact_id": "metrics", "path": artifact["relative_path"],
                          "sha256": artifact["sha256"], "view": "files",
                          "locator": {"kind": "file"}}],
        }

    score = 0
    evidence = []
    for key, correct in expected.items():
        matches = found.get(key, [])
        actual = None
        if len(matches) == 1:
            try:
                actual = float(matches[0][1])
            except ValueError:
                pass
        tolerance = 1e-6 if key.endswith("_rate") else 0
        passed = (actual is not None and math.isfinite(actual)
                  and abs(actual - correct) <= tolerance)
        score += int(passed)
        evidence.append({
            "artifact_id": "metrics", "path": artifact["relative_path"],
            "sha256": artifact["sha256"], "view": "files",
            "locator": ({"kind": "csv_rows", "rows": [item[0] for item in matches]}
                        if matches else {"kind": "absence", "expected_metric": key}),
            "metric": key, "passed": passed, "expected": correct,
            "observed": [item[1] for item in matches],
        })
    return {
        "status": "completed", "raw_score": score, "scale_max": 5,
        "reason_code": "evaluated", "feedback": f"五项指标中 {score} 项正确。",
        "evidence": evidence,
    }
