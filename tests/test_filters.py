## title, term, eligibility, and ranking rules
import pytest

from finder import filters as f

cfg = {"search": {"term": {"season": "summer", "year": 2027}, "bigCities": ["houston", "seattle", "chicago", "los angeles"]}}


@pytest.mark.parametrize("title,ok", [
    ("Mechanical Engineering Intern - Summer 2027", True),
    ("2027 Summer Intern - Motorsports Aerodynamics", True),
    ("Engineering Internship/Co-op (Summer 2027)", True),
    ("Manufacturing Engineering Co-Op", True),
    ("Materials Engineering Lab Co-Op (Spring/Summer 2027)", True),
    ("Summer 2027 Structural & Mechanical Engineering Internship - Undergraduate", True),
    ("Hardware Engineering Intern", True),
    ("Test Engineer Intern", True),
    ("Software Engineering Intern", False),
    ("Firmware Intern", False),
    ("Electrical Engineering Intern", False),
    ("Systems Integration/Electrical Test Engineer-INTERN", False),  # electrical test is ee work
    ("Civil Engineering Internship Summer 2027", False),
    ("Summer 2027 Supply Chain Internship", False),
    ("Operations Management Intern", False),
    ("Finance Intern", False),
    ("Product Marketing and Strategy Intern 2027", False),
    ("Internal Audit Manager", False),
    ("International Logistics Manager", False),
    ("Senior Mechanical Engineer", False),
])
def test_title_match(title, ok):
    assert (f.isInternTitle(title) and f.disciplineOk(title)) == ok


@pytest.mark.parametrize("title,desc,expect", [
    ("Mechanical Engineering Intern - Summer 2027", "", "match"),
    ("2027 Mechanical Engineer Intern", "", "match"),
    ("Materials Engineering Co-Op (Spring/Summer 2027)", "", "match"),
    ("Mechanical Engineering Intern - Summer 2026", "", "other"),
    ("Materials Engineering Co-op Fall 2027", "", "other"),
    ("Tesla Battery Mechanical Design Intern Winter/Spring 2027", "", "other"),
    ("Mechanical Engineering Intern", "Join us for summer 2027 in Houston", "match"),
    ("Mechanical Engineering Intern", "This internship ran in Summer 2025", "other"),
    ("Mechanical Engineering Intern", "Twelve week paid program", "unspecified"),
    ("Engineering Intern '27", "", "unspecified"),
])
def test_term(title, desc, expect):
    assert f.termStatus(title, desc) == expect


@pytest.mark.parametrize("text,flag", [
    ("Must have completed junior year by the start date", "risingJuniorMin"),
    ("Students must have completed their sophomore year by the start of the internship.", "sophomoreDone"),
    ("Must have completed third year of study", "risingJuniorMin"),
    ("Minimum of 60 credit hours completed", "risingJuniorMin"),
    ("Junior or senior standing in Mechanical Engineering", "risingJuniorMin"),
    ("Open to rising juniors and seniors", "sophomoreDone"),
    ("Entering the junior or senior year of study", "sophomoreDone"),
    ("Rising seniors only", "risingJuniorMin"),
    ("Current 3rd or 4th year undergraduate", "risingJuniorMin"),
    ("Must be a U.S. Person as defined by ITAR", "usPerson"),
    ("U.S. citizenship is required", "usPerson"),
    ("Ability to obtain a DoD Secret clearance", "clearance"),
    ("Open to freshmen, sophomores and juniors", "sophomoreFriendly"),
])
def test_flags(text, flag):
    assert flag in {x["flag"] for x in f.eligibilityFlags(text)}


def test_no_false_rising_junior_flag():
    flags = {x["flag"] for x in f.eligibilityFlags("Pursuing a BS in mechanical engineering, 12 week program, 40 hours per week")}
    assert "risingJuniorMin" not in flags


def test_flags_carry_evidence():
    x = f.eligibilityFlags("Pay is great. Must have completed junior year before June. Apply now.")[0]
    assert "completed junior year" in x["evidence"]


def test_ranking_prefers_hands_on_and_penalizes_mep_and_transit():
    company = {"tier": 2}
    good = {"title": "Mechanical Engineering Prototyping Intern", "location": "Seattle, WA", "description": ""}
    mep = {"title": "Mechanical Engineering Intern - MEP Building Systems", "location": "Seattle, WA", "description": ""}
    rail = {"title": "Track and Rail Mechanical Engineering Intern", "location": "Chicago, IL", "description": ""}
    sg, _ = f.score(good, company, cfg["search"]["bigCities"])
    sm, why = f.score(mep, company, cfg["search"]["bigCities"])
    sr, _ = f.score(rail, company, cfg["search"]["bigCities"])
    assert sg > sm and sg > sr and "building/transit/maintenance" in why


def test_rising_junior_flag_lowers_but_keeps_match():
    j = {"title": "Mechanical Engineering Intern - Summer 2027", "location": "Houston, TX",
         "description": "Junior or senior standing required. U.S. citizen required."}
    assert f.evaluate(j, {"tier": 1}, cfg) is True
    assert {"risingJuniorMin", "usPerson"} <= {x["flag"] for x in j["flags"]}
    clean = {"title": "Mechanical Engineering Intern - Summer 2027", "location": "Houston, TX", "description": ""}
    f.evaluate(clean, {"tier": 1}, cfg)
    assert clean["score"] > j["score"]


def test_notable_company_outside_big_city_still_ranks():
    j = {"title": "Propulsion Engineering Intern - Summer 2027", "location": "McGregor, TX", "description": ""}
    f.evaluate(j, {"tier": 1}, cfg)
    assert j["score"] >= 70


## fixes from the first real run (oct 22)
@pytest.mark.parametrize("title,strict,ok", [
    ("Software Development Engineer Intern, ROBOTICS - 2027", False, False),
    ("Flight Software Engineering Intern (Simulation/Hardware-In-The-Loop)", False, False),
    ("Summer 2027 Test Engineering Internship - Graduate", False, False),
    ("Summer 2027 Test Engineering Internship - Undergraduate", False, True),
    ("Robotics Research, Humanoid Manipulation Intern (Summer 2027) | PhD", False, False),
    ("Hardware Sourcing Intern", False, False),
    ("Wireless Hardware Engineer Intern - Summer 2027", False, False),
    ("Data Center Engineering Operations - 2027 Internship", False, False),
    ("Civil Engineering Intern-Coastal Infrastructure (Summer 2027)", False, False),
    ("Mechanical Engineering Co-op", False, True),
    ("Performance Engineering Intern - Poughkeepsie", True, False),
    ("Hardware Developer Engineer Intern (Mechanical) 2027", True, True),
])
def test_title_fixes(title, strict, ok):
    assert (f.isInternTitle(title) and f.disciplineOk(title, strict)) == ok


@pytest.mark.parametrize("loc,ok", [
    ("Los Angeles, CA", True), ("Milpitas, CA", True), ("Paris, TX", True), ("Ontario, CA", True),
    ("Cape Canaveral, FL, US, 32925", True), ("Seattle, WA / Toronto, Ontario", True), ("Multiple Cities", True), ("", True),
    ("Markham, CA", False), ("Mississauga, ON, CA", False), ("Hanoi, VNM", False), ("Singapore, SG, 627596", False),
    ("Rotterdam, ZH, NL, 3197 KA", False), ("Mansfield, England, GBR", False), ("Ehningen, DE", False),
])
def test_us_locations(loc, ok):
    assert f.usLocationOk(loc) == ok


def test_bare_season_in_title():
    assert f.termStatus("Spring CoOp - Mechanical Engineering", "") == "other"
    assert f.termStatus("Summer Intern - Mechanical Engineering", "") == "unspecified"


def test_flag_false_positives():
    assert f.eligibilityFlags("40-50 hours per week with set hourly salary") == []
    assert f.eligibilityFlags("expectations comparable to those of a first-year engineer") == []
    flags = {x["flag"] for x in f.eligibilityFlags("At minimum completed Sophomore year of college by the internship")}
    assert flags == {"sophomoreDone"}
    assert "sophomoreFriendly" in {x["flag"] for x in f.eligibilityFlags("must have obtained sophomore standing")}


## fixes from the overnight runs (oct 22)
@pytest.mark.parametrize("title,strict,ok", [
    ("Research Intern - Agentic Data Memory", True, False),
    ("Research Intern - Brain-Computer Interfaces", True, False),
    ("NVIDIA 2027 Internships: Hardware Physical Design / VLSI", True, False),
    ("Intern - Design Engineer, HBM", True, False),
    ("Mechanical Engineer Intern - Thermal", True, True),
    ("Summer 2027 Internship - Information Security Engineer", False, False),
    ("Military DoD SkillBridge Internship - Structure Parts Operations Supervisor", False, False),
    ("Test Engineer Intern - Summer 2027 (For SNC Summer 2026 Interns Only)", False, False),
    ("Manufacturing Engineering Intern – US – Summer 2027 - Returning Students", False, False),
    ("Presale Systems Engineer - Summer 2027 Internship", False, False),
    ("Structures Engineering Internship - Summer 2027", False, True),
])
def test_overnight_title_fixes(title, strict, ok):
    assert (f.isInternTitle(title) and f.disciplineOk(title, strict)) == ok


def test_overnight_location_and_term_fixes():
    assert not f.usLocationOk("Fab 10N/X, Singapore")
    assert not f.usLocationOk("Auckland, NZ")
    assert f.usLocationOk("Long Beach, CA / Auckland, NZ")
    assert f.termStatus("Test Engineering Co-op (Jan27-May27)", "") == "other"
    assert f.termStatus("Engineering Co-op (Jan- Aug) 27", "") == "unspecified"
