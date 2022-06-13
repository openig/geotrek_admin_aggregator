from gag_app.config.config import GAG_BASE_LANGUAGE

# List of potential names for label columns (i.e. textual name of a category)
list_label_field = [
    'label',
    'name',
    'type',
    'route',
    'organism',
    'difficulty',
    'network',
    'reservation_system'
]

# All fields that are in common between models or have a common handling
common = {
    "db_column_api_field": {
        "eid": "external_id",
        "uuid": "uuid",
        "reservation_id": "reservation_id",
    },
    "languages": [
        "access",
        "accessibility",
        "accessibility_advice",
        "accessibility_covering",
        "accessibility_exposure",
        "accessibility_signage",
        "accessibility_slope",
        "accessibility_width",
        "advice",
        "advised_parking",
        "ambiance",
        "arrival",
        "departure",
        "description",
        "description_teaser",
        "gear",
        "name",
        "public_transport",
        "published",
        "ratings_description",
        "practical_info",
    ],
    "attachments": {
        "author": "author",
        "title": "title",
        "legend": "legend",
        "uuid": "uuid",
    },
    "default_values": {
        "review": False,
        "attachment_video": "",
        "attachment_file": "",
        "attachment_link": "",
        "marque": False,
        "deleted": False,
    },
    "fk_mapped": {
        "ReservationSystem": "reservationsystem",
        "Theme": "theme",
    },
    "fk_not_mapped": {
        "InformationDesk": "informationdesk",
        "RecordSource": "source",
    },
}

core_topology = {
    "db_column_api_field": {
        "uuid": "uuid",
    },
    "default_values": {
        "offset": 0,
        "geom_need_update": False,
        "deleted": False
    }
}

# List of data models to import and their specific properties.
# Order in the dict matters as they are imported in the same order.
model_to_import = {
    "POI": {
        "db_column_api_field": {},
        "fk_mapped": {
            "POIType": "poi_type",
        },
        "fk_not_mapped": {},
    },
    "Trek": {
        "db_column_api_field": {
            "accessibility_infrastructure": [
                "disabled_infrastructure",
                GAG_BASE_LANGUAGE
            ],
            "accessibility_infrastructure_en": [
                "disabled_infrastructure",
                "en"
            ],
            "accessibility_infrastructure_es": [
                "disabled_infrastructure",
                "es"
            ],
            "accessibility_infrastructure_fr": [
                "disabled_infrastructure",
                "fr"
            ],
            "accessibility_infrastructure_it": [
                "disabled_infrastructure",
                "it"
            ],
            "duration": "duration",
            "eid2": "second_external_id",
        },
        "fk_mapped": {
            "DifficultyLevel": "trek_difficulty",
            "Practice": "trek_practice",
            "Route": "trek_route",
            "TrekNetwork": "trek_network",
            "AccessibilityLevel": "trek_accessibility_level",
        },
        "fk_not_mapped": {
            "Label": "label",
            "Accessibility": "trek_accessibility",
            # "Rating": "trek_rating",
        },
    },
    "TouristicContent": {
        "db_column_api_field": {
            "contact": "contact",
            "email": "email",
            "website": "website",
            "approved": "approved"
        },
        "fk_mapped": {
            "TouristicContentCategory": "touristiccontent_category",
            "TouristicContentType1": "touristiccontent_category",
            "TouristicContentType2": "touristiccontent_category",
        },
        "fk_not_mapped": {
            "LabelAccessibility": "label_accessibility"
        }
    },
}
