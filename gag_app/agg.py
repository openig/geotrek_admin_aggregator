import logging
from time import perf_counter

import requests
from django.db import transaction
from geotrek.authent.models import Structure
from geotrek.core.models import Topology

from gag_app.classes import ParserAPIv2ImportContentTypeModel
from gag_app.config.config import AUTHENT_STRUCTURE, GADMIN_BASE_URL
from gag_app.env import model_to_import

log = logging.getLogger()
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.INFO)

tic = perf_counter()

# Encapsulate script in transaction to avoid import of partial data
with transaction.atomic():
    coretopology_fields = Topology._meta.get_fields()
    structure = Structure.objects.get(name=AUTHENT_STRUCTURE)
    api_base_url = f'https://{GADMIN_BASE_URL}/api/v2/'

    log.info("Checking API version...")
    version = requests.get(api_base_url + 'version').json()['version']
    log.info(f'API version is: {version}')

    # Iterate in env.model_to_import var, which sets models processing order
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
log.info(f'Performed aggregation in {toc - tic:.0f} seconds')
