############################################################################
# Test File for the Spatial (SP) libraries
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
import os
import glob
import traceback
import webbrowser
# Open source spatial libraries
import shapely
import numpy

# SpaPy libraries
from SpaTestUtil import *
from SpaPy import SpaVectors
from SpaPy import SpaView
from SpaPy import SpaReferencing
from SpaPy import SpaDensify
from SpaTestUtil import *

# Paths to files
DataPath="../Data/"
CountriesFilePath=DataPath+"NaturalEarth/ne_110m_admin_0_countries.shp"
CountriesFilePath=DataPath+"NaturalEarth/ne_110m_admin_0_countries_Simple_Attributes2.shp"

OutputFolderPath="../Temp/GeometryTest/"

TheHTMLFile=None

#########################################################################
# Start of code
#########################################################################
if ( os.path.exists(OutputFolderPath)==False): os.makedirs(OutputFolderPath)

HTMLOpen(OutputFolderPath+"_SpaGeometryCollectionTest.html")

HTMLHeading("Spa Geometry Collection Test")
HTMLParagraph("At the bottom of the web page is the number of errors.  Search for 'Error:' to find the errors.")

NumErrors=0

#########################################################################
# Utility functions

def GetCoordinateArrayForBox(XMin,YMin,XMax,YMax):
	# bottom-left, top-left, top-right,bottom-right, back to bottom-left
	CoordinateArray=[(XMin,YMin), (XMin,YMax), (XMax,YMax), (XMax,YMin),(XMin,YMin)] 
	return(CoordinateArray)

#########################################################################
# Point (works)
try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('Point') 
	TheDataset.SetCRS(4326)   
	
	# add a square geometry in at 0,0
	ThePointGeometry1=shapely.geometry.Point(0,0)
	TheDataset.AddFeature(ThePointGeometry1)
	
	ThePointGeometry2=shapely.geometry.Point(10,10)
	TheDataset.AddFeature(ThePointGeometry2)
	
	ThePointGeometry3=shapely.geometry.Point(10,-10)
	TheDataset.AddFeature(ThePointGeometry3)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"Points.shp") 
	print("Saved Points")
	
	HTMLHeading("Three Points")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"Polygon.png")
	HTMLImage("Polygon.png")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
# Polygon (works)

try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('Polygon') 
	TheDataset.SetCRS(4326)   
	
	# add a square geometry in at 0,0
	CoordinateArray=GetCoordinateArrayForBox(-10,-10,10,10)
	PolygonGeometry=shapely.geometry.Polygon(CoordinateArray) # holes are optional for a simple polygon
	
	TheDataset.AddFeature(PolygonGeometry)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"Polygon.shp") 
	print("Saved Polygon")
	
	HTMLHeading("Polygon Geometry")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"PolygonGeometry.png")
	HTMLImage("PolygonGeometry.png")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
# Polygon with hole (works)

try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('Polygon') 
	TheDataset.SetCRS(4326)   
	
	# add a square geometry in at 0,0
	Exterior=GetCoordinateArrayForBox(-10,-10,10,10)
	Hole=GetCoordinateArrayForBox(-1,-1,1,1)
	
	PolygonGeometryWithHole=shapely.geometry.Polygon(Exterior,[Hole]) # includes a hole
	TheDataset.AddFeature(PolygonGeometryWithHole)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"PolygonWithHole.shp") 
	print("Saved PolygonWithHole")
	
	HTMLHeading("PolygonGeometryWithHole")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"PolygonGeometryWithHole.png")
	HTMLImage("PolygonGeometryWithHole.png")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
# MultiPolygon

try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('MultiPolygon') 
	TheDataset.SetCRS(4326)   
	
	# create a square geometry in at 0,0 with a hole
	Exterior=GetCoordinateArrayForBox(-30,30,-20,40)
	Hole=GetCoordinateArrayForBox(-26,34,-24,36)
	Polygon1=(Exterior,[Hole]) # holes appear to be required when more than one polygon is in a multipolygon
	
	# create another square
	Exterior2=GetCoordinateArrayForBox(-30,-30,-20,-20)
	Polygon2=(Exterior2,[])
	
	MultiPolygonGeometry=shapely.geometry.MultiPolygon([ Polygon1,Polygon2])
	TheDataset.AddFeature(MultiPolygonGeometry)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"MultiPolygon.shp") 
	print("Saved MultiPolygon")
	
	HTMLHeading("MultiPolygon")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"MultiPolygon.png")
	HTMLImage("MultiPolygon.png")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
# Polyline

try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('LineString') 
	TheDataset.SetCRS(4326)   
	
	# add a square geometry in at 0,0
	LineStringGeometry=shapely.geometry.LineString([(-10,10), (10,10), (10,-10)])
	
	TheDataset.AddFeature(LineStringGeometry)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"LineString.shp") 
	print("Saved LineString")
	
	HTMLHeading("LineString")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"LineString.png")
	HTMLImage("LineString.png")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
# MultiLineString

try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('MultiLineString') 
	TheDataset.SetCRS(4326)   
	
	# add a square geometry in at 0,0
	LineString1=((0,20), (20,20), (20,0))
	LineString2=((0,30), (30,30), (30,0))
	
	MultiLineStringGeometry=shapely.geometry.MultiLineString([LineString1,LineString2])
	TheDataset.AddFeature(MultiLineStringGeometry)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"MultiLineString.shp") 
	print("Saved MultiLineString")
		
	HTMLHeading("MultiLineString")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"MultiLineString.png")
	HTMLImage("MultiLineString.png")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
# GeometryCollection

try:

	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
	TheDataset.SetType('GeometryCollection') 
	TheDataset.SetCRS(4326)   
	
	# add a square geometry in at 0,0
	CollectionGeometry=shapely.geometry.GeometryCollection([ThePointGeometry1,PolygonGeometryWithHole,MultiPolygonGeometry,LineStringGeometry,MultiLineStringGeometry])
	TheDataset.AddFeature(CollectionGeometry)
	
	# Save the result
	TheDataset.Save(OutputFolderPath+"GeometryCollection_Point.shp","Point") 
		
	TheDataset.Save(OutputFolderPath+"GeometryCollection_LineString.shp","MultiLineString") 
	
	TheDataset.Save(OutputFolderPath+"GeometryCollection_Polygon.shp","MultiPolygon") 
		
	HTMLHeading("GeometryCollection_Polygon")
	RenderDatasetToImage(TheDataset,OutputFolderPath+"GeometryCollection.png")
	HTMLImage("GeometryCollection_Polygon.png")
	
	print("Saved GeometryCollection")
	
except Exception  as TheException: HTMLError(TheException)

#########################################################################
print("done")
HTMLClose()

# Open the browser to show the file
Thing=os.path.abspath("../Temp/GeometryTest")

WebPagePath="file:///"+Thing+"/_SpaGeometryCollectionTest.html"

webbrowser.open(WebPagePath)
