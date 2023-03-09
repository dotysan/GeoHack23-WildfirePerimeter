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

# Spa Libraries
from SpaTestUtil import *
from SpaPy import SpaPlot
from SpaPy import SpaVectors
from SpaPy import SpaView
from SpaPy import SpaReferencing

############################################################################
# Globals
############################################################################
CountriesFilePath="../Data/NaturalEarth/ne_110m_admin_0_countries.shp"

OutputFolderPath="../Temp/"

############################################################################
# STLayerVector functions
############################################################################

#########################################################################
# Load the dataset into SpaDatasetVector object.

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer

TheDataset.Load(CountriesFilePath) # load the contents of the layer

#########################################################################
# Plotting operations

if (True):
	ThePlotter=SpaPlot.SpaPlot()
	
	ThePlotter.Plot(TheDataset)
	
	ThePlotter.Show()

