# URL du Geotrek-admin source :
GADMIN_BASE_URL = 'geotrek-admin.cevennes-parcnational.net'

# Si nécessaire, nom du (ou des) portail(s) de la base source
# dont on veut récupérer les données :
PORTALS = ['DEP_48']

# Attribution des données à une structure.
# Doit correspondre à une entrée dans la table "authent_structure".
# Indispensable pour la tracabilité des données.
# /!\ Il ne s'agit pas d'un filtre des données importées.
# Il s'agit uniquement d'attribuer les données importées à une structure
# dans la base aggregator.
# Ne dépend donc pas des structures enregistrées dans la BDD source
AUTHENT_STRUCTURE = 'PNC'

# Nom de l'user auquel sera attribuée la création des médias
# Par exemple un compte d'administration.
AUTH_USER = 'gadmin48'

GAG_BASE_LANGUAGE = 'fr'  # langue par défaut de la base de données aggregator

# Exemples :
# 'geotrek-admin.cevennes-parcnational.net'
# AUTHENT_STRUCTURE = 'PNC' PORTALS = ['DEP_48']

# admin48.openig.org
# AUTHENT_STRUCTURE = 'Conseil départemental de la Lozère' PORTALS = None

# geotrekdemo.ecrins-parcnational.fr
# AUTHENT_STRUCTURE = 'PNE' PORTALS = None

# openig-geotrek-pnrgca.ataraxie.fr
# AUTHENT_STRUCTURE = 'PNRGCA' PORTALS = ['Rando Lozère']
