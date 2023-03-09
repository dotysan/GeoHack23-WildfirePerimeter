############################################################################
# Test File for the Spatial (Spa) libraries
#
# Copyright (C) 2020, Humboldt State University, Jim Graham
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software  Foundation, either version 3 of the License, or (at your
# option) any later  version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# A copy of the GNU General Public License is available at
# <http://www.gnu.org/licenses/>.
############################################################################

import sys  

# Open source spatial libraries
import shapely
import numpy

# Spa Libraries
from SpaTestUtil import *
from SpaPy import SpaPlot
from SpaPy import SpaVectors
from SpaPy import SpaView
from SpaPy import SpaReferencing
from SpaPy import SpaDensify
from SpaPy import SpaRasters
from SpaPy import SpaTopo

############################################################################
# Globals
############################################################################

CountriesFilePath="../Data/NaturalEarth/ne_110m_admin_0_countries.shp"
RiversFilePath="../Data/NaturalEarth/ne_110m_rivers_lake_centerlines.shp"
CitiesFilePath="../Data/NaturalEarth/ne_110m_populated_places_simple.shp"

OutputFolderPath="../Temp/"

RasterFilePath="../Data/MtStHelens/Mt St Helens Post Eruption DEM Int16.tif"
#RasterFilePath2="../Data/MtStHelens/Mt St Helens PreEruption DEM Float32.tif"

Path1="../Data/MtStHelens/Mt St Helens PreEruption DEM Float32.tif"
#Path2="../Data/MtStHelens/Mt St Helens Post Eruption DEM.tif"

############################################################################
# SpaView Tests
############################################################################
# Create a new shapefile

TheDataset1=SpaVectors.SpaDatasetVector() #create a new layer

# add a square geometry in at 0,0
TheGeometry=shapely.geometry.Polygon([(-10,10), (10,10), (10,-10), (-10,-10),(-10,10)])
TheDataset1.AddFeature(TheGeometry)

# Save the result
TheDataset1.Save(OutputFolderPath+"Inside.shp") 

############################################################################
# Show a vector shapefile
TheDataset2=SpaVectors.SpaDatasetVector() #create a new layer

# add a square geometry in at 0,0
TheGeometry=shapely.geometry.Polygon([(-20,0), (0,0), (0,-20), (-20,-20),(-20,0)])
TheDataset2.AddFeature(TheGeometry)

# Save the result
TheDataset2.Save(OutputFolderPath+"NewBox2.shp") 

############################################################################
# Show a vector shapefile
TheDataset3=SpaVectors.SpaDatasetVector() #create a new layer

# add a square geometry in at 0,0
TheGeometry=shapely.geometry.Polygon([(-200,-100), (-100,-100), (-100,-30), (-200,-30),(-200,-100)])
TheDataset3.AddFeature(TheGeometry)

# Save the result
TheDataset3.Save(OutputFolderPath+"NewBox2.shp") 

############################################################################

Flag=TheDataset2.Intersects(TheDataset1)
print(Flag) # should be true

Flag=TheDataset3.Intersects(TheDataset1)
print(Flag) # should be false

Flag=TheDataset2.Touches(TheDataset1) # have at least one point in common but interiors do not intersect
print(Flag) # should be False

Flag=TheDataset2.Disjoint(TheDataset1)
print(Flag) # should be False

Flag=TheDataset2.Overlaps(TheDataset1)
print(Flag) # should be true

Flag=TheDataset2.Crosses(TheDataset1)
print(Flag) # should be False

Flag=TheDataset2.Contains(TheDataset1)
print(Flag) # should be False
