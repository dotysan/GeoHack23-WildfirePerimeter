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

#CountriesFilePath="../Data/HumboldtCounty/EelRiver_ClippingArea_Buffered1km.shp"
#CountriesFilePath="C:/Temp/celltowsp.shp"
TriangleFilePath=DataPath+"Overlay/Triangle.shp"
BoxFilePath=DataPath+"Overlay/Box.shp"

OutputFolderPath="../Temp/SpaVectorTest/"

TheHTMLFile=None

#########################################################################
# Start of code
#########################################################################

# Create the HTML output file

SetupOutputFolder(OutputFolderPath)


HTMLOpen(OutputFolderPath+"_SpaVectorTest.html")

HTMLHeading("Spa Vector Test")
HTMLParagraph("At the bottom of the web page is the number of errors.  Search for 'Error:' to find the errors.")

NumErrors=0

#########################################################################
# added centroid here for debugging
NewLayer=SpaVectors.Centroid(TriangleFilePath)
NewLayer.Save(OutputFolderPath+"Centroid.shp")

#########################################################################
# Informational and then save a clone

try:
	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer

	print("Loading")
	TheDataset.Load(CountriesFilePath) # load the contents of the layer

	NumAttributes=TheDataset.GetNumAttributes()

	HTMLHeading("Info")
	HTMLParagraph("Type: "+format(TheDataset.GetType()))
	HTMLParagraph("CRS: "+format(TheDataset.GetCRS()))
	HTMLParagraph("NumFeatures: "+format(TheDataset.GetNumFeatures()))
	HTMLParagraph("Bounds: "+format(TheDataset.GetBounds()))
	HTMLParagraph("NumAttributes: "+format(NumAttributes))

	HTMLTableStart()
	HTMLTableHeader(["Attribute","Type","Width"])

#	RenderDatasetToImage(TheDataset,OutputFolderPath+"Country_AttributesRemoved.png")
#	HTMLImage("Country_AttributesRemoved.png")
	HTMLRenderDataset(TheDataset,OutputFolderPath,"Country_AttributesRemoved.png")

	Index=0
	while (Index<NumAttributes):
		HTMLTableRow([TheDataset.GetAttributeName(Index),TheDataset.GetAttributeType(Index),TheDataset.GetAttributeWidth(Index)])
		#print("Attribute: "+format(TheDataset.GetAttributeName(Index))+", Type: "+format(TheDataset.GetAttributeType(Index))+", Width: "+format(TheDataset.GetAttributeWidth(Index))) 
		Index+=1

	HTMLTableEnd()

	# Save the result
	TheDataset.Save(OutputFolderPath+"CountryClone.shp") 

except Exception  as TheException: HTMLError(TheException)

#########################################################################
# Clean up the attributes

try:
	TheDataset=SpaVectors.SpaDatasetVector() #create a new layer

	TheDataset.Load(CountriesFilePath) # load the contents of the layer

	# Remove some attributes
	TheDataset.DeleteAttribute("ADM0_DIF")
	TheDataset.DeleteAttribute("GEOU_DIF")
	TheDataset.DeleteAttribute("SU_DIF")
	TheDataset.DeleteAttribute("BRK_A3")

	# Save the result
	TheDataset.Save(OutputFolderPath+"Country_AttributesRemoved.shp") 
	print("Saved copy with some attributes deleted")

except Exception  as TheException: HTMLError(TheException)

#########################################################################
# Delete features

HTMLHeading("Features Removed")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset.Load(CountriesFilePath) # load the contents of the layer

# delete the first 10 features
Index=1
while (Index<10):
	TheDataset.DeleteFeature(0)
	Index+=1

RenderDatasetToImage(TheDataset,OutputFolderPath+"Country_FeaturesRemoved.png")
HTMLImage("Country_FeaturesRemoved.png")

# Save the result
TheDataset.Save(OutputFolderPath+"Country_First 10 gone.shp","MultiPolygon") 
print("Saved copy with a feature deleted")

#########################################################################
# Add a new feature

HTMLHeading("Features Added")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset.Load(TriangleFilePath) # load the contents of the layer

# add a square geometry in at 0,0
TheGeometry=shapely.geometry.Polygon([(20,10), (30,10), (30,-10), (20,-10),(20,10)])

TheDataset.AddFeature(TheGeometry)

# Save the result
TheDataset.Save(OutputFolderPath+"Triangle_AddedPoly.shp","MultiPolygon") 
print("Saved copy with a feature added")

HTMLRenderDataset(TheDataset,OutputFolderPath,"Triangle_AddedPoly.png")

#########################################################################
# Create a new shapefile

HTMLHeading("New Shapefile")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer

# add a square geometry in at 0,0
TheGeometry=shapely.geometry.Polygon([(-10,10), (10,10), (10,-10), (-10,-10),(-10,10)])

TheDataset.AddFeature(TheGeometry)

TheDataset.AddAttribute("Name","str",100)
TheDataset.SetAttributeValue("Name",0,"This is a box")

# Save the result
TheDataset.Save(OutputFolderPath+"NewBox.shp") 
print("Saved a new shapefile")

HTMLRenderDataset(TheDataset,OutputFolderPath,"NewBox.png")

#########################################################################
# Remove label ranks <= 2

HTMLHeading("Label Ranks Greater Than 2")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset.Load(CountriesFilePath) # load the contents of the layer

# remove all label ranks of 2 or below
LabelRanks=TheDataset.GetAttributeColumn("LABELRANK")
Selection=numpy.greater(LabelRanks,2)
TheDataset.SubsetBySelection(Selection)

# Save the result
TheDataset.Save(OutputFolderPath+"Country_LabelRanksGreaterThan2.shp") 
print("Saved a new LabelRanksGreaterThan2")

HTMLRenderDataset(TheDataset,OutputFolderPath,"Country_LabelRanksGreaterThan2.png")

#########################################################################
# Attribute value functions

HTMLHeading("Label Ranks Greater Than 2")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer

TheDataset.Load(CountriesFilePath) # load the contents of the layer

# Add a new attribute
TheDataset.AddAttribute("testy","str",254,"hi")

print("Attribute: "+format(TheDataset.GetAttributeValue("ADMIN",0))) # return a single attribute in row 0

TheDataset.SetAttributeValue("testy",0,"test2") # set an attribute in row 0

# sum all of the label rank attribute values in the dataset
NumFeatures=TheDataset.GetNumFeatures()
Index=0
Sum=0
while (Index<NumFeatures):
	Sum+=TheDataset.GetAttributeValue("LABELRANK",Index)
	Index+=1

HTMLParagraph("Sum of label ranks:"+format(Sum))
HTMLParagraph("Mean of label ranks:"+format(Sum/NumFeatures))

# Save the result
TheDataset.Save(OutputFolderPath+"Country_AttributeValues.shp") 

#########################################################################
# Remove all the features except the US and then breaking it into mulitple features

HTMLHeading("Selecting the United States of America and breaking it into individual features for each polygon")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset.Load(CountriesFilePath) # load the contents of the layer

# remove all label ranks of 2 or below
Selection=TheDataset.SelectEqual("ADMIN","United States of America")
TheDataset.SubsetBySelection(Selection)

TheDataset.SplitFeatures()

# Save the result
TheDataset.Save(OutputFolderPath+"Country_US.shp") 

HTMLRenderDataset(TheDataset,OutputFolderPath,"Country_US.png")

#########################################################################
# One layer operations
# Buffer

HTMLHeading("One layer operations")

TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
TheDataset.Load(CountriesFilePath) # load the contents of the layer

HTMLHeading("Buffer",2)

NewLayer=TheDataset.Buffer(30) # 
NewLayer.Save(OutputFolderPath+"Buffer.shp") # save the output

HTMLRenderDataset(TheDataset,OutputFolderPath,"Buffer.png")

# Simplify

HTMLHeading("Simplify",2)

NewLayer=TheDataset.Simplify(1) # 
NewLayer.Save(OutputFolderPath+"Simplify.shp") # save the output

HTMLRenderDataset(TheDataset,OutputFolderPath,"Simplify.png")

# Centroid

HTMLHeading("Centroid",2)

NewLayer=TheDataset.Centroid() # 
NewLayer.Save(OutputFolderPath+"Centroid.shp") # save the output

HTMLRenderDataset(TheDataset,OutputFolderPath,"Centroid.png")

# Union with self

HTMLHeading("Union with self",2)

NewLayer=TheDataset.Union() # 
NewLayer.Save(OutputFolderPath+"UnionWithSelf.shp") # save the output

HTMLRenderDataset(TheDataset,OutputFolderPath,"UnionWithSelf.png")

#########################################################################
# Overlay operations

HTMLHeading("Overlay operations")

#Create the bounding polygon
Top=90
Bottom=0
Left=-180
Right=0

HTMLHeading("Intersection",2)

BoundingPoly=shapely.geometry.Polygon([(Left,Top), (Right,Top), (Right,Bottom), (Left,Bottom),(Left,Top)])

NewLayer=TheDataset.Intersection(BoundingPoly) # perform an intersection on a geometry to get the new layer
NewLayer.Save(OutputFolderPath+"Intersection.shp") # save the output

HTMLRenderDataset(NewLayer,OutputFolderPath,"Intersection.png")

HTMLHeading("Union",2)

NewLayer=TheDataset.Union(BoundingPoly) # perform an intersection on a geometry to get the new layer
NewLayer.Save(OutputFolderPath+"Union.shp") # save the output

HTMLRenderDataset(NewLayer,OutputFolderPath,"Union.png")

HTMLHeading("Difference",2)

NewLayer=TheDataset.Difference(BoundingPoly) # 
NewLayer.Save(OutputFolderPath+"Difference.shp") # save the output

HTMLRenderDataset(NewLayer,OutputFolderPath,"Difference.png")

############################################################################
# projection tests
############################################################################

# Moved to referencing
#HTMLHeading("Projection")

#Parameters={
	#"datum":"WGS84",
	#"proj":"aea",
	#"lon_0":0,
	#"lat_1":60,
	#"lat_2":40
#}
#TheDataset=SpaVectors.SpaDatasetVector() #create a new layer
#TheDataset.Load(CountriesFilePath) # load the contents of the layer

#NewDataset=SpaDensify.Densify(TheDataset,1) # 

############################################################################
# One-line operations
############################################################################
############################################################################
# Basic vector operations
############################################################################

HTMLHeading("One line operations")

HTMLHeading("Buffered",2)

BufferedLayer=SpaVectors.Buffer(CountriesFilePath,10)
BufferedLayer.Save(OutputFolderPath+"Buffered.shp")

HTMLRenderDataset(BufferedLayer,OutputFolderPath,"Buffered.png")

HTMLHeading("Centroid",2)

NewLayer=SpaVectors.Centroid(CountriesFilePath)
NewLayer.Save(OutputFolderPath+"Centroid.shp")

HTMLRenderDataset(NewLayer,OutputFolderPath,"Centroid.png")

HTMLHeading("ConvexHull",2)

NewLayer=SpaVectors.ConvexHull(CountriesFilePath)
NewLayer.Save(OutputFolderPath+"ConvexHull.shp")

HTMLRenderDataset(NewLayer,OutputFolderPath,"ConvexHull.png")

HTMLHeading("Simplify",2)

NewLayer=SpaVectors.Simplify(CountriesFilePath,10)
NewLayer.Save(OutputFolderPath+"Simplify.shp")

HTMLRenderDataset(NewLayer,OutputFolderPath,"Simplify.png")

HTMLHeading("UnionWithSelf",2)

NewLayer=SpaVectors.Union(CountriesFilePath)
NewLayer.Save(OutputFolderPath+"UnionWithSelf.shp")

HTMLRenderDataset(NewLayer,OutputFolderPath,"UnionWithSelf.png")

############################################################################
# Overlay operations with a geometry
#############################################################################

# Create the bounding polygon
Top=45  
Bottom=20
Left=-125
Right=-40

BoundingPoly=shapely.geometry.Polygon([(Left,Top), (Right,Top), (Right,Bottom), (Left,Bottom),(Left,Top)])

# Crop a shapefile with a polygon 
NewLayer=SpaVectors.Intersection(CountriesFilePath,BoundingPoly) # perform an intersection on a geometry to get the new layer
NewLayer.Save(OutputFolderPath+"Intersection.shp")

# Union the shapefile with the polygon
NewLayer=SpaVectors.Union(CountriesFilePath,BoundingPoly) # perform a union on a geometry to get the new layer
NewLayer.Save(OutputFolderPath+"Union.shp") # save the output

# Find the difference between the shapefile and the polygon
NewLayer=SpaVectors.Difference(CountriesFilePath,BoundingPoly) # 
NewLayer.Save(OutputFolderPath+"Difference.shp") # save the output

print("done")

HTMLClose()

# Open the browser to show the file
Thing=os.path.abspath("../Temp/SpaVectorTest")

WebPagePath="file:///"+Thing+"/_SpaVectorTest.html"

webbrowser.open(WebPagePath)
