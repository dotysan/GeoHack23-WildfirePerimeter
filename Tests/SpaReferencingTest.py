############################################################################
# Test File for the Spatial (Spa) libraries.  This file runs a series of tests
# for the spatial referencing (e.g. SRS, CRS) functions in SpaPy.
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
import webbrowser

# Open source spatial libraries
import shapely
import numpy
from osgeo import gdal
import math
import random

# SpaPy libraries
from SpaTestUtil import *
from SpaPy import SpaBase
from SpaPy import SpaVectors
from SpaPy import SpaView
from SpaPy import SpaReferencing
from SpaPy import SpaDensify
from SpaPy import SpaView
from SpaPy import SpaRasters
from SpaPy import SpaTopo
from SpaPy import SpaRasterVectors
from SpaTestUtil import *

# Paths to files
DataPath="../Data/"
CountriesFilePath="../Data/NaturalEarth/ne_110m_admin_0_countries.shp"
CountriesFilePath=DataPath+"NaturalEarth/ne_110m_admin_0_countries_Simple_Attributes2.shp"

OverlayFile="../Data/Overlay/Box.shp"

HumbRiverPath="../Data/HumboldtCounty/hydrography/nhd24kst_l_ca023.shp"

HumbZoningPath="../Data/HumboldtCounty/humz55sp.shp"

Zoning_Bay="../Data/HumboldtCounty/Zoning_Bay.shp"

NASABlueMarble="../Data/NASA/BlueMarbleNG-TB_2004-12-01_rgb_1440x720.TIFF"

OutputFolderPath="../Temp/SpaReferencing/"

SetupOutputFolder(OutputFolderPath)
TheHTMLFile=None
HTMLOpen(OutputFolderPath+"_SpaVectorTest.html")
HTMLHeading("Spa Referencing Test")

#########################################################################
AlbersEqualArea_Parameters={
	"datum":"WGS84",
	"proj":"aea",
	"lat_1":40,
	"lat_2":60
}

if (True):
	
	HTMLHeading("Vector projections")
	
	CountriesDataset=SpaVectors.SpaDatasetVector() #create a new layer
	CountriesDataset.Load(CountriesFilePath) # load the contents of the layer
	
	# Need to make sure each line segment has enough points to look good after being projected (i.e. the may curve)
	CountriesDataset=SpaDensify.Densify(CountriesDataset,5)
	
	# Clip the bounds of the geographic data to be within the possible bounds of the projection
	WestCoastDataset=SpaVectors.Clip(CountriesDataset,-156,-90,-90,90) # the zone is 6 degrees wide but we can go wider
	
	# WGS 84 / UTM zone 10N
	Dataset_UTMZone10North=SpaReferencing.Transform(WestCoastDataset,32610)
	#SpaView.Show(Dataset_UTMZone10North)
	
	HTMLHeading("Countries UTM",2)
	HTMLRenderDataset(Dataset_UTMZone10North,OutputFolderPath,"UTMZone10North.png")
	
	# Project from UTM to WGS 84
	UTMToGeographic=SpaReferencing.Transform(Dataset_UTMZone10North,4326)
	#SpaView.Show(UTMToGeographic)
	
	UTMToGeographic.Save(OutputFolderPath+"Geographic.shp")
	
	HTMLHeading("Back Projected To Geographic",2)
	HTMLRenderDataset(UTMToGeographic,OutputFolderPath,"BackProjectedToGeographic.png")
	
	# Project to NAD83 / California zone 1
	UTMToStatePlane=SpaReferencing.Transform(Dataset_UTMZone10North,26941)
	#SpaView.Show(UTMToStatePlane)
	
	HTMLHeading("California zone 1",2)
	HTMLRenderDataset(UTMToStatePlane,OutputFolderPath,"CaliforniaZone1.png")
	
	# Project to Albers Equal Area
	AlbersEqualArea=SpaReferencing.Transform(CountriesDataset,AlbersEqualArea_Parameters)
	#SpaView.Show(AlbersEqualArea)
	
	HTMLHeading("Albers Equal Area",2)
	HTMLRenderDataset(AlbersEqualArea,OutputFolderPath,"AlbersEqualArea.png")

#######################################################################
	
HTMLHeading("Raster projections")

BlueMarbleRaster=SpaRasters.SpaDatasetRaster() #create a new layer
BlueMarbleRaster.Load(NASABlueMarble) # load the contents of the layer

#SpaView.Show(BlueMarbleRaster)

# Currently, we are using a GDAL function that requires an output path for the projected raster file so there is a different function to projecting rasters
AlbersEqualArea=SpaReferencing.TransformRaster(BlueMarbleRaster,OutputFolderPath+"BlueMarble_Albers.tif",AlbersEqualArea_Parameters)
#SpaView.Show(AlbersEqualArea)

HTMLHeading("Albers Equal Area",2)
HTMLRenderDataset(AlbersEqualArea,OutputFolderPath,"AlbersEqualArea.png")

# Project to UTM
UTMZone10North=SpaReferencing.TransformRaster(BlueMarbleRaster,OutputFolderPath+"BlueMarble_UTM.tif",32610)
#SpaView.Show(UTMZone10North)

HTMLHeading("UTM Zone 10 North",2)
HTMLRenderDataset(UTMZone10North,OutputFolderPath,"UTMZone10North.png")

HTMLClose()

# Open the browser to show the file
Thing=os.path.abspath("../Temp/SpaReferencing")

WebPagePath="file:///"+Thing+"/_SpaVectorTest.html"

webbrowser.open(WebPagePath)