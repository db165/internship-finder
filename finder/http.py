## polite http: one session, per-host spacing, retries, and a clear status when a site blocks us
import threading
import time
from urllib.parse import urlparse

import requests

userAgent = "Mozilla/5.0 (compatible; internship-finder/1.0; personal job alerts; +https://github.com/db165/internship-finder)"


class Blocked(Exception):
    # site refused us (403/429/captcha). we never try to get around it
    pass


class Http:
    def __init__(self, delaySeconds=1.5, timeoutSeconds=25, session=None):
        self.delay = delaySeconds
        self.timeout = timeoutSeconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": userAgent, "Accept": "application/json, text/xml;q=0.9, */*;q=0.5"})
        self.lastHit = {}
        self.locks = {}
        self.guard = threading.Lock()
        self.requestCount = 0

    def hostLock(self, host):
        with self.guard:
            if host not in self.locks:
                self.locks[host] = threading.Lock()
            return self.locks[host]

    def request(self, method, url, **kw):
        host = urlparse(url).netloc
        kw.setdefault("timeout", self.timeout)
        with self.hostLock(host):
            for attempt in range(3):
                wait = self.lastHit.get(host, 0) + self.delay - time.time()
                if wait > 0:
                    time.sleep(wait)
                self.lastHit[host] = time.time()
                self.requestCount += 1
                try:
                    resp = self.session.request(method, url, **kw)
                except requests.RequestException:
                    if attempt == 2:
                        raise
                    time.sleep(3 * (attempt + 1))
                    continue
                if resp.status_code in (403, 429) or looksLikeChallenge(resp):
                    raise Blocked(f"{resp.status_code} from {host}")
                if resp.status_code >= 500 and attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp

    def getJson(self, url, **kw):
        return self.request("GET", url, **kw).json()

    def postJson(self, url, body, **kw):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        return self.request("POST", url, json=body, headers=headers, **kw).json()

    def getText(self, url, **kw):
        return self.request("GET", url, **kw).text


def looksLikeChallenge(resp):
    # bot walls usually answer 200 with an html challenge page where we expected json/xml
    ctype = resp.headers.get("content-type", "")
    if "html" not in ctype:
        return False
    head = resp.text[:3000].lower()
    return any(w in head for w in ("captcha", "cf-chl", "challenge-platform", "are you a robot", "access denied", "perimeterx"))
