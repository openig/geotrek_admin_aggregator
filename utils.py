def geom4326_to_wkt(data):
    from gag_v2.config import SRID
    from json import dumps as json_dumps
    from geojson import loads as geojson_loads
    from shapely.wkt import loads, dumps
    from shapely.geometry import shape
    from shapely.ops import transform
    from pyproj import CRS, Transformer

    j = json_dumps(data)
    g = geojson_loads(j)
    s = shape(g)
    geom = loads(dumps(s, output_dimension=2))

    wgs84 = CRS('EPSG:4326')
    srid_gag = CRS('EPSG:{}'.format(SRID))
    project = Transformer.from_crs(wgs84, srid_gag, always_xy=True).transform
    geom_transformed = transform(project, geom)

    geom_wkt="SRID={};{}".format(SRID, geom_transformed)

    return geom_wkt


def get_or_create(model, **kwargs):
    from gag_v2.app import DB

    instance = DB.session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        print("get")
        return instance
    else:
        print("create")
        instance = model(**kwargs)
        return instance

def create_topology(model, **kwargs):
    from gag_v2.app import DB

    instance = model(**kwargs)
    return instance

def get_fk_row(model, **kwargs):
    from gag_v2.app import DB

    instance = DB.session.query(model).filter_by(**kwargs).one()
    return instance

def camel_case(s):
    from re import sub

    s = sub(r"(_)+", " ", s).title().replace(" ", "")
    return ''.join(s)

def get_api_field(r, index, c_name, value, dict_to_insert):
    print(c_name)
    if type(value[c_name]) is list and value[c_name][1] in r[index][value[c_name][0]]:
        dict_to_insert[c_name] = r[index][value[c_name][0]][value[c_name][1]]
    elif type(value[c_name]) is str:
        dict_to_insert[c_name] = r[index][value[c_name]]
    
    return dict_to_insert

def deserialize_translated_fields(r, index, c_name, dict_to_insert, normal_columns):
    from re import search
    from gag_v2.config import GAG_BASE_LANGUAGE
    # objectif : access => {"access" = "bla_fr", "access_fr" = "bla_fr", "access_en" = "bla_en"}
    reg = "^{}_.*".format(c_name)
    languages_gag = [(column['name'])[-2:] for column in normal_columns if search(reg, column['name'])]


    print('languages_gag: ', languages_gag)

    dict_to_insert[c_name] = r[index][c_name][GAG_BASE_LANGUAGE]

    for l in languages_gag:
        translated_column_name = c_name + "_" + l
        if l in r[index][c_name]:
            dict_to_insert[translated_column_name] = r[index][c_name][l]
        elif c_name == "published":
            dict_to_insert[translated_column_name] = False
    
    return dict_to_insert