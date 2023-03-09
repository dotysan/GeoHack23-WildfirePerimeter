############################################################################
# Adds coordinates to geometries as needed
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
import math

import shapely

#import SpaPy
from SpaPy import SpaVectors
from SpaPy import SpaBase

############################################################################
# Globals
############################################################################

class SpaDensify(SpaBase.SpaTransform):
	""" 
	Class to manage increasing the density of points in vector data.
	
	Inherites from SpaBase.SpaTranform.
	"""

	def DensifyCoords(self,TheCoords,Amount,Closed=True):
		"""
		Increases density of points in
		
		Parameters:
			Amount: 
			TheCoords: 
		Returns:
			A SpaDatasetVector object
		"""
		NumPoints=len(TheCoords)
		if (Closed==False): NumPoints-=1
		
		NewCoords=[]

		# Get the first coordinate
		PointIndex=0
		X1=TheCoords[PointIndex][0]
		Y1=TheCoords[PointIndex][1]
		NewCoords.append((X1,Y1))
		
		# Add the other coordinates while adding additional coordinates along the way if needed
		PointIndex=1
		while (PointIndex<=NumPoints):

			if (PointIndex<NumPoints) or (Closed==False): # either in the middle of a polygon or just have one line segment
				X2=TheCoords[PointIndex][0]
				Y2=TheCoords[PointIndex][1]
			else: # Join a the last coordinate in a polygon back to its start
				X2=TheCoords[0][0]
				Y2=TheCoords[0][1]

			###########################################
			# densify one line segement
			Length=SpaBase.GetSegmentLength(X1,Y1,X2,Y2) # find the length of the segment

			if (Length>0):
				DX=(X2-X1)/Length*Amount # find the x and y distances along the line that the new points should be spaced
				DY=(Y2-Y1)/Length*Amount

				NewX=X1+DX # create the first new coordinate
				NewY=Y1+DY

				while (Length>Amount): # keep adding coordinates until the distance to the second point is less than the desired amount
					NewCoords.append((NewX,NewY)) # add the new coordinate

					NewX+=DX # find the next coordinate along the line segement
					NewY+=DY

					Length-=Amount # remove the distance between the previous coordinate and the new coordinate

				# add the second coordinate 
				NewCoords.append((X2,Y2))

				# make the second coordinate the first coordinate for the next time through
				X1=X2
				Y1=Y2

			PointIndex+=1

		return(NewCoords)

	def DensifyPolygon(self,ThePolygon,Amount):
		"""
		Parameters:
			Amount: 
			ThePolygon: 
		Returns:
			A SpaDatasetVector dataset object 
		"""		
		TheCoords=ThePolygon.exterior.coords
		NewCoords=self.DensifyCoords(TheCoords,Amount)
		return(shapely.geometry.Polygon(NewCoords))

	def DensifyGeometry(self,TheGeometry,Amount):
		""" Render the specified geomery into the specified view.  This is called by Render() """

		NewGeometry=None

		# take the appropriate action based on the type of geometry
		TheType=TheGeometry.geom_type

		if (TheType=="Polygon"):
			NewGeometry=self.DensifyPolygon(TheGeometry,Amount)

		elif (TheType=="MultiPolygon"):
			NumPolys=len(TheGeometry.geoms)
			PolyIndex=0
			NewPolys=[]
			while (PolyIndex<NumPolys):
				##print("PolyIndex="+format(PolyIndex))
				ThePolygon=TheGeometry.geoms[PolyIndex]
				NewPolys.append(self.DensifyPolygon(ThePolygon,Amount))
				PolyIndex+=1
			NewGeometry=shapely.geometry.MultiPolygon(NewPolys)

		elif (TheType=="GeometryCollection"): # collections are typically empty for shapefiles
			TheGeometries=TheGeometry.geoms
			NumGeometries=len(TheGeometries)
			GeometryIndex=0
			while (GeometryIndex<NumGeometries):
				#self.DensifyGeometry(TheView,TheGeometries[GeometryIndex])
				GeometryIndex+=1

		else:
			print("Unsupported Type: "+TheType)

		return(NewGeometry)

	def Densify(self,TheDataset,Amount):
		NewDataset=SpaVectors.SpaDatasetVector()
		NewDataset.CopyMetadata(TheDataset)
		NewDataset.SetType(None)
		
		NumFeatures=TheDataset.GetNumFeatures()
		FeatureIndex=0
		while (FeatureIndex<NumFeatures): # interate through all the features finding the intersection with the geometry
			TheGeometry=TheDataset.TheGeometries[FeatureIndex]

			TheGeometry=self.DensifyGeometry(TheGeometry,Amount)

			NewDataset.AddFeature(TheGeometry,TheDataset.TheAttributes[FeatureIndex])

			FeatureIndex+=1
		return(NewDataset)
######################################################################################################
# Single line transforms for one layer
######################################################################################################

def Densify(TheDataset,MaxDistance=1):
	"""
	Add coordinates to the data in the input so that there are not line segments longer than MaxDistance

	Parameters:
		MaxDistance: 
			Maximum distance for line segments between coordinates.

	Returns:
		New dataset 
	"""
	TheTransform=SpaDensify()
	
	if (isinstance(TheDataset,SpaVectors.SpaDatasetVector)):
		Result=TheTransform.Densify(TheDataset,MaxDistance)
	else:
		Result=TheTransform.DensifyGeometry(TheDataset,MaxDistance)
	return(Result)
