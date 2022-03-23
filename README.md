# geotrek-admin-aggregator

## Contexte
[OPenIG](https://www.openig.org/), le [Parc national des Cévennes](https://www.cevennes-parcnational.fr/) et le [Département de la Lozère](https://lozere.fr/ )ont décidé de s'impliquer dans l'évolution du Geotrek-aggregator. En effet, Geotrek-aggregator dans sa version actuelle n'est pas compatible avec la V3 de Geotrek-rando et atteint ses limites face aux développements dernièrement réalisés par la communauté.
C'est pourquoi ce travail de développement est porté par OPenIG, afin de pouvoir agréger les données des 3 bases de données Geotrek-admin présentes sur la Lozère pour les valoriser sur un même site Internet Geotrek-rando V3.
Ce travail est soutenu financièrement par le Département de la Lozère et appuyé techniquement par [Amandine Sahl](https://github.com/amandine-sahl) du Parc national des Cévennes.
Au-delà du « territoire pilote » que constitue la Lozère, le travail a vocation à servir d’autres structures utilisatrices de Geotrek, en Occitanie et sur le territoire national ; il est notamment prévu de rédiger des procédures / guides de bonnes pratiques sur Geotrek-aggregator et de réaliser des tutoriels vulgarisés.

## Choix techniques
L’application développée se connectera à l’API V2 pour récupérer des données d’une base source et adaptera les données reçues aux catégories de la base de données aggregator, ainsi qu'au modèle objet de Geotrek-admin. Les technologies privilégiées sont le langage Python, le framework Flask et le toolkit SQLAlchemy.