"""Fetch Chennai's ward-level property-tax resource without pasting URLs."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
resource="27905e77-2ef3-45b6-b14a-562bd3e37944"
urls=["https://newdata.opencity.in/dataset/3107497a-f12a-49a8-bc2a-c92c3ccb0b67/resource/"+resource+"/download/7a9e3e30-9a96-4826-89da-12e3fa1902d1.csv","https://data.opencity.in/api/3/action/datastore_search?resource_id="+resource+"&limit=1000"]
Path("data/raw").mkdir(parents=True,exist_ok=True)
for u in urls:
    try:
        with urlopen(Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:b=r.read()
        target=Path("data/raw/chennai_property_tax.json" if b.startswith(b"{") else "data/raw/chennai_property_tax.csv");target.write_bytes(b);print("Downloaded",len(b),"bytes to",target);raise SystemExit(0)
    except (HTTPError,URLError) as e:print("Attempt failed:",u.split("/")[2],e)
raise SystemExit("All automated endpoints blocked. Download manually from the OpenCity Chennai resource page, then run inspect_csv.py on the saved file.")
