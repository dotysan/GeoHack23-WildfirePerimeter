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

OutputFolderPath="../Temp/"

RasterFilePath="../Data/MtStHelens/Mt St Helens Post Eruption DEM Int16.tif"
#RasterFilePath2="../Data/MtStHelens/Mt St Helens PreEruption DEM Float32.tif"

Path1="../Data/MtStHelens/Mt St Helens PreEruption DEM Float32.tif"
#Path2="../Data/MtStHelens/Mt St Helens Post Eruption DEM.tif"

############################################################################
# SpaView Tests
############################################################################
TheDataset=SpaRasters.Load(Path1)
SpaTopo.Contour(Path1,OutputFilePath=OutputFolderPath+"Countours.shp")
#SpaView.Show(OutputFolderPath+"Countours.shp")

SpaTopo.TRI(Path1,OutputFilePath=OutputFolderPath+"TRI.tif")
SpaView.Show(OutputFolderPath+"TRI.tif") # deal with no data values
#TRIDataset.Save(OutputFolderPath+"TRI.tif")

SpaTopo.Slope(TheDataset,OutputFilePath=OutputFolderPath+"Slope.tif")
SpaView.Show(OutputFolderPath+"Slope.tif")

SpaTopo.Aspect(TheDataset,OutputFilePath=OutputFolderPath+"Aspect.tif")
SpaView.Show(OutputFolderPath+"Aspect.tif")

SlopeDataset=SpaRasters.Load(OutputFolderPath+"Slope.tif")
AspectDataset=SpaRasters.Load(OutputFolderPath+"Aspect.tif")

SteepDataset=SlopeDataset>20
SpaView.Show(SteepDataset)

GreaterThan90Degrees=AspectDataset>90
SpaView.Show(GreaterThan90Degrees)

LessThan270Degres=AspectDataset<270
SpaView.Show(LessThan270Degres)

SouthDataset=SpaRasters.And(GreaterThan90Degrees,LessThan270Degres)
SpaView.Show(SouthDataset)

NewDataset3=SpaRasters.And(SouthDataset,SteepDataset)
SpaView.Show(NewDataset3)

# works 
NewDataset=SpaTopo.Hillshade(Path1)
NewDataset.Save(OutputFolderPath+"Hillshade.tif")
SpaView.Show(NewDataset)
