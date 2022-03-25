import click
import json
from flask import current_app
from flask.cli import with_appcontext
from gag.app import DB
from config.config import GAG_BASE_LANGUAGE
from gag.utils import deserialize_translated_fields
#from gag.codegen import CoreNetwork


@click.command("test")
@with_appcontext
def test():
    import gag.models as models
    # from gag.models import CoreTopology, TrekkingPoi, TrekkingPoitype, AuthentStructure, TrekkingTrek, TrekkingDifficultylevel, TrekkingRoute, TrekkingPractice, CommonReservationsystem
    from gag.env import fk_not_integrated, specific, source_cat_to_gag_cat, core_topology, common, list_label_field
    from config.config import API_BASE_URL, AUTHENT_STRUCTURE
    from gag.utils import geom4326_to_wkt, camel_case, get_fk_row, create_topology, get_api_field
    from sqlalchemy import inspect
    import requests

    print("Inspecting...")
    insp = inspect(DB.get_engine(current_app))
    coretopology_columns = insp.get_columns("core_topology")

    for table_name, table_specifics in specific.items():

        api_model = table_name.partition("_")[-1] # ex: trekking_poi => poi
        url = API_BASE_URL + api_model

        print("Fetching API...")
        response = requests.get(url)
        r = response.json()["results"]
        
        all_columns = insp.get_columns(table_name) #toutes les colonnes de la table

        fkeys_columns = insp.get_foreign_keys(table_name)

        fkeys_name = []
        for fkey in fkeys_columns:
            fkeys_name.append(', '.join(fkey["constrained_columns"]))

        pkey_column = insp.get_pk_constraint(table_name)["constrained_columns"]
        normal_columns = [c for c in all_columns if c['name'] not in fkeys_name]

        for index in range(len(r)):
            dict_to_insert = {}

            for c in normal_columns:
                c_name = c['name']
                if c_name in table_specifics:
                    dict_to_insert = get_api_field(r, index, c_name, table_specifics, dict_to_insert)
                elif c_name in common['db_column_api_field']:
                    dict_to_insert = get_api_field(r, index, c_name, common['db_column_api_field'], dict_to_insert)
                elif c_name in common['languages']:
                    dict_to_insert = deserialize_translated_fields(r, index, c_name, dict_to_insert, normal_columns)
                elif c_name in common['default_values']:
                    dict_to_insert[c['name']] = common['default_values'][c_name]
            
            main_class = eval('models.' + camel_case(table_name))
            obj_to_insert = main_class(**dict_to_insert)
            
            for c in fkeys_columns:
                print(c)
                fk_to_insert = {}               
                c_referred_table = c['referred_table']
                referred_table_columns = insp.get_columns(c_referred_table)
                referred_table_columns_name = [rtc['name'] for rtc in referred_table_columns if rtc['name'] in list_label_field]
                fk_column = ', '.join(c["constrained_columns"])
                fk_class = eval('models.' + camel_case(c_referred_table))

                if len(referred_table_columns_name) == 1:
                    name_field = ''.join(referred_table_columns_name)
                elif c_referred_table != "core_topology":
                    print('referred_table_columns:', referred_table_columns)
                    print('referred_table_columns_name:', referred_table_columns_name)
                    raise Exception("len(referred_table_columns_name) !=1 whereas exactly one column amongst {} should exist in {} table".format(list_label_field, c_referred_table))
                
                if c_referred_table == 'core_topology':
                    print(table_name, ': core_topology exists')
                    fk_to_insert['kind'] = api_model.upper()

                    geom_wkt = geom4326_to_wkt(r[index]['geometry'])
                    fk_to_insert['geom'] = geom_wkt

                    for ctc in coretopology_columns:
                        if ctc['name'] in core_topology['db_column_api_field']:
                            fk_to_insert[ctc['name']] = r[index][core_topology['db_column_api_field'][ctc['name']]]
                        elif ctc['name'] in core_topology['default_values']:
                            fk_to_insert[ctc['name']] = core_topology['default_values'][ctc['name']]

                    print(fk_to_insert)
                    obj_to_insert.core_topology = models.CoreTopology(**fk_to_insert)

                elif c_referred_table == 'authent_structure':
                    setattr(obj_to_insert, "authent_structure", get_fk_row(models.AuthentStructure, name = AUTHENT_STRUCTURE))

                elif c_referred_table in fk_not_integrated and r[index][fk_not_integrated[c_referred_table]["api_field"]] is not None:
                    api_main_route = fk_not_integrated[c_referred_table]["api_main_route"]
                    url = API_BASE_URL + api_main_route + '/' + str(r[index][fk_not_integrated[c_referred_table]["api_field"]])

                    params = {"language" : GAG_BASE_LANGUAGE}

                    print("Fetching API for referred table route...")
                    response2 = requests.get(url, params = params)
                    r2 = response2.json()
                    print('r2:', r2)

                    api_labels = [r2k for r2k in r2.keys() if r2k in list_label_field]

                    if len(api_labels) == 1:
                        api_label = ''.join(api_labels)
                    elif c_referred_table != "core_topology":
                        print('APi response keys:', r2.keys())
                        print('api_labels:', api_labels)
                        raise Exception("len(api_labels) !=1 whereas exactly one column amongst {} should exist in {} API route".format(list_label_field, api_main_route))

                    old_value = r2[api_label]
                    new_value = source_cat_to_gag_cat[c_referred_table][old_value]
                    fk_to_insert[name_field] = new_value
                    setattr(obj_to_insert, c_referred_table, get_fk_row(fk_class, **fk_to_insert))

                elif fk_column in specific[table_name]:
                    api_field = specific[table_name][fk_column]

                    if type(api_field) is list:
                        old_value = r[index][api_field[0]][api_field[1]]
                    else:
                        old_value = r[index][api_field]
                    
                    new_value = source_cat_to_gag_cat[c_referred_table][old_value]
                    fk_to_insert[name_field] = new_value
                    setattr(obj_to_insert, c_referred_table, get_fk_row(fk_class, **fk_to_insert))
           
            DB.session.add(obj_to_insert)
            #click.echo("{} topology n°{} inserted!".format(api_model, index))
                
    DB.session.commit()

    # CoreTopology(geom = "geom", trekking_poi = TrekkingPoi(name = "random_poi", trekking_poitype = TrekkingPoitype(name = "Flore")))

    # TrekkingPoi(name = "random_poi", core_topology = CoreTopology(geom = "geom"), trekking_poitype = TrekkingPoitype(name = "Flore"))



@click.command("populate_db")
@with_appcontext
def populate_db():
    from gag.models import TrekkingPoi, TrekkingPoitype
    from gag.env import fk_not_integrated, source_cat_to_gag_cat
    from sqlalchemy import inspect

    with open('data.json', 'r') as openedfile:  
        # Reading from JSON file
        data = json.load(openedfile)

    r = data["results"]

    click.echo("Inserting...")

    # for index in range(len(r)):
    #     dict_to_insert = {}
    #     for key, value in trekking_poi.items():
    #         if type(value) is list:
    #             dict_to_insert[key] =  r[index][value[0]][value[1]]
    #         else:
    #             dict_to_insert[key] =  r[index][value]

    #     print(dict_to_insert)

    #     trekking_poi_to_join = TrekkingPoi(**dict_to_insert)
    #     DB.session.add(trekking_poi_to_join)
    #     jointure
    
    ##DB.session.commit()
    ##click.echo("Inserted!")

    insp = inspect(DB.get_engine(current_app))
    fkeys = insp.get_foreign_keys("trekking_poi")

    ## Itération dans les résultats de l'API
    for index in range(len(r)):
        dict_to_insert = {}
        ## Itération dans les objets du dictionnaire trekking_poi qui décrit
        ## la correspondance entre les champs de l'API et les colonnes de la BDD
        for key, value in fk_not_integrated.items():
            ## Itération dans les colonnes de la table trekking_poi
            ## identifiées comme étant des clefs étrangères
            for fk in fkeys:
                # print("key: ", key)
                # print("fk: ", fk["constrained_columns"][0])
                if key == fk["constrained_columns"][0]:
                    ## Si la colonne de la BDD est présente dans la liste des clefs étrangères
                    print("FK: ", key)
                    if type(value) is list:
                        print("LIST: ", value)
                        new_value = source_cat_to_gag_cat[fk["referred_table"]][r[index][value[0]][value[1]]]["new_id"]
                        dict_to_insert[key] =  new_value
                    else:
                        dict_to_insert[key] =  r[index][value]
                else:
                    if type(value) is list:
                        dict_to_insert[key] =  r[index][value[0]][value[1]]
                    else:
                        dict_to_insert[key] =  r[index][value]

        print(dict_to_insert)
        print("/n")
