import requests
import os
import urllib.request
from mimetypes import guess_type
from warnings import warn
from geotrek.common.models import FileType, Attachment
from geotrek.authent.models import User
from geotrek.trekking.models import Trek, OrderedTrekChild
from django.conf import settings
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from gag_app.env import model_to_import, source_cat_to_gag_cat, core_topology, common, list_label_field
from gag_app.config.config import AUTHENT_STRUCTURE, AUTH_USER, GAG_BASE_LANGUAGE, PORTALS
from gag_app.utils import geom_to_wkt, get_api_field, deserialize_translated_fields


class ParserAPIv2ImportContentTypeModel():
    def __init__(self, api_base_url, model_to_import_name, model_to_import_properties, structure, coretopology_fields):
        self.api_base_url = api_base_url
        self.model_to_import_name = model_to_import_name
        self.model_to_import_properties = model_to_import_properties
        # self.process_data = process_data  # inutile pr l'instant
        self.structure = structure
        self.coretopology_fields = coretopology_fields
        self.url_params = {}
        self.model_lowercase = self.model_to_import_name.lower()

        # Get Django model
        self.app_label = ContentType.objects.get(
            model=self.model_lowercase
        ).app_label
        print('app_label: ', self.app_label)
        self.current_model = apps.get_model(
            app_label=self.app_label,
            model_name=self.model_to_import_name
        )
        print('current_model: ', self.current_model)
        # Define request API url
        self.url = self.api_base_url + self.model_lowercase

    def query_api(self, additional_params={}, api_route=''):
        if api_route:
            url = self.api_base_url + api_route
        else:
            url = self.url

        params = {**self.url_params, **additional_params}

        print("Fetching API...")
        response = requests.get(url, params=params)
        response_results = response.json()["results"]

        while response.json()["next"] is not None:
            response = requests.get(response.json()["next"], params=params)
            response_results.extend(response.json()["results"])

        return response_results

    def get_portals_ids(self):
        portals_results = self.query_api(additional_params={'fields': 'id,name'}, api_route='portal')
        print('portals_response: ', portals_results)
        portal_ids_list = [p['id'] for p in portals_results if p['name'] in PORTALS]
        portal_ids_str = ','.join(str(id) for id in portal_ids_list)

        return portal_ids_str

    def is_populated(self):
        return self.current_model.objects.filter(structure=self.structure).exists()

    def delete_data_using_uuid(self):
        to_delete_names = []
        to_delete_ids = []

        uuids_results = self.query_api(additional_params={'fields': 'uuid'})
        uuids_list = [u['uuid'] for u in uuids_results]

        for obj in self.current_model.objects.filter(structure=self.structure).iterator(chunk_size=200):
            if str(obj.uuid) not in uuids_list:
                print(obj.uuid)
                to_delete_names.append(obj.name)
                to_delete_ids.append(obj.topo_object_id)

        objs_to_delete = self.current_model.objects.filter(topo_object_id__in=to_delete_ids)
        objs_to_delete.delete()

        for tdi, tdn in zip(to_delete_ids, to_delete_names):
            print('{} n°{} deleted: {}'.format(self.model_to_import_name, tdi, tdn))

    def get_last_import_datetime(self):
        last_aggregation_datetime = self.current_model.objects.filter(structure=self.structure).latest('date_update').date_update
        print('last_aggregation_datetime: ', last_aggregation_datetime)

        return last_aggregation_datetime.strftime('%Y-%m-%d')

    def get_fk_api_values(self):
        fk_api_values = {}

        all_fk_fields_to_get = {**model_to_import[self.model_to_import_name]["fk_mapped"], **model_to_import[self.model_to_import_name]["fk_not_mapped"]}

        for fk_model_name, api_fk_route in all_fk_fields_to_get.items():
            fk_results = self.query_api(additional_params={"language": GAG_BASE_LANGUAGE}, api_route=api_fk_route)
            print('fk_results:', fk_results)

            if fk_results:
                if 'name' in fk_results[0].keys():
                    api_labels = ['name']
                else:
                    api_labels = [rk for rk in fk_results[0].keys() if rk in list_label_field]

                if len(api_labels) == 1:
                    api_label = ''.join(api_labels)
                else:
                    print('API response keys:', fk_results[0].keys())
                    print('api_labels:', api_labels)
                    raise Exception("len(api_labels) !=1 whereas exactly one column amongst {} should exist in {} API route".format(list_label_field, api_fk_route))

                print('api_label: ', api_label)
                fk_api_values[fk_model_name] = {}
                fk_api_values[fk_model_name]['data'] = fk_results
                fk_api_values[fk_model_name]['api_label'] = api_label

        print('fk_api_values: ', fk_api_values)
        return fk_api_values

    def delete_update_insert_data(self):
        if PORTALS:
            self.url_params['portals'] = self.get_portals_ids()

        if self.is_populated():
            # Delete objects whose uuid isn't present anymore in API results
            self.delete_data_using_uuid()

            # Get last import date to only fetch objects updated after it
            self.url_params['updated_after'] = self.get_last_import_datetime()  # VRAIMENT BESOIN D'UNE FONCTION ?
        else:
            print(f'No {self.current_model} already existing for {self.structure} structure in GAG database, thus no update or delete operations needed')

        # Data insertion

        api_data = self.query_api()

        if api_data:
            self.fk_api_values = self.get_fk_api_values()

            UpdateAndInsert(
                api_data=api_data,
                current_model=self.current_model,
                model_to_import_name=self.model_to_import_name,
                model_to_import_properties=self.model_to_import_properties,
                coretopology_fields=self.coretopology_fields,
                structure=self.structure,
                app_label=self.app_label,
                model_lowercase=self.model_lowercase,
                fk_api_values=self.fk_api_values
            ).run()


class UpdateAndInsert():
    def __init__(self, api_data, current_model, model_to_import_name, model_to_import_properties, coretopology_fields, structure, app_label, model_lowercase, fk_api_values):
        self.api_data = api_data
        self.current_model = current_model
        self.model_to_import_name = model_to_import_name
        self.model_to_import_properties = model_to_import_properties
        self.coretopology_fields = coretopology_fields
        self.structure = structure
        self.app_label = app_label
        self.model_lowercase = model_lowercase
        self.fk_api_values = fk_api_values

        all_fields = self.current_model._meta.get_fields(include_parents=False)  # toutes les colonnes du modèle
        # print('all_fields: ', all_fields)

        self.many_to_one_fields = [f for f in all_fields if f.many_to_one]
        self.many_to_many_fields = [f for f in all_fields if f.many_to_many]
        self.one_to_one_fields = [f for f in all_fields if f.one_to_one]
        self.normal_fields = [f for f in all_fields if f.is_relation is False]

        # print('normal_fields: ', self.normal_fields)

    def one_to_one_fields_build_dict(self):
        for f in self.one_to_one_fields:
            print(f)
            fk_to_insert = {}
            obj_content_type = ContentType.objects.get_for_model(f.related_model)
            f_related_model_name = f'{obj_content_type.app_label}_{obj_content_type.model}'

            if f_related_model_name == 'core_topology' and self.api_data[self.index]['geometry'] is not None:
                print(self.model_to_import_name, ': topology exists')
                fk_to_insert['kind'] = self.model_to_import_name.upper()

                fk_to_insert['geom'] = geom_to_wkt(self.api_data[self.index])

                for ctf in self.coretopology_fields:
                    ctf_name = ctf.name
                    if ctf_name in core_topology['db_column_api_field']:
                        fk_to_insert[ctf_name] = self.api_data[self.index][core_topology['db_column_api_field'][ctf_name]]
                    elif ctf_name in core_topology['default_values']:
                        fk_to_insert[ctf_name] = core_topology['default_values'][ctf_name]

                print('fk_to_insert: ', fk_to_insert)

        return fk_to_insert

    def normal_fields_build_dict(self):
        for f in self.normal_fields:
            f_name = f.name
            print('f_name: ', f_name)
            if f_name in self.api_data[self.index]:
                if f_name in self.model_to_import_properties['db_column_api_field']:
                    self.dict_to_insert = get_api_field(self.api_data, self.index, f_name, self.model_to_import_properties['db_column_api_field'], self.dict_to_insert)
                elif f_name in common['db_column_api_field']:
                    self.dict_to_insert = get_api_field(self.api_data, self.index, f_name, common['db_column_api_field'], self.dict_to_insert)
                elif f_name in common['languages']:
                    self.dict_to_insert = deserialize_translated_fields(self.api_data[self.index], f_name, self.dict_to_insert)
                elif f_name in common['default_values']:
                    self.dict_to_insert[f_name] = common['default_values'][f_name]

        return self.dict_to_insert

    def many_to_one_fields_build_dict(self):
        for field in self.many_to_one_fields:
            self.fk_to_insert = {}
            self.f_related_model_name, self.fk_model_label_name, self.fk_field_name = self.get_names_api_label_field_and_django_fk_field(field)

            if self.f_related_model_name == 'Structure':
                self.dict_to_insert['structure'] = self.structure
            # elif self.fk_field_name in model_to_import[self.model_to_import_name]["db_column_api_field"]:
            #     api_field = model_to_import[self.model_to_import_name]["db_column_api_field"][self.fk_field_name]

            #     if type(api_field) is list:
            #         old_value = self.api_data[self.index][api_field[0]][api_field[1]]
            #     else:
            #         old_value = self.api_data[self.index][api_field]

            #     new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][self.model_to_import_name][self.f_related_model_name][old_value]

            #     print('old_value: ', old_value)
            #     print('new_value: ', new_value)

            #     self.fk_to_insert[self.fk_model_label_name] = new_value
            #     print('self.fk_to_insert: ', self.fk_to_insert)
            #     self.dict_to_insert[self.fk_field_name] = field.related_model.objects.get(**self.fk_to_insert)
            #     raise Exception('LOOK HERE!')
            elif self.f_related_model_name in self.fk_api_values:
                self.query_fk_api_values_dict(relation_type='many_to_one', field=field)
            else:
                warn("Related model doesn't conform to any handled possibility.")

        return self.dict_to_insert

    def many_to_many_fields_build_dict(self):
        for field in self.many_to_many_fields:
            self.fk_to_insert = {}
            self.f_related_model_name, self.fk_model_label_name, self.fk_field_name = self.get_names_api_label_field_and_django_fk_field(field)

            if self.f_related_model_name in self.fk_api_values:
                self.query_fk_api_values_dict(relation_type='many_to_many', field=field)
            else:
                warn("Related model doesn't conform to any handled possibility.")

    def get_names_api_label_field_and_django_fk_field(self, field):
        print('field: ', field)
        field_related_model_name = field.related_model.__name__
        print('field_related_model_name: ', field_related_model_name)
        related_model_fields = field.related_model._meta.get_fields()
        related_model_normal_fields_name = [f.name for f in related_model_fields if f.is_relation is False and f.name in list_label_field]
        print('related_model_normal_fields_name: ', related_model_normal_fields_name)
        fk_field_name = field.name
        print("fk_field_name: ", fk_field_name)

        if len(related_model_normal_fields_name) == 1:
            fk_model_label_name = related_model_normal_fields_name[0]
            return field_related_model_name, fk_model_label_name, fk_field_name
        elif field_related_model_name != 'Topology':
            print('related_model_fields:', self.related_model_fields)
            print('related_model_normal_fields_name:', related_model_normal_fields_name)
            raise Exception("len(related_model_normal_fields_name) !=1 whereas exactly one field amongst {} should exist in {} model".format(list_label_field, self.field_related_model_name))

    def build_fk_to_insert_dict(self, api_label, id):
        fk_to_insert = {}
        old_value = [cat[api_label] for cat in self.fk_api_values[self.f_related_model_name]['data'] if cat['id'] == id]

        if not old_value:
            print('old_value: ', old_value)
            warn('No old_value found')
        elif len(old_value) > 1:
            print('old_value: ', old_value)
            raise Exception('Multiple categories found for given id!')
        elif self.f_related_model_name in model_to_import[self.model_to_import_name]["fk_mapped"]:
            new_value = source_cat_to_gag_cat[AUTHENT_STRUCTURE][self.model_to_import_name][self.f_related_model_name][old_value[0]]

            print('old_value: ', old_value)
            print('new_value: ', new_value)
            fk_to_insert[self.fk_model_label_name] = new_value
        elif self.f_related_model_name in model_to_import[self.model_to_import_name]["fk_not_mapped"]:
            fk_to_insert[self.fk_model_label_name] = old_value[0]

        return fk_to_insert

    def query_fk_api_values_dict(self, relation_type, field):
        api_label = self.fk_api_values[self.f_related_model_name]['api_label']
        print('api_label: ', api_label)
        old_fk_id = self.api_data[self.index][self.fk_field_name]
        print('old_fk_id: ', old_fk_id)

        if old_fk_id:
            if isinstance(old_fk_id, list):
                old_fk_id_list = old_fk_id
            else:
                old_fk_id_list = [old_fk_id]

            for old_fk_id in old_fk_id_list:
                fk_to_insert = self.build_fk_to_insert_dict(api_label=api_label, id=old_fk_id)
                print('fk_to_insert: ', fk_to_insert)

                if self.fk_model_label_name in fk_to_insert:
                    if relation_type == 'many_to_many':
                        mtm_to_add = field.related_model.objects.get(**fk_to_insert)
                        print('mtm_to_add: ', mtm_to_add)
                        getattr(self.obj_to_insert, field.name).add(mtm_to_add)
                    elif relation_type == 'many_to_one':
                        self.dict_to_insert[self.fk_field_name] = field.related_model.objects.get(**fk_to_insert)
                        return self.dict_to_insert

    def import_attachments(self):
        if 'attachments' in self.api_data[self.index] and len(self.api_data[self.index]['attachments']) > 0:
            for attachment in self.api_data[self.index]['attachments']:
                attachment_dict = {}

                for db_name, api_field in common['attachments'].items():
                    attachment_dict[db_name] = attachment[api_field]
                for db_name, default_value in common['default_values'].items():
                    if db_name in attachment:
                        attachment_dict[db_name] = default_value

                print('self.obj_to_insert.pk: ', self.obj_to_insert.pk)
                print('self.obj_to_insert: ', vars(self.obj_to_insert))
                attachment_dict['object_id'] = self.obj_to_insert.pk
                attachment_dict['content_type_id'] = ContentType.objects.get(app_label=self.app_label, model=self.model_lowercase).id
                attachment_dict['creator_id'] = User.objects.get(username=AUTH_USER).id

                mt = guess_type(attachment['url'], strict=True)[0]
                if mt is not None and mt.split('/')[0].startswith('image'):
                    attachment_name = attachment['url'].rpartition('/')[2]
                    folder_name = f'paperclip/{self.app_label}_{self.model_lowercase}'
                    pk = str(self.obj_to_insert.pk)

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
                self.obj_to_insert.attachments.add(attachment_to_add, bulk=False)

    def get_treks_relationships(self):
        signal = False

        if self.api_data[self.index]['children']:
            print('children: ', self.api_data[self.index]['children'])

            for old_id in self.api_data[self.index]['children']:
                uuid = [ad['uuid'] for ad in self.api_data if ad['id'] == old_id]
                if uuid:
                    child = Trek.objects.get(uuid=uuid[0])
                    parent = Trek.objects.get(uuid=self.api_data[self.index]['uuid'])
                    to_add = OrderedTrekChild(child=child, parent=parent)
                    parent.trek_children.add(to_add, bulk=False)
                    signal = True
                else:
                    print(f"{old_id} trek may be not published, therefore isn't in API results")

        return signal

    def run(self):
        for self.index in range(len(self.api_data)):
            # print('self.api_data[self.index]: ', self.api_data[self.index])
            self.dict_to_insert = {}

            self.dict_to_insert = self.one_to_one_fields_build_dict()
            self.dict_to_insert = self.normal_fields_build_dict()
            self.dict_to_insert = self.many_to_one_fields_build_dict()

            self.obj_to_insert, created = self.current_model.objects.update_or_create(uuid=self.dict_to_insert['uuid'], defaults={**self.dict_to_insert})

            self.many_to_many_fields_build_dict()

            print('self.obj_to_insert: ', vars(self.obj_to_insert))
            self.obj_to_insert.save()

            self.import_attachments()

            print("\n{} OBJECT N°{} INSERTED!\n".format(self.model_lowercase.upper(), self.index+1))

        for self.index in range(len(self.api_data)):
            if self.model_to_import_name == 'Trek':
                signal = self.get_treks_relationships()
                if signal:
                    print("\nRELATIONSHIPS OF {} OBJECT N°{} CREATED!\n".format(self.model_lowercase.upper(), self.index+1))
