def geom4326_to_wkt(data):
    from gag_app.config.config import SRID
    from json import dumps as json_dumps
    from geojson import loads as geojson_loads
    from django.contrib.gis.geos import GEOSGeometry

    geom = GEOSGeometry(str(data)) #default SRID of GEOSGeometry is 4326
    geom.transform(SRID)

    return geom.wkt


def get_or_create(model, **kwargs):
    from gag.app import DB

    instance = DB.session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        print("get")
        return instance
    else:
        print("create")
        instance = model(**kwargs)
        return instance

def create_topology(model, **kwargs):
    from gag.app import DB

    instance = model(**kwargs)
    return instance

def get_fk_row(model, **kwargs):
    from gag.app import DB

    instance = DB.session.query(model).filter_by(**kwargs).one()
    return instance

def camel_case(s):
    from re import sub

    s = sub(r"(_)+", " ", s).title().replace(" ", "")
    return ''.join(s)

def get_api_field(r, index, f_name, value, dict_to_insert):
    print(f_name)
    if type(value[f_name]) is list and value[f_name][1] in r[index][value[f_name][0]]:
        dict_to_insert[f_name] = r[index][value[f_name][0]][value[f_name][1]]
    elif type(value[f_name]) is str:
        dict_to_insert[f_name] = r[index][value[f_name]]
    
    return dict_to_insert

def deserialize_translated_fields(r_index, f_name, dict_to_insert, normal_columns):
    from gag_app.config.config import GAG_BASE_LANGUAGE
    from django.conf import settings
    
    languages_gag = settings.MODELTRANSLATION_LANGUAGES
    print('languages_gag: ', languages_gag)

    dict_to_insert[f_name] = r_index[f_name][GAG_BASE_LANGUAGE]

    for l in languages_gag:
        translated_column_name = f_name + "_" + l
        if l in r_index[f_name]:
            dict_to_insert[translated_column_name] = r_index[f_name][l]
        elif f_name == "published":
            dict_to_insert[translated_column_name] = False
        else:
            dict_to_insert[translated_column_name] = ''
    
    return dict_to_insert