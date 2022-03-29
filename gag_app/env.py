from config.config import GAG_BASE_LANGUAGE, AUTHENT_STRUCTURE

list_label_field = ['label', 'name', 'type', 'route', 'organism', 'difficulty', 'network']

common = {
    "db_column_api_field" : {
        "eid" : "external_id",
    },
    "languages" : [
        "access",
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
    ],
    "default_values" : {
        "review" : False,
    }
}

core_topology = {
    "db_column_api_field" : {
        "uuid" : "uuid",
    },
    "default_values" : {
        "offset" : 0,
        "geom_need_update" : False,
        "deleted" : False
    }
}

fk_not_integrated = {
    "trekking_difficultylevel": {
        "api_field" : "difficulty",
        "api_main_route" : "trek_difficulty",
    },
    "trekking_practice": {
        "api_field" : "practice",
        "api_main_route" : "trek_practice",
    },
    "trekking_route": {
        "api_field" : "route",
        "api_main_route" : "trek_route",
    },
    "common_reservationsystem": {
        "api_field" : "reservation_system",
        "api_main_route" : "reservationsystem",
    },
}

specific = {
    "POI" : {
        "type" : ["type_label", GAG_BASE_LANGUAGE],
    },
    "Trek" : {
        "accessibility_infrastructure" : ["disabled_infrastructure", GAG_BASE_LANGUAGE],
        "accessibility_infrastructure_en" : ["disabled_infrastructure", "en"],
        "accessibility_infrastructure_es" : ["disabled_infrastructure", "es"],
        "accessibility_infrastructure_fr" : ["disabled_infrastructure", "fr"],
        "accessibility_infrastructure_it" : ["disabled_infrastructure", "it"],
        "duration" : "duration",
        "eid2" : "second_external_id",
        "reservation_id": "reservation_id",
    },
}

source_cat_to_gag_cat = {
    "trekking_poitype" : {
        "Flore" : "Flore",
        "Faune" : "Faune",
        "Géologie" : "Géologie",
        "Architecture" : "Architecture",
        "Point de vue" : "Paysage",
        "Petit patrimoine" : "Tradition",
        "Col" : "Col",
        "Histoire" : "Histoire",
        "Sommet" : "Paysage",
    },
    "trekking_difficultylevel" : {
        "Très facile" : "Très facile",
        "Facile" : "Facile",
        "Intermédiaire" : "Moyen",
        "Difficile" : "Difficile",
        "Très difficile" : "Très difficile",
    },
    "trekking_route" : {
        "Boucle" : "Boucle",
        "Aller-retour" : "Aller-retour",
        "Traversée" : "Itinérance",
        "Itinérance" : "Itinérance",
        "Etape" : "Itinérance",
    },
    "trekking_practice" : {
        "VTT" : "VTT",
        "Pédestre" : "Rando à pied",
        "Vélo" : "VTT",
        "Raquettes" : "Rando à pied",
        "Cheval" : "A cheval",
    },
    "common_reservationsystem" : {
        "OpenSystem" : "OpenSystem",
        "Itinérance" : "Gîtes de France"
    },
}
