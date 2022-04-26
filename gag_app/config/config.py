# URL du Geotrek-admin source :
GADMIN_BASE_URL = 'admin48.openig.org'

# Si nécessaire, nom du (ou des) portail(s) de la base source
# dont on veut récupérer les données :
PORTALS = None

# Nom de la source des données.
# Doit correspondre à une entrée dans la table "authent_structure".
# Indispensable pour la tracabilité des données.
AUTHENT_STRUCTURE = 'Conseil départemental de la Lozère'

# Nom de l'user auquel sera attribuée la création des médias
# Par exemple un compte d'administration.
AUTH_USER = 'gadmin48'

GAG_BASE_LANGUAGE = 'fr'  # langue par défaut de la base de données aggregator

# Exemples :
# geotrek-admin.cevennes-parcnational.net
# AUTHENT_STRUCTURE='PNC' PORTALS=['DEP_48']

# admin48.openig.org
# AUTHENT_STRUCTURE='Conseil départemental de la Lozère' PORTALS = None

# geotrekdemo.ecrins-parcnational.fr
# AUTHENT_STRUCTURE='PNE' PORTALS = None

# openig-geotrek-pnrgca.ataraxie.fr
# AUTHENT_STRUCTURE='PNRGCA' PORTALS = [1]
