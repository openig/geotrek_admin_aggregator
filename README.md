# geotrek-admin-aggregator

## Contexte
[OPenIG](https://www.openig.org/), le [Parc national des Cévennes](https://www.cevennes-parcnational.fr/) et le [Département de la Lozère](https://lozere.fr/) ont décidé de s'impliquer dans l'évolution du Geotrek-aggregator. En effet, Geotrek-aggregator dans sa version actuelle n'est pas compatible avec la V3 de Geotrek-rando et atteint ses limites face aux développements dernièrement réalisés par la communauté.

C'est pourquoi ce travail de développement est porté par OPenIG, afin de pouvoir agréger les données des 3 bases de données Geotrek-admin présentes sur le territoire lozérien pour les valoriser sur un même site Internet Geotrek-rando V3.

Ce travail est soutenu financièrement par le Département de la Lozère et appuyé techniquement par [Amandine Sahl](https://github.com/amandine-sahl) du Parc national des Cévennes.

Au-delà du « territoire pilote » que constitue la Lozère, le travail a vocation à servir d’autres structures utilisatrices de Geotrek, en Occitanie et sur le territoire national ; il est notamment prévu de rédiger des procédures / guides de bonnes pratiques sur Geotrek-admin aggregator et de réaliser des tutoriels vulgarisés.

## Choix techniques
L’application développée se connecte à l’API V2 pour récupérer des données d’une base source et adapter les données reçues aux catégories de la base de données aggregator, ainsi qu'au modèle objet de Geotrek-admin. Cette version s'intègre à Geotrek-admin en utilisant les modèles Django déjà disponibles. Aucune librairie supplémentaire n'est donc nécessaire.

## Prérequis

Le Geotrek-admin aggregator (surnommé GAG) est prévu pour alimenter une base de données utilisée uniquement pour de la valorisation via un Geotrek-rando. C'est pourquoi seules des données de valorisation sont agrégées, et pas de gestion. Aussi, aucune interaction avec des tronçons n'est possible, et la segmentation dynamique doit être désactivée dans la base de données GAG.
Les modèles de données compatibles avec l'aggregator sont : `Trek`, `POI`, `TouristicContent`.

Avant de procéder à une agrégation, la base de données aggregator doit être préparée :
 - désactivation de la segmentation dynamique : ajout de la ligne `TREKKING_TOPOLOGY_ENABLED = False` au fichier `/opt/geotrek-admin/var/conf/custom.py`.
 - ajout d'un compte utilisateur auquel sera attribuée la création des médias, par exemple un compte administrateur. Son nom sera utilisé par le paramètre `AUTH_USER` du fichier de configuration du GAG.
 - ajout d'une structure `authent_structure` par source de données pour l'agrégation. Le nom de ces structures sera utilisé par le paramètre `AUTHENT_STRUCTURE` de chaque source du paramètre `SOURCES`du fichier de configuration du GAG.
 - renseignement de toutes les catégories de données nécessaires avec les valeurs souhaitées. Liste ci-dessous.

### Liste des catégories à renseigner avant agrégation

Cette liste présente, pour chaque modèle de données, les catégories gérées par l'aggregator et donc à renseigner dans la base de données GAG avec les valeurs souhaitées par la structure gestionnaire avant la première agrégation. Pour sélectionner les modèles et catégories à importer selon chaque source, voir plus bas dans ce document, section « Configuration/env.py ».

Guide de compréhension de la liste : Nom vulgarisé (nom de la table PostgreSQL / nom du modèle Django)

Les catégories qui doivent obligatoirement être renseignées si l'on souhaite agréger le modèle de données dont elles dépendent sont signalées par une mention spéciale.

#### Itinéraires (trekking_trek / Trek) :
 - difficulté (trekking_difficultylevel / DifficultyLevel)
 - pratique (trekking_practice / Practice)
 - parcours (trekking_route/ Route)
 - catégories liens web (trekking_weblinkcategory / WebLinkCategory)
 - réseaux (trekking_treknetwork / TrekNetwork)
 - niveaux d'accessibilité (trekking_accessibilitylevel, AccessibilityLevel)
 - thèmes (common_theme / Theme)
 - systèmes de réservation (common_reservationsystem / ReservationSystem)

#### POI (trekking_poi / POI) :
 - types de POI (trekking_poitype / POIType) (obligatoire)

#### Contenu touristique (tourism_touristiccontent / TouristicContent):
 - catégories de contenu touristique (tourism_touristiccontentcategory / TouristicContentCategory) (obligatoire)
 - types de contenu touristique (tourism_touristiccontenttype1 / TouristicContentType1et tourism_touristiccontenttype2 / TouristicContentType2) (obligatoire)
 - labels accessibilité (tourism_labelaccessibility, LabelAccessibility)
 - thèmes (common_theme / Theme)

En plus de cela, les catégories de données de la liste qui suit doivent être renseignées, non pas avec les valeurs souhaitées par la structure gestionnaire de l'aggregator, mais avec les valeurs directement issues des bases de données source. Il faut par exemple importer des bases sources l'ensemble des bureaux d'informations. Nous considérons que ces catégories ne sont pas à faire correspondre avec une nouvelle catégorie définie par l'organisation gestionnaire de l'aggregator, car cela aurait peu de sens de modifier le nom d'un bureau d'information, ou bien d'une source d'un itinéraire.

#### Itinéraires (trekking_trek / Trek) :
 - sources des fiches (common_recordsource / RecordSource)
 - étiquettes (common_label / Label)
 - lieux de renseignement (tourism_informationdesk / InformationDesk)
 - accessibilités (trekking_accessibility, Accessibility)
 - liens webs (trekking_weblink / Weblink)

#### Contenu touristique (tourism_touristiccontent / TouristicContent):
 - sources des fiches (common_recordsource / RecordSource)


/!\ Cela peut être contre-intuitif, mais il faut bien renseigner manuellement les liens web (`trekking_weblink`) et pas uniquement les catégories de liens web (`trekking_weblinkcategory`). Les noms des liens web peuvent être différents dans la base de données GAG par rapport à la base source (seule catégorie pour laquelle c'est autorisé), afin d'éviter les doublons et de la confusion. La reconnaissance se fait par l'URL du lien, qui doit être identique dans la base de données GAG et dans la base source. Cas d'usage : si deux structures sources ont un lien web nommé "TER SNCF" mais renvoyant chacun vers une page web différente car les deux structures sont dans des régions différentes, il est autorisé de modifier le nom des liens web en "TER SNCF Occitanie" et "TER SNCF Auvergne", tant que les URL ne sont pas modifiées.

## Configuration

### Fichier `gag_app/config/config.py.sample`
Copier le fichier `config.py.sample` vers `config.py`.

Renseigner tous les paramètres pour les adapter à son contexte organisationnel :
 - `AUTH_USER` : nom du compte utilisateur auquel sera attribuée la création des médias. Ce nom doit déjà exister dans la base, il n'est pas créé par le GAG.
 - `GAG_BASE_LANGUAGE` : langue par défaut de la base de données GAG (sous forme de code : fr, en, de...)
 - `SOURCES` : liste des sources de données à agréger. Chaque élément de la liste est un dictionnaire Python décrivant les paramètres de chaque source grâce aux clefs suivantes :
  - `AUTHENT_STRUCTURE` : nom de la structure à laquelle seront attribuées les données importées. Ce nom doit déjà exister dans la base, il n'est pas créé par le GAG.
  - `GADMIN_BASE_URL` : URL du Geotrek-admin source (dans sa version la plus simple, soit l'hôte : sous-domaine.domaine / Ex : "admin48.openig.org")
  - `DATA_TO_IMPORT` : liste des données que l'on souhaite importer depuis cette source. Utilise les noms des modèles Django, listés dans la section précédente de ce document ou disponibles dans la variable `model_to_import` du fichier `gag_app/env.py`. On peut ainsi importer des données différentes selon la source.
  - `PORTALS` : liste des noms des portails de la base de données source dont on souhaite agréger les données. Peut être égal à `None` si on n'en a pas l'utilité.
  - `IMPORT_ATTACHMENTS` : peut prendre les valeurs `True` ou `False`, permet d'activer ou de désactiver l'import des médias pour cette source de données.

Exemple :
``` python
AUTH_USER = 'gadmin48'
GAG_BASE_LANGUAGE = 'fr
SOURCES = [
    {
        "AUTHENT_STRUCTURE": 'PNC',
        "GADMIN_BASE_URL": 'geotrek-admin.cevennes-parcnational.net',
        "DATA_TO_IMPORT": ['Trek', 'POI', 'TouristicContent'],
        "PORTALS": ['DEP_48'],
    },
    {
        "AUTHENT_STRUCTURE": 'Conseil départemental de la Lozère',
        "GADMIN_BASE_URL": 'admin48.openig.org',
        "DATA_TO_IMPORT": ['Trek', 'POI'],
        "PORTALS": None,
    },
]
```

### Fichier `gag_app/env.py`
/!\ À terme, n'a pas vocation à être un fichier à configurer manuellement /!\

Pour l'instant, la mise en correspondance des catégories des bases de données source et aggregator se fait via le dictionnaire `source_cat_to_gag_cat`. Chaque type de catégorie de données y est recensée. Pour chaque type de catégorie, l'ensemble des catégories de la base de données source est listée, et il faut associer à chacune d'entre elles la catégorie à laquelle elle correspond dans la base GAG.
Si on ne souhaite pas agréger un type de catégorie de données (par exemple les thèmes, ou le type de parcours), il suffit de supprimer ce type du dictionnaire. Cela peut être personnalisé source par source. Dans l'exemple suivant, les types de POI et les thèmes des itinéraires du PNC seront agrégés, alors que pour le PNRGCA, ce sont les types de POI et les types de parcours qui le seront.
Si une catégorie de données de la base source ne correspond à aucune catégorie dans la base GAG, il faut tout de même renseigner cette catégorie source, et lui associer la valeur `None` du côté GAG. La donnée (itinéraire, contenu touristique...) liée sera quand même importée, mais aura par exemple un thème en moins par rapport à la base de données source, ou un niveau de difficulté vide. Bien sûr, cela ne peut fonctionner pour les types de catégorie dont la présence est requise par Geotrek-admin (`POIType` pour les POI, `TouristicContentType` pour les contenus touristiques, etc.)

La structure est la suivante :

``` python
"PNC": { # source de données (cette clef doit correspondre à la valeur de AUTHENT_STRUCTURE renseignée dans config.py)
        "POIType": { # modèle de données (cette clef doit correspondre au nom du modèle Django)
            "Flore": "Flore et faune",  # catégorie de la source de données (à gauche) à faire correspondre avec une catégorie de l'aggregator (à droite)
            "Faune": "Flore et faune",
            "Géologie": "Géologie",
        },
        "Theme": {
            "Histoire et culture": "Histoire",
            "Causses et Cévennes / UNESCO": None, # Catégorie à laquelle ne correspond aucune catégorie du GAG.
        }
},
"PNRGCA": { # deuxième source de données, même fonctionnement
        "POIType": { # les modèles de données à faire correspondre doivent être les mêmes pour chaque source de données
            "Architecture": "Architecture",
            "Histoire et patrimoine": "Histoire",
            "Archéologie": "Archéologie",
        },
        "Route": {
            "Boucle": "Boucle",
            "Aller-retour": "Aller-retour",
        }
},
# etc.
```


## Utilisation
/!\ Prototype en développement /!\

Copier le dossier `gag_app` à l'emplacement suivant : `/opt/geotrek-admin/var/conf/`

Copier la ligne suivante en haut du fichier `geotrek-admin/var/conf/parsers.py` :
``` python
    from export_schema.custom_parser import SerializerSchemaItinerairesRando
```

Dans un terminal, lancer la commande `geotrek import GeotrekAdminAggregatorParser` (le mode sudo sera sûrement nécessaire).

## Fonctionnement

Le fichier `env.py` fait office d'instructions de traitement des champs issus de l'API pour l'application. Selon la présence d'un champ dans la variable `common` ou bien dans les dictionnaires `fk_mapped`, `fk_not_mapped` ou `db_column_api_field` de la variable `model_to_import`, il ne sera pas traité de la même manière.



Three options for the general functioning:
 - overload Parser class with redefinition of `parse()` function to call the GAG application present in `var/conf` directory of Geotrek;
 - modify the Parser class in order to avoid the necessity to have the `url` and `model` variables set in the overload;
 - create a new command to get rid of parsers structure and redefine everything from scratch.

Option 1 is the current choice.


&nbsp;
<p align="middle">
  <img src="img/logo_openig.png" height="100" />
  &nbsp; &nbsp; &nbsp; &nbsp;
  <img src="img/logo_lozere.jpg" height="100" />
  &nbsp; &nbsp; &nbsp; &nbsp;
  <img src="img/logo_pnc.jpg" height="100" />
</p>
