# Internship Finder

Watches the official careers boards of 140 engineering employers (Fortune 250 companies, big aerospace, defense, automotive, industrial, energy and medical device firms, and hardware startups in space, fusion and fission, robotics, defense tech, eVTOL and batteries) for Summer 2027 mechanical, manufacturing, aerospace, materials, design, test and hardware engineering internships and co-ops. A new posting pings your phone through ntfy within about 15 to 30 minutes and lands on a dashboard you can open on your phone.

Dashboard: https://db165.github.io/internship-finder/

## How it works

```
Raspberry Pi at home (every 15 min)
   ├─ Greenhouse, Lever, Ashby ......... public job-board APIs
   ├─ Workday ......................... /wday/cxs/{tenant}/{site}/jobs search
   ├─ SuccessFactors .................. official career-site RSS feed
   ├─ Eightfold, Oracle, SmartRecruiters, amazon.jobs, IBM careers
   │
   ├─ filters.py ── intern/co-op titles only, ME-type disciplines, Summer 2027 (or term not stated),
   │                flags rising-junior minimums, US person and clearance, ranks by taste
   ├─ ntfy ──────── one ping per new posting, or one batched summary when a lot land at once
   └─ push ──────── jobs.json + seen.json to the "snapshot" branch over an ssh deploy key
                         │
                         ▼
        GitHub Pages dashboard (docs/index.html) reads snapshot/jobs.json
        "MechE Internship Sweep" scheduled task reads the same file
```

"New" means a job id this Pi has never seen before. The time it was first seen is recorded and shown. Board-wide "updated" timestamps are ignored on purpose (Anduril, Neuralink, Vast, Astranis, Varda and others batch-touch every posting). The first time a company is checked its existing postings are recorded quietly, so the first run and any newly added company never flood your phone.

Rising-junior-minimum language ("completed junior year", "completed sophomore year by...", "60 credit hours", "junior or senior standing", "rising junior", "3rd or 4th year") is flagged, never hidden. The flag shows the exact sentence it matched, so you can judge it. US person, ITAR and clearance requirements get their own flags. Ranking boosts hands-on R&D, prototyping, test and hardware roles, notable companies anywhere, and big cities; it lowers MEP/building systems, transit and plant maintenance roles.

## Raspberry Pi

Runs alongside the car finder without touching it: its own folder (`~/internship-finder`), deploy key (`~/.ssh/internships_deploy`, ssh alias `github-internships`), and systemd units (`internships.service` / `internships.timer`). It only needs `git`, `python3-requests` and `python3-yaml`.

First time:

```
curl -fsSL https://raw.githubusercontent.com/db165/internship-finder/main/pi/setup.sh | bash
```

Re-run any time (safe, skips what's done):

```
cd ~/internship-finder && git pull && bash pi/setup.sh
```

The setup script asks for an ntfy topic and saves it to `~/.config/internship-finder/env` on the Pi only. The topic is never committed, since this repo is public. Logs: `journalctl -u internships -n 60`.

## Phone alerts (ntfy)

Install the ntfy app (iOS App Store or Google Play), tap +, and subscribe to the topic name the setup script printed. Keep it separate from the car alerts topic. High-scoring matches arrive as high priority. More than 5 new matches in one run arrive as a single summary.

## The sweep task

The snapshot is public at `https://raw.githubusercontent.com/db165/internship-finder/snapshot/jobs.json` (GitHub caches it for about 5 minutes). Each job has `key`, `company`, `sector`, `title`, `location`, `url`, `firstSeen`, `postedAt`, `term` (`match` or `unspecified`), `flags` (with evidence), `score`, `why`, `closedAt` and a description `snippet`.

## Editing the company list

Everything lives in `config.yml`. The Pi pulls changes every run, so editing on github.com is enough. Each company names its board type and the fields it needs (see the comment at the top of the list). Mark `priority: true` to check a company every run instead of every second run. The dashboard's Boards tab shows each board as ok, 0 jobs, blocked or error.

## Manners

Official public job-board endpoints only. No LinkedIn, Handshake, Indeed or Glassdoor, and no getting around bot walls: a 403, 429 or captcha page marks that board blocked and the run moves on. One board at a time (a Pi 3 froze when it parsed several big boards at once), at most one request per host every 1.5 seconds, a 700 MB memory cap, companies staggered across runs, Workday intern facets cached for a day, and each posting's full description fetched once and cached.

## Coverage

Checked and verified to return jobs (October 2026): 58 Greenhouse boards, 32 Workday sites, 21 Ashby, 13 Lever, 5 SuccessFactors feeds (ULA, Westinghouse, John Deere, ExxonMobil, Boston Scientific), Eightfold (Lockheed Martin, Eaton, Microsoft), Oracle (Honeywell, Emerson), SmartRecruiters (Intuitive, Bosch, Continental, Western Digital), amazon.jobs and IBM.

Not covered yet, and why:

| Company | Reason |
| --- | --- |
| Tesla | Custom careers site behind bot protection, no public API |
| Apple, Google, Meta | Custom careers sites, search needs session tokens, no public API |
| L3Harris | Radancy front end, no public jobs endpoint exposed |
| Ford | Radancy front end, no public jobs endpoint exposed |
| BAE Systems | Phenom front end over BrassRing, no clean public endpoint |
| Textron (Bell, Textron Aviation, Textron Systems) | Oracle Taleo career sections, no clean public JSON |
| Rivian, Joby Aviation | iCIMS, no public JSON API |
| Oshkosh | Phenom front end, backing system not exposed |
| PACCAR | Legacy SuccessFactors page without the RSS feed |
| Boom Supersonic | Rippling ATS, no documented public API |
| Qualcomm | Eightfold board answered 429 (rate limited) when checked |
| General Dynamics (Electric Boat, GDMS, Gulfstream, NASSCO), HII, Cummins, Parker Hannifin, Whirlpool, Corning, Dell | Workday tenant guesses failed and no clean public endpoint found yet |
| Impulse Space, Castelion, Axiom Space, TAE, Carbon | Board not found on any supported ATS yet |
| National labs (LLNL, LANL, Sandia, NNL, JPL), Naval Nuclear Lab | Custom career sites, not researched yet |

If one of these turns up on a supported ATS, add a line to `config.yml`.

## Tests

`pip install pytest requests pyyaml && python -m pytest -q` runs offline tests for every board parser (trimmed real-shaped responses), the title, term and eligibility filters, ranking, the quiet first run, new-id detection, closed postings, blocked boards, staggering and alert batching.
