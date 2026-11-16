"""Fetch the Pune FY2017-18 resource without copying a URL from chat."""
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RESOURCE = "3b4c2a42-4fa3-48f4-a0b6-c8209252e5d3"
URLS = [
    "https://newdata.opencity.in/dataset/18ce1d9a-54a4-49df-885a-07eea33680d0/resource/" + RESOURCE + "/download/e938f657-c8d1-4109-872d-d6a38f9db709.csv",
    "https://data.opencity.in/api/3/action/datastore_search?resource_id=" + RESOURCE + "&limit=1000",
    "https://newdata.opencity.in/api/3/action/datastore_search?resource_id=" + RESOURCE + "&limit=1000",
]
out = Path("data/raw/pune_property_tax_2017_18")
out.parent.mkdir(parents=True, exist_ok=True)
for url in URLS:
    try:
        request = Request(url, headers={"User-Agent":"Mozilla/5.0", "Accept":"text/csv,application/json,text/html;q=0.9,*/*;q=0.8"})
        with urlopen(request, timeout=30) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
        if body.startswith(b"{"):
            target = out.with_suffix(".json")
        elif b"ORIGINAL DEMAND 2017-18" in body[:10000]:
            target = out.with_suffix(".csv")
        else:
            print("Rejected unexpected response from", url.split("/")[2], "content type:", content_type)
            continue
        target.write_bytes(body)
        print("Downloaded", len(body), "bytes to", target)
        raise SystemExit(0)
    except (HTTPError, URLError) as err:
        print("Attempt failed:", url.split("/")[2], err)
raise SystemExit("All automated endpoints were blocked. Open the OpenCity resource page in a normal browser, use Download, save the CSV as data/raw/pune_property_tax_2017_18.csv, then run prepare_pune_2017_18.py.")
