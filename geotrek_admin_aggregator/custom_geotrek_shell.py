import requests
from geotrek.trekking.models import Trek, POIType
from config.config import API_BASE_URL, GAG_BASE_LANGUAGE


def fetch_api(API_BASE_URL):
    url = API_BASE_URL + "poi_type/15"

    print("Fetching API...")
    response = requests.get(url)
    r = response.json()#["results"]
    print(r)

    newPoiType = POIType.objects.create(label=r["label"][GAG_BASE_LANGUAGE])
    newPoiType.save()


def get_name_trek(identifiant):
    trek = Trek.objects.get(id=identifiant)
    trek_name = trek.name_fr
    print(trek_name)

fetch_api(API_BASE_URL)
