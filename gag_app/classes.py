import logging
import os
import urllib.request
from mimetypes import guess_type

import requests
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from geotrek.authent.models import User
from geotrek.common.models import Attachment, FileType
from geotrek.trekking.models import OrderedTrekChild, Trek

from gag_app.config.config import AUTH_USER, GAG_BASE_LANGUAGE
from gag_app.env import (common, core_topology, list_label_field,
                         model_to_import)
from gag_app.category_mapping import source_cat_to_gag_cat
from gag_app.utils import geom_to_wkt

log = logging.getLogger()

class ParserAPIv2ImportContentTypeModel():
    def __init__(self, api_base_url, model_to_import_name,
                 model_to_import_properties, structure,
                 coretopology_fields, AUTHENT_STRUCTURE,
                 IMPORT_ATTACHMENTS):
        self.api_base_url = api_base_url
        self.model_to_import_name = model_to_import_name
        self.model_to_import_properties = model_to_import_properties
        self.structure = structure
        self.coretopology_fields = coretopology_fields
        self.url_params = {}
        self.model_lowercase = model_to_import_name.lower()
        self.AUTHENT_STRUCTURE = AUTHENT_STRUCTURE
        self.IMPORT_ATTACHMENTS = IMPORT_ATTACHMENTS

        # Get Django model
        self.app_label = ContentType.objects.get(
            model=self.model_lowercase
        ).app_label
        log.debug(f'{self.app_label=}')

        self.current_model = apps.get_model(
            app_label=self.app_label,
            model_name=model_to_import_name
        )
        log.debug(f'{self.current_model=}')

        # Define request API url
        self.url = api_base_url + self.model_lowercase

    def query_api(self, additional_params={}, api_route=''):
        if api_route:  # additional argument to overwrite default url
            url = self.api_base_url + api_route
        else:
            url = self.url

        params = {**self.url_params, **additional_params}

        log.info("Fetching API...")
        response = requests.get(url, params=params)
        log.info(f'{response.url}')
        response_results = response.json()["results"]

        # Get data even if it's in several pages response pages
        while response.json()["next"] is not None:
            response = requests.get(response.json()["next"])
            response_results.extend(response.json()["results"])

        return response_results

    def get_portals_ids(self, PORTALS):
        # Create string of portal ids to pass as parameter for an api request
        portals_results = self.query_api(
            additional_params={'fields': 'id,name'},
            api_route='portal'
            )
        log.debug(f'{portals_results=}')
        portal_ids_list = [p['id']
                           for p in portals_results
                           if p['name'] in PORTALS]
        portal_ids_str = ','.join(map(str, portal_ids_list))

        return portal_ids_str

    def is_populated(self):
        m = self.current_model
        return m.objects.filter(structure=self.structure).exists()

    def delete_data_using_uuid(self):
        to_delete_names = []
        to_delete_ids = []

        uuids_results = self.query_api(
            additional_params={'fields': 'uuid', 'page_size': '500'})
        uuids_list = [u['uuid'] for u in uuids_results]

        # Evaluate each object to see if its uuid's missing from API results
        objs = self.current_model.objects.filter(structure=self.structure)
        for obj in objs.iterator(chunk_size=200):
            if str(obj.uuid) not in uuids_list:
                log.debug(f'{obj.uuid=}')
                to_delete_names.append(obj.name)
                to_delete_ids.append(obj.topo_object_id)

        # Gather all objects whose uuid's missing from API results
        objs_to_delete = self.current_model.objects.filter(pk__in=to_delete_ids)
        objs_to_delete.delete()

        for tdi, tdn in zip(to_delete_ids, to_delete_names):
            log.info(f'{self.model_to_import_name} n°{tdi} deleted: {tdn}')

    def get_last_import_datetime(self):
        curr_objs = self.current_model.objects.filter(structure=self.structure)
        last_aggregation_datetime = curr_objs.latest('date_update').date_update
        log.debug(f'{last_aggregation_datetime=}')

        return last_aggregation_datetime.strftime('%Y-%m-%d')

    def process_touristic_content_type_api_data(self, fk_results):
        # Touristic content types aren't available at their own api route.
        # Instead we have to query subdicts in touristiccontent_category route.
        api_label = 'label'
        touristic_content_type_api_data = []
        for category in fk_results:
            for cat_list in category['types']:
                touristic_content_type_api_data.extend(cat_list['values'])

        return api_label, touristic_content_type_api_data

    def get_fk_api_label(self, fk_results, api_fk_route):
        # As labels for Geotrek models aren't named the same,
        # we have to retrieve them within a given list
        if 'name' in fk_results[0].keys():
            # Common case.
            # Avoids exception raised for models with "name" and "type" fields
            api_labels = ['name']
        else:
            api_labels = [rk for rk in fk_results[0].keys()
                          if rk in list_label_field]

        # If zero or more than one label is found, an exception is raised
        if len(api_labels) == 1:
            api_label = api_labels[0]
        else:
            log.debug(f'API response keys: {fk_results[0].keys()=}')
            log.debug(f'{api_labels=}')
            raise Exception('len(api_labels) !=1 whereas exactly one column '
                            f'amongst {list_label_field} should exist '
                            f'in {api_fk_route} API route.')

        log.debug(f'{api_label=}')

        return api_label

    def get_fk_api_values(self, all_fields):
        # Build a dict with all category models values fetched from API.
        # Allows to query API once at the beginning and not several times.
        fk_api_values = {}
        relation_fields_names = [f.related_model.__name__
                                 for f in all_fields
                                 if f.is_relation]

        # Store foreign key fields as per their mapped/non-mapped status
        fk_mapped = {**common["fk_mapped"],
                     **model_to_import[self.model_to_import_name]["fk_mapped"]}
        fk_not_mapped = {**common["fk_not_mapped"],
                         **model_to_import[self.model_to_import_name]["fk_not_mapped"]}
        self.fk_mapped = {k: v for k, v in fk_mapped.items()
                          if k in relation_fields_names
                          and k in source_cat_to_gag_cat[self.AUTHENT_STRUCTURE]}
        self.fk_not_mapped = {k: v for k, v in fk_not_mapped.items()
                              if k in relation_fields_names}

        all_fk_fields_to_get = {**self.fk_mapped, **self.fk_not_mapped}

        # For each fk field to store, get its values and the name of its label.
        # All of them are stored in the same dictionary.
        for fk_model_name, api_fk_route in all_fk_fields_to_get.items():
            fk_results = self.query_api(
                additional_params={"language": GAG_BASE_LANGUAGE},
                api_route=api_fk_route)

            log.debug(f'{fk_results=}')

            if fk_results:
                fk_api_values[fk_model_name] = {}

                if fk_model_name.startswith('TouristicContentType'):
                    api_label, fk_results = self.process_touristic_content_type_api_data(fk_results)
                else:
                    api_label = self.get_fk_api_label(fk_results, api_fk_route)

                fk_api_values[fk_model_name]['data'] = fk_results
                fk_api_values[fk_model_name]['api_label'] = api_label

        log.debug(f'{fk_api_values=}')
        return fk_api_values

    def delete_update_insert_data(self, PORTALS):
        if PORTALS:
            self.url_params['portals'] = self.get_portals_ids(PORTALS)

        if self.is_populated():
            # Delete objects whose uuid isn't present anymore in API results
            self.delete_data_using_uuid()

            # Get last import date to only fetch objects updated after it
            self.url_params['updated_after'] = self.get_last_import_datetime() # VRAIMENT BESOIN D'UNE FONCTION ?
        else:
            log.info(f'No {self.current_model.__name__} already existing for '
                     f'{self.structure} structure in GAG database, thus no '
                     'update or delete operations needed. '
                     'Skipping to insertion.')

        # Data insertion
        api_data = self.query_api()

        if api_data:
            all_fields = self.current_model._meta.get_fields(include_parents=False)
            # log.debug(f'{all_fields=}')

            fk_api_values = self.get_fk_api_values(all_fields)

            # Once all data is ready, we can process it
            UpdateAndInsert(
                api_data=api_data,
                current_model=self.current_model,
                model_to_import_name=self.model_to_import_name,
                model_to_import_properties=self.model_to_import_properties,
                coretopology_fields=self.coretopology_fields,
                structure=self.structure,
                app_label=self.app_label,
                model_lowercase=self.model_lowercase,
                fk_api_values=fk_api_values,
                all_fields=all_fields,
                fk_mapped=self.fk_mapped,
                fk_not_mapped=self.fk_not_mapped,
                AUTHENT_STRUCTURE=self.AUTHENT_STRUCTURE
            ).run(IMPORT_ATTACHMENTS=self.IMPORT_ATTACHMENTS)


class UpdateAndInsert():
    def __init__(self, api_data, current_model, model_to_import_name,
                 model_to_import_properties, coretopology_fields,
                 structure, app_label, model_lowercase, fk_api_values,
                 all_fields, fk_mapped, fk_not_mapped, AUTHENT_STRUCTURE):
        self.api_data = api_data
        self.current_model = current_model
        self.model_to_import_name = model_to_import_name
        self.model_to_import_properties = model_to_import_properties
        self.coretopology_fields = coretopology_fields
        self.structure = structure
        self.app_label = app_label
        self.model_lowercase = model_lowercase
        self.fk_api_values = fk_api_values
        all_fields = all_fields
        self.fk_mapped = fk_mapped
        self.fk_not_mapped = fk_not_mapped
        self.AUTHENT_STRUCTURE = AUTHENT_STRUCTURE

        # Separate fields as per their Django relationship status
        self.many_to_one_fields = [f for f in all_fields if f.many_to_one]
        self.many_to_many_fields = [f for f in all_fields if f.many_to_many]
        self.one_to_one_fields = [f for f in all_fields if f.one_to_one]
        self.normal_fields = [f for f in all_fields if f.is_relation is False]

        # log.debug(f'{self.normal_fields=}')

    def get_api_field(self, api_data, index, f_name, value):
        # If field is listed in a "db_column_api_field" dict in env.py file,
        # the path given can be a list or a simple string
        # (e.g. "eid": "external_id" or "eid": ["external_id", "value"]).
        # Depending on that, retrieving of value in API results isn't the same.
        log.debug(f'{f_name=}')
        if (type(value[f_name]) is list and
                value[f_name][1] in api_data[index][value[f_name][0]]):
            self.dict_to_insert[f_name] = api_data[index][value[f_name][0]][value[f_name][1]]
        elif type(value[f_name]) is str:
            self.dict_to_insert[f_name] = api_data[index][value[f_name]]

    def deserialize_translated_fields(self, api_data_i, f_name):
        # Get all languages activated in GAG DB
        languages_gag = settings.MODELTRANSLATION_LANGUAGES
        # log.debug(f'{languages_gag=}')

        # Is the translated field a dict with keys/values for each language?
        field_is_dict = isinstance(api_data_i[f_name], dict)

        if field_is_dict:
            self.dict_to_insert[f_name] = api_data_i[f_name][GAG_BASE_LANGUAGE]
        else:
            self.dict_to_insert[f_name] = api_data_i[f_name]

        # Iterate over GAG languages, and build the translated field for each
        for lan in languages_gag:
            translated_column_name = f_name + "_" + lan
            if field_is_dict and lan in api_data_i[f_name]:
                self.dict_to_insert[translated_column_name] = api_data_i[f_name][lan]
            elif f_name == "published" and lan == GAG_BASE_LANGUAGE:
                # Necessary for touristiccontent API route
                # which doesn't provide translated fields for "published"
                self.dict_to_insert[translated_column_name] = True
            elif f_name == "published":
                self.dict_to_insert[translated_column_name] = False
            else:
                # Handle GAG languages not present in source DB
                self.dict_to_insert[translated_column_name] = ''

    def get_names_api_label_field_and_django_fk_field(self, field):
        # For many to (one or many) relationships, get necessary variables
        log.debug(f'{field=}')
        fk_field_name = field.name
        log.debug(f'{fk_field_name=}')
        field_related_model_name = field.related_model.__name__
        log.debug(f'{field_related_model_name=}')
        related_model_fields = field.related_model._meta.get_fields()

        # Get all the normal fields of the related model.
        # (e.g. field is "themes": we want "Theme" model's normal fields.)
        # Then we want to retrieve the label field amongst them.
        related_model_normal_fields_names = [f.name
                                             for f in related_model_fields
                                             if f.is_relation is False]
        related_model_label_field = [n
                                     for n in related_model_normal_fields_names
                                     if n in list_label_field]
        log.debug(f'{related_model_label_field=}')

        # If there's only one field left, we can return the variables
        if len(related_model_label_field) == 1:
            related_model_label_name = related_model_label_field[0]
            return (field_related_model_name,
                    related_model_label_name,
                    fk_field_name)
        elif field_related_model_name != 'Topology':
            log.debug(f'{self.related_model_fields=}')
            log.debug(f'{related_model_label_field=}')
            raise Exception('len(related_model_label_field) !=1 whereas exactly '
                            f'one field amongst {list_label_field} should '
                            f'exist in {self.field_related_model_name} model.')

    def get_gag_cat_textual_value(self, api_label, id):
        # Changes category values (Practice, POIType...) from API
        # into new values present in GAG database
        fk_to_insert = {}
        category_values = self.fk_api_values[self.f_related_model_name]['data']

        log.debug(f'{id=}')
        # log.debug(f"{category_values=}")
        # Retrieve the textual value using id comparison

        old_value = [cat[api_label]
                     for cat in category_values
                     if cat['id'] == id]

        log.debug(f'{old_value=}')
        if not old_value:
            log.warn('No old_value found')
        elif len(old_value) > 1:
            raise Exception('Multiple categories found for given id!')
        elif self.f_related_model_name in self.fk_mapped:
            # If this category is mapped
            # we retrieve the new_value in category_mapping.source_cat_to_gag_cat
            new_value = source_cat_to_gag_cat[self.AUTHENT_STRUCTURE][self.f_related_model_name][old_value[0]]

            log.debug(f'{new_value=}')
            fk_to_insert[self.related_model_label_name] = new_value
        elif self.f_related_model_name in self.fk_not_mapped:
            # If this category isn't mapped, we just import the same value
            fk_to_insert[self.related_model_label_name] = old_value[0]

        return fk_to_insert

    def query_fk_api_values_dict(self, relationship_type, field):
        # Get foreign key field's API id
        if self.fk_field_name == 'type1':
            type1_key = min(self.api_data[self.index]['types'])
            api_fk_id = self.api_data[self.index]['types'][type1_key]
        elif self.fk_field_name == 'type2':
            type2_key = max(self.api_data[self.index]['types'])
            api_fk_id = self.api_data[self.index]['types'][type2_key]
        else:
            api_fk_id = self.api_data[self.index][self.fk_field_name]
        log.debug(f'{api_fk_id=}')

        if api_fk_id:
            if relationship_type == 'many_to_many':
                api_fk_id_list = api_fk_id
            else:
                api_fk_id_list = [api_fk_id]

            api_label = self.fk_api_values[self.f_related_model_name]['api_label']
            log.debug(f'{api_label=}')

            # For each id: retrieve the matching GAG category textual value,
            # then the corresponding object in GAG related model,
            # add it to dict_to_insert for many to one relationships
            # or directly to obj_to_insert for many to many relationships
            for api_fk_id in api_fk_id_list:
                gag_textual_value = self.get_gag_cat_textual_value(
                    api_label=api_label,
                    id=api_fk_id)
                log.debug(f'{gag_textual_value=}')

                if gag_textual_value[self.related_model_label_name]:
                    # If category is mapped and not None:
                    if relationship_type == 'many_to_one':
                        try:
                            self.dict_to_insert[self.fk_field_name] = field.related_model.objects.get(**gag_textual_value)
                        except ObjectDoesNotExist:
                            log.info(f'\nERROR: {gag_textual_value=}')
                            raise
                    elif relationship_type == 'many_to_many':
                        gag_textual_value[self.related_model_label_name + '__iexact'] = gag_textual_value.pop(self.related_model_label_name)
                        try:
                            mtm_obj_to_add = field.related_model.objects.get(**gag_textual_value)
                        except ObjectDoesNotExist:
                            log.info(f"\nERROR: gag_textual_value='{gag_textual_value[self.related_model_label_name + '__iexact']}'")
                            raise
                        log.debug(f'{mtm_obj_to_add=}')
                        getattr(self.obj_to_insert, field.name).add(mtm_obj_to_add)

    def build_topo_dict(self):
        log.debug(f'{self.model_to_import_name}: topology exists')
        self.dict_to_insert['kind'] = self.model_to_import_name.upper()
        self.dict_to_insert['geom'] = geom_to_wkt(self.api_data[self.index])

        # Fill every CoreTopology field as per the env.py specification
        for ctf in self.coretopology_fields:
            ctf_name = ctf.name
            if ctf_name in core_topology['db_column_api_field']:
                self.dict_to_insert[ctf_name] = self.api_data[self.index][core_topology['db_column_api_field'][ctf_name]]
            elif ctf_name in core_topology['default_values']:
                self.dict_to_insert[ctf_name] = core_topology['default_values'][ctf_name]

        log.debug(f'{self.dict_to_insert=}')

    def one_to_one_fields_build_dict(self):
        # Handle every field in a one to one relationship.
        # This function is separate from normal fields' one
        # because we need to create the Topology object before
        # being able to fill fields for a related object as a Trek or a POI.
        for f in self.one_to_one_fields:
            log.debug(f'{f=}')
            if (f.related_model.__name__ == 'Topology'
                    and self.api_data[self.index]['geometry'] is not None):
                self.build_topo_dict()

    def normal_fields_build_dict(self):
        # Handle every field not in a Django relationship
        # as per its env.py situation
        for f in self.normal_fields:
            # log.debug(f'{f.name=}')
            if f.name in self.api_data[self.index]:
                if f.name in self.model_to_import_properties['db_column_api_field']:
                    self.get_api_field(
                        self.api_data,
                        self.index,
                        f.name,
                        self.model_to_import_properties['db_column_api_field'])
                elif f.name in common['db_column_api_field']:
                    self.get_api_field(
                        self.api_data,
                        self.index,
                        f.name,
                        common['db_column_api_field'])
                elif f.name in common['languages']:
                    self.deserialize_translated_fields(
                        self.api_data[self.index],
                        f.name)
                elif f.name in common['default_values']:
                    self.dict_to_insert[f.name] = common['default_values'][f.name]
            elif f.name == 'geom':
                self.dict_to_insert['geom'] = geom_to_wkt(self.api_data[self.index])

    def many_to_one_fields_build_dict(self):
        # Handle every field in a many to one Django relationship
        for field in self.many_to_one_fields:
            (self.f_related_model_name,
             self.related_model_label_name,
             self.fk_field_name) = self.get_names_api_label_field_and_django_fk_field(field)

            if self.f_related_model_name == 'Structure':
                self.dict_to_insert['structure'] = self.structure
            elif self.f_related_model_name in self.fk_api_values:
                self.query_fk_api_values_dict(
                    relationship_type='many_to_one',
                    field=field)
            else:
                log.warn(f'Foreign key field {self.fk_field_name} and its'
                         f' related model {self.f_related_model_name}'
                         " don't conform to any handled possibility.")

    def many_to_many_fields_build_dict(self):
        # Handle every field in a many to many Django relationship
        for field in self.many_to_many_fields:
            (self.f_related_model_name,
             self.related_model_label_name,
             self.fk_field_name) = self.get_names_api_label_field_and_django_fk_field(field)

            if self.f_related_model_name in self.fk_api_values:
                self.query_fk_api_values_dict(
                    relationship_type='many_to_many',
                    field=field)
            elif self.f_related_model_name == 'WebLink':
                for weblink in self.api_data[self.index]['web_links']:
                    mtm_obj_to_add = field.related_model.objects.get(url=weblink['url'])
                    log.debug(f'{mtm_obj_to_add=}')
                    getattr(self.obj_to_insert, field.name).add(mtm_obj_to_add)
            else:
                log.warn(f'Foreign key field {self.fk_field_name} and its'
                         f' related model {self.f_related_model_name}'
                         " don't conform to any handled possibility.")

    def import_attachments(self):
        if ('attachments' in self.api_data[self.index]
                and len(self.api_data[self.index]['attachments']) > 0):
            for attachment in self.api_data[self.index]['attachments']:
                attachment_dict = {}

                for db_name, api_field in common['attachments'].items():
                    attachment_dict[db_name] = attachment[api_field]
                for db_name, default_value in common['default_values'].items():
                    if db_name in attachment:
                        attachment_dict[db_name] = default_value

                log.debug(f'{self.obj_to_insert.pk=}')
                log.debug(f'{vars(self.obj_to_insert)=}')
                attachment_dict['object_id'] = self.obj_to_insert.pk
                attachment_dict['content_type_id'] = ContentType.objects.get(
                    app_label=self.app_label,
                    model=self.model_lowercase).id
                attachment_dict['creator_id'] = User.objects.get(username=AUTH_USER).id

                mt = guess_type(attachment['url'], strict=True)[0]
                if mt is not None and mt.split('/')[0].startswith('image'):
                    attachment_name = attachment['url'].rpartition('/')[2]
                    folder_name = f'paperclip/{self.app_label}_{self.model_lowercase}'
                    pk = str(self.obj_to_insert.pk)

                    attachment_dict['filetype_id'] = FileType.objects.get(type='Photographie').id
                    attachment_dict['is_image'] = True
                    attachment_dict['attachment_file'] = os.path.join(
                        folder_name,
                        pk,
                        attachment_name)

                    full_filepath = os.path.join(
                        settings.MEDIA_ROOT,
                        attachment_dict['attachment_file'])
                    # Create folder if it doesn't exist
                    os.makedirs(os.path.dirname(full_filepath), exist_ok=True)

                    attachment_response = requests.get(attachment['url'])
                    if not os.path.isfile(full_filepath):
                        if attachment_response.status_code == 200:
                            log.info(f"Downloading {attachment['url']} to {full_filepath}")
                            urllib.request.urlretrieve(
                                attachment['url'],
                                full_filepath)
                        else:
                            log.info(f'Error {attachment_response.status_code} '
                                     'for {attachment_response.url}')

                elif attachment['type'] == 'video':
                    attachment_dict['filetype_id'] = FileType.objects.get(type='Vidéo').id
                    attachment_dict['is_image'] = False
                    attachment_dict['attachment_video'] = attachment['url']
                else:
                    log.debug(f'{attachment=}')
                    log.debug(f'{mt=}')
                    attachment_dict['filetype_id'] = FileType.objects.get(type='Autre').id
                    attachment_dict['is_image'] = False

                attachment_to_add, created = Attachment.objects.update_or_create(
                    uuid=attachment_dict['uuid'],
                    defaults={**attachment_dict})
                self.obj_to_insert.attachments.add(
                    attachment_to_add,
                    bulk=False)

    def create_treks_relationships(self):
        # Handle many to many relationships between two Trek objects.
        # Needs that all objects are created before running,
        # hence why its position in run() function.
        signal = False

        # Handle OrderedTrekChild model
        children_ids = self.api_data[self.index]['children']
        if children_ids:
            log.debug(f'{children_ids=}')
            # Create an OrderedTrekChild relationship for each id in "children" API field
            for child_id in children_ids:
                # Retrieve uuid for each child
                uuid = [ad['uuid'] for ad in self.api_data
                        if ad['id'] == child_id]
                if uuid:
                    child = Trek.objects.get(uuid=uuid[0])
                    parent = Trek.objects.get(uuid=self.api_data[self.index]['uuid'])
                    to_add = OrderedTrekChild(child=child, parent=parent)
                    parent.trek_children.add(to_add, bulk=False)
                    signal = True
                else:
                    # A trek not published in source DB, so not present in API,
                    # is still referenced in "children" API field
                    # if its parent is itself published (and present in API).
                    log.warn(f'{child_id} trek may be not published, '
                             "therefore isn't in API results")

        return signal

    def run(self, IMPORT_ATTACHMENTS):
        for self.index in range(len(self.api_data)):
            # log.debug(f'{self.api_data[self.index]=}')
            self.dict_to_insert = {}

            self.one_to_one_fields_build_dict()
            self.normal_fields_build_dict()
            self.many_to_one_fields_build_dict()

            # Create the object in memory, allows to reference it later
            self.obj_to_insert, created = self.current_model.objects.update_or_create(
                uuid=self.dict_to_insert['uuid'],
                defaults={**self.dict_to_insert})

            self.many_to_many_fields_build_dict()

            if IMPORT_ATTACHMENTS:
                self.import_attachments()

            log.info(f'\n{self.model_lowercase.upper()} OBJECT '
                     f'N°{self.index+1}'
                     f" ({self.dict_to_insert['name']}) "
                     f'INSERTED!\n')

        if self.model_to_import_name == 'Trek':
            for self.index in range(len(self.api_data)):
                signal = self.create_treks_relationships()
                if signal:
                    log.info(f'\nRELATIONSHIPS OF {self.model_lowercase.upper()} '
                             f'OBJECT N°{self.index+1} CREATED!\n')
