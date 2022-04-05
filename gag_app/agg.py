import requests
import os
import urllib.request
from time import perf_counter
from mimetypes import guess_type
from geotrek.trekking.models import Trek, POI, POIType, Route, Practice, DifficultyLevel
from geotrek.core.models import Topology
from geotrek.common.models import FileType, Attachment
from geotrek.authent.models import Structure, User
from os.path import join
from django.conf import settings

def agg():
    tic = perf_counter()
    from django.apps import apps
    from django.db import transaction
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.gis.geos import GEOSGeometry, WKBWriter
    from gag_app.env import specific, source_cat_to_gag_cat, core_topology, common, list_label_field
    from gag_app.config.config import API_BASE_URL, AUTHENT_STRUCTURE, SRID, AUTH_USER, GAG_BASE_LANGUAGE, PORTALS
    from gag_app.utils import geom4326_to_wkt, camel_case, get_fk_row, create_topology, get_api_field, deserialize_translated_fields

    with transaction.atomic():        
        coretopology_fields = Topology._meta.get_fields()

        print("Checking API version...")
        version = requests.get(API_BASE_URL + 'version').json()['version']
        print("API version is: {}".format(version))

        for model_name, model_specifics in specific.items():

            api_model = model_name.lower() # ex: Trek => trek
            url = API_BASE_URL + api_model
            params = {}
            if PORTALS:
                portals_response = requests.get(API_BASE_URL + 'portal', params = {'fields' : 'id,name'}).json()['results']
                print('portals_response: ', portals_response)
                portal_ids = [p['id'] for p in portals_response if p['name'] in PORTALS]
                portal_params = ','.join(str(id) for id in portal_ids)
                params = {"portals" : portal_params}

            print("Fetching API...")
            response = requests.get(url, params = params)
            print (response.url)
            r = response.json()["results"]

            while response.json()["next"] is not None:
                response = requests.get(response.json()["next"], params = params)
                r.extend(response.json()["results"])
            print(r)
            
            app_name = ContentType.objects.get(model = api_model).app_label
            print('app_name: ', app_name)
            current_model = apps.get_model(app_name, model_name)
            print('current_model: ', current_model)
            all_fields = current_model._meta.get_fields(include_parents = False) # toutes les colonnes du modèle
            print('all_fields: ', all_fields)

            fkeys_fields = [f for f in all_fields if f.many_to_one]
            one_to_one_fields = [f for f in all_fields if f.one_to_one]

            fk_not_integrated = {}
            for fk_model_name, api_main_route in model_specifics["fk_not_integrated"].items():
                url = API_BASE_URL + api_main_route

                params_fk = {"language" : GAG_BASE_LANGUAGE}

                print("Fetching API for related model route...")
                response_fk = requests.get(url, params = params_fk).json()
                r_fk = response_fk['results']
                print('r2:', r_fk)

                api_labels = [rk for rk in r_fk[0].keys() if rk in list_label_field]

                if len(api_labels) == 1:
                    api_label = ''.join(api_labels)
                else:
                    print('API response keys:', r_fk.keys())
                    print('api_labels:', api_labels)
                    raise Exception("len(api_labels) !=1 whereas exactly one column amongst {} should exist in {} API route".format(list_label_field, api_main_route))

                print('api_label: ', api_label)
                fk_not_integrated[fk_model_name] = {}
                fk_not_integrated[fk_model_name]['data'] = r_fk
                fk_not_integrated[fk_model_name]['api_label'] = api_label
            print('fk_not_integrated: ', fk_not_integrated)

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
                    f_related_model = obj_content_type.app_label + '_' + obj_content_type.model
           
                    if f_related_model == 'core_topology' and r[index]['geometry'] is not None:
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
                    if f_name in r[index]:
                        if f_name in model_specifics["db_column_api_field"]:
                            dict_to_insert = get_api_field(r, index, f_name, model_specifics["db_column_api_field"], dict_to_insert)
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
                    f_related_model = f.related_model.__name__
                    print('f_related_model: ', f_related_model)
                    related_model_fields = f.related_model._meta.get_fields()
                    related_model_normal_fields_name = [f.name for f in related_model_fields if f.is_relation is False and f.name in list_label_field]
                    print('related_model_normal_fields_name: ', related_model_normal_fields_name)
                    fk_field = f.name
                    print("fk_field: ", fk_field)

                    if len(related_model_normal_fields_name) == 1:
                        name_field = related_model_normal_fields_name[0]
                    elif f_related_model != 'Topology':
                        print('related_model_fields:', related_model_fields)
                        print('related_model_normal_fields_name:', related_model_normal_fields_name)
                        raise Exception("len(related_model_normal_fields_name) !=1 whereas exactly one field amongst {} should exist in {} model".format(list_label_field, f_related_model))

                    if f_related_model == 'Structure':
                        obj_to_insert.structure = Structure.objects.get(name = AUTHENT_STRUCTURE)

                    elif f_related_model in fk_not_integrated:
                        print('FK_NOT_INTEGRATED')
                        api_label = fk_not_integrated[f_related_model]['api_label']
                        print('api_label: ', api_label)
                        old_fk_id = r[index][fk_field]
                        old_value = [cat[api_label] for cat in fk_not_integrated[f_related_model]['data'] if cat['id'] == old_fk_id]
                        
                        if old_value is not None and len(old_value) == 1:
                            new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][model_name][f_related_model][old_value[0]]
                            fk_to_insert[name_field] = new_value
                            setattr(obj_to_insert, fk_field, f.related_model.objects.get(**fk_to_insert))
                        elif len(old_value) != 1:
                            print('old_value: ', old_value)
                            raise Exception('Multiple categories found for given id!')

                    elif fk_field in specific[model_name]["db_column_api_field"]:
                        api_field = specific[model_name]["db_column_api_field"][fk_field]

                        if type(api_field) is list:
                            old_value = r[index][api_field[0]][api_field[1]]
                        else:
                            old_value = r[index][api_field]
                        
                        new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][model_name][f_related_model][old_value]

                        fk_to_insert[name_field] = new_value
                        print('fk_to_insert: ', fk_to_insert)
                        setattr(obj_to_insert, fk_field, f.related_model.objects.get(**fk_to_insert))
                    else:
                        raise Exception("Related model doesn't conform to any handled possibility.")

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
                            attachment_name = a['url'].rpartition('/')[2]
                            folder_name = 'paperclip/' + app_name + '_' + api_model
                            pk = str(obj_to_insert.pk)

                            attachment_dict['filetype_id'] = FileType.objects.get(type='Photographie').id
                            attachment_dict['is_image'] = True
                            attachment_dict['attachment_file'] = os.path.join(folder_name, pk, attachment_name)

                            full_filename = os.path.join(settings.MEDIA_ROOT, attachment_dict['attachment_file'])
                            # create folder if it doesn't exist
                            os.makedirs(os.path.dirname(full_filename), exist_ok=True)
                            print(f"Downloading {a['url']} to {full_filename}")

                            attachment_response = requests.get(a['url'])
                            if attachment_response.status_code == 200:
                                urllib.request.urlretrieve(a['url'], full_filename)
                            else:
                                print("Error {} for {}".format(attachment_response.status_code, a['url']))

                        elif a['type'] == 'video':
                            attachment_dict['filetype_id'] = FileType.objects.get(type='Vidéo').id
                            attachment_dict['is_image'] = False
                            attachment_dict['attachment_video'] = a['url']
                        else:
                            print(a)
                            print('mimetype: ', mt)
                            attachment_dict['filetype_id'] = FileType.objects.get(type='Autre').id
                            attachment_dict['is_image'] = False

                        attachment_to_add = Attachment(**attachment_dict)
                        obj_to_insert.attachments.add(attachment_to_add, bulk=False)                        


                print("\n{} OBJECT N°{} INSERTED!\n".format(api_model.upper(), index+1))

    toc = perf_counter()
    print(f"Performed aggregation in {toc - tic:0.4f} seconds")

agg()
