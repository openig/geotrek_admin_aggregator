# geotrek-admin-aggregator

## Contexte
[OPenIG](https://www.openig.org/), le [Parc national des Cévennes](https://www.cevennes-parcnational.fr/) et le [Département de la Lozère](https://lozere.fr/) ont décidé de s'impliquer dans l'évolution du Geotrek-aggregator. En effet, Geotrek-aggregator dans sa version actuelle n'est pas compatible avec la V3 de Geotrek-rando et atteint ses limites face aux développements dernièrement réalisés par la communauté.

C'est pourquoi ce travail de développement est porté par OPenIG, afin de pouvoir agréger les données des 3 bases de données Geotrek-admin présentes sur la Lozère pour les valoriser sur un même site Internet Geotrek-rando V3.

Ce travail est soutenu financièrement par le Département de la Lozère et appuyé techniquement par [Amandine Sahl](https://github.com/amandine-sahl) du Parc national des Cévennes.

Au-delà du « territoire pilote » que constitue la Lozère, le travail a vocation à servir d’autres structures utilisatrices de Geotrek, en Occitanie et sur le territoire national ; il est notamment prévu de rédiger des procédures / guides de bonnes pratiques sur Geotrek-aggregator et de réaliser des tutoriels vulgarisés.

## Choix techniques
L’application développée se connectera à l’API V2 pour récupérer des données d’une base source et adaptera les données reçues aux catégories de la base de données aggregator, ainsi qu'au modèle objet de Geotrek-admin. Cette version s'intègre à Geotrek-admin en utilisant les modèles Django déjà disponibles. Aucune librairie supplémentaire n'est donc nécessaire.

## Configuration

### Fichier `config.py.sample`
Renseigner tous les paramètres :
 - `API_BASE_URL` : URL de l'API v2 de la base de données source
 - `AUTHENT_STRUCTURE` : Nom de la source des données. Doit correspondre à une entrée dans la table "authent_structure". Indispensable pour la tracabilité des données.
 - `GAG_BASE_LANGUAGE` : langue par défaut de la base de données aggregator
 - `SRID` : SRID du système de coordoonées de la base de données aggregator

 Renommer le fichier `config.py.sample` en `config.py`

### Fichier `env.py`
/!\ À terme, n'a pas vocation à être un fichier à configurer manuellement /!\
Pour l'instant, la mise en correspondance des catégories des bases de données source et aggregator se fait via le dictionnaire `source_cat_to_gag_cat`. Chaque table de catégories y est recensée. Pour chaque table, l'ensemble des catégories de la base de données source est listée, et pour chacune d'entre elles la catégorie à laquelle elle correspond dans la base aggregator.

## Utilisation
/!\ Prototype en développement /!\

Copier le dossier `gag_app` à l'emplacement suivant : `/opt/geotrek-admin/var/conf/`

Ajouter la classe suivante au fichier `geotrek-admin/var/conf/parsers.py` :
``` python
from geotrek.trekking.models import POIType

class GeotrekAdminAggregatorParser(Parser):
    url = 'just_so_its_not_none'
    model = POIType # Useless but shouldn't be None

    def parse(self, filename=None, limit=None):
        import importlib

        from os.path import join
        from django.conf import settings

        module_path = join(settings.VAR_DIR, 'conf/gag_app/agg.py')
        spec = importlib.util.spec_from_file_location("agg", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
```

Dans un terminal, lancer la commande `geotrek import GeotrekAdminAggregatorParser`

## Fonctionnement

Le fichier `env.py` fait office d'instructions de traitement des champs issus de l'API pour l'application. Différentes opérations sont effectuées selon la catégorie de variables.

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
