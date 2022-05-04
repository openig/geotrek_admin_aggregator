def geom_to_wkt(data):
    from django.conf import settings
    from django.contrib.gis.geos import GEOSGeometry, WKBWriter

    geom = GEOSGeometry(str(data['geometry']))  # default SRID of GEOSGeometry is 4326
    geom.transform(settings.SRID)
    geom = WKBWriter().write(geom)  # drop Z dimension
    geom = GEOSGeometry(geom)

    return geom


def get_api_field(r, index, f_name, value, dict_to_insert):
    print(f_name)
    if type(value[f_name]) is list and value[f_name][1] in r[index][value[f_name][0]]:
        dict_to_insert[f_name] = r[index][value[f_name][0]][value[f_name][1]]
    elif type(value[f_name]) is str:
        dict_to_insert[f_name] = r[index][value[f_name]]

    return dict_to_insert


def deserialize_translated_fields(api_data_index, f_name, dict_to_insert):
    from gag_app.config.config import GAG_BASE_LANGUAGE
    from django.conf import settings

    languages_gag = settings.MODELTRANSLATION_LANGUAGES
    print('languages_gag: ', languages_gag)

    field_is_dict = isinstance(api_data_index[f_name], dict)

    if field_is_dict:
        dict_to_insert[f_name] = api_data_index[f_name][GAG_BASE_LANGUAGE]
    else:
        dict_to_insert[f_name] = api_data_index[f_name]

    for lan in languages_gag:
        translated_column_name = f_name + "_" + lan
        if field_is_dict and lan in api_data_index[f_name]:
            dict_to_insert[translated_column_name] = api_data_index[f_name][lan]
        elif f_name == "published" and lan == GAG_BASE_LANGUAGE:
            dict_to_insert[translated_column_name] = True
        elif f_name == "published":
            dict_to_insert[translated_column_name] = False
        else:
            dict_to_insert[translated_column_name] = ''

    return dict_to_insert
