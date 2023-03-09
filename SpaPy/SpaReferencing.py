##############################################################################################################################
# Module with definitions for managing projections.
# 
# External Classes:
# - SpaProj - projector based on the proj4 engine
#
# The easiest approach is to call the global function: Transform(Input1,CRS1,CRS2)
# 1. Input1 can be a list of coordinate values, a geometry, or a dataset. For now, rasters are supported through TransformRaster(...)
# 2. CRS1 is the new CRS unless CRS2 is specified and then CRS1 is the original CRS.  If CRS2 is not specied, the current CRS in the Input will be used 
# 3. CRS2 is the new CRS if it is specified.
#
# CRSes can be a wide range of values defined by pyproj4 at: https://pyproj4.github.io/pyproj/stable/api/crs/crs.html
# The simplest approach is just to use an EPSG Number which are avialable at: http://gsp.humboldt.edu/websites/EPSG/CRSs.html#
#
# To use SpaProj:
# 1. Call Transform for an object that has an internal CRS: 
#    NewDataset=Transform(OriginalDataset, NewCRS)
# 2. Call Transform for a geometry or another object that does not have an internal CRS:
#    NewDataset=Transform(OriginalDataset, OriginalCRS, NewCRS)
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
import math
import os
import sys

# Open source spatial libraries
import pyproj
import shapely
import shapely.geometry
from osgeo import gdal
from osgeo import osr
from pyproj import Transformer

# SpaPy libraries
from SpaPy import SpaVectors 
from SpaPy import SpaBase
from SpaPy import SpaRasters

################################################################
# Base class for projectors
################################################################
class SpaProjector(SpaBase.SpaBase):
	""" 
	Abstract class to define projectors
	"""
	def __init__(self):
		super().__init__()
		# below are the properties that make up a shapefile using Fiona for reading and writing from and to shapefiles
		self.TheProjection=None

	def ProjectFromGeographic(self,TheObject):
		""" 
		Abstract function to be overriden by subclasses.  Takes TheObject and converts
		its coordinates from Goegraphic to the specified spatial reference.

		Parameters:
			TheObject:
				raster or vector object to be projected
		Return:
			none
		"""

		Result=None

		return(Result)

############################################################################
# Public class to project based on the Proj4 library
############################################################################

class SpaProj(SpaProjector):
	""" 
	Class to project data from one CRS (FromCRS) to another CRS (ToCRS).
	"""
	def __init__(self):
		super().__init__()
		# below are the properties that make up a shapefile using Fiona for reading and writing from and to shapefiles
		self.Reset()

		self.FromCRS=None
		self.ToCRS=None

		self.ErrorMessages=""
		self.WarningMessages=""
		self.InfoMessages=""
	############################################################################
	# Private Functions
	############################################################################
	def AddToErrorMessages(self,TheMessage):
		self.ErrorMessages=self.ErrorMessages+", "+TheMessage

	def AddToWarningMessages(self,TheMessage):
		self.WarningMessages=self.WarningMessages+", "+TheMessage

	def AddToInfoMessages(self,TheMessage):
		self.InfoMessages=self.InfoMessages+", "+TheMessage

	############################################################################
	# SpaBase Functions
	############################################################################
	def SetSettings(self,Class,Settings):
		super().SetSettings(Class,Settings)
		if (Class==SpaProj):
			self.FromCRS=pyproj.CRS.from_user_input(4326 ) # WGS84 Geographic
			self.ToCRS=pyproj.crs.CRS(Settings["Parameters"])
		
		self.Reset()

	def SetCRSes(self,FromCRS,ToCRS):
		if (isinstance(FromCRS,osr.SpatialReference)):
			self.FromCRS=FromCRS.ExportToProj4()
			#self.FromCRS=pyproj.CRS.from_user_input(FromCRS)
		else:
			self.FromCRS=pyproj.CRS.from_user_input(FromCRS)
			
		if (isinstance(ToCRS,osr.SpatialReference)):
			self.ToCRS=ToCRS.ExportToProj4()
		else:
			self.ToCRS=pyproj.CRS.from_user_input(ToCRS)


	############################################################################
	# SpaProjector Functions
	############################################################################
	def Reset(self):
		"""
		Resets the current projection

		Parameters:
			none
		Returns:
			none
		"""
		self.TheTransform=None
		self.InserseTransform=None
		
	############################################################################
	# SpaProj Protected Functions
	############################################################################
	def Initialize(self):
		if (self.TheTransform==None):
			if (self.FromCRS!=None) and (self.ToCRS!=None):
				self.TheTransform=Transformer.from_crs(self.FromCRS, self.ToCRS, always_xy=True)
	##############################################################################
	def TransformCoordinate(self,X,Y):
		"""
		Perform a transform on a coordinate.
		"""

		TheCoordinate=None
		
		self.Initialize()

		if (self.TheTransform!=None):
			TheCoordinate=self.TheTransform.transform(X,Y)

		return(TheCoordinate)

	##############################################################################
	def InverseTransformCoordinate(self,X,Y):
		"""
		Perform an inverse transform on a coordinate (i.e. transform from the ToCRS to the FromCRS).
		"""
		if (self.InserseTransform==None):
			if (self.FromCRS!=None) and (self.ToCRS!=None):
				self.InserseTransform=Transformer.from_crs(self.ToCRS,self.FromCRS,  always_xy=True)

		if (self.InserseTransform!=None):
			TheCoordinate=self.InserseTransform.transform(X,Y)

		return(TheCoordinate)

	##############################################################################
	def Transform(self,TheObject):
		""" 
		Handles projecting a wide variety of types of data

		This function will be called recursively for datasets and shapely geometries until coordiantes are
		reached and then ProjectCoordinateFromGeographic() will be called.  Shapely is very picky about
		the contents of geometries so anything that is not considered valid is not added to the result.

		Parameters:
			TheObject:
				Vector object to be projected
		Return:
			none
		""" 

		Result=None

		if (isinstance(TheObject,SpaVectors.SpaDatasetVector)): # have a layer, make a duplicate and then project all the contents of the layer
			NewLayer=SpaVectors.SpaDatasetVector()
			NewLayer.CopyMetadata(TheObject)
			NewLayer.SetType(None)

			NumFeatures=TheObject.GetNumFeatures()
			FeatureIndex=0
			while (FeatureIndex<NumFeatures): # interate through all the features finding the intersection with the geometry
				TheGeometry=TheObject.TheGeometries[FeatureIndex]

				TheGeometry=self.Transform(TheGeometry)

				if (TheGeometry!=None):
					NewLayer.AddFeature(TheGeometry,TheObject.TheAttributes[FeatureIndex])

				FeatureIndex+=1

			#TheCRS=self.GetProjParametersFromSettings()

			NewLayer.SetCRS(self.ToCRS)

			Result=NewLayer

		elif (isinstance(TheObject,shapely.geometry.MultiPolygon)): # have a polygon, 
			ThePolygons=[]
			for ThePolygon in TheObject.geoms:
				NewPolygon=self.Transform(ThePolygon) # deal with interior polys later
				if (NewPolygon!=None):
					ThePolygons.append(NewPolygon)
			if (len(ThePolygons)>0):
				Result=shapely.geometry.MultiPolygon(ThePolygons)

		elif (isinstance(TheObject,shapely.geometry.MultiLineString)): # have an array of line strings , 
			TheLineStrings=[]
			for TheLineString in TheObject.geoms:
				NewLineString=self.Transform(TheLineString) # deal with interior polys later
				if (NewLineString!=None):
					TheLineStrings.append(NewLineString)
			if (len(TheLineStrings)>0):
				Result=shapely.geometry.MultiLineString(TheLineStrings)

		elif (isinstance(TheObject,shapely.geometry.Polygon)): # have a polygon, 
			TheCoordinates=self.Transform(TheObject.exterior.coords) # deal with interior polys later
			if (TheCoordinates!=None):
				if (len(TheCoordinates)>=3): # polygon must have at least 3 coordinates
					Result=shapely.geometry.Polygon(TheCoordinates)

		elif (isinstance(TheObject,shapely.geometry.LineString)): # have a polygon, 
			TheCoordinates=self.Transform(TheObject.coords) # deal with interior polys later
			if (len(TheCoordinates)>=2): # polygon must have at least 3 coordinates
				Result=shapely.geometry.LineString(TheCoordinates)

		elif (isinstance(TheObject,shapely.geometry.Point)): # have a polygon, 
			TheCoordinates=self.Transform(TheObject.coords) # deal with interior polys later
			Result=shapely.geometry.Point(TheCoordinates)

		elif (isinstance(TheObject,shapely.coords.CoordinateSequence)): # have an shapely coordinate sequence
			Result=[]
			for TheEntry in TheObject:
				Coordinate2=self.Transform(TheEntry)
				if (Coordinate2!=None):
					Easting2=Coordinate2[0]
					Northing2=Coordinate2[1]

					if ((math.isnan(Easting2)==False) and (math.isnan(Northing2)==False) and (Easting2!=1e+30) and (Northing2!=1e+30)
						and (math.isfinite(Northing2)) and (math.isfinite(Easting2))):
						Result.append((Easting2,Northing2))

		elif (isinstance(TheObject,SpaRasters.SpaDatasetRaster)): # have a raster
			raise("Sorry, you'll need to call ProjectRaster()")
			# 
			#raise Exception("Sorry, SpPy does not yet support projecting raster datasets")
		else: # should be two coordinate values		
			if (TheObject!=None):# and (self.TheProjection!=None):

				Coordinate=TheObject

				if (len(Coordinate)>0):
					X=Coordinate[0]

					if (isinstance(X, (list, tuple, set))): # have an array of coordinate pairs
						Result=[]
						for TheCoordinate in Coordinate:
							TheCoordinate=self.TransformCoordinate(TheCoordinate[0],TheCoordinate[1])
							Result.append(TheCoordinate)

					else: # Must be a single coordinate
						Y=Coordinate[1]

						Result=self.TransformCoordinate(X,Y)


		return(Result)

	def TransformRaster(self,TheObject,OutputFilePath): # Create the destination SRS
		"""
		Projects a raster dataset

		Parameters:
			TheRaster:
				Raster dataset to be projected
			OutputFilePath: 
				File path to location where output will be stored
		Returns:
			Projected raster dataset
		"""
		#Settings=self.GetSettings(SpaProj)
		self.Initialize()

		DesitnationSRS=self.ToCRS.to_proj4()

		# Create the new dataset
		NewDataset=SpaRasters.SpaDatasetRaster()
		NewDataset.CopyPropertiesButNotData(TheObject)
		NewDataset.AllocateArray()
		NewDataset.Save(OutputFilePath) # this is ugly but it is the only way we could figure out to create a GDALDataset
		#NewDataset.Load(OutputFilePath)

		InputGDALDataset = TheObject.GetGDALDataset()
		
		# warp the dataset (jjg - put the new dataset into a new SpaRaster object)
		TempGDALDataset = gdal.Warp(OutputFilePath,InputGDALDataset,dstSRS=DesitnationSRS)

		NewDataset.Load(OutputFilePath)

		return(NewDataset)
################################################################
# Public Utility functions
################################################################

def Transform(Input1,CRS1,CRS2=None):
	"""
	Projects just about anything to a new spatial reference.

	Parameters:
		Input1: The spatial data to be transformed.  This can be one of the following:
		- SpaVectors.SpaDatasetVector object
		- shapely.geometry.MultiPolygon object
		- shapely.geometry.MultiLineString object
		- shapely.geometry.Polygon object
		- shapely.geometry.LineString object
		- shapely.geometry.CoordinateSequence object
		- Array with an X and Y coordinate value (e.g. [123.456,65.432])
		
		CRS1: The source CRS if CRS2 is provided, else the destination CRS
		CRS2: The destination CRS if provided
	Returns:
	        Projected raster or vector dataset object
	"""
	Input1=SpaBase.GetInput(Input1)

	TheProjector=SpaProj() # Create the projector object

	# setup the Original and New CRSes
	if (CRS2==None): # first CRS is the new CRS
		CRS2=CRS1
		CRS1=Input1.GetCRS()
		
	TheProjector.SetCRSes(CRS1,CRS2)

	# Transform the object
	NewLayer=TheProjector.Transform(Input1)

	return(NewLayer)

def TransformRaster(Input1,OutputFilePath,CRS1,CRS2=None):
	"""
	Project a raster to a new CRS.
	Currently, it is assume the inputs are in geographic coordinates and the datum does not change.

	Parameters:
		Input1: raster or vector dataset object to be projected
		Parameters: input dataset parameters
	Returns:
	        Projected raster dataset object
	"""
	Input1=SpaBase.GetInput(Input1)
	
	TheProjector=SpaProj() # Create the projector object

	# setup the Original and New CRSes
	if (CRS2==None): # first CRS is the new CRS
		CRS2=CRS1
		CRS1=Input1.GetCRS()		
	TheProjector.SetCRSes(CRS1,CRS2)

	# Transform the object

	NewLayer=TheProjector.TransformRaster(Input1,OutputFilePath)

	return(NewLayer)
