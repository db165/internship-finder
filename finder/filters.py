## what counts as a match, eligibility flags, and ranking
import re

## title gate (cheap, used by adapters before anything is stored)
internRe = re.compile(r"\bintern(s|ship|ships)?\b|\bco-?op\b|\bco op\b|\bcooperative education\b", re.I)
notInternRe = re.compile(r"\binternal\b|\binternational\b", re.I)


def isInternTitle(title):
    t = title or ""
    return bool(internRe.search(notInternRe.sub(" ", t)))


## discipline
wantRe = re.compile(
    r"mechanic|manufactur|aerospace|aeronaut|astronaut|aero|materials?\b|metallurg|propulsion|structur|"
    r"thermal|fluid|design eng|product design|product develop|mechanical design|cad\b|test eng|test &|"
    r"\btest\b|hardware|mechatronic|robotic|prototyp|\br&d\b|research|vehicle|engine\b|nuclear|reactor|"
    r"process eng|industrial eng|quality eng|reliability|additive|composite|weld|machin|tooling|"
    r"integration|launch|spacecraft|satellite|avionics mech|packaging eng|advanced eng|systems eng", re.I)
genericEngRe = re.compile(r"\bengineer(ing)?\b", re.I)
excludeRe = re.compile(
    r"software|firmware|\bsde\b|developer|data scien|data analy|data eng|machine learning|\bml\b|\bai\b engineer|"
    r"cyber|security analyst|\bit\b|information tech|cloud|devops|web\b|front.?end|back.?end|full.?stack|"
    r"electrical|electronics?\b|\brf\b|fpga|asic|pcb|analog|mixed.?signal|power electronics|circuit|"
    r"civil|environmental|geotech|transportation eng|"
    r"supply chain|procurement|purchasing|logistics|warehouse|operations intern|operations management|"
    r"finance|accounting|audit|tax\b|marketing|sales|business|hr\b|human resources|people ops|recruit|talent|"
    r"legal|paralegal|contracts|communications|public relations|design intern \(ux|ux\b|ui\b|graphic|"
    r"program manag|project coordinat|project manag|product manag|strategy|analyst intern|"
    r"clinical|regulatory|medical affairs|biolog|chemist|pharma|nurse|"
    r"technician|machinist|mechanic intern|apprentice", re.I)
# a mechanical word anywhere in the title beats a soft exclusion (e.g. "mechanical and electrical engineering intern")
mechTitleRe = re.compile(r"mechanic|manufactur|aerospace|materials|propulsion|structur|thermal|hardware|nuclear|test eng", re.I)
# these only get rescued by the word "mechanical" itself
hardExcludeRe = re.compile(
    r"software|firmware|supply chain|sourcing|material planning|material requirements|program manag|"
    r"data cent|site reliability|\bsre\b|algorithm|error correction|reinforcement learning|computer vision|"
    r"deep learning|foundation model|embodied ai|autonomy eng|network|platform|infrastructure|\bgpu\b|\bhpc\b|"
    r"electrical|electronics?\b|wireless|\brf\b|circuit|\beda\b|fpga|asic|"
    r"civil|coastal|waterfront|water eng|chemical eng|forward deployed|operations eng|engineering operations|"
    r"sales|marketing|finance|licensing|storage|performance eng", re.I)
gradOnlyRe = re.compile(r"(?<!under)graduate\b(?! *(?:\w+ +)?(?:program|rotation))|\bph\.?d\b|master'?s\b|\bmba\b", re.I)
undergradRe = re.compile(r"undergrad|bachelor|bs/ms|\bbs\b", re.I)


def disciplineOk(title, strict=False):
    t = title or ""
    if hardExcludeRe.search(t) and not re.search(r"mechanic", t, re.I):
        return False
    if excludeRe.search(t) and not mechTitleRe.search(t):
        return False
    if gradOnlyRe.search(t) and not undergradRe.search(t):
        return False  # graduate, phd and master's-only internships
    if strict:
        return bool(wantRe.search(t))  # big tech: "engineering intern" alone is usually software
    return bool(wantRe.search(t) or genericEngRe.search(t))


## location: us only (a posting with any us location counts)
foreignRe = re.compile(
    r"\b(?:canada|ontario|toronto|markham|mississauga|vancouver|montreal|quebec|mexico|brazil|argentina|chile|colombia|"
    r"uk|united kingdom|england|scotland|ireland|dublin|germany|deutschland|berlin|munich|ehningen|france|paris|spain|"
    r"barcelona|madrid|italy|milan|netherlands|rotterdam|belgium|antwerp\w*|luxembourg|switzerland|zurich|sweden|"
    r"poland|czech|austria|denmark|norway|finland|portugal|israel|india|bangalore|bengaluru|hyderabad|pune|chennai|china|"
    r"shanghai|beijing|shenzhen|hong kong|taiwan|taipei|japan|tokyo|korea|seoul|singapore|malaysia|kuala lumpur|penang|"
    r"vietnam|hanoi|ho chi minh|thailand|philippines|indonesia|australia|sydney|melbourne|new zealand|south africa|"
    r"cape town|uae|dubai|abu dhabi|saudi|riyadh|qatar|egypt|turkey|"
    r"can|mex|gbr|irl|deu|fra|esp|ita|nld|bel|lux|che|swe|pol|ind|chn|twn|jpn|kor|sgp|mys|vnm|tha|phl|aus|zaf|are|sau|isr)\b"
    r"|, (?:fr|es|it|nl|be|sg|my|cn|jp|kr|gb|ie|ch|se|pl|au|br|mx)(?:,|$)|\bl'hospitalet\b", re.I)


usStates = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR "
            "PA RI SC SD TN TX UT VT VA WA WV WI WY DC")
# "Paris, TX" or "Berlin, NH" are american even though the city name isn't
usRe = re.compile(r"united states|\busa\b|, us\b|, (?:" + "|".join(usStates.split()) + r")\b(?!,? *(?:ca|canada)\b)")


usStrongRe = re.compile(r"united states|\busa\b|, us\b", re.I)
# names that win over a state-looking suffix ("markham, ca" is canada, "ehningen, de" is germany)
canadaRe = re.compile(r"\b(?:ehningen|b[oö]blingen|bangalore|bengaluru|hyderabad|canada|toronto|markham|mississauga|ottawa|waterloo, on|vancouver|montreal|quebec|calgary|"
                      r"edmonton|winnipeg|halifax)\b|, (?:on|bc|qc|ab|mb|ns), ca\b", re.I)


def usLocationOk(location):
    loc = (location or "").strip()
    if not loc:
        return True
    parts = [p for p in re.split(r"\s*(?:/|;|\||\n)\s*", loc) if p]
    return any(usStrongRe.search(p) or (not canadaRe.search(p) and (usRe.search(p) or not foreignRe.search(p))) for p in parts)


## term: summer 2027 internships and co-ops
seasonRe = re.compile(r"\b(spring|summer|fall|autumn|winter)\b[\s/,&-]*(?:and|&|/)?\s*(?:(?:spring|summer|fall|autumn|winter)[\s/,&-]*)*'?(20\d\d|\d\d)\b|"
                      r"\b(20\d\d)\s+(spring|summer|fall|autumn|winter)\b", re.I)
yearRe = re.compile(r"\b(20[2-3]\d)\b")


def termsIn(text):
    found = set()
    for m in seasonRe.finditer(text or ""):
        chunk = m.group(0).lower()
        year = m.group(2) or m.group(3)
        year = int(year) if len(year) == 4 else 2000 + int(year)
        for season in re.findall(r"spring|summer|fall|autumn|winter", chunk):
            found.add((season.replace("autumn", "fall"), year))
    return found


def termStatus(title, description, season="summer", year=2027):
    # returns "match", "unspecified", or "other" (an explicit term that isn't ours)
    target = (season, year)
    titleTerms = termsIn(title)
    if titleTerms:
        return "match" if target in titleTerms else "other"
    bareSeasons = set(re.findall(r"\b(spring|summer|fall|autumn|winter)\b", title or "", re.I))
    if bareSeasons and season not in {b.lower() for b in bareSeasons}:
        return "other"  # e.g. "Spring CoOp - Mechanical Engineering"
    titleYears = {int(y) for y in yearRe.findall(title or "")}
    if titleYears and year not in titleYears:
        return "other"
    descTerms = termsIn((description or "")[:4000])
    if target in descTerms:
        return "match"
    if titleYears == {year}:
        return "match"  # e.g. "2027 Mechanical Engineering Intern"
    if descTerms and all(t[1] < year for t in descTerms):
        return "other"  # only mentions past cycles, so likely a stale repost
    return "unspecified"


## eligibility flags (flag, never hide)
risingJuniorRes = [
    r"complet\w*\s+(?:at least\s+)?(?:(?:his|her|their|your)\s+)?(?:the\s+)?(?:junior|sophomore|second|third)[\s-]+year",
    r"rising\s+(?:junior|senior)", r"junior\s+(?:or|/|and)\s+senior", r"junior(?:\s+or\s+senior)?\s+(?:class\s+)?standing",
    r"(?:third|3rd)\s+(?:or|/)\s+(?:fourth|4th)[\s-]+year", r"entering\s+(?:their|your)\s+(?:junior|senior|third|fourth)\s+year",
    r"minimum\s+of\s+(?:junior|third[\s-]year)", r"at least (?:a )?junior",
]
risingJuniorRe = re.compile("|".join(risingJuniorRes), re.I)
creditsRe = re.compile(r"(\d{2,3})\s*\+?\s*(?:or more\s+)?(?:college\s+|semester\s+|academic\s+)?(?:credit[\s-]+hours|credits|units)", re.I)
sophomoreFriendlyRe = re.compile(r"\bsophomores?\b|\bfreshm[ae]n\b|first[\s-]year (?:student|undergrad)|second[\s-]year (?:student|undergrad)|rising sophomore|sophomore standing", re.I)
usPersonRe = re.compile(r"u\.?\s?s\.?\s+person|us person|u\.?s\.?\s+citizen|united states citizen|citizenship (?:is )?required|\bitar\b|export control", re.I)
clearanceRe = re.compile(r"security clearance|secret clearance|\bts/sci\b|top secret|obtain (?:and maintain )?a? ?(?:dod |doe )?clearance|\bq clearance\b", re.I)


def eligibilityFlags(text):
    text = text or ""
    flags = []
    m = risingJuniorRe.search(text)
    if m:
        flags.append({"flag": "risingJuniorMin", "evidence": snippet(text, m)})
    else:
        for cm in creditsRe.finditer(text):
            if 45 <= int(cm.group(1)) <= 120:
                flags.append({"flag": "risingJuniorMin", "evidence": snippet(text, cm)})
                break
    sm = sophomoreFriendlyRe.search(risingJuniorRe.sub(" ", text))
    if sm:
        m2 = sophomoreFriendlyRe.search(text, max(0, sm.start() - 200))  # evidence from the original text
        flags.append({"flag": "sophomoreFriendly", "evidence": snippet(text, m2 or sm)})
    m = usPersonRe.search(text)
    if m:
        flags.append({"flag": "usPerson", "evidence": snippet(text, m)})
    m = clearanceRe.search(text)
    if m:
        flags.append({"flag": "clearance", "evidence": snippet(text, m)})
    return flags


def snippet(text, m, pad=70):
    a, b = max(0, m.start() - pad), min(len(text), m.end() + pad)
    return ("..." if a else "") + re.sub(r"\s+", " ", text[a:b]).strip() + ("..." if b < len(text) else "")


## taste and ranking
loveRe = re.compile(r"r&d|research|prototyp|hardware|design|test\b|propulsion|robotic|advanced|lab\b|build|vehicle|"
                    r"spacecraft|rocket|launch|\bengines?\b|structures|mechanisms|thermal|fluids|additive", re.I)
meh = re.compile(r"\bmep\b|hvac|building systems|buildings?\b|facilit|plumbing|fire protection|transit|rail|track|"
                 r"plant maintenance|maintenance|reliability|utility|utilities|construction|consult", re.I)
mehDescRe = re.compile(r"\bmep\b|hvac|building systems|plumbing|fire protection|transit agency|railroad|plant maintenance", re.I)


def score(j, company, bigCities):
    s = 50
    title = j["title"]
    text = title + " " + (j.get("description") or "")[:3000]
    reasons = []
    if re.search(r"mechanic", title, re.I):
        s += 10; reasons.append("mechanical")
    if loveRe.search(title):
        s += 15; reasons.append("hands-on/R&D")
    elif loveRe.search(text):
        s += 5
    if meh.search(title) or mehDescRe.search((j.get("description") or "")[:600]) or company.get("sector") in ("consulting", "transit"):
        s -= 30; reasons.append("building/transit/maintenance")
    if company.get("tier") == 1:
        s += 10; reasons.append("notable company")
    loc = (j.get("location") or "").lower()
    if any(city in loc for city in bigCities):
        s += 8; reasons.append("big city")
    flags = {f["flag"] for f in j.get("flags", [])}
    if "risingJuniorMin" in flags:
        s -= 20; reasons.append("rising-junior minimum")
    if "sophomoreFriendly" in flags:
        s += 5
    if j.get("term") == "unspecified":
        s -= 5
    return max(0, min(100, s)), reasons


def evaluate(j, company, cfg):
    # fills term/flags/score on a job and says whether it's a match
    term = cfg["search"]["term"]
    j["term"] = termStatus(j["title"], j.get("description"), term["season"], term["year"])
    j["flags"] = eligibilityFlags(j.get("description"))
    j["score"], j["why"] = score(j, company, cfg["search"].get("bigCities", []))
    strict = company.get("sector") in ("big tech", "semiconductors")
    return (isInternTitle(j["title"]) and disciplineOk(j["title"], strict) and j["term"] != "other"
            and usLocationOk(j.get("location")))
