## ntfy pushes: one ping per new match, or a single batched summary when lots arrive at once
import os

import requests


def ntfyTarget():
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").strip().rstrip("/")
    return (server, topic) if topic else (server, None)


def flagWords(j):
    names = {"risingJuniorMin": "rising-junior min", "sophomoreDone": "needs sophomore yr done", "usPerson": "US person", "clearance": "clearance"}
    return [names[f["flag"]] for f in j.get("flags", []) if f["flag"] in names]


def plan(newJobs, maxPerRun):
    # returns a list of messages (title, body, url, priority, tags)
    ranked = sorted(newJobs, key=lambda j: -j["score"])
    if len(ranked) <= maxPerRun:
        return [single(j) for j in ranked]
    top = ranked[:8]
    lines = [f"{j['company']}: {j['title']}" + (f" ({', '.join(flagWords(j))})" if flagWords(j) else "") for j in top]
    if len(ranked) > len(top):
        lines.append(f"+{len(ranked) - len(top)} more on the dashboard")
    return [{"title": f"{len(ranked)} new internships", "body": "\n".join(lines), "url": None, "priority": "default", "tags": "briefcase"}]


def single(j):
    bits = [j.get("location") or "location n/a"]
    flags = flagWords(j)
    if flags:
        bits.append("flag: " + ", ".join(flags))
    if j.get("term") == "unspecified":
        bits.append("term not stated")
    return {"title": f"{j['company']}: {j['title']}"[:180], "body": " | ".join(bits), "url": j.get("url"),
            "priority": "high" if j["score"] >= 75 else "default", "tags": "wrench" if j["score"] >= 75 else "briefcase"}


def send(messages, dashboardUrl=None, log=print):
    server, topic = ntfyTarget()
    if not topic:
        log("ntfy: no NTFY_TOPIC set, skipping alerts")
        return 0
    sent = 0
    for m in messages:
        headers = {"Title": m["title"].encode("utf-8"), "Priority": m["priority"], "Tags": m["tags"]}
        click = m.get("url") or dashboardUrl
        if click:
            headers["Click"] = click
        if dashboardUrl:
            headers["Actions"] = f"view, Dashboard, {dashboardUrl}"
        try:
            requests.post(f"{server}/{topic}", data=m["body"].encode("utf-8"), headers=headers, timeout=15).raise_for_status()
            sent += 1
        except requests.RequestException as e:
            log(f"ntfy: send failed ({e})")
    return sent
