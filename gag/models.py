from gag.app import DB
from flask import current_app
from sqlalchemy.ext.automap import automap_base
from geoalchemy2 import Geometry, Raster

print("Automapping database and preparing classes...")
Base = automap_base()
Base.prepare(DB.get_engine(current_app), reflect = True)

CoreTopology = Base.classes.core_topology

TrekkingPoi = Base.classes.trekking_poi

TrekkingPoitype = Base.classes.trekking_poitype

CoreNetwork = Base.classes.core_network

AuthentStructure = Base.classes.authent_structure

TrekkingTrek = Base.classes.trekking_trek

TrekkingDifficultylevel = Base.classes.trekking_difficultylevel

TrekkingRoute = Base.classes.trekking_route

TrekkingPractice = Base.classes.trekking_practice

CommonReservationsystem = Base.classes.common_reservationsystem

TrekkingAccessibilitylevel = Base.classes.trekking_accessibilitylevel



# class CoreTopology(Base):
#     __table__ = Base.metadata.tables['core_topology']

# class TrekkingPoi(Base):
#     __table__ = Base.metadata.tables['trekking_poi']

# class TrekkingPoiType(Base):
#     __table__ = Base.metadata.tables['trekking_poitype']
