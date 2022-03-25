from tkinter import E
import requests
from geotrek.trekking.models import Trek, POI, POIType, Route, Practice, DifficultyLevel
from geotrek.core.models import Topology
from geotrek.authent.models import Structure
from config.config import API_BASE_URL, GAG_BASE_LANGUAGE


def fetch_api(API_BASE_URL):
    url = API_BASE_URL + "poi_type/15"

    print("Fetching API...")
    response = requests.get(url)
    r = response.json()#["results"]
    print(r)

    newPoiType = POIType.objects.create(label=r["label"][GAG_BASE_LANGUAGE])
    newPoiType.save()


def get_name_trek(identifiant):
    trek = Trek.objects.get(id=identifiant)
    trek_name = trek.name_fr
    print(trek_name)

def test():
    from django.apps import apps
    from env import fk_not_integrated, specific, source_cat_to_gag_cat, core_topology, common, list_label_field
    from config.config import API_BASE_URL, AUTHENT_STRUCTURE
    from utils import geom4326_to_wkt, camel_case, get_fk_row, create_topology, get_api_field, deserialize_translated_fields
    from sqlalchemy import inspect
    import requests

    print("Inspecting...")
    coretopology_fields = Topology._meta.get_fields()

    for model_name, model_specifics in specific.items():

        api_model = model_name.lower() # ex: Trek => trek
        url = API_BASE_URL + api_model

        print("Fetching API...")
        response = requests.get(url)
        r = response.json()["results"]
        
        model = apps.get_model('trekking', model_name)
        all_fields = model._meta.get_fields() # toutes les colonnes du modèle

        fkeys_fields = [f for f in all_fields if f.is_relation]

        fkeys_name = []
        for fkey in fkeys_fields:
            fkeys_name.append(', '.join(fkey.name))

        pkey_field = [f for f in all_fields if f.primary_key]
        normal_fields = [f for f in all_fields if f.name not in fkeys_name]

        for index in range(len(r)):
            dict_to_insert = {}

            for f in normal_fields:
                f_name = f.name
                if f_name in model_specifics:
                    dict_to_insert = get_api_field(r, index, f_name, model_specifics, dict_to_insert)
                elif f_name in common['db_column_api_field']:
                    dict_to_insert = get_api_field(r, index, f_name, common['db_column_api_field'], dict_to_insert)
                elif f_name in common['languages']:
                    dict_to_insert = deserialize_translated_fields(r, index, f_name, dict_to_insert, normal_fields)
                elif f_name in common['default_values']:
                    dict_to_insert[f_name] = common['default_values'][f_name]
            
            #main_class = eval('models.' + camel_case(model_name))
            obj_to_insert = model(**dict_to_insert)
            
            for f in fkeys_fields:
                print(f)
                fk_to_insert = {}               
                f_related_model = f.related_model
                related_model_fields = f_related_model._meta.get_fields()
                related_model_fields_name = [rmf['name'] for rmf in related_model_fields if rmf.name in list_label_field]
                fk_field = f.name

                if len(related_model_fields_name) == 1:
                    name_field = ''.join(related_model_fields_name)
                elif f_related_model != "core_topology":
                    print('related_model_fields:', related_model_fields)
                    print('related_model_fields_name:', related_model_fields_name)
                    raise Exception("len(related_model_fields_name) !=1 whereas exactly one field amongst {} should exist in {} table".format(list_label_field, f_related_model))
                
                if f_related_model == Topology:
                    print(model_name, ': topology exists')
                    fk_to_insert['kind'] = api_model.upper()

                    geom_wkt = geom4326_to_wkt(r[index]['geometry'])
                    fk_to_insert['geom'] = geom_wkt

                    for ctf in coretopology_fields:
                        ctf_name = ctf.name
                        if ctf_name in core_topology['db_column_api_field']:
                            fk_to_insert[ctf_name] = r[index][core_topology['db_column_api_field'][ctf_name]]
                        elif ctf_name in core_topology['default_values']:
                            fk_to_insert[ctf_name] = core_topology['default_values'][ctf_name]

                    print(fk_to_insert)
                    obj_to_insert.core_topology = models.CoreTopology(**fk_to_insert)

                elif f_related_model == 'authent_structure':
                    setattr(obj_to_insert, "authent_structure", get_fk_row(models.AuthentStructure, name = AUTHENT_STRUCTURE))

                elif f_related_model in fk_not_integrated and r[index][fk_not_integrated[f_related_model]["api_field"]] is not None:
                    api_main_route = fk_not_integrated[f_related_model]["api_main_route"]
                    url = API_BASE_URL + api_main_route + '/' + str(r[index][fk_not_integrated[f_related_model]["api_field"]])

                    params = {"language" : GAG_BASE_LANGUAGE}

                    print("Fetching API for referred table route...")
                    response2 = requests.get(url, params = params)
                    r2 = response2.json()
                    print('r2:', r2)

                    api_labels = [r2k for r2k in r2.keys() if r2k in list_label_field]

                    if len(api_labels) == 1:
                        api_label = ''.join(api_labels)
                    elif f_related_model != "core_topology":
                        print('APi response keys:', r2.keys())
                        print('api_labels:', api_labels)
                        raise Exception("len(api_labels) !=1 whereas exactly one column amongst {} should exist in {} API route".format(list_label_field, api_main_route))

                    old_value = r2[api_label]
                    new_value = source_cat_to_gag_cat[f_related_model][old_value]
                    fk_to_insert[name_field] = new_value
                    setattr(obj_to_insert, f_related_model, get_fk_row(fk_class, **fk_to_insert))

                elif fk_field in specific[model_name]:
                    api_field = specific[model_name][fk_field]

                    if type(api_field) is list:
                        old_value = r[index][api_field[0]][api_field[1]]
                    else:
                        old_value = r[index][api_field]
                    
                    new_value = source_cat_to_gag_cat[f_related_model][old_value]
                    fk_to_insert[name_field] = new_value
                    setattr(obj_to_insert, f_related_model, get_fk_row(fk_class, **fk_to_insert))
           
            DB.session.add(obj_to_insert)
            #click.echo("{} topology n°{} inserted!".format(api_model, index))
                
    DB.session.commit()

fetch_api(API_BASE_URL)
