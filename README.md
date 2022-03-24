# geotrek-admin-aggregator

## Contexte
[OPenIG](https://www.openig.org/), le [Parc national des Cévennes](https://www.cevennes-parcnational.fr/) et le [Département de la Lozère](https://lozere.fr/) ont décidé de s'impliquer dans l'évolution du Geotrek-aggregator. En effet, Geotrek-aggregator dans sa version actuelle n'est pas compatible avec la V3 de Geotrek-rando et atteint ses limites face aux développements dernièrement réalisés par la communauté.

C'est pourquoi ce travail de développement est porté par OPenIG, afin de pouvoir agréger les données des 3 bases de données Geotrek-admin présentes sur la Lozère pour les valoriser sur un même site Internet Geotrek-rando V3.

Ce travail est soutenu financièrement par le Département de la Lozère et appuyé techniquement par [Amandine Sahl](https://github.com/amandine-sahl) du Parc national des Cévennes.

Au-delà du « territoire pilote » que constitue la Lozère, le travail a vocation à servir d’autres structures utilisatrices de Geotrek, en Occitanie et sur le territoire national ; il est notamment prévu de rédiger des procédures / guides de bonnes pratiques sur Geotrek-aggregator et de réaliser des tutoriels vulgarisés.

## Choix techniques
L’application développée se connectera à l’API V2 pour récupérer des données d’une base source et adaptera les données reçues aux catégories de la base de données aggregator, ainsi qu'au modèle objet de Geotrek-admin. Les technologies privilégiées sont le langage Python, le framework Flask et le toolkit SQLAlchemy.

## Configuration

### Fichier `config.py.sample`
Renseigner tous les paramètres :
 - `API_BASE_URL` : URL de l'API v2 de la base de données source
 - `AUTHENT_STRUCTURE` : Nom de la source des données. Doit correspondre à une entrée dans la table "authent_structure". Indispensable pour la tracabilité des données.
 - `SQLALCHEMY_DATABASE_URI` : URI de la base de données aggregator, au format SQLAlchemy
 - `GAG_BASE_LANGUAGE` : langue par défaut de la base de données aggregator
 - `SRID` : SRID du système de coordoonées de la base de données aggregator
 
 Renommer le fichier `config.py.sample` en `config.py`

### Fichier `env.py`
/!\ N'a pas vocation à être un fichier à configurer manuellement /!\
Pour l'instant, la mise en correspondance des catégories des bases de données source et aggregator se fait via le dictionnaire `source_cat_to_gag_cat`. Chaque table de catégories y est recensée. Pour chaque table, l'ensemble des catégories de la base de données source est listée, et pour chacune d'entre elles la catégorie à laquelle elle correspond dans la base aggregator.

## Utilisation
/!\ Prototype en développement /!\

Se placer dans le répertoire principal de l'application, créer un environnement virtuel et l'activer :
``` zsh
python3 -m venv venv
source venv/bin/activate
```

Installer les packages requis :
``` zsh
pip install -r requirements.txt
```

Lancer la commande suivante pour interroger l'API et remplir la base de données indiquées dans la configuration :
``` zsh
flask test
```

## Fonctionnement


&nbsp;
<p align="middle">
  <img src="img/logo_openig.png" height="100" />
  &nbsp; &nbsp; &nbsp; &nbsp;
  <img src="img/logo_lozere.jpg" height="100" />
  &nbsp; &nbsp; &nbsp; &nbsp;
  <img src="img/logo_pnc.jpg" height="100" />
</p>
