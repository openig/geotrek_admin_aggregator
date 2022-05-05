def geom_to_wkt(data):
    from django.conf import settings
    from django.contrib.gis.geos import GEOSGeometry, WKBWriter

    geom = GEOSGeometry(str(data['geometry']))  # default SRID of GEOSGeometry is 4326
    geom.transform(settings.SRID)  # transform from 4326 to GAG's SRID
    geom = WKBWriter().write(geom)  # drop Z dimension by writing to WKB
    geom = GEOSGeometry(geom)  # recreate a GEOS object which will fit in geom field

    return geom
