import requests
from mimetypes import guess_type
from geotrek.trekking.models import Trek, POI, POIType, Route, Practice, DifficultyLevel
from geotrek.core.models import Topology
from geotrek.common.models import FileType, Attachment
from geotrek.authent.models import Structure, User

def test():
    from django.apps import apps
    from django.db import transaction
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.gis.geos import GEOSGeometry, WKBWriter
    from datetime import datetime, date
    from gag_app.env import fk_not_integrated, specific, source_cat_to_gag_cat, core_topology, common, list_label_field
    from gag_app.config.config import API_BASE_URL, AUTHENT_STRUCTURE, SRID, AUTH_USER, GAG_BASE_LANGUAGE
    from gag_app.utils import geom4326_to_wkt, camel_case, get_fk_row, create_topology, get_api_field, deserialize_translated_fields

    with transaction.atomic():        
        print("Inspecting...")
        coretopology_fields = Topology._meta.get_fields()

        for model_name, model_specifics in specific.items():

            api_model = model_name.lower() # ex: Trek => trek
            url = API_BASE_URL + api_model

            print("Fetching API...")
            response = requests.get(url)
            r = response.json()["results"]
            
            app_name = ContentType.objects.get(model = api_model).app_label
            print('app_name: ', app_name)
            current_model = apps.get_model(app_name, model_name)
            print('current_model: ', current_model)
            all_fields = current_model._meta.get_fields(include_parents = False) # toutes les colonnes du modèle
            print('all_fields: ', all_fields)

            fkeys_fields = [f for f in all_fields if f.many_to_one]
            one_to_one_fields = [f for f in all_fields if f.one_to_one]

            #print(fkeys_fields)

            pkey_field = [f for f in all_fields if hasattr(f, 'primary_key')]
            normal_fields = [f for f in all_fields if f.is_relation is False]

            print('normal_fields: ', normal_fields)

            for index in range(len(r)):
                dict_to_insert = {}

                for f in one_to_one_fields:
                    print(f)
                    fk_to_insert = {}
                    obj_content_type = ContentType.objects.get_for_model(f.related_model)
                    f_related_table = obj_content_type.app_label + '_' + obj_content_type.model
           
                    if f_related_table == 'core_topology' and r[index]['geometry'] is not None:
                        print(model_name, ': topology exists')
                        fk_to_insert['kind'] = api_model.upper()

                        geom = GEOSGeometry(str(r[index]['geometry'])) #default SRID of GEOSGeometry is 4326
                        geom.transform(SRID)
                        geom = WKBWriter().write(geom)
                        fk_to_insert['geom'] = geom

                        for ctf in coretopology_fields:
                            ctf_name = ctf.name
                            if ctf_name in core_topology['db_column_api_field']:
                                fk_to_insert[ctf_name] = r[index][core_topology['db_column_api_field'][ctf_name]]
                            elif ctf_name in core_topology['default_values']:
                                fk_to_insert[ctf_name] = core_topology['default_values'][ctf_name]

                        print('fk_to_insert: ', fk_to_insert)
                        #obj_to_insert.topo_object = Topology(**fk_to_insert)
                        #obj_to_insert = current_model.objects.create(**fk_to_insert)
                        # dict_to_insert['topo_object'] = new_topo
                        # print(dict_to_insert['topo_object'])
                        dict_to_insert = fk_to_insert

                for f in normal_fields:
                    f_name = f.name
                    print('f_name: ', f_name)
                    if f_name in model_specifics:
                        dict_to_insert = get_api_field(r, index, f_name, model_specifics, dict_to_insert)
                    elif f_name in common['db_column_api_field']:
                        dict_to_insert = get_api_field(r, index, f_name, common['db_column_api_field'], dict_to_insert)
                    elif f_name in common['languages']:
                        dict_to_insert = deserialize_translated_fields(r[index], f_name, dict_to_insert, normal_fields)
                    elif f_name in common['default_values']:
                        dict_to_insert[f_name] = common['default_values'][f_name]
                
                # print('dict_to_insert: ', vars(dict_to_insert['topo_object']))
                obj_to_insert = current_model(**dict_to_insert)
                print('obj_to_insert: ', vars(obj_to_insert))
                
                for f in fkeys_fields:
                    print('f: ', f)
                    fk_to_insert = {}
                    obj_content_type = ContentType.objects.get_for_model(f.related_model)
                    f_related_table = obj_content_type.app_label + '_' + obj_content_type.model
                    related_model_fields = f.related_model._meta.get_fields()
                    related_model_normal_fields_name = [f.name for f in related_model_fields if f.is_relation is False and f.name in list_label_field]
                    print('related_model_normal_fields_name: ', related_model_normal_fields_name)
                    fk_field = f.name
                    print("fk_field: ", fk_field)

                    if len(related_model_normal_fields_name) == 1:
                        name_field = related_model_normal_fields_name[0]
                    elif f_related_table != 'core_topology':
                        print('related_model_fields:', related_model_fields)
                        print('related_model_normal_fields_name:', related_model_normal_fields_name)
                        raise Exception("len(related_model_normal_fields_name) !=1 whereas exactly one field amongst {} should exist in {} table".format(list_label_field, f_related_table))

                    if f_related_table == 'authent_structure':
                        obj_to_insert.structure = Structure.objects.get(name = AUTHENT_STRUCTURE)

                    elif f_related_table in fk_not_integrated and r[index][fk_not_integrated[f_related_table]["api_field"]] is not None:
                        api_main_route = fk_not_integrated[f_related_table]["api_main_route"]
                        url = API_BASE_URL + api_main_route + '/' + str(r[index][fk_not_integrated[f_related_table]["api_field"]])

                        params = {"language" : GAG_BASE_LANGUAGE}

                        print("Fetching API for referred table route...")
                        response2 = requests.get(url, params = params)
                        r2 = response2.json()
                        print('r2:', r2)

                        api_labels = [r2k for r2k in r2.keys() if r2k in list_label_field]

                        if len(api_labels) == 1:
                            api_label = ''.join(api_labels)
                        elif f_related_table != "core_topology":
                            print('API response keys:', r2.keys())
                            print('api_labels:', api_labels)
                            raise Exception("len(api_labels) !=1 whereas exactly one column amongst {} should exist in {} API route".format(list_label_field, api_main_route))

                        old_value = r2[api_label]
                        new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][f_related_table][old_value]
                        fk_to_insert[name_field] = new_value
                        setattr(obj_to_insert, fk_field, f.related_model.objects.get(**fk_to_insert))

                    elif fk_field in specific[model_name]:
                        api_field = specific[model_name][fk_field]

                        if type(api_field) is list:
                            old_value = r[index][api_field[0]][api_field[1]]
                        else:
                            old_value = r[index][api_field]
                        
                        new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][f_related_table][old_value]

                        fk_to_insert[name_field] = new_value
                        print('fk_to_insert: ', fk_to_insert)
                        setattr(obj_to_insert, fk_field, f.related_model.objects.get(**fk_to_insert))

                print('obj_to_insert: ', vars(obj_to_insert))
                obj_to_insert.save()

                if 'attachments' in r[index] and len(r[index]['attachments']) > 0:
                    for a in r[index]['attachments']:
                        attachment_dict = {}

                        for db_name, api_field in common['attachments'].items():
                            attachment_dict[db_name] = a[api_field]
                        for db_name, default_value in common['default_values'].items():
                            if db_name in a:
                                attachment_dict[db_name] = default_value
                        
                        print('obj_to_insert.pk: ', obj_to_insert.pk)
                        print('obj_to_insert: ', vars(obj_to_insert))
                        attachment_dict['object_id'] = obj_to_insert.pk
                        attachment_dict['content_type_id'] = ContentType.objects.get(app_label=app_name, model=api_model).id
                        attachment_dict['creator_id'] = User.objects.get(username=AUTH_USER).id
                        
                        mt = guess_type(a['url'], strict=True)[0]
                        if mt is not None and mt.split('/')[0].startswith('image'):
                            attachment_dict['filetype_id'] = FileType.objects.get(type='Photographie').id
                            attachment_dict['is_image'] = True
                        elif a['type'] == 'video':
                            attachment_dict['filetype_id'] = FileType.objects.get(type='Vidéo').id
                            attachment_dict['is_image'] = False                            
                        else:
                            print(a)
                            print('mimetype: ', mt)
                            raise Exception('Filetype not recognized')


                        attachment_to_add = Attachment(**attachment_dict)
                        obj_to_insert.attachments.add(attachment_to_add, bulk=False)

                print("{} object n°{} inserted!".format(api_model, index))

test()
