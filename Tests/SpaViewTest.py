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
from SpaPy import SpaBase
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

def GetBoundingPolygon(MinX,MinY=None,MaxX=None,MaxY=None):
	if (isinstance(MinX,(tuple,list))):
		TheBounds=MinX
		MinX=TheBounds[0]
		MinY=TheBounds[1]
		MaxX=TheBounds[2]
		MaxY=TheBounds[3]
		
	BoundingPoly=shapely.geometry.Polygon([(MinX,MaxY), (MaxX,MaxY), (MaxX,MinY), (MinX,MinY),(MinX,MaxY)])
	return(BoundingPoly)

def GetViewForDataset(TheDataset,Width,Height,TheGeographicBounds=(-180,-90,180,90)):
	"""
	Example function for rendering spatial datasets into a SpaView.  This function will
	create a view of the specified dimensions, render a light blue background 
	and then render the dataset into the view.  The view is returned for the user
	to futher customize, save, or display the contents of the view
	"""
	
	TheView=SpaView.SpaView(Width,Height)
	
	TheBounds=TheDataset.GetBounds()
	TheView.SetBounds(TheBounds)
	
	# render the ocean and a neat line around the spatial data
	TheGeographicBounds=GetBoundingPolygon(TheGeographicBounds)
	TheGeographicBounds=SpaDensify.Densify(TheGeographicBounds,5)
	
	TheProjectedBounds=SpaReferencing.Transform(TheGeographicBounds,4326,TheDataset.GetCRS())
	TheView.SetFillColor((210,220,250))
	TheView.RenderRefGeometry(TheProjectedBounds)
	
	# Render the spatial data
	TheLayer=SpaVectors.SpaLayerVector()
	TheLayer.SetDataset(TheDataset)
	TheLayer.Render(TheView,RandomColors=True)

	return(TheView)

#########################################################################
# Load the countries dataset

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset.Load(CountriesFilePath) # load the contents of the layer

#########################################################################
# Render a shapefile to a view
# Simple example to render an existing dataset with a bounding box

if (True):
	# Create an 800 x 400 pixel view
	TheView=SpaView.SpaView(800,400)
	
	# Move the view to match the bounds of the dataset
	TheBounds=TheDataset.GetBounds()
	TheView.SetBounds(TheBounds)
	
	# Add a neat line
	TheView.SetFillColor((210,220,255))
	TheView.RenderRect(0,0,799,399)
	
	# Render the dataset into the view
	TheLayer=SpaVectors.SpaLayerVector() # Create a layer to do the rendering and manage the symbology
	TheLayer.SetDataset(TheDataset)
	TheLayer.Render(TheView,True) # Renders a random set of pastel colors by default
	
	# Render the rivers into the view
	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.Load(RiversFilePath) # load the contents of the layer
	#TheView.Render(TheDataset)
	
	TheLayer.SetDataset(TheDataset)
	TheView.SetLineWidth(2)
	TheView.SetOutlineColor((0,0,255))
	TheLayer.Render(TheView) # Renders a random set of pastel colors by default 
	
	# Render the cities into the view
	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.Load(CitiesFilePath) # load the contents of the layer
	TheLayer.SetDataset(TheDataset)
	TheView.SetLineWidth(2)
	TheView.SetFillColor((255,255,0))
	TheView.SetOutlineColor((0,0,0))
	TheLayer.Render(TheView) # Renders a random set of pastel colors by default
	
	# Save to a PNG file
	TheView.Save(OutputFolderPath+"RenderedVectors.png")

	TheView.Show()
	

#########################################################################
# Project a dataset based on a EPSG number

if (True):
	# Clip the dataset around the valid UTM Zone area
	TheDataset=SpaVectors.Clip(CountriesFilePath,-160,-90,-90,90)
	
	TheDataset=SpaDensify.Densify(TheDataset,5)
	
	TheDataset=SpaReferencing.Transform(TheDataset,32610) # EPSG Number for UTM Zone 10 North
	
	TheDataset.Save(OutputFolderPath+"UTMZone10North.shp")
		
	# Get the view to write out a PNG and display the dataset in a tkinter window
	TheView=GetViewForDataset(TheDataset,800,800,(-160,-90,-90,90))
	TheView.Save(OutputFolderPath+"UTMZone10North.png")
	TheView.Show()
	
#########################################################################
# Project a dataset based on a EPSG number

if (True):

	TheDataset=SpaRasters.SpaDatasetRaster()
	TheDataset.Load(RasterFilePath)
	
	TheView=SpaView.SpaView(800,800)
	
	TheBounds=TheDataset.GetBounds()
	TheView.SetBounds(TheBounds)

	TheView.RenderRaster(TheDataset)
	
	TheView.Save(OutputFolderPath+"Raster.png")
	TheView.Show()

#######################################################################
# find missing area of mt st helens

if (True):
	import math
	SpaView.Show(Path1) # deal with no data values
	
	TheDataset=SpaRasters.Load(Path1)
	SpaTopo.Contour(Path1,OutputFilePath=OutputFolderPath+"Countours.shp")
	
	TRIDataset=SpaTopo.TRI(Path1)
	SpaView.Show(TRIDataset) # deal with no data values
	TRIDataset.Save(OutputFolderPath+"TRI.tif")
	
	SlopeDataset=SpaTopo.Slope(TheDataset)
	SpaView.Show(SlopeDataset)
	
	AspectDataset=SpaTopo.Aspect(TheDataset)
	SpaView.Show(AspectDataset)
	
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


#######################################################################
# show a dataset and a shapefile from a file path

#TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset=SpaVectors.Load(CountriesFilePath) # load the contents of the layer

# Show a vector dataset (points)
SpaView.Show(TheDataset)

# Show a vector shapefile
SpaView.Show(CountriesFilePath)

