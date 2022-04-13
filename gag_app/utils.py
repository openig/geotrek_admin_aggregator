def geom4326_to_wkt(data):
    from gag_app.config.config import SRID
    from django.contrib.gis.geos import GEOSGeometry

    geom = GEOSGeometry(str(data))  # default SRID of GEOSGeometry is 4326
    geom.transform(SRID)

    return geom.wkt


def get_api_field(r, index, f_name, value, dict_to_insert):
    print(f_name)
    if type(value[f_name]) is list and value[f_name][1] in r[index][value[f_name][0]]:
        dict_to_insert[f_name] = r[index][value[f_name][0]][value[f_name][1]]
    elif type(value[f_name]) is str:
        dict_to_insert[f_name] = r[index][value[f_name]]

    return dict_to_insert


def deserialize_translated_fields(r_index, f_name, dict_to_insert):
    from gag_app.config.config import GAG_BASE_LANGUAGE
    from django.conf import settings

    languages_gag = settings.MODELTRANSLATION_LANGUAGES
    print('languages_gag: ', languages_gag)

    dict_to_insert[f_name] = r_index[f_name][GAG_BASE_LANGUAGE]

    for lan in languages_gag:
        translated_column_name = f_name + "_" + lan
        if lan in r_index[f_name]:
            dict_to_insert[translated_column_name] = r_index[f_name][lan]
        elif f_name == "published":
            dict_to_insert[translated_column_name] = False
        else:
            dict_to_insert[translated_column_name] = ''

    return dict_to_insert
