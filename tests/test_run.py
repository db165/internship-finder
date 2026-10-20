## end to end cycle with a fake board: quiet first run, new id alerts, closed postings, batching
from finder import ats, notify, run

cfg = {
    "search": {"term": {"season": "summer", "year": 2027}, "bigCities": ["seattle"]},
    "alerts": {"maxPerRun": 2, "minScore": 0},
    "schedule": {"defaultEveryRuns": 2, "priorityEveryRuns": 1},
    "http": {"workers": 2, "maxDetailFetchesPerRun": 50},
    "companies": [{"name": "Acme Rockets", "sector": "space", "tier": 1, "ats": "fake", "token": "acme", "priority": True}],
}

board = []


def fakeList(c, http, keep, cache):
    return [dict(j) for j in board if keep(j["title"])]


def fakeDetail(c, j, http):
    return "Open to sophomores. Must be a U.S. person."


ats.adapters["fake"] = (fakeList, fakeDetail)


def posting(id, title, updated="2026-10-19"):
    # updated mimics a board-wide touch; it must never make an old posting look new
    return {"id": id, "title": title, "location": "Seattle, WA", "url": f"https://x/{id}", "postedAt": None, "updated": updated}


def fresh():
    return {"runCount": 0, "jobs": {}, "companies": {}, "wdFacets": {}}


def test_first_run_is_quiet_then_new_ids_alert():
    state = fresh()
    board[:] = [posting(1, "Mechanical Engineering Intern - Summer 2027"), posting(2, "Software Intern")]
    out = run.runCycle(cfg, state, http=None)
    assert out["newMatches"] == []  # baseline
    rec = state["jobs"]["fake:acme:1"]
    assert rec["match"] and rec["alerted"] and "U.S. person" in rec["description"]

    # every posting gets batch-touched, nothing new should fire
    board[:] = [posting(1, "Mechanical Engineering Intern - Summer 2027", updated="2026-10-20"), posting(2, "Software Intern", "2026-10-20")]
    assert run.runCycle(cfg, state, http=None)["newMatches"] == []

    # a genuinely new id fires once, with its first-seen time
    board.append(posting(3, "Propulsion Test Intern - Summer 2027"))
    out = run.runCycle(cfg, state, http=None)
    assert [j["key"] for j in out["newMatches"]] == ["fake:acme:3"]
    assert state["jobs"]["fake:acme:3"]["firstSeen"]
    assert run.runCycle(cfg, state, http=None)["newMatches"] == []


def test_closed_postings_and_snapshot():
    state = fresh()
    board[:] = [posting(1, "Mechanical Engineering Intern - Summer 2027")]
    run.runCycle(cfg, state, http=None)
    board[:] = []
    run.runCycle(cfg, state, http=None)
    assert state["jobs"]["fake:acme:1"]["closedAt"]
    snap = run.buildSnapshot(cfg, state)
    assert snap["jobs"][0]["closedAt"] and snap["companies"][0]["status"] == "0 jobs"
    board[:] = [posting(1, "Mechanical Engineering Intern - Summer 2027")]
    run.runCycle(cfg, state, http=None)
    assert "closedAt" not in state["jobs"]["fake:acme:1"]


def test_blocked_board_is_marked_and_skipped():
    from finder.http import Blocked

    def blocked(c, http, keep, cache):
        raise Blocked("403 from acme")
    ats.adapters["fakeblocked"] = (blocked, None)
    c2 = dict(cfg, companies=[{"name": "Walled Co", "ats": "fakeblocked", "token": "w"}])
    state = fresh()
    out = run.runCycle(c2, state, http=None)
    assert out["results"]["Walled Co"]["status"] == "blocked"
    assert state["companies"]["Walled Co"]["status"] == "blocked"
    assert "blocked" in run.statusTable(out["results"], out["due"], state)


def test_staggering_spreads_non_priority_companies():
    companies = [{"name": f"Co {i}", "ats": "fake"} for i in range(40)]
    state = {"companies": {c["name"]: {"lastOk": "2026-10-19T00:00:00+00:00"} for c in companies}}
    c = {"schedule": {"defaultEveryRuns": 2}}
    a = {x["name"] for x in run.dueCompanies(companies, state, c, 10)}
    b = {x["name"] for x in run.dueCompanies(companies, state, c, 11)}
    assert a and b and not (a & b) and len(a | b) == 40


def test_alert_batching():
    jobs = [{"company": "Acme", "title": f"ME Intern {i}", "score": 50 + i, "flags": [], "url": f"u{i}", "location": "Seattle"} for i in range(6)]
    msgs = notify.plan(jobs, maxPerRun=5)
    assert len(msgs) == 1 and msgs[0]["title"] == "6 new internships"
    assert notify.plan(jobs[:2], maxPerRun=5)[0]["title"].startswith("Acme: ME Intern 1")


def test_rising_junior_flag_in_alert_text():
    j = {"company": "ULA", "title": "Weld Engineering Internship", "score": 40, "url": "u", "location": "Decatur, AL",
         "flags": [{"flag": "risingJuniorMin"}, {"flag": "usPerson"}], "term": "match"}
    assert "rising-junior min" in notify.single(j)["body"] and "US person" in notify.single(j)["body"]
