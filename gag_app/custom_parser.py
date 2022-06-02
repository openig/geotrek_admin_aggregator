from geotrek.common.parsers import Parser
from geotrek.trekking.models import POIType

class GeotrekAdminAggregatorParser(Parser):
    url = 'just_so_its_not_none'
    model = POIType # Useless but shouldn't be None

    def parse(self, filename=None, limit=None):
        import importlib

        from os.path import join
        from django.conf import settings

        module_path = join(settings.VAR_DIR, 'conf/gag_app/agg.py')
        spec = importlib.util.spec_from_file_location("agg", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
