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
    ("Systems Integration/Electrical Test Engineer-INTERN", True),  # test engineering beats the electrical exclusion
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
    ("Students must have completed their sophomore year by the start of the internship.", "risingJuniorMin"),
    ("Minimum of 60 credit hours completed", "risingJuniorMin"),
    ("Junior or senior standing in Mechanical Engineering", "risingJuniorMin"),
    ("Open to rising juniors and seniors", "risingJuniorMin"),
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
