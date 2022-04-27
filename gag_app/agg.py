import requests
from time import perf_counter
from geotrek.core.models import Topology
from geotrek.authent.models import Structure
from django.db import transaction
from gag_app.env import model_to_import
from gag_app.config.config import GADMIN_BASE_URL, AUTHENT_STRUCTURE
from gag_app.classes import ParserAPIv2ImportContentTypeModel

tic = perf_counter()

with transaction.atomic():
    coretopology_fields = Topology._meta.get_fields()
    structure = Structure.objects.get(name=AUTHENT_STRUCTURE)
    api_base_url = f'https://{GADMIN_BASE_URL}/api/v2/'

    print("Checking API version...")
    version = requests.get(api_base_url + 'version').json()['version']
    print("API version is: {}".format(version))

    for model_to_import_name, model_to_import_properties in model_to_import.items():
        main_parser = ParserAPIv2ImportContentTypeModel(
            api_base_url=api_base_url,
            model_to_import_name=model_to_import_name,
            model_to_import_properties=model_to_import_properties,
            structure=structure,
            coretopology_fields=coretopology_fields
        )

        main_parser.delete_update_insert_data()

toc = perf_counter()
print(f"Performed aggregation in {toc - tic:0.4f} seconds")
