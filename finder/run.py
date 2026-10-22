## one crawl cycle: pick due companies, crawl, detect new postings, alert, write the snapshot
import argparse
import json
import os
import sys
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import yaml

from . import ats, filters, notify
from .http import Blocked, Http


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat(timespec="seconds")


def parseIso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


## state on disk (lives on the pi, outside the repo)
def loadState(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"runCount": 0, "jobs": {}, "companies": {}, "wdFacets": {}}


def saveState(state, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, separators=(",", ":"))
    os.replace(tmp, path)


## scheduling: priority companies every run, the rest spread across runs by a stable hash of the name
def dueCompanies(companies, state, cfg, runCount, forceAll=False, only=None):
    sched = cfg.get("schedule", {})
    every = max(1, int(sched.get("defaultEveryRuns", 2)))
    prio = max(1, int(sched.get("priorityEveryRuns", 1)))
    due = []
    for c in companies:
        if only and c["name"].lower() not in only:
            continue
        info = state["companies"].get(c["name"], {})
        if forceAll or only or not info.get("lastOk"):
            due.append(c)
        elif c.get("priority"):
            if runCount % prio == 0:
                due.append(c)
        elif (zlib.crc32(c["name"].encode()) + runCount) % every == 0:
            due.append(c)
    return due


def crawlOne(c, http, cfg, facetCache):
    listFn, _ = ats.adapters[c["ats"]]
    keep = filters.isInternTitle
    started = time.time()
    try:
        if c["ats"] == "workday":
            jobs = listFn(c, http, keep, facetCache, wdCfg=cfg.get("workday", {}))
        else:
            jobs = listFn(c, http, keep, facetCache)
        return {"status": "ok" if jobs else "0 jobs", "jobs": jobs, "seconds": round(time.time() - started, 1)}
    except Blocked as e:
        return {"status": "blocked", "error": str(e), "jobs": None}
    except Exception as e:  # keep going, one bad board shouldn't stop the run
        return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:160]}", "jobs": None}


def jobKey(c, j):
    return f"{c['ats']}:{ats.boardKey(c)}:{j['id']}"


## main cycle
def runCycle(cfg, state, http, log=print, forceAll=False, only=None, quiet=False):
    t = now()
    state["runCount"] = state.get("runCount", 0) + 1
    runCount = state["runCount"]
    companies = cfg["companies"]
    byName = {c["name"]: c for c in companies}
    due = dueCompanies(companies, state, cfg, runCount, forceAll, only)
    log(f"run {runCount}: checking {len(due)} of {len(companies)} companies")

    facetCache = {k: v for k, v in state.get("wdFacets", {}).items()
                  if (parseIso(v.get("date", "")) or t) > t - timedelta(days=1)}
    results = {}
    with ThreadPoolExecutor(max_workers=int(cfg.get("http", {}).get("workers", 4))) as pool:
        futures = {pool.submit(crawlOne, c, http, cfg, facetCache): c for c in due}
        for i, (fut, c) in enumerate(futures.items(), 1):
            r = fut.result()
            results[c["name"]] = r
            n = len(r["jobs"]) if r["jobs"] is not None else "-"
            log(f"  [{i}/{len(due)}] {c['name']}: {r['status']} ({n} intern titles)")
    state["wdFacets"] = {k: dict(v, date=v.get("date") or iso(t)) for k, v in facetCache.items()}

    detailBudget = int(cfg.get("http", {}).get("maxDetailFetchesPerRun", 80))
    newMatches = []
    for c in due:
        r = results[c["name"]]
        info = state["companies"].setdefault(c["name"], {})
        info.update({"ats": c["ats"], "lastRun": iso(t), "status": r["status"], "error": r.get("error")})
        if r["jobs"] is None:
            continue
        baseline = not info.get("lastOk")  # first good crawl of a company is recorded quietly
        info["lastOk"] = iso(t)
        info["count"] = len(r["jobs"])
        seenNow = set()
        for j in r["jobs"]:
            key = jobKey(c, j)
            seenNow.add(key)
            rec = state["jobs"].get(key)
            if rec is None:
                rec = {"key": key, "company": c["name"], "firstSeen": iso(t), "alerted": baseline or quiet}
                state["jobs"][key] = rec
            rec.update({k: v for k, v in j.items() if v not in (None, "") and k != "description"})
            rec["lastSeen"] = iso(t)
            rec.pop("closedAt", None)
            if j.get("description"):
                rec["description"] = j["description"][:8000]
        # anything that vanished from a board we read fine is closed
        for key, rec in state["jobs"].items():
            if rec["company"] == c["name"] and key not in seenNow and not rec.get("closedAt"):
                rec["closedAt"] = iso(t)

    # descriptions: fetched once per new posting that already looks right by title
    for rec in state["jobs"].values():
        c = byName.get(rec["company"])
        if not c or rec.get("closedAt"):
            continue
        detailFn = ats.adapters[c["ats"]][1]
        if detailFn and not rec.get("description") and not rec.get("detailFailed") and filters.disciplineOk(rec["title"]):
            if detailBudget <= 0:
                rec["detailPending"] = True
                continue
            detailBudget -= 1
            try:
                rec["description"] = (detailFn(c, rec, http) or "")[:8000] or " "
                rec.pop("detailPending", None)
            except Blocked:
                rec["detailFailed"] = "blocked"
            except Exception as e:
                rec["detailFailed"] = f"{type(e).__name__}"
        rec["match"] = filters.evaluate(rec, c, cfg)
        if rec["match"] and not rec.get("alerted") and not rec.get("detailPending"):
            rec["alerted"] = True
            if rec["score"] >= cfg.get("alerts", {}).get("minScore", 0):
                newMatches.append(dict(rec))

    # tidy: drop closed postings after a while, and title-only rejects nobody needs
    dropDays = cfg.get("dropClosedAfterDays", 14)
    for key in list(state["jobs"]):
        rec = state["jobs"][key]
        closed = parseIso(rec.get("closedAt", ""))
        if closed and closed < t - timedelta(days=dropDays):
            del state["jobs"][key]
        elif rec["company"] not in byName:
            del state["jobs"][key]
        elif not rec.get("match") and rec.get("description"):
            rec["description"] = " "  # keep the key (so it never counts as new again) but not the text

    for name in list(state["companies"]):
        if name not in byName:
            del state["companies"][name]

    return {"results": results, "due": due, "newMatches": newMatches}


## snapshot for the dashboard and the sweep task
def buildSnapshot(cfg, state):
    byName = {c["name"]: c for c in cfg["companies"]}
    jobs = []
    for rec in state["jobs"].values():
        if not rec.get("match"):
            continue
        c = byName.get(rec["company"], {})
        desc = (rec.get("description") or "").strip()
        jobs.append({
            "key": rec["key"], "company": rec["company"], "sector": c.get("sector", ""), "tier": c.get("tier", 2),
            "ats": c.get("ats"), "title": rec["title"], "location": rec.get("location", ""), "url": rec.get("url"),
            "firstSeen": rec["firstSeen"], "lastSeen": rec.get("lastSeen"), "postedAt": rec.get("postedAt"),
            "closedAt": rec.get("closedAt"), "term": rec.get("term"), "score": rec.get("score"), "why": rec.get("why", []),
            "flags": rec.get("flags", []), "detailPending": bool(rec.get("detailPending")),
            "snippet": desc[:500],
        })
    jobs.sort(key=lambda j: (j["closedAt"] is not None, -(j["score"] or 0), j["firstSeen"]))
    companies = []
    for c in cfg["companies"]:
        info = state["companies"].get(c["name"], {})
        companies.append({"name": c["name"], "sector": c.get("sector", ""), "ats": c["ats"], "status": info.get("status", "pending"),
                          "error": info.get("error"), "lastRun": info.get("lastRun"), "lastOk": info.get("lastOk"),
                          "internTitles": info.get("count", 0),
                          "matches": sum(1 for j in jobs if j["company"] == c["name"] and not j["closedAt"])})
    return {"generatedAt": iso(now()), "runCount": state.get("runCount", 0), "jobs": jobs, "companies": companies}


def statusTable(results, due, state):
    lines = [f"{'company':28} {'ats':15} {'status':8} {'intern titles':>13} {'matches':>7}  note"]
    order = {"error": 0, "blocked": 1, "0 jobs": 2, "ok": 3}
    for c in sorted(due, key=lambda c: (order.get(results[c["name"]]["status"], 9), c["name"])):
        r = results[c["name"]]
        n = len(r["jobs"]) if r["jobs"] is not None else "-"
        m = sum(1 for j in state["jobs"].values() if j["company"] == c["name"] and j.get("match") and not j.get("closedAt"))
        lines.append(f"{c['name'][:28]:28} {c['ats']:15} {r['status']:8} {str(n):>13} {m:>7}  {r.get('error') or ''}")
    counts = {}
    for c in due:
        counts[results[c["name"]]["status"]] = counts.get(results[c["name"]]["status"], 0) + 1
    lines.append("summary: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yml")
    ap.add_argument("--data", default=os.path.expanduser("~/internship-data"))
    ap.add_argument("--out", default=os.path.expanduser("~/internship-out"))
    ap.add_argument("--all", action="store_true", help="check every company now")
    ap.add_argument("--only", help="comma separated company names to check")
    ap.add_argument("--quiet", action="store_true", help="record without sending alerts")
    ap.add_argument("--table", action="store_true", help="print the per-company status table")
    a = ap.parse_args(argv)

    # pi 3 safety: print progress as it happens, and fail with MemoryError instead of
    # pushing the whole pi into swap (that froze it on the first run)
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass
    try:
        import resource
        capMb = int(os.environ.get("FINDER_MEMORY_MB", "700"))
        resource.setrlimit(resource.RLIMIT_AS, (capMb * 1024 * 1024, capMb * 1024 * 1024))
    except (ImportError, ValueError, OSError):
        pass

    with open(a.config) as f:
        cfg = yaml.safe_load(f)
    os.makedirs(a.data, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)
    statePath = os.path.join(a.data, "state.json")
    state = loadState(statePath)
    firstEver = state.get("runCount", 0) == 0

    h = cfg.get("http", {})
    http = Http(h.get("perHostDelaySeconds", 1.5), h.get("timeoutSeconds", 25))
    only = {s.strip().lower() for s in a.only.split(",")} if a.only else None
    out = runCycle(cfg, state, http, forceAll=a.all, only=only, quiet=a.quiet or firstEver)
    saveState(state, statePath)

    snap = buildSnapshot(cfg, state)
    with open(os.path.join(a.out, "jobs.json"), "w") as f:
        json.dump(snap, f, indent=1)
    with open(os.path.join(a.out, "seen.json"), "w") as f:
        json.dump({k: v["firstSeen"] for k, v in state["jobs"].items()}, f, separators=(",", ":"))

    if a.table or firstEver or a.all or only:
        print(statusTable(out["results"], out["due"], state))
    openMatches = sum(1 for j in snap["jobs"] if not j["closedAt"])
    print(f"{http.requestCount} requests, {openMatches} open matches, {len(out['newMatches'])} new")

    if out["newMatches"]:
        msgs = notify.plan(out["newMatches"], cfg.get("alerts", {}).get("maxPerRun", 5))
        sent = notify.send(msgs, cfg.get("alerts", {}).get("dashboardUrl"))
        print(f"sent {sent} alert(s)")
    elif firstEver:
        print("first run recorded quietly, alerts start with the next new posting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
