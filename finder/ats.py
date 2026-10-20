## one small adapter per applicant tracking system, all using official public job-board endpoints
# every adapter returns normalized job dicts:
#   id, title, location, url, postedAt (iso or None), description (text or None)
# keep(title) is a cheap title prefilter so huge boards don't get carried around in memory
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

tagRe = re.compile(r"<[^>]+>")
spaceRe = re.compile(r"[ \t\r\f\v]+")


def htmlToText(s):
    if not s:
        return ""
    s = html.unescape(s)
    if "&lt;" in s or "&gt;" in s:
        s = html.unescape(s)  # greenhouse double-escapes content
    s = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</div>|</h\d>", "\n", s)
    s = html.unescape(tagRe.sub(" ", s))
    s = spaceRe.sub(" ", s)
    s = re.sub(r" *\n *", "\n", s)
    return re.sub(r"\n{2,}", "\n", s).strip()


def isoFromEpoch(value, millis=False):
    if value in (None, ""):
        return None
    try:
        v = float(value) / (1000 if millis else 1)
        return datetime.fromtimestamp(v, timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError):
        return None


def job(id, title, location, url, postedAt=None, description=None):
    return {"id": str(id), "title": (title or "").strip(), "location": (location or "").strip(),
            "url": url, "postedAt": postedAt, "description": description}


## greenhouse
def greenhouseList(c, http, keep, cache):
    data = http.getJson(f"https://boards-api.greenhouse.io/v1/boards/{c['token']}/jobs")
    return greenhouseParse(data, keep)


def greenhouseParse(data, keep):
    out = []
    for j in data.get("jobs", []):
        if not keep(j.get("title", "")):
            continue
        # updated_at gets batch-touched on many boards, so only first_published counts as a date
        out.append(job(j["id"], j.get("title"), (j.get("location") or {}).get("name"), j.get("absolute_url"),
                       postedAt=j.get("first_published")))
    return out


def greenhouseDetail(c, j, http):
    data = http.getJson(f"https://boards-api.greenhouse.io/v1/boards/{c['token']}/jobs/{j['id']}")
    return htmlToText(data.get("content"))


## lever
def leverList(c, http, keep, cache):
    data = http.getJson(f"https://api.lever.co/v0/postings/{c['token']}?mode=json")
    return leverParse(data, keep)


def leverParse(data, keep):
    out = []
    for p in data or []:
        if not keep(p.get("text", "")):
            continue
        cats = p.get("categories") or {}
        locs = cats.get("allLocations") or ([cats["location"]] if cats.get("location") else [])
        parts = [p.get("descriptionPlain") or ""]
        for block in p.get("lists") or []:
            parts.append(block.get("text", "") + "\n" + htmlToText(block.get("content", "")))
        parts.append(p.get("additionalPlain") or "")
        out.append(job(p["id"], p.get("text"), " / ".join(locs), p.get("hostedUrl"),
                       postedAt=isoFromEpoch(p.get("createdAt"), millis=True), description="\n".join(parts).strip()))
    return out


## ashby
def ashbyList(c, http, keep, cache):
    data = http.getJson(f"https://api.ashbyhq.com/posting-api/job-board/{c['token']}")
    return ashbyParse(data, keep)


def ashbyParse(data, keep):
    out = []
    for p in data.get("jobs", []):
        if p.get("isListed") is False or not keep(p.get("title", "")):
            continue
        locs = [p.get("location") or ""] + [s.get("location", "") for s in p.get("secondaryLocations") or []]
        desc = p.get("descriptionPlain") or htmlToText(p.get("descriptionHtml"))
        out.append(job(p["id"], p.get("title"), " / ".join(l for l in locs if l), p.get("jobUrl"),
                       postedAt=p.get("publishedAt"), description=desc or None))
    return out


## workday (cxs json search, POST)
internFacetRe = re.compile(r"intern|co-?op|student", re.I)
facetPreference = ["workerSubType", "timeType", "jobFamilyGroup", "jobFamily"]


def workdayFacetPick(facets):
    # finds facet values tagged intern/co-op/student, preferring worker-type style facets
    found = {}

    def walk(node, param):
        for v in node.get("values") or []:
            if v.get("values"):
                walk(v, v.get("facetParameter") or param)
            elif internFacetRe.search(v.get("descriptor") or ""):
                found.setdefault(param, []).append((v.get("id"), v.get("count") or 0))
    for f in facets or []:
        walk(f, f.get("facetParameter"))
    if not found:
        return None, []
    ranked = sorted(found, key=lambda p: (facetPreference.index(p) if p in facetPreference else 9, -sum(n for _, n in found[p])))
    param = ranked[0]
    return param, [i for i, _ in found[param] if i]


def workdayList(c, http, keep, cache, wdCfg=None):
    wdCfg = wdCfg or {}
    host = c["host"]
    tenant = host.split(".")[0]
    maxPages = wdCfg.get("maxPages", 8)
    out, seen = [], set()
    for site in c.get("sites") or [c.get("site")]:
        api = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        cacheKey = f"{host}/{site}"
        facet = cache.get(cacheKey)
        if facet is None:
            first = http.postJson(api, {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
            param, ids = workdayFacetPick(first.get("facets"))
            facet = {"param": param, "ids": ids}
            cache[cacheKey] = facet
        passes = []
        if facet.get("param"):
            passes.append(({facet["param"]: facet["ids"]}, "", maxPages))
        for q in wdCfg.get("queries", ["internship", "co-op"]):
            passes.append(({}, q, wdCfg.get("keywordPages", 2) if facet.get("param") else maxPages))
        for applied, text, pages in passes:
            for page in range(pages):
                data = http.postJson(api, {"appliedFacets": applied, "limit": 20, "offset": page * 20, "searchText": text})
                rows = data.get("jobPostings") or []
                for j in workdayParse(data, keep, host, site):
                    if j["id"] not in seen:
                        seen.add(j["id"])
                        out.append(j)
                if len(rows) < 20 or (page + 1) * 20 >= (data.get("total") or 0):
                    break
    return out


def workdayParse(data, keep, host, site):
    out = []
    for p in data.get("jobPostings") or []:
        title = p.get("title", "")
        if not keep(title) or not p.get("externalPath"):
            continue
        bullets = p.get("bulletFields") or []
        reqId = bullets[0] if bullets else p["externalPath"].rsplit("_", 1)[-1]
        out.append(job(reqId, title, p.get("locationsText"), f"https://{host}/en-US/{site}{p['externalPath']}",
                       postedAt=None, description=None) | {"detailPath": p["externalPath"], "site": site})
    return out


def workdayDetail(c, j, http):
    host = c["host"]
    tenant = host.split(".")[0]
    data = http.getJson(f"https://{host}/wday/cxs/{tenant}/{j['site']}{j['detailPath']}")
    info = data.get("jobPostingInfo") or {}
    locs = [info.get("location") or ""] + list(info.get("additionalLocations") or [])
    j["location"] = " / ".join(l for l in locs if l) or j["location"]
    if info.get("startDate"):
        j["postedAt"] = info["startDate"]
    return htmlToText(info.get("jobDescription"))


## successfactors career site (official rss job feed, newest 20 per keyword)
def successfactorsList(c, http, keep, cache):
    out, seen = [], set()
    for kw in c.get("keywords") or ["internship", "intern", "co-op"]:
        text = http.getText(f"https://{c['host']}/services/rss/job/?locale=en_US&keywords={quote(kw)}")
        for j in successfactorsParse(text, keep):
            if j["id"] not in seen:
                seen.add(j["id"])
                out.append(j)
    return out


def successfactorsParse(text, keep):
    out = []
    root = ET.fromstring(text.encode("utf-8") if isinstance(text, str) else text)
    for item in root.iter("item"):
        raw = (item.findtext("title") or "").strip()
        # titles look like "Mechanical Engineering Internship - Summer 2027 (Decatur, AL, US, 35601)"
        m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", raw)
        title, location = (m.group(1), m.group(2)) if m else (raw, "")
        if not keep(title):
            continue
        link = (item.findtext("link") or "").strip()
        idMatch = re.search(r"/(\d{6,})/?(?:\?|$)", link)
        jobId = idMatch.group(1) if idMatch else (item.findtext("guid") or link)
        posted = None
        try:
            posted = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            pass
        out.append(job(jobId, title, location, link.split("?")[0], postedAt=posted,
                       description=htmlToText(item.findtext("description"))))
    return out


## eightfold (pcsx career-site search)
def eightfoldList(c, http, keep, cache):
    out, seen = [], set()
    for q in c.get("queries") or ["intern", "co-op"]:
        for page in range(c.get("pages", 5)):
            url = (f"https://{c['host']}/api/pcsx/search?domain={c['domain']}&query={quote(q)}"
                   f"&location=&start={page * 10}&sort_by=timestamp")
            data = http.getJson(url)
            rows = eightfoldParse(data, keep, c["host"])
            for j in rows:
                if j["id"] not in seen:
                    seen.add(j["id"])
                    out.append(j)
            got = len((data.get("data") or {}).get("positions") or [])
            if got < 10:
                break
    return out


def eightfoldParse(data, keep, host):
    out = []
    for p in (data.get("data") or {}).get("positions") or []:
        if not keep(p.get("name", "")):
            continue
        out.append(job(p["id"], p.get("name"), " / ".join(p.get("locations") or []),
                       f"https://{host}{p.get('positionUrl') or '/careers/job/' + str(p['id'])}",
                       postedAt=isoFromEpoch(p.get("postedTs"))))
    return out


def eightfoldDetail(c, j, http):
    data = http.getJson(f"https://{c['host']}/api/pcsx/position_details?position_id={j['id']}&domain={c['domain']}&hl=en")
    return htmlToText((data.get("data") or {}).get("jobDescription"))


## oracle recruiting cloud (candidate experience rest api)
def oracleList(c, http, keep, cache):
    out, seen = [], set()
    for q in c.get("queries") or ["intern", "co-op"]:
        for page in range(c.get("pages", 4)):
            url = (f"https://{c['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
                   f"&expand=requisitionList&finder=findReqs;siteNumber={c['site']},keyword={quote(q)},"
                   f"limit=25,offset={page * 25},sortBy=POSTING_DATES_DESC")
            data = http.getJson(url)
            rows = oracleParse(data, keep, c["host"], c["site"])
            for j in rows:
                if j["id"] not in seen:
                    seen.add(j["id"])
                    out.append(j)
            items = data.get("items") or [{}]
            if len(items[0].get("requisitionList") or []) < 25:
                break
    return out


def oracleParse(data, keep, host, site):
    out = []
    for item in data.get("items") or []:
        for r in item.get("requisitionList") or []:
            if not keep(r.get("Title", "")):
                continue
            out.append(job(r["Id"], r.get("Title"), r.get("PrimaryLocation"),
                           f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{r['Id']}",
                           postedAt=r.get("PostedDate")))
    return out


def oracleDetail(c, j, http):
    url = (f"https://{c['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all"
           f"&onlyData=true&finder=ById;Id=%22{j['id']}%22,siteNumber={c['site']}")
    items = http.getJson(url).get("items") or [{}]
    d = items[0]
    return "\n".join(htmlToText(d.get(k)) for k in ("ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr"))


## smartrecruiters
def smartrecruitersList(c, http, keep, cache):
    out = []
    for page in range(c.get("pages", 10)):
        data = http.getJson(f"https://api.smartrecruiters.com/v1/companies/{c['token']}/postings"
                            f"?limit=100&offset={page * 100}&country=us")
        out += smartrecruitersParse(data, keep, c["token"])
        if (page + 1) * 100 >= (data.get("totalFound") or 0):
            break
    return out


def smartrecruitersParse(data, keep, token):
    out = []
    for p in data.get("content") or []:
        if not keep(p.get("name", "")):
            continue
        loc = (p.get("location") or {}).get("fullLocation") or (p.get("location") or {}).get("city")
        out.append(job(p["id"], p.get("name"), loc, f"https://jobs.smartrecruiters.com/{token}/{p['id']}",
                       postedAt=p.get("releasedDate")))
    return out


def smartrecruitersDetail(c, j, http):
    data = http.getJson(f"https://api.smartrecruiters.com/v1/companies/{c['token']}/postings/{j['id']}")
    sections = ((data.get("jobAd") or {}).get("sections")) or {}
    return "\n".join(htmlToText((sections.get(k) or {}).get("text")) for k in ("jobDescription", "qualifications", "additionalInformation"))


## amazon.jobs (public search json)
amazonQueries = ["mechanical engineering intern", "hardware engineering intern", "manufacturing engineering intern",
                 "engineering co-op", "robotics intern"]


def amazonList(c, http, keep, cache):
    out, seen = [], set()
    for q in c.get("queries") or amazonQueries:
        data = http.getJson(f"https://www.amazon.jobs/en/search.json?base_query={quote(q)}&result_limit=100&offset=0&sort=recent")
        for j in amazonParse(data, keep):
            if j["id"] not in seen:
                seen.add(j["id"])
                out.append(j)
    return out


def amazonParse(data, keep):
    out = []
    for p in data.get("jobs") or []:
        if not keep(p.get("title", "")):
            continue
        desc = "\n".join(htmlToText(p.get(k)) for k in ("description", "basic_qualifications", "preferred_qualifications"))
        posted = None
        try:
            posted = datetime.strptime(p.get("posted_date", ""), "%B %d, %Y").date().isoformat()
        except ValueError:
            pass
        out.append(job(p.get("id_icims") or p.get("id"), p.get("title"), p.get("normalized_location") or p.get("location"),
                       "https://www.amazon.jobs" + (p.get("job_path") or ""), postedAt=posted, description=desc))
    return out


## ibm careers (public search api behind ibm.com/careers)
def ibmList(c, http, keep, cache):
    body = {"appId": "careers", "scopes": ["careers2"], "size": 100, "from": 0,
            "query": {"bool": {"must": [{"simple_query_string": {"query": "intern", "fields": ["title^3", "description^2", "keywords"]}}]}},
            "sort": [{"dcdate": "desc"}, {"_score": "desc"}], "lang": "zz", "localeSelector": {}, "sm": {"query": "intern", "lang": "zz"},
            "_source": ["_id", "title", "url", "description", "dcdate", "field_keyword_17", "field_keyword_18", "field_keyword_19"]}
    data = http.postJson("https://www-api.ibm.com/search/api/v2", body)
    return ibmParse(data, keep)


def ibmParse(data, keep):
    out = []
    for h in (data.get("hits") or {}).get("hits") or []:
        s = h.get("_source") or {}
        if not keep(s.get("title", "")):
            continue
        loc = s.get("field_keyword_19") or s.get("field_keyword_17") or ""
        if isinstance(loc, list):
            loc = " / ".join(loc)
        out.append(job(h.get("_id"), s.get("title"), loc, s.get("url"), postedAt=s.get("dcdate"),
                       description=htmlToText(s.get("description"))))
    return out


## registry
adapters = {
    "greenhouse": (greenhouseList, greenhouseDetail),
    "lever": (leverList, None),
    "ashby": (ashbyList, None),
    "workday": (workdayList, workdayDetail),
    "successfactors": (successfactorsList, None),
    "eightfold": (eightfoldList, eightfoldDetail),
    "oracle": (oracleList, oracleDetail),
    "smartrecruiters": (smartrecruitersList, smartrecruitersDetail),
    "amazon": (amazonList, None),
    "ibm": (ibmList, None),
}


def boardKey(c):
    # stable identity for a company's board, used to namespace job ids
    return c.get("token") or c.get("host") or c["ats"]
