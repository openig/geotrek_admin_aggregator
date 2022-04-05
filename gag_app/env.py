from gag_app.config.config import GAG_BASE_LANGUAGE, AUTHENT_STRUCTURE

list_label_field = ['label', 'name', 'type', 'route', 'organism', 'difficulty', 'network', 'reservation_system']

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
    "attachments" : {
        "author" : "author",
        "title" : "title",
        "legend" : "legend",
        "uuid" : "uuid",
    },
    "default_values" : {
        "review" : False,
        "attachment_video" : "",
        "attachment_file" : "",
        "attachment_link" : "",
        "marque" : False,
    },
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

specific = {
    "POI" : {
        "db_column_api_field" : {},
        "fk_not_integrated" : {
            "POIType": "poi_type",
        },
    },
    "Trek" : {
        "db_column_api_field" : {
            "accessibility_infrastructure" : ["disabled_infrastructure", GAG_BASE_LANGUAGE],
            "accessibility_infrastructure_en" : ["disabled_infrastructure", "en"],
            "accessibility_infrastructure_es" : ["disabled_infrastructure", "es"],
            "accessibility_infrastructure_fr" : ["disabled_infrastructure", "fr"],
            "accessibility_infrastructure_it" : ["disabled_infrastructure", "it"],
            "duration" : "duration",
            "eid2" : "second_external_id",
            "reservation_id": "reservation_id",
        },
        "fk_not_integrated" : {
            "DifficultyLevel": "trek_difficulty",
            "Practice": "trek_practice",
            "Route": "trek_route",
            "ReservationSystem": "reservationsystem",
        },
    }
}

source_cat_to_gag_cat = {
    "PNE" : {
        "POI" : {
            "POIType" : {
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
        },
        "Trek" : {
            "DifficultyLevel" : {
                "Très facile" : "Très facile",
                "Facile" : "Facile",
                "Intermédiaire" : "Moyen",
                "Difficile" : "Difficile",
                "Très difficile" : "Très difficile",
            },
            "Route" : {
                "Boucle" : "Boucle",
                "Aller-retour" : "Aller-retour",
                "Traversée" : "Itinérance",
                "Itinérance" : "Itinérance",
                "Etape" : "Itinérance",
            },
            "Practice" : {
                "VTT" : "VTT",
                "Pédestre" : "Rando à pied",
                "Vélo" : "VTT",
                "Raquettes" : "Rando à pied",
                "Cheval" : "A cheval",
            },
            "ReservationSystem" : {
                "OpenSystem" : "OpenSystem",
                "Itinérance" : "Gîtes de France"
            },
        },
    },
    "PNC" : {
        "POI" : {
            "POIType" : {
                "Flore" : "Flore",
                "Faune" : "Faune",
                "Géologie" : "Géologie",
                "Architecture" : "Architecture",
                "Paysage" : "Paysage",
                "Tradition" : "Tradition",
                "Histoire" : "Histoire",
                "Archéologie" : "Archéologie",
                "Eau" : "Eau",
                "Pastoralisme" : "Pastoralisme",
                "Savoir-faire" : "Savoir-faire",
                "Agriculture" : "Agriculture",
                "Milieu naturel" : "Milieu naturel",
            },
        },
        "Trek" : {
            "DifficultyLevel" : {
                "Très facile" : "Très facile",
                "Facile" : "Facile",
                "Moyen" : "Moyen",
                "Difficile" : "Difficile",
                "Très difficile" : "Très difficile",
            },
            "Route" : {
                "Boucle" : "Boucle",
                "Aller-retour" : "Aller-retour",
                "Itinérance" : "Itinérance",
            },
            "Practice" : {
                "VTT" : "VTT",
                "Rando à pied" : "Rando à pied",
                "Sentiers de découverte" : "Sentiers de découverte",
                "Trail" : "Trail",
                "A cheval" : "A cheval",
            },
            "ReservationSystem" : {
                "OpenSystem" : "OpenSystem",
                "Itinérance" : "Gîtes de France",
                "FFCAM" : "FFCAM",
            },
        },
    },
    "Conseil départemental de la Lozère" : {
        "POI" : {
            "POIType" : {
                "Faune et Flore" : "Flore",
                "Eau et géologie" : "Géologie",
                "Architecture" : "Architecture",
                "Forêts" : "Milieu naturel",
                "Agriculture et élevage" : "Pastoralisme",
                "Histoire et culture" : "Histoire",
                "Cols et Sommets" : "Paysage",
                "Accessibilité handicap" : "Savoir-faire"
            },
        },
        "Trek" : {
            "DifficultyLevel" : {
                "Très facile" : "Très facile",
                "Facile" : "Facile",
                "Intermédiaire" : "Moyen",
                "Difficile" : "Difficile",
                "Très difficile" : "Très difficile",
            },
            "Route" : {
                "Boucle" : "Boucle",
                "Aller-retour" : "Aller-retour",
                "Traversée" : "Itinérance",
            },
            "Practice" : {
                "VTT" : "VTT",
                "Cyclo route" : "VTT",
                "Pédestre" : "Rando à pied",
                "Raquettes" : "Rando à pied",
                "Cheval" : "A cheval",
            },
            "ReservationSystem" : {
                "OpenSystem" : "OpenSystem",
                "Gites de France" : "Gîtes de France"
            },
        },
    },
    "PNRGCA" : {
        "POI" : {
            "POIType" : {
                "Flore" : "Flore",
                "Faune" : "Faune",
                "Géologie" : "Géologie",
                "Architecture" : "Architecture",
                "Histoire et patrimoine" : "Histoire",
                "Archéologie" : "Archéologie",
                "Agropastoralisme" : "Pastoralisme",
                "Savoir-faire" : "Savoir-faire",
                "Dolmen" : "Tradition",
                "Installation artistique" : "Paysage",
                "Petit patrimoine" : "Architecture",
                "Point de vue" : "Paysage",
                "Statue-menhir" : "Tradition",
            },
        },
        "Trek" : {
            "DifficultyLevel" : {
                "Très facile" : "Très facile",
                "Facile" : "Facile",
                "Moyen" : "Moyen",
                "Difficile" : "Difficile",
                "Très difficile" : "Très difficile",
            },
            "Route" : {
                "Boucle" : "Boucle",
                "Aller-retour" : "Aller-retour",
                "Etape" : "Itinérance",
                "Séjour itinérant" : "Itinérance",
                "Descente" : "Boucle",
                "Montée" : "Boucle",
            },
            "Practice" : {
                "VTT" : "VTT",
                "Cyclo" : "VTT",
                "Pédestre" : "Rando à pied",
                "Raquettes" : "Rando à pied",
                "Equestre" : "A cheval",
                "Canoë" : "A cheval",
                "Trail" : "Rando à pied",
                "Gravel" : "VTT",
                "Enduro VTT" : "VTT",
            },
            "ReservationSystem" : {
            },
        },
    },
}
