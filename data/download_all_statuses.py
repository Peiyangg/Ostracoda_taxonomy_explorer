"""
Download all Ostracoda taxa (via AphiaChildrenByAphiaID recursion) and count
the distribution of `status` values.

Strategy A: children-tree only (no synonym endpoint calls).
Expected runtime: ~15-25 minutes.

Outputs:
  - ostracoda_all_records.json  (every record encountered)
  - ostracoda_status_report.json (summary counts)
"""
from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path

import requests

BASE = "https://www.marinespecies.org/rest"
OSTRACODA_APHIA_ID = 1078
DELAY = 0.35  # seconds between calls
OUT_DIR = Path(__file__).parent

session = requests.Session()
session.headers.update({"Accept": "application/json"})


def fetch_children(aphia_id: int) -> list[dict]:
    """Fetch all children of a taxon (paginated, 50 per page)."""
    out: list[dict] = []
    offset = 1
    while True:
        time.sleep(DELAY)
        url = f"{BASE}/AphiaChildrenByAphiaID/{aphia_id}"
        for attempt in range(4):
            resp = session.get(url, params={"marine_only": "false", "offset": offset})
            if resp.status_code == 200:
                break
            if resp.status_code == 204:
                return out
            if resp.status_code == 429:
                backoff = 2 ** attempt
                print(f"  [429] backing off {backoff}s")
                time.sleep(backoff)
                continue
            print(f"  [HTTP {resp.status_code}] {url}?offset={offset}")
            return out
        else:
            return out

        batch = resp.json() if resp.content else []
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 50:
            break
        offset += 50
    return out


def fetch_record(aphia_id: int) -> dict | None:
    time.sleep(DELAY)
    resp = session.get(f"{BASE}/AphiaRecordByAphiaID/{aphia_id}")
    if resp.status_code == 200 and resp.content:
        return resp.json()
    return None


def main() -> None:
    started = time.time()
    print(f"Root AphiaID: {OSTRACODA_APHIA_ID}")
    root = fetch_record(OSTRACODA_APHIA_ID)
    if root is None:
        print("Could not fetch root.")
        return

    all_records: dict[int, dict] = {OSTRACODA_APHIA_ID: root}
    queue: list[int] = [OSTRACODA_APHIA_ID]
    visited: set[int] = {OSTRACODA_APHIA_ID}
    calls = 1

    status_counter: Counter[str] = Counter()
    rank_counter: Counter[str] = Counter()

    status_counter[str(root.get("status"))] += 1
    rank_counter[str(root.get("rank"))] += 1

    while queue:
        current = queue.pop(0)
        children = fetch_children(current)
        calls += max(1, (len(children) + 49) // 50)  # pagination calls

        for child in children:
            cid = child.get("AphiaID")
            if cid is None or cid in visited:
                continue
            visited.add(cid)
            all_records[cid] = child
            queue.append(cid)
            status_counter[str(child.get("status"))] += 1
            rank_counter[str(child.get("rank"))] += 1

        elapsed = time.time() - started
        print(
            f"  processed AphiaID {current} | "
            f"+{len(children)} children | "
            f"total records: {len(all_records)} | "
            f"queue: {len(queue)} | "
            f"calls: {calls} | "
            f"elapsed: {elapsed/60:.1f} min"
        )

        # Periodic checkpoint every 500 records
        if len(all_records) % 500 == 0 and len(all_records) > 0:
            (OUT_DIR / "ostracoda_all_records.json").write_text(
                json.dumps(list(all_records.values()), ensure_ascii=False, indent=2)
            )

    # Final write
    (OUT_DIR / "ostracoda_all_records.json").write_text(
        json.dumps(list(all_records.values()), ensure_ascii=False, indent=2)
    )

    report = {
        "total_records": len(all_records),
        "api_calls": calls,
        "elapsed_seconds": time.time() - started,
        "status_counts": dict(status_counter.most_common()),
        "rank_counts": dict(rank_counter.most_common()),
    }
    (OUT_DIR / "ostracoda_status_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)
    )

    # CSV: status distribution
    with (OUT_DIR / "ostracoda_status_distribution.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["status", "count"])
        for s, n in status_counter.most_common():
            w.writerow([s, n])

    # CSV: rank distribution
    with (OUT_DIR / "ostracoda_rank_distribution.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "count"])
        for r, n in rank_counter.most_common():
            w.writerow([r, n])

    print("\n" + "=" * 60)
    print(f"DONE in {report['elapsed_seconds']/60:.1f} minutes")
    print(f"Total records: {report['total_records']}")
    print(f"API calls: {report['api_calls']}")
    print("\nStatus distribution:")
    for s, n in status_counter.most_common():
        print(f"  {s:40s} {n}")
    print("\nRank distribution (top 15):")
    for r, n in rank_counter.most_common(15):
        print(f"  {r:25s} {n}")
    print(f"\nSaved: ostracoda_all_records.json, ostracoda_status_report.json")


if __name__ == "__main__":
    main()
