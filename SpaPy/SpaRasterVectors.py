###############################################################################################
# Seems like this should be part of SpaRasters
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
import os
import numbers
import math

# Open source spatial libraries
from osgeo import gdal
import numpy
import scipy
from osgeo import ogr
import scipy.ndimage
from osgeo import osr
import shapely

# Spa Libraries
from SpaPy import SpaBase
from SpaPy import SpaVectors

############################################################################################

def Polygonize(Input1):
	""" 
	Converts a raster to a polygon feature set.  Each contiguous area of the raster
	(i.e. ajoining pixels that have the same value) are grouped as one polygon.  The
	only attribute is "band1" as this only works for one band.

	Parameters:
		An SpaDatasetRaster object OR a string representing the path to the raster file
	Returns:
		A RasterDataset
	"""	
	Input1=SpaBase.GetInput(Input1)
	
	# get spatial reference info 
	srs = osr.SpatialReference()
	TheCRS=Input1.GetCRS()
	srs.ImportFromWkt(TheCRS.ExportToWkt())

	# Create a temporary vector data set in memory
	TheDriver = ogr.GetDriverByName("Memory")

	DestinDataSource = TheDriver.CreateDataSource('out')	
	DestinLayer = DestinDataSource.CreateLayer('', srs = srs ) #

	# add the attribute for the pixel values
	AttributeType=ogr.OFTInteger
	GDALDataType=Input1.GetType()
	
	if ((GDALDataType==gdal.GDT_Float32) or (GDALDataType==gdal.GDT_Float64)): 
		AttributeType=ogr.OFSTFloat32

	FieldDefinition = ogr.FieldDefn("band1", AttributeType)
	DestinLayer.CreateField(FieldDefinition)
	AttributeIndex = 0

	# create polygons from the first raster band
	
	TheInputGDALDataset=Input1.GetGDALDataset()
	FirstBand=TheInputGDALDataset.GetRasterBand(1)

	#FirstBand=Input1.GetBand(0)
	
	gdal.Polygonize(FirstBand, None, DestinLayer, AttributeIndex, [], callback=None)	

	# create a new dataset in SpaVectors
	OutDataset = SpaVectors.SpaDatasetVector()

	OutDataset.AddAttribute("Name","int",1)
#	OutDataset.AttributeDefs["band1"]='int:1'

	for feature in DestinLayer:
		# get the spatial reference and convert to WKT and then convert to a ShapelyGeometry
		#ShapelyGeometry=feature.GetGeometryRef().Clone()

		Geometry=feature.GetGeometryRef().ExportToWkt() # This is slow but currently required.  In the future we might support both types and then convert as needed jjg
		ShapelyGeometry=shapely.wkt.loads(Geometry)

		# setup the attribute array and add the feature to the output dataset
		Value=feature.GetField(0)
		if (isinstance(Value,list)): Value=Value[0]
		Attributes=[Value]

		OutDataset.AddFeature(ShapelyGeometry,Attributes)

	return(OutDataset)
