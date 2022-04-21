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
from warnings import warn


def agg():
    tic = perf_counter()
    from django.apps import apps
    from django.db import transaction
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.gis.geos import GEOSGeometry, WKBWriter
    from gag_app.env import specific, source_cat_to_gag_cat, core_topology, common, list_label_field
    from gag_app.config.config import GADMIN_BASE_URL, AUTHENT_STRUCTURE, AUTH_USER, GAG_BASE_LANGUAGE, PORTALS
    from gag_app.utils import get_api_field, deserialize_translated_fields

    with transaction.atomic():
        coretopology_fields = Topology._meta.get_fields()

        api_base_url = f'https://{GADMIN_BASE_URL}/api/v2/'

        print("Checking API version...")
        version = requests.get(api_base_url + 'version').json()['version']
        print("API version is: {}".format(version))

        current_structure = Structure.objects.get(name=AUTHENT_STRUCTURE)

        for model_name, model_specifics in specific.items():
            app_name = ContentType.objects.get(model=model_name.lower()).app_label
            print('app_name: ', app_name)
            current_model = apps.get_model(app_name, model_name)
            print('current_model: ', current_model)

            api_model = model_name.lower()  # ex: Trek => trek
            url = api_base_url + api_model
            params = {}
            if PORTALS:
                portals_results = requests.get(api_base_url + 'portal', params={'fields': 'id,name'}).json()['results']
                print('portals_results: ', portals_results)
                portal_ids = [p['id'] for p in portals_results if p['name'] in PORTALS]
                portal_params = ','.join(str(id) for id in portal_ids)
                params = {'portals': portal_params}

            params['fields'] = 'uuid'
            print(f'Fetching API for {api_model} uuids...')
            uuids_response = requests.get(url, params=params)
            uuids_results = uuids_response.json()["results"]

            while uuids_response.json()["next"] is not None:
                uuids_response = requests.get(uuids_response.json()["next"], params=params)
                uuids_results.extend(uuids_response.json()["results"])

            uuids_list = [u['uuid'] for u in uuids_results]

            params.pop('fields')

            print(f"Identifying GAG {api_model}s to delete")
            to_delete_names = []
            to_delete_ids = []

            try:
                for obj in current_model.objects.filter(structure=current_structure).iterator(chunk_size=200):
                    if str(obj.uuid) not in uuids_list:
                        print(obj.uuid)
                        to_delete_names.append(obj.name)
                        to_delete_ids.append(obj.topo_object_id)
                objs_to_delete = current_model.objects.filter(topo_object_id__in=to_delete_ids)
                objs_to_delete.delete()
                for tdi, tdn in zip(to_delete_ids, to_delete_names):
                    print('{} n°{} deleted: {}'.format(api_model, tdi, tdn))

                last_aggregation_datetime = current_model.objects.filter(structure=current_structure).latest('date_update').date_update
                print('last_aggregation_datetime: ', last_aggregation_datetime)
                params['updated_after'] = last_aggregation_datetime.strftime('%Y-%m-%d')
            except current_model.DoesNotExist:
                print(f'No data in {current_model} from {current_structure} structure')

            print("Fetching API...")
            response = requests.get(url, params=params)
            print(response.url)
            api_data = response.json()["results"]

            while response.json()["next"] is not None:
                response = requests.get(response.json()["next"], params=params)
                api_data.extend(response.json()["results"])
            #  print(api_data)

            if api_data:
                all_fields = current_model._meta.get_fields(include_parents=False)  # toutes les colonnes du modèle
                print('all_fields: ', all_fields)

                fkeys_fields = [f for f in all_fields if f.many_to_one]
                one_to_one_fields = [f for f in all_fields if f.one_to_one]

                fk_not_integrated = {}
                for fk_model_name, api_main_route in model_specifics["fk_not_integrated"].items():
                    url = api_base_url + api_main_route

                    print(url)
                    params_fk = {"language": GAG_BASE_LANGUAGE}

                    print("Fetching API for related model route...")
                    fk_response = requests.get(url, params=params_fk).json()
                    fk_results = fk_response['results']
                    print('fk_results:', fk_results)

                    if fk_results:
                        api_labels = [rk for rk in fk_results[0].keys() if rk in list_label_field]

                        if len(api_labels) == 1:
                            api_label = ''.join(api_labels)
                        else:
                            print('API response keys:', fk_results.keys())
                            print('api_labels:', api_labels)
                            raise Exception("len(api_labels) !=1 whereas exactly one column amongst {} should exist in {} API route".format(list_label_field, api_main_route))

                        print('api_label: ', api_label)
                        fk_not_integrated[fk_model_name] = {}
                        fk_not_integrated[fk_model_name]['data'] = fk_results
                        fk_not_integrated[fk_model_name]['api_label'] = api_label

                print('fk_not_integrated: ', fk_not_integrated)

                # print(fkeys_fields)

                normal_fields = [f for f in all_fields if f.is_relation is False]

                print('normal_fields: ', normal_fields)

                for index in range(len(api_data)):
                    print('api_data[index]: ', api_data[index])
                    dict_to_insert = {}

                    for f in one_to_one_fields:
                        print(f)
                        fk_to_insert = {}
                        obj_content_type = ContentType.objects.get_for_model(f.related_model)
                        f_related_model = obj_content_type.app_label + '_' + obj_content_type.model

                        if f_related_model == 'core_topology' and api_data[index]['geometry'] is not None:
                            print(model_name, ': topology exists')
                            fk_to_insert['kind'] = api_model.upper()

                            geom = GEOSGeometry(str(api_data[index]['geometry']))  # default SRID of GEOSGeometry is 4326
                            geom.transform(settings.SRID)
                            geom = WKBWriter().write(geom)  # drop Z dimension
                            geom = GEOSGeometry(geom)
                            fk_to_insert['geom'] = geom

                            for ctf in coretopology_fields:
                                ctf_name = ctf.name
                                if ctf_name in core_topology['db_column_api_field']:
                                    fk_to_insert[ctf_name] = api_data[index][core_topology['db_column_api_field'][ctf_name]]
                                elif ctf_name in core_topology['default_values']:
                                    fk_to_insert[ctf_name] = core_topology['default_values'][ctf_name]

                            print('fk_to_insert: ', fk_to_insert)
                            dict_to_insert = fk_to_insert

                    for f in normal_fields:
                        f_name = f.name
                        print('f_name: ', f_name)
                        if f_name in api_data[index]:
                            if f_name in model_specifics["db_column_api_field"]:
                                dict_to_insert = get_api_field(api_data, index, f_name, model_specifics["db_column_api_field"], dict_to_insert)
                            elif f_name in common['db_column_api_field']:
                                dict_to_insert = get_api_field(api_data, index, f_name, common['db_column_api_field'], dict_to_insert)
                            elif f_name in common['languages']:
                                dict_to_insert = deserialize_translated_fields(api_data[index], f_name, dict_to_insert)
                            elif f_name in common['default_values']:
                                dict_to_insert[f_name] = common['default_values'][f_name]

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
                            dict_to_insert['structure'] = current_structure
                            # obj_to_insert.structure = current_structure

                        elif f_related_model in fk_not_integrated:
                            print('FK_NOT_INTEGRATED')
                            api_label = fk_not_integrated[f_related_model]['api_label']
                            print('api_label: ', api_label)
                            old_fk_id = api_data[index][fk_field]
                            print('old_fk_id: ', old_fk_id)
                            old_value = [cat[api_label] for cat in fk_not_integrated[f_related_model]['data'] if cat['id'] == old_fk_id]

                            if not old_value:
                                print('old_value: ', old_value)
                                warn('No old_value found')
                            elif len(old_value) > 1:
                                print('old_value: ', old_value)
                                raise Exception('Multiple categories found for given id!')
                            else:
                                new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][model_name][f_related_model][old_value[0]]
                                fk_to_insert[name_field] = new_value
                                dict_to_insert[fk_field] = f.related_model.objects.get(**fk_to_insert)
                                # setattr(obj_to_insert, fk_field, f.related_model.objects.get(**fk_to_insert))

                        elif fk_field in specific[model_name]["db_column_api_field"]:
                            api_field = specific[model_name]["db_column_api_field"][fk_field]

                            if type(api_field) is list:
                                old_value = api_data[index][api_field[0]][api_field[1]]
                            else:
                                old_value = api_data[index][api_field]

                            new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][model_name][f_related_model][old_value]

                            fk_to_insert[name_field] = new_value
                            print('fk_to_insert: ', fk_to_insert)
                            dict_to_insert[fk_field] = f.related_model.objects.get(**fk_to_insert)
                            # setattr(obj_to_insert, fk_field, f.related_model.objects.get(**fk_to_insert))
                        else:
                            warn("Related model doesn't conform to any handled possibility.")

                    obj_to_insert, created = current_model.objects.update_or_create(uuid=dict_to_insert['uuid'], defaults={**dict_to_insert})

                    print('obj_to_insert: ', vars(obj_to_insert))
                    obj_to_insert.save()

                    if 'attachments' in api_data[index] and len(api_data[index]['attachments']) > 0:
                        for attachment in api_data[index]['attachments']:
                            attachment_dict = {}

                            for db_name, api_field in common['attachments'].items():
                                attachment_dict[db_name] = attachment[api_field]
                            for db_name, default_value in common['default_values'].items():
                                if db_name in attachment:
                                    attachment_dict[db_name] = default_value

                            print('obj_to_insert.pk: ', obj_to_insert.pk)
                            print('obj_to_insert: ', vars(obj_to_insert))
                            attachment_dict['object_id'] = obj_to_insert.pk
                            attachment_dict['content_type_id'] = ContentType.objects.get(app_label=app_name, model=api_model).id
                            attachment_dict['creator_id'] = User.objects.get(username=AUTH_USER).id

                            mt = guess_type(attachment['url'], strict=True)[0]
                            if mt is not None and mt.split('/')[0].startswith('image'):
                                attachment_name = attachment['url'].rpartition('/')[2]
                                folder_name = 'paperclip/' + app_name + '_' + api_model
                                pk = str(obj_to_insert.pk)

                                attachment_dict['filetype_id'] = FileType.objects.get(type='Photographie').id
                                attachment_dict['is_image'] = True
                                attachment_dict['attachment_file'] = os.path.join(folder_name, pk, attachment_name)

                                full_filepath = os.path.join(settings.MEDIA_ROOT, attachment_dict['attachment_file'])
                                # create folder if it doesn't exist
                                os.makedirs(os.path.dirname(full_filepath), exist_ok=True)

                                attachment_response = requests.get(attachment['url'])
                                if not os.path.isfile(full_filepath):
                                    if attachment_response.status_code == 200:
                                        print(f"Downloading {attachment['url']} to {full_filepath}")
                                        urllib.request.urlretrieve(attachment['url'], full_filepath)
                                    else:
                                        print("Error {} for {}".format(attachment_response.status_code, attachment['url']))

                            elif attachment['type'] == 'video':
                                attachment_dict['filetype_id'] = FileType.objects.get(type='Vidéo').id
                                attachment_dict['is_image'] = False
                                attachment_dict['attachment_video'] = attachment['url']
                            else:
                                print(attachment)
                                print('mimetype: ', mt)
                                attachment_dict['filetype_id'] = FileType.objects.get(type='Autre').id
                                attachment_dict['is_image'] = False

                            attachment_to_add, created = Attachment.objects.update_or_create(uuid=attachment_dict['uuid'], defaults={**attachment_dict})
                            obj_to_insert.attachments.add(attachment_to_add, bulk=False)

                    print("\n{} OBJECT N°{} INSERTED!\n".format(api_model.upper(), index+1))

    toc = perf_counter()
    print(f"Performed aggregation in {toc - tic:0.4f} seconds")


agg()
