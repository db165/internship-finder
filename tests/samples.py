## realistic (trimmed) responses from each job board api, shaped like what they returned in october 2026

greenhouseList = {
    "jobs": [
        {"absolute_url": "https://job-boards.greenhouse.io/spacex/jobs/8621740002", "internal_job_id": 7001, "location": {"name": "Hawthorne, CA"},
         "metadata": None, "id": 8621740002, "updated_at": "2026-10-18T09:01:02-04:00", "requisition_id": "R-1",
         "title": "Engineering Internship/Co-op (Summer 2027)", "first_published": "2026-09-16T10:00:00-04:00"},
        {"absolute_url": "https://job-boards.greenhouse.io/spacex/jobs/8001", "id": 8001, "location": {"name": "Starbase, TX"},
         "updated_at": "2026-10-18T09:01:02-04:00", "title": "Senior Propulsion Engineer"},
        {"absolute_url": "https://job-boards.greenhouse.io/spacex/jobs/8002", "id": 8002, "location": {"name": "Redmond, WA"},
         "updated_at": "2026-10-18T09:01:02-04:00", "title": "International Trade Compliance Specialist"},
    ],
    "meta": {"total": 3},
}

greenhouseDetail = {
    "id": 8621740002, "title": "Engineering Internship/Co-op (Summer 2027)",
    "content": "&lt;p&gt;&lt;strong&gt;BASIC QUALIFICATIONS:&lt;/strong&gt;&lt;/p&gt;&lt;ul&gt;&lt;li&gt;Currently pursuing a bachelor&amp;#39;s degree in mechanical engineering&lt;/li&gt;"
               "&lt;li&gt;To conform to U.S. Government export regulations, applicant must be a U.S. person&lt;/li&gt;&lt;/ul&gt;",
}

leverList = [
    {"id": "c672a37e-007d-45ee-a4f9-b5d4dd25a2e3", "text": "Summer 2027 Internship - Mechanical Engineering",
     "categories": {"commitment": "Intern", "location": "Austin, TX", "team": "Engineering", "allLocations": ["Austin, TX"]},
     "createdAt": 1789000000000, "hostedUrl": "https://jobs.lever.co/xcimer/c672a37e-007d-45ee-a4f9-b5d4dd25a2e3",
     "descriptionPlain": "Xcimer is building laser fusion. You will design and test hardware.",
     "lists": [{"text": "Requirements", "content": "<li>Rising junior or senior in mechanical engineering</li><li>CAD experience</li>"}],
     "additionalPlain": "Must be a US citizen."},
    {"id": "aaa", "text": "Laser Physicist", "categories": {"location": "Denver, CO"}, "createdAt": 1789000000000,
     "hostedUrl": "https://jobs.lever.co/xcimer/aaa", "descriptionPlain": "physics", "lists": []},
]

ashbyList = {
    "apiVersion": "1",
    "jobs": [
        {"id": "4f1d", "title": "Mechanical Engineering Intern - Summer 2027", "department": "Engineering", "team": "Mechanical",
         "employmentType": "Intern", "location": "Burlingame, CA", "secondaryLocations": [{"location": "Remote"}],
         "publishedAt": "2026-09-20T17:00:00.000+00:00", "isListed": True, "isRemote": False,
         "jobUrl": "https://jobs.ashbyhq.com/xona-space/4f1d", "applyUrl": "https://jobs.ashbyhq.com/xona-space/4f1d/application",
         "descriptionPlain": "Open to sophomores and juniors. Prototype mechanisms for satellites."},
        {"id": "hidden", "title": "Software Intern", "isListed": False, "location": "SF", "jobUrl": "x"},
    ],
}

workdayFacets = {
    "total": 531,
    "jobPostings": [{"title": "Principal Emulation & Prototyping Engineer", "externalPath": "/job/Hutto-TX/Principal_R71075",
                     "locationsText": "3 Locations", "postedOn": "Posted 30+ Days Ago", "bulletFields": ["R71075"]}],
    "facets": [
        {"facetParameter": "jobFamilyGroup", "descriptor": "Job Category", "values": [
            {"descriptor": "Engineering", "id": "aa11", "count": 300},
            {"descriptor": "INT - Interns, Externs & Scholars", "id": "bb22", "count": 31}]},
        {"facetParameter": "workerSubType", "descriptor": "Worker Sub Type", "values": [
            {"descriptor": "Regular", "id": "cc33", "count": 480},
            {"descriptor": "Intern - Undergraduate", "id": "dd44", "count": 16},
            {"descriptor": "Intern - Graduate", "id": "ee55", "count": 15}]},
        {"facetParameter": "locationMainGroup", "values": [
            {"facetParameter": "locations", "descriptor": "Locations", "values": [{"descriptor": "Kent, WA", "id": "ff66", "count": 200}]}]},
    ],
}

workdayPage = {
    "total": 2,
    "jobPostings": [
        {"title": "Summer 2027 Structural & Mechanical Engineering Internship - Undergraduate",
         "externalPath": "/job/Greater-Seattle-Area/Summer-2027-Structural-Mechanical-Engineering-Internship-Undergraduate_R73001",
         "locationsText": "Greater Seattle Area", "postedOn": "Posted Today", "bulletFields": ["R73001"]},
        {"title": "Summer 2027 Supply Chain Internship", "externalPath": "/job/Huntsville-AL/Summer-2027-Supply-Chain-Internship_R73002",
         "locationsText": "Huntsville, AL", "postedOn": "Posted Yesterday", "bulletFields": ["R73002"]},
    ],
}

workdayDetail = {
    "jobPostingInfo": {
        "id": "fd07", "title": "Summer 2027 Structural & Mechanical Engineering Internship - Undergraduate",
        "jobDescription": "<p>Design, analyze and test flight hardware.</p><p>Must have completed your sophomore year by June 2027.</p>"
                          "<p>This position requires access to export-controlled information; applicants must be a U.S. Person.</p>",
        "location": "Kent, WA", "additionalLocations": ["Huntsville, AL"], "postedOn": "Posted Today",
        "startDate": "2026-10-19", "timeType": "Full time", "jobReqId": "R73001",
        "externalUrl": "https://blueorigin.wd5.myworkdayjobs.com/BlueOrigin/job/Kent/R73001"},
    "hiringOrganization": {"name": "Blue Origin"},
}

successfactorsRss = """<?xml version="1.0" encoding="UTF-8" ?><rss version='2.0' xmlns:atom='http://www.w3.org/2005/Atom'><channel>
<title>United Launch Alliance - Custom Search internship</title><link>https://jobs.ulalaunch.com</link>
<item><title><![CDATA[Composite Engineering Internship - Summer 2027 (Decatur, AL, US, 35601)]]></title>
<description><![CDATA[<p>Students must have completed their sophomore year by the start of the internship.</p><p>U.S. citizenship is required.</p>]]></description>
<pubDate>Wed, 07 Oct 2026 15:12:00 GMT</pubDate>
<link>https://jobs.ulalaunch.com/job/Decatur-Composite-Engineering-Internship-Summer-2027-AL-35601/1427397600/?feedId=1&amp;utm_source=rss</link>
<guid>https://jobs.ulalaunch.com/job/Decatur-Composite-Engineering-Internship-Summer-2027-AL-35601/1427397600/</guid></item>
<item><title><![CDATA[Material & Process Engineer 1 (Decatur, AL, US, 35601)]]></title><description>x</description>
<pubDate>Wed, 07 Oct 2026 15:12:00 GMT</pubDate><link>https://jobs.ulalaunch.com/job/Decatur/1427390000/</link></item>
</channel></rss>"""

eightfoldSearch = {
    "status": 200,
    "data": {"count": 92, "positions": [
        {"id": 996477338210, "displayJobId": "19374", "name": "Systems Integration/Electrical Test Engineer-INTERN",
         "locations": ["Cape Canaveral, FL"], "postedTs": 1792444976, "creationTs": 1791835590, "department": "Space",
         "positionUrl": "/careers/job/996477338210", "atsJobId": "19374"},
        {"id": 996477338299, "name": "Mechanical Engineer Intern - Summer 2027", "locations": ["Grand Prairie, TX", "Orlando, FL"],
         "postedTs": 1792440000, "department": "Missiles and Fire Control", "positionUrl": "/careers/job/996477338299"},
    ]},
}

eightfoldDetail = {"status": 200, "data": {"id": 996477338299, "name": "Mechanical Engineer Intern - Summer 2027",
                   "jobDescription": "<p>Hands-on prototyping of missile hardware.</p><p>Candidates must be able to obtain a DoD Secret clearance.</p>"}}

oracleSearch = {
    "items": [{"SearchId": 1, "TotalJobsCount": 623, "requisitionList": [
        {"Id": "160296", "Title": "Digitalization Engineering Intern - Master's", "PostedDate": "2026-10-19",
         "PrimaryLocation": "Charlotte, NC, United States", "PrimaryLocationCountry": "US"},
        {"Id": "160300", "Title": "Mechanical Design Engineering Intern - Summer 2027", "PostedDate": "2026-10-18",
         "PrimaryLocation": "Phoenix, AZ, United States", "PrimaryLocationCountry": "US"},
    ]}],
    "count": 1, "hasMore": False,
}

oracleDetail = {"items": [{"ExternalDescriptionStr": "<p>Work on aircraft engine hardware.</p>",
                           "ExternalQualificationsStr": "<ul><li>Junior or senior standing in Mechanical Engineering</li></ul>",
                           "ExternalResponsibilitiesStr": ""}]}

smartrecruitersList = {
    "offset": 0, "limit": 100, "totalFound": 2,
    "content": [
        {"id": "744000156384760", "name": "Event Manager, Tradeshows", "releasedDate": "2026-10-19T17:12:23.880Z",
         "location": {"city": "San Jose", "region": "CA", "country": "us", "fullLocation": "San Jose, CA, United States"}},
        {"id": "744000156384999", "name": "Mechanical Engineering Intern - Summer 2027", "releasedDate": "2026-10-19T17:00:00.000Z",
         "location": {"city": "Sunnyvale", "region": "CA", "country": "us", "fullLocation": "Sunnyvale, CA, United States"}},
    ],
}

smartrecruitersDetail = {"jobAd": {"sections": {
    "jobDescription": {"title": "Job Description", "text": "<p>Design surgical robot instruments in our prototype lab.</p>"},
    "qualifications": {"title": "Qualifications", "text": "<p>Freshman, sophomore or junior pursuing a BS in ME.</p>"},
    "additionalInformation": {"text": ""}}}}

amazonSearch = {
    "error": None, "hits": 2,
    "jobs": [
        {"id": "3070001", "id_icims": "3070001", "title": "Hardware Engineering Intern - Summer 2027 (Amazon Robotics)",
         "normalized_location": "North Reading, Massachusetts, USA", "posted_date": "October 15, 2026",
         "job_path": "/en/jobs/3070001/hardware-engineering-intern-summer-2027", "is_intern": True,
         "description": "Build and test robotic drive units.", "basic_qualifications": "- Currently enrolled in a BS program",
         "preferred_qualifications": ""},
        {"id": "3070002", "id_icims": "3070002", "title": "Software Development Engineer Intern", "normalized_location": "Seattle, WA",
         "posted_date": "October 14, 2026", "job_path": "/en/jobs/3070002/sde-intern", "description": "code"},
    ],
}

ibmSearch = {"hits": {"total": {"value": 244, "relation": "eq"}, "hits": [
    {"_id": "64512", "_source": {"title": "Hardware Design Intern 2027", "url": "https://careers.ibm.com/careers/JobDetail?jobId=64512",
                                 "description": "Mechanical packaging of mainframe systems in Poughkeepsie.", "dcdate": "2026-10-10",
                                 "field_keyword_19": "Poughkeepsie, US"}},
    {"_id": "64513", "_source": {"title": "Product Marketing and Strategy Intern 2027", "url": "https://careers.ibm.com/x",
                                 "description": "marketing", "dcdate": "2026-10-11"}},
]}}
