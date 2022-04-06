API_BASE_URL = 'https://geotrekdemo.ecrins-parcnational.fr/api/v2/' ## URL de l'API v2 de la base de données source
PORTALS = [] ## Si nécessaire, nom du (ou des) portail(s) de la base source dont on veut récupérer les données.
AUTHENT_STRUCTURE = 'PNE' ## Nom de la source des données. Doit correspondre à une entrée dans la table "authent_structure". Indispensable pour la tracabilité des données.
AUTH_USER = 'gadmin48' ## Nom de l'user auquel sera attribuée la création des médias. Par exemple un compte d'administration.
GAG_BASE_LANGUAGE = 'fr' ## langue par défaut de la base de données aggregator
SRID = 2154 ## SRID du système de coordonnées de la base de données aggregator


#https://geotrek-admin.cevennes-parcnational.net/api/v2/ PNC portal 'DEP_48'
#https://admin48.openig.org/api/v2/ Conseil départemental de la Lozère portal None
#https://geotrekdemo.ecrins-parcnational.fr/api/v2/ PNE portal None
#https://openig-geotrek-pnrgca.ataraxie.fr/api/v2/ portal 1 ??
