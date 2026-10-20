## offline tests for every ats adapter, using trimmed real-shaped responses
from finder import ats
from finder.filters import isInternTitle as keep

from . import samples as s


class FakeHttp:
    # answers by url substring, records calls
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def find(self, url, body=None):
        self.calls.append((url, body))
        for pattern, value in self.routes:
            if pattern in url and (not callable(value)):
                return value
            if pattern in url:
                return value(url, body)
        raise AssertionError(f"unexpected url {url}")

    def getJson(self, url, **kw):
        return self.find(url)

    def postJson(self, url, body, **kw):
        return self.find(url, body)

    def getText(self, url, **kw):
        return self.find(url)


def test_greenhouse_list_and_detail():
    http = FakeHttp([("/jobs/8621740002", s.greenhouseDetail), ("/boards/spacex/jobs", s.greenhouseList)])
    c = {"ats": "greenhouse", "token": "spacex"}
    jobs = ats.greenhouseList(c, http, keep, {})
    assert [j["id"] for j in jobs] == ["8621740002"]  # internal/international titles don't count as intern
    assert jobs[0]["postedAt"].startswith("2026-09-16")  # first_published, never updated_at
    text = ats.greenhouseDetail(c, jobs[0], http)
    assert "U.S. person" in text and "<" not in text


def test_lever():
    jobs = ats.leverParse(s.leverList, keep)
    assert len(jobs) == 1
    j = jobs[0]
    assert j["location"] == "Austin, TX" and j["url"].startswith("https://jobs.lever.co/xcimer/")
    assert "Rising junior" in j["description"] and "US citizen" in j["description"]
    assert j["postedAt"].startswith("2026-")


def test_ashby_skips_unlisted():
    jobs = ats.ashbyParse(s.ashbyList, keep)
    assert [j["id"] for j in jobs] == ["4f1d"]
    assert jobs[0]["location"] == "Burlingame, CA / Remote"
    assert "sophomores" in jobs[0]["description"]


def test_workday_facet_pick_prefers_worker_type():
    param, ids = ats.workdayFacetPick(s.workdayFacets["facets"])
    assert param == "workerSubType" and ids == ["dd44", "ee55"]


def test_workday_list_uses_facets_then_keywords_and_dedups():
    def route(url, body):
        if body["limit"] == 1:
            return s.workdayFacets
        return s.workdayPage
    http = FakeHttp([("/wday/cxs/blueorigin/BlueOrigin/jobs", route)])
    c = {"ats": "workday", "host": "blueorigin.wd5.myworkdayjobs.com", "sites": ["BlueOrigin"]}
    cache = {}
    jobs = ats.workdayList(c, http, keep, cache, wdCfg={"maxPages": 3, "keywordPages": 1, "queries": ["internship"]})
    assert {j["id"] for j in jobs} == {"R73001", "R73002"}
    assert cache["blueorigin.wd5.myworkdayjobs.com/BlueOrigin"]["param"] == "workerSubType"
    bodies = [b for _, b in http.calls]
    assert bodies[1]["appliedFacets"] == {"workerSubType": ["dd44", "ee55"]}
    assert bodies[2]["searchText"] == "internship"
    # second run reuses the cached facet, no extra facet lookup
    http.calls.clear()
    ats.workdayList(c, http, keep, cache, wdCfg={"maxPages": 3, "keywordPages": 1, "queries": []})
    assert all(b["limit"] == 20 for _, b in http.calls)
    assert jobs[0]["url"] == "https://blueorigin.wd5.myworkdayjobs.com/en-US/BlueOrigin" + jobs[0]["detailPath"]


def test_workday_detail_fills_location_and_date():
    http = FakeHttp([("/job/", s.workdayDetail)])
    c = {"host": "blueorigin.wd5.myworkdayjobs.com"}
    j = ats.workdayParse(s.workdayPage, keep, c["host"], "BlueOrigin")[0]
    text = ats.workdayDetail(c, j, http)
    assert "completed your sophomore year" in text
    assert j["location"] == "Kent, WA / Huntsville, AL" and j["postedAt"] == "2026-10-19"
    assert http.calls[0][0].startswith("https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/job/")


def test_successfactors_rss():
    jobs = ats.successfactorsParse(s.successfactorsRss, keep)
    assert len(jobs) == 1
    j = jobs[0]
    assert j["id"] == "1427397600"
    assert j["title"] == "Composite Engineering Internship - Summer 2027" and j["location"] == "Decatur, AL, US, 35601"
    assert "?" not in j["url"] and j["postedAt"] == "2026-10-07T15:12:00+00:00"
    assert "sophomore year" in j["description"]


def test_eightfold_list_and_detail():
    http = FakeHttp([("position_details", s.eightfoldDetail), ("/api/pcsx/search", s.eightfoldSearch)])
    c = {"ats": "eightfold", "host": "lockheedmartin.eightfold.ai", "domain": "lockheedmartin.com", "queries": ["intern"], "pages": 1}
    jobs = ats.eightfoldList(c, http, keep, {})
    assert len(jobs) == 2
    j = jobs[1]
    assert j["url"] == "https://lockheedmartin.eightfold.ai/careers/job/996477338299"
    assert j["location"] == "Grand Prairie, TX / Orlando, FL" and j["postedAt"].startswith("2026-")
    assert "Secret clearance" in ats.eightfoldDetail(c, j, http)


def test_oracle_list_and_detail():
    http = FakeHttp([("recruitingCEJobRequisitionDetails", s.oracleDetail), ("recruitingCEJobRequisitions", s.oracleSearch)])
    c = {"ats": "oracle", "host": "ibqbjb.fa.ocs.oraclecloud.com", "site": "Honeywell", "queries": ["intern"], "pages": 1}
    jobs = ats.oracleList(c, http, keep, {})
    assert [j["id"] for j in jobs] == ["160296", "160300"]
    assert jobs[1]["url"].endswith("/sites/Honeywell/job/160300")
    assert "siteNumber=Honeywell,keyword=intern" in http.calls[0][0]
    assert "Junior or senior standing" in ats.oracleDetail(c, jobs[1], http)


def test_smartrecruiters():
    http = FakeHttp([("/postings/744000156384999", s.smartrecruitersDetail), ("/postings?", s.smartrecruitersList)])
    c = {"ats": "smartrecruiters", "token": "Intuitive"}
    jobs = ats.smartrecruitersList(c, http, keep, {})
    assert [j["id"] for j in jobs] == ["744000156384999"]
    assert jobs[0]["location"] == "Sunnyvale, CA, United States"
    assert "sophomore" in ats.smartrecruitersDetail(c, jobs[0], http)


def test_amazon():
    jobs = ats.amazonParse(s.amazonSearch, keep)
    assert len(jobs) == 2  # title gate only; discipline filtering happens later
    assert jobs[0]["url"] == "https://www.amazon.jobs/en/jobs/3070001/hardware-engineering-intern-summer-2027"
    assert jobs[0]["postedAt"] == "2026-10-15"


def test_ibm():
    jobs = ats.ibmParse(s.ibmSearch, keep)
    assert [j["id"] for j in jobs] == ["64512", "64513"]
    assert jobs[0]["location"] == "Poughkeepsie, US"


def test_html_to_text():
    assert ats.htmlToText("&lt;p&gt;a&amp;amp;b&lt;/p&gt;&lt;li&gt;c&lt;/li&gt;") == "a&b\nc"
