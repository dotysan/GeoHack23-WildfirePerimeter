############################################################################
# Code to make it easy to plot a variety of spatial data with MatPlotLib.
# Note that this is not fast and SpaView should be used for faster rendering of spatial data to
# a window
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

import matplotlib
from matplotlib import pyplot
from SpaPy import SpaBase

############################################################################
# Globals
############################################################################

class SpaPlot:
	""" 
	Class to plot spatial data in a matplotlib
	"""
	def __init__(self):
		# below are the properties that make up a shapefile using Fiona for reading and writing from and to shapefiles
		self.TheGeometries=[]
		self.TheAttributes=[]

	############################################################################
	def PlotCoords(self,TheCoords):
		"""
		Plots (x,y) coordinates 
		
		Parameters:
			TheCoords: 
				coordinate data 
		Returns:
			none
		"""
		Xs,Ys=SpaBase.GetXYsFromCoords(TheCoords)
		
		if (len(Xs)>2):
			matplotlib.pyplot.plot(Xs,Ys, color='#000000', alpha=0.7,linewidth=1, solid_capstyle='round', zorder=2)

	def PlotPolygon(self,ThePolygon):
		"""
		Plots polygon data
		
		Parameters:
			ThePolygon: 
				Polygon geometry
		Returns:
			none
		"""		
		Coords=ThePolygon.exterior.coords
		self.PlotCoords(Coords)
		
	def PlotGeometry(self,TheGeometry):
		"""
		Plots geometry data
		
		Parameters:
			TheGeometry: 
				object geometry
		Returns:
			none
		"""				
		if (TheGeometry!=None):
			# take the appropriate action based on the type of geometry
			TheType=TheGeometry.geom_type
			
			if (TheType=="Polygon"):
				self.PlotPolygon(TheGeometry)
			#if (TheType=="Point"):
				#pyplot.scatter(CoordXs,CoordYs, color='#6699cc', marker='^')
				
			elif (TheType=="MultiPolygon"):
				for ThePolygon in TheGeometry.geoms:
					self.PlotPolygon(ThePolygon)
					
			elif (TheType=="GeometryCollection"): # collections are typically empty for shapefiles
				for TheSubGeometry in TheGeometry.geoms:
					self.PlotGeometry(TheSubGeometry)
					
			else:
				print("Unsupported Type: "+TheType)
		
	def Plot(self,TheDataset):
		"""
		Plot the specified dataset into the chart
		
		Parameters:
			TheDataset: 
				Insert dataset to be plotted
		Returns: None
		"""
		NumFeatures=TheDataset.GetNumFeatures()
		Index=0
		while (Index<NumFeatures):
			TheGeometry=TheDataset.GetGeometry(Index)
			
			self.PlotGeometry(TheGeometry)
			
			Index+=1

	def Show(self):
		"""
		Make the chart visible
		
		Parameters:
			none
		Returns:
			none
		"""
		matplotlib.pyplot.show()		

def PlotRasterHistogram(TheRasterDataset,Title=None):
	"""
	Example showing how to plot the histgram for a raster
	
	Parameters:
		TheRasterDataset
	"""
	import matplotlib.pyplot as plt
	
	# Get the histogram and bin edges from the raster dataset
	Histogram=TheRasterDataset.GetHistogram()
	#print("HistogramAndBinEdges="+format(HistogramAndBinEdges))
	
	# Setup the arrays for displaying the histogram
	BarCenters = []
	Labels=[]
	Min,Max=TheRasterDataset.GetMinMax()
	
	NumBins=len(Histogram)
	BinWidth=(Max-Min)/NumBins
	
	Index=0
	while (Index<NumBins):
		BarCenter=Min+Index*BinWidth+BinWidth/2
		Labels.append(format(BarCenter,"6.0f"))
		
		BarCenters.append(Index)
		Index+=1
	
	# Setup and show the plot
	plt.bar(BarCenters,Histogram,tick_label=Labels, align='center')
	plt.xlabel("Bins")
	plt.ylabel("Number of Pixels")
	
	if (Title==None): Title="Raster Histogram"
	
	plt.title(Title)
	
	plt.show()	