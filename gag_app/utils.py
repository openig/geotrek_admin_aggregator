def geom_to_wkt(data):
    from django.conf import settings
    from django.contrib.gis.geos import GEOSGeometry, WKBWriter

    geom = GEOSGeometry(str(data['geometry']))  # default SRID of GEOSGeometry is 4326
    geom.transform(settings.SRID)
    geom = WKBWriter().write(geom)  # drop Z dimension
    geom = GEOSGeometry(geom)

    return geom
