import logging
import sys
from time import perf_counter

import requests
from django.db import transaction
from geotrek.authent.models import Structure
from geotrek.core.models import Topology

from gag_app.classes import ParserAPIv2ImportContentTypeModel
from gag_app.config.config import SOURCES
from gag_app.env import model_to_import

log = logging.getLogger()
console_handler = logging.StreamHandler()
c_format = logging.Formatter('%(message)s')
console_handler.setFormatter(c_format)
log.addHandler(console_handler)
log.setLevel(logging.INFO)


for source in SOURCES:
    try:
        tic = perf_counter()

        log.info(f"Beginning aggregation of {source['AUTHENT_STRUCTURE']} data")

        # Encapsulate script in transaction to avoid import of partial data
        with transaction.atomic():
            coretopology_fields = Topology._meta.get_fields()
            structure = Structure.objects.get(name=source['AUTHENT_STRUCTURE'])
            api_base_url = f"https://{source['GADMIN_BASE_URL']}/api/v2/"

            log.info("Checking API version...")
            version = requests.get(api_base_url + 'version').json()['version']
            log.info(f'API version is: {version}')

            # Iterate in env.model_to_import, which sets models processing order
            for mti_name in source['DATA_TO_IMPORT']:
                main_parser = ParserAPIv2ImportContentTypeModel(
                    api_base_url=api_base_url,
                    model_to_import_name=mti_name,
                    model_to_import_properties=model_to_import[mti_name],
                    structure=structure,
                    coretopology_fields=coretopology_fields,
                    AUTHENT_STRUCTURE=source['AUTHENT_STRUCTURE'],
                    IMPORT_ATTACHMENTS=source['IMPORT_ATTACHMENTS'],
                )

                main_parser.delete_update_insert_data(PORTALS=source['PORTALS'])

        toc = perf_counter()
        log.info(f'Performed aggregation in {toc - tic:.0f} seconds\n')
    except Exception as err:
        log.exception(err)
        log.error(f'\n{source["AUTHENT_STRUCTURE"]} aggregation was stopped'
                  ' because the above exception occurred\n')
