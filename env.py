from gag_v2.config import GAG_BASE_LANGUAGE, AUTHENT_STRUCTURE

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
        "date_insert" : "create_datetime",
        "date_update" : "update_datetime",
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
    "trekking_poi" : {
        "type_id" : ["type_label", GAG_BASE_LANGUAGE],
    },
    "trekking_trek" : {
        "accessibility_infrastructure" : ["disabled_infrastructure", GAG_BASE_LANGUAGE],
        "accessibility_infrastructure_en" : ["disabled_infrastructure", "en"],
        "accessibility_infrastructure_es" : ["disabled_infrastructure", "es"],
        "accessibility_infrastructure_fr" : ["disabled_infrastructure", "fr"],
        "accessibility_infrastructure_it" : ["disabled_infrastructure", "it"],
        "duration" : "duration",
        "eid2" : "second_external_id",
        "reservation_id": "reservation_id",
    }
}

source_cat_to_gag_cat = {
    "trekking_poitype" : {
        "Flore" : "Faune et Flore",
        "Faune" : "Faune et Flore",
        "Géologie" : "Eau et géologie",
        "Architecture" : "Architecture",
        "Point de vue" : "Cols et Sommets",
        "Petit patrimoine" : "Histoire et culture",
        "Col" : "Cols et Sommets",
        "Histoire" : "Histoire et culture",
        "Sommet" : "Cols et Sommets",
    },
    "trekking_difficultylevel" : {
        "Très facile" : "Facile",
        "Facile" : "Facile",
        "Intermédiaire" : "Intermédiaire",
        "Difficile" : "Difficile",
        "Très difficile" : "Difficile",    
    },
    "trekking_route" : {
        "Boucle" : "Boucle",
        "Aller-retour" : "Aller-retour",
        "Traversée" : "Traversée",
        "Itinérance" : "Traversée",
        "Etape" : "Traversée",
    },
    "trekking_practice" : {
        "VTT" : "VTT",
        "Pédestre" : "Pédestre",
        "Vélo" : "Cyclo route",
        "Raquettes" : "Raquettes",
        "Cheval" : "Cheval",      
    },
    "common_reservationsystem" : {
        "OpenSystem" : "OpenSystem",
        "Itinérance" : "Gites de France"
    },
}
