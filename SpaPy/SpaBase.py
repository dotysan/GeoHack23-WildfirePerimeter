############################################################################
# Base class for transforms
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
import types

import math

############################################################################
#Global variables
############################################################################

SpaTempFolder="../Temp/"

############################################################################
# Basic Geometry utilities
############################################################################

def GetXYsFromCoords(TheCoords):
	""" 
	Convert shapely coordinates [(x1,y1),(x2,y2)] to arrays of xs and ys 
	
	Parameters:
		TheCoords:
			Input coordinated here formatted as followed: [(x1,y1),(x2,y2)]
	Returns:
		Array of Xs and Ys 
	"""
	NumPoints=len(TheCoords)
	
	Xs=[]
	Ys=[]

	PointIndex=0
	while (PointIndex<NumPoints):
		Lon2=TheCoords[PointIndex][0]
		Lat2=TheCoords[PointIndex][1]

		Xs.append(Lon2)
		Ys.append(Lat2)

		PointIndex+=1
	return(Xs,Ys)

def GetSegmentLength(X1,Y1,X2,Y2):
	"""
	Compute the length of the line segment that is between the two specified coordinates
	
	Parameters:
		X1: x-value of first coordinate of segment
		Y1: y-value of first coordinate of segment
		X2: x-value of second coordinate of segment
		Y2: y-value of second coordinate of segment
	Returns:
	        Length of line segment
	"""
	DX=X2-X1
	DY=Y2-Y1
	Length=math.sqrt(DX*DX+DY*DY)
	return(Length)

def SetTempFolderPath(NewTempFolderPath):
	SpaTempFolder=NewTempFolderPath

def GetTempFolderPath():
	return(SpaTempFolder)
	


############################################################################
# Base Class definitions
############################################################################

class SpaBase:
	""" 
	Base class for all SpaPy classes that have settings
	"""
	def __init__(self):
		i=0 # something so we don't get an error

		self.Settings={}
	
	def SetSettings(self,Class,Settings):
		# this function is still in development
		self.Settings[Class]=Settings
	
	def GetSettings(self,Class):
		# this function is still in development		
		return(self.Settings[Class])
	
class SpaTransform(SpaBase):
	""" 
	Base class for all transforms
	"""
	def __init__(self):
		super().__init__()
		
	def Transform():
		"""
		@Override
		"""
		print("*** Must be overriden ****")
		

############################################################################
# Utility functions for subclasses
############################################################################

# These modules have to be included after the code above because SpaRasters
# and SpaVectors use the code above in defining their classes
from SpaPy import SpaRasters
from SpaPy import SpaVectors

def GetInput(InputFile):
	""" 
	Return an object that can be used for transforming.  This is typically
	a layer object
	@Protected
	
	Parameters:
		InputFile: File to be used in transform (vector or raster file)
	Returns:
		a SpaDatasetRaster or SpaDatasetVector object
	"""
	#print(type(InputFile))
	if (isinstance(InputFile, str)):
		Extension = os.path.splitext(InputFile)[1]		
		Extension=Extension.lower()
		if (Extension==".shp"):
			FilePath=InputFile
			InputFile=SpaVectors.SpaDatasetVector()
			InputFile.Load(FilePath)
		else:
			FilePath=InputFile
			InputFile=SpaRasters.SpaDatasetRaster()
			InputFile.Load(FilePath)
			
	return(InputFile)

