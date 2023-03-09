############################################################################
# Handles rendering SpaLayers and Geometries to Python Image Library (PIL)
# based raster images.  This class has functions that allow rendering in
# either pixel or reference units.
#
# This class is under construction.
#
# Note: the name of this file, SpaView, does not really match its function
# at this time because the class renders to an image that can be displayed
# to the screen rather than to the screen directly.  This class can also be
# used to render images that are saved to a file such as PNG.
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
import json
import random
import colorsys
import math
import tkinter
import PIL
import numpy
from PIL import Image, ImageDraw,ImageTk 

# SpaPy libraries
#import SpaPy
from SpaPy import SpaRasters
from SpaPy import SpaVectors
from SpaPy import SpaBase

############################################################################
# Globals
############################################################################

class SpaView():
	""" 
	Class to display geospatial data into a Canvas widget object
	This class uses a Python Image Library (PIL) image to render the
	data as this is much faster than the standard Canvas objects
	"""
	def __init__(self, WidthInPixels,HeightInPixels):
		"""
		Called on creation of the object to intiailize it.
	
		Parameters:
			WidthInPixels: Hozitonal dimension of the view in pixels
			HeightInPixels: Vertical dimension of the view in pixels
	
		Return:
			A SpaDatasetRaster object depicting aspect	
		"""	
		self.WidthInPixels = WidthInPixels
		self.HeightInPixels = HeightInPixels

		# these values determine the location and zoom factor for the view
		self.EastingMin=None
		self.NorthingMin=None
		self.Factor=1 # scaling factor (Ref/Pixels)

		# current style settings for rendering
		self.FillColor=(255,255,255)
		self.OutlineColor=(0,0,0)
		self.BackgroundColor=(255,255,255)
		self.LineWidth=1
		
		self.Reset()

	############################################################################
	# Public functions
	############################################################################
	def GetDimensions(self):
		return((self.WidthInPixels,self.HeightInPixels))
	
	def Resize(self, WidthInPixels,HeightInPixels):
		"""
		Call when the size of the view changes.
	
		Parameters:
			WidthInPixels: Hozitonal dimension of the view in pixels
			HeightInPixels: Vertical dimension of the view in pixels
		"""	
		self.WidthInPixels = WidthInPixels
		self.HeightInPixels = HeightInPixels
		self.Reset()

	def Reset(self):
		"""
		Called to reset drawing.  This reinitializeds the PIL image which effecitvely clears the view.
		"""	
		
		self.TheImage = PIL.Image.new('RGBA', (self.WidthInPixels,self.HeightInPixels),self.BackgroundColor) #jjg, has to be RGBA or python just quits, maybe someone is accessing the image arrays as 4 band?
		self.TheImageDrawing = PIL.ImageDraw.Draw(self.TheImage)

	def SetBounds(self,EastingMin,EastingMax=None,NorthingMin=None,NorthingMax=None): # jjg - these do not match standard XMin,YMin,XMax,YMax
		"""
		Called to set the reference dimensions of the view.
	
		Parameters:
			EastingMin: left edge of the view in refenerence coordinates.  The first parameter can also contain an array of the format [EastingMin, NorthingMin,EastingMax,NorthingMax]
			EastingMax: right edge of the view in refenerence coordinates
			NorthingMin: top of the view in refenerence coordinates
			NorthingMax: bottom of the view in refenerence coordinates
		"""	
		if (isinstance(EastingMin, (list, tuple))):
			TheBounds=EastingMin
			EastingMin=TheBounds[0]
			NorthingMin=TheBounds[1]
			EastingMax=TheBounds[2]
			NorthingMax=TheBounds[3]
		
		if ((EastingMin==None) or (EastingMax==None) or (NorthingMin==None) or (NorthingMax==None)):
			raise BaseException("Sorry, the bounds must have 4 valid values")
		else:
			EastingRange=EastingMax-EastingMin
			NorthingRange=NorthingMax-NorthingMin

			CenterRefX=EastingMin+EastingRange/2
			CenterRefY=NorthingMin+NorthingRange/2

			self.Factor=EastingRange/self.WidthInPixels

			if (NorthingRange/self.HeightInPixels>self.Factor): 
				self.Factor=NorthingRange/self.HeightInPixels
			
			self.EastingMin=CenterRefX-self.Factor*self.WidthInPixels/2
			self.NorthingMin=CenterRefY-self.Factor*self.HeightInPixels/2

		#self.Factor=EastingRange/500

	def GetBounds(self):
		EastingMax=self.EastingMin+self.Factor*self.WidthInPixels
		NorthingMax=self.NorthingMin+self.Factor*self.HeightInPixels
		
		Bounds=[self.EastingMin,self.NorthingMin,EastingMax,NorthingMax]
		
		return(Bounds)
	def Zoom(self,Multiplier):
		# Find the center of the viewing area
		CenterRefX=self.EastingMin+self.Factor*self.WidthInPixels/2
		CenterRefY=self.NorthingMin+self.Factor*self.HeightInPixels/2

		# Change the zoom factor
		self.Factor*=Multiplier

		# compute the new min coordinate value using the new zoom factor
		self.EastingMin=CenterRefX-self.Factor*self.WidthInPixels/2
		self.NorthingMin=CenterRefY-self.Factor*self.HeightInPixels/2

	def Move(self,DeltaX,DeltaY):
		"""
		Function to move the viewing location
		"""
		DeltaRefX=self.GetRefWidthFromPixelWidth(DeltaX)
		DeltaRefY=self.GetRefHeightFromPixelHeight(DeltaY)


		self.EastingMin=self.EastingMin+DeltaRefX
		self.NorthingMin=self.NorthingMin+DeltaRefY


	############################################################################
	# Functions to convert from ref coordinates to pixel coordinates and 
	# back again.
	############################################################################

	def CheckNumericType(self,Value):
		Type=type(Value)
		if (Type!=float) and (Type!=int): 
			if  (isinstance( Value, numpy.float64 ) or isinstance( Value, numpy.float32 ) or isinstance( Value, numpy.float16 )):
				Value = numpy.float32(Value)
			else:
				print("Sorry, the specified value is not a recognized type ")
		return(Value)
		
	def GetRefWidthFromPixelWidth(self,PixelWidth):
		"""
		Convert a width in pixels to a width in reference units
		"""
		RefWidth=(PixelWidth*self.Factor)
		return(RefWidth)

	def GetRefHeightFromPixelHeight(self,PixelHeight):
		RefHeight=-(PixelHeight*self.Factor)
		return(RefHeight)

	def GetRefXFromPixelX(self,PixelX):
		PixelX=self.CheckNumericType(PixelX)
		RefX=(PixelX*self.Factor)+self.EastingMin
		return(RefX)

	def GetRefYFromPixelY(self,PixelY):
		PixelY=self.CheckNumericType(PixelY)
		RefY=((self.HeightInPixels-PixelY)*self.Factor)+self.NorthingMin

		return(RefY)
	
	def GetPixelXFromRefX(self,RefX):
		RefX=self.CheckNumericType(RefX)
		PixelX=(RefX-self.EastingMin)/self.Factor
		return(PixelX)

	def GetPixelYFromRefY(self,RefY):
		RefY=self.CheckNumericType(RefY)
		PixelY=(RefY-self.NorthingMin)/self.Factor
		PixelY=self.HeightInPixels-PixelY
		return(PixelY)

	def GetPixelWidthFromRefWidth(self,RefWidth):
		"""
		Convert a width in pixels to a width in reference units
		"""
		PixelWidth=RefWidth/self.Factor
		#RefWidth=(PixelWidth*self.Factor)
		return(PixelWidth)

	def GetPixelHeightFromRefHeight(self,RefHeight):
		PixelHeight=-RefHeight/self.Factor
		#RefHeight=-(PixelHeight*self.Factor)
		return(PixelHeight)

	############################################################################
	# Settings
	############################################################################
	def SetFillColor(self,TheColor):
		self.FillColor=TheColor

	def SetOutlineColor(self,TheColor):
		self.OutlineColor=TheColor

	def GetOutlineColor(self):
		return(self.OutlineColor)

	def SetBackgroundColor(self,TheColor):
		self.BackgroundColor=TheColor

	def SetLineWidth(self,LineWidth):
		self.LineWidth=LineWidth
		
	############################################################################
	# Functions to render objects using Pixel Coordinates
	############################################################################
	def RenderRect(self,X,Y,Width,Height):
		self.TheImageDrawing.rectangle([X,Y,X+Width,Y+Height], outline=self.OutlineColor,fill=self.FillColor) #[x0, y0, x1, y1]
		
	def RenderLine(self,X1,Y1,X2,Y2):
		self.TheImageDrawing.line([X1,Y1,X2,Y2], fill=self.OutlineColor,width=self.LineWidth)
		
	def RenderPolygon(self,Coordinates,Closed=True):
		"""
		PILs polygon function does not support a width parameter for the outline so we
		break up drawing polygons into the PIL polygon function and drawing the outline 
		as line segmenets
		"""
		try:
			if (len(Coordinates)>=6):
				#TheDrawing=self.TheImageDrawing
				
				# 
				if (Closed) and (self.FillColor!=None):
					self.TheImageDrawing.polygon(Coordinates, outline=None,fill=self.FillColor)
				
				NumCoordinateValues=len(Coordinates)
				Index=2
				LastX=Coordinates[0]
				LastY=Coordinates[1]
				
				while (Index<NumCoordinateValues-1):
					X=Coordinates[Index]
					Y=Coordinates[Index+1]
					
					self.RenderLine(LastX,LastY,X,Y)
					
					Index+=2
					
					LastX=X
					LastY=Y
					
				# Close the poly if desired
				if (Closed):
					X=Coordinates[0]
					Y=Coordinates[1]
					self.RenderLine(LastX,LastY,X,Y)
				
		except:
			TheError=sys.exc_info()
			print("Unexpected error:", TheError[0])
			raise	
		
	def RenderEllipse(self,X1,Y1,X2,Y2):
		"""
		Note that X1,Y1 are the upper left coordinate, in pixels, while X2,Y2 are the lower
		left.  Thus, X1,Y1 need be less than X2,Y2 respectively or the ellipse will not render
		"""
		self.TheImageDrawing.ellipse((X1,Y1,X2,Y2), fill =self.FillColor, outline =self.OutlineColor)
	
	############################################################################
	# Functions to render objects using reference (map) coordinates.
	############################################################################
	def RenderRefLine(self,RefX1,RefY1,RefX2,RefY2):

		X1=self.GetPixelXFromRefX(RefX1)
		X2=self.GetPixelXFromRefX(RefX2)
		Y1=self.GetPixelYFromRefY(RefY1)
		Y2=self.GetPixelYFromRefY(RefY2)

		try:
			if ((math.isfinite(X1)) and (math.isfinite(X2))  and (math.isfinite(Y1))  and (math.isfinite(Y2))):
				self.TheImageDrawing.line([X1,Y1,X2,Y2], fill=self.OutlineColor,width=self.LineWidth)
		except:
			print("Unexpected error:", sys.exc_info()[0])
			raise		

	def RenderRefEllipse(self,RefX1,RefY1,RefWidth=None,RefHeight=None,Width=None,Height=None):
		
		if (RefWidth!=None):		
			if (RefHeight==None): RefHeight=-RefWidth
			Width=self.GetPixelWidthFromRefWidth(RefWidth)
			Height=self.GetPixelHeightFromRefHeight(RefHeight)
		
		CenterX=self.GetPixelXFromRefX(RefX1)
		CenterY=self.GetPixelYFromRefY(RefY1)
		
		if (Height==None): Height=Width
		
		X1=CenterX-Width/2
		Y1=CenterY-Height/2
		X2=X1+Width
		Y2=Y1+Height
		
		self.RenderEllipse(X1,Y1,X2,Y2)

		
	def RenderRefPolygonFromArrays(self,RefXs,RefYs,Closed=True):
		""" 
		Renders a polygon from X and Y arrays of coordinate values
		"""
		NumCoordinates=len(RefXs)
		Coordinates=[]
		Index=1
		PixelX1=self.GetPixelXFromRefX(RefXs[0])
		PixelY1=self.GetPixelYFromRefY(RefYs[0])
		Coordinates.append(PixelX1)
		Coordinates.append(PixelY1)
		while (Index<NumCoordinates):

			PixelX2=self.GetPixelXFromRefX(RefXs[Index])
			PixelY2=self.GetPixelYFromRefY(RefYs[Index])

			if ((abs(PixelX1-PixelX2)>1) or (abs(PixelY1-PixelY2)>1)): # require at least one pixel of change before drawing the coordinate
				Coordinates.append(PixelX2)
				Coordinates.append(PixelY2)

				PixelX1=PixelX2
				PixelY1=PixelY2

			Index+=1
			
		self.RenderPolygon(Coordinates,Closed)
	
	############################################################################
	# Functions to render objects using reference (map) coordinates using shapely
	# data structures.  
	############################################################################
	def RenderRefPolygonFromCoordinates(self,TheCoords,Closed=True):
		""" 
		Renders a polygon from an array of coordinate pairs
		"""
		NumCoordinates=len(TheCoords)
		Coordinates=[]
		Index=1
		PixelX1=self.GetPixelXFromRefX(TheCoords[0][0])
		PixelY1=self.GetPixelYFromRefY(TheCoords[0][1])
		Coordinates.append(PixelX1)
		Coordinates.append(PixelY1)
		while (Index<NumCoordinates):

			PixelX2=self.GetPixelXFromRefX(TheCoords[Index][0])
			PixelY2=self.GetPixelYFromRefY(TheCoords[Index][1])

			if (abs(PixelX2==math.isfinite)):
				print("SpaView.RenderRefPolygonFromCoordinates PixelX2==math.infinity")

			if ((abs(PixelX1-PixelX2)>1) or (abs(PixelY1-PixelY2)>1)):

				Coordinates.append(PixelX2)
				Coordinates.append(PixelY2)

			PixelX1=PixelX2
			PixelY1=PixelY2

			Index+=1
			
		self.RenderPolygon(Coordinates,Closed)
		
		#try:
			#if (len(Coordinates)>=6):
				#self.TheImageDrawing.polygon(Coordinates, outline=self.OutlineColor,fill=self.FillColor)
		#except:
			#TheError=sys.exc_info()
			#print("Unexpected error:", TheError[0])
			#raise	

	def RenderRefCoords(self,TheCoords,Closed=True):
		Xs,Ys=SpaBase.GetXYsFromCoords(TheCoords)

		if (len(Xs)>2):
			self.RenderRefPolygonFromArrays(Xs,Ys,Closed)

	def RenderRefLineString(self,ThePolygon):
		if (ThePolygon!=None):
			Coords=ThePolygon.coords
			self.RenderRefCoords(Coords,False)

	def RenderRefPolygon(self,ThePolygon):
		if (ThePolygon!=None):
			Coords=ThePolygon.exterior.coords
			self.RenderRefCoords(Coords,True)

	def RenderRefGeometry(self,TheGeometry):
		""" 
		Render the specified geomery into the specified view.  This is called by Render() 
		"""

		if (TheGeometry!=None):
			# take the appropriate action based on the type of geometry
			TheType=TheGeometry.geom_type
			if (TheType=="Point"):
				TheCoords=TheGeometry.coords
				self.RenderRefEllipse(TheGeometry.x,TheGeometry.y,Width=4) # this is really done by the layer
			elif (TheType=="Polygon"):
				self.RenderRefPolygon(TheGeometry)
			elif (TheType=="MultiPolygon"):
				#print(len(TheGeometry.geoms))
				for ThePolygon in TheGeometry.geoms:
					self.RenderRefPolygon(ThePolygon)
			elif (TheType=="LineString"):
				self.RenderRefLineString(TheGeometry)
			elif (TheType=="MultiLineString"):
				for ThePolygon in TheGeometry.geoms:
					self.RenderRefLineString(ThePolygon)				
			elif (TheType=="GeometryCollection"): # collections are typically empty for shapefiles
				for TheSubGeometry in TheGeometry.geoms:
					self.RenderRefGeometry(TheSubGeometry)
			else:
				print("Unsupported Type: "+TheType)

	############################################################################
	# Functions to Render rasters into a view
	############################################################################
	def RenderRaster(self,TheRasterDataset,Stretch=True):
		
		########################################################################
		# Crop the raster to the vewing area if needed
		TheRasterBounds=TheRasterDataset.GetBounds() # upper left, lower right (XMin,YMax,XMax,YMin)
		
		TheViewBounds=self.GetBounds()
		
		RasterXMin=TheRasterBounds[0]
		RasterYMin=TheRasterBounds[1]
		RasterXMax=TheRasterBounds[2]
		RasterYMax=TheRasterBounds[3]
		
		DoCrop=False
		if (TheRasterBounds[0]<TheViewBounds[0]): # crop left side
			RasterXMin=TheViewBounds[0]
			DoCrop=True
		
		if (TheRasterBounds[1]<TheViewBounds[1]): # crop bottom
			RasterYMin=TheViewBounds[1]
			DoCrop=True
		
		if (TheRasterBounds[2]>TheViewBounds[2]): # crop right
			RasterXMax=TheViewBounds[2]
			DoCrop=True
		
		if (TheRasterBounds[3]>TheViewBounds[3]): # crop top
			RasterYMax=TheViewBounds[3]
			DoCrop=True
		
		if (DoCrop):
			TheRasterDataset=SpaRasters.Crop( TheRasterDataset,[RasterXMin,RasterYMin,RasterXMax,RasterYMax])

		TheRasterBounds=TheRasterDataset.GetBounds()
		RasterXMin=TheRasterBounds[0]
		RasterYMin=TheRasterBounds[1]
		RasterXMax=TheRasterBounds[2]
		RasterYMax=TheRasterBounds[3]
		
		#############################################
		# Scale the raster to match the view

		XFactor=(RasterXMax-RasterXMin)/TheRasterDataset.GetWidthInPixels()
		ChangeFactor=XFactor/self.Factor
		
		if (ChangeFactor!=1): TheRasterDataset=SpaRasters.Resample(TheRasterDataset,ChangeFactor)
		
		#############################################
		# Stretch the raster if needed
		TheBands=TheRasterDataset.GetBands()
		
		WidthInPixels=TheRasterDataset.GetWidthInPixels()
		HeightInPixels=TheRasterDataset.GetHeightInPixels()
		RasterSize=WidthInPixels*HeightInPixels
		TheBand=TheBands[0]
		
		if (Stretch):
			Min,Max=TheRasterDataset.GetMinMax(0)
	#		Min=numpy.amin(TheBand)
			
		#	Max=numpy.amax(TheBand)
			#super_threshold_indices = TheBand<0.00000001
			#TheBand[super_threshold_indices] = 0
			#Min=numpy.amin(TheBand)
			
			if (Max!=0):
				Range=(Max-Min)
				Factor=255/Range
				TheBand=(TheBand-Min)*Factor
		
			###########################################
		# 
		TheMask=TheRasterDataset.GetMask()
		if (isinstance(TheMask,numpy.ndarray)):
			TheBand=numpy.uint8(TheBand)
			#OutputBand=numpy.ma.masked_array(TheBand,TheMask)
			TheMask=numpy.logical_not(TheMask)
			TheMaskImage = PIL.Image.fromarray(TheMask)
			TheRasterImage = PIL.Image.fromarray(TheBand)
			TheRasterImage.putalpha(TheMaskImage)
		else:
			TheRasterImage = PIL.Image.fromarray(numpy.uint8(TheBand))
			
		#TheRasterImage = PIL.Image.fromarray(numpy.uint8(TheBand))		###########################################
		# Draw the raster into the view
		TheImage=self.GetImage()

		PixelXMin=self.GetPixelXFromRefX(RasterXMin)
		PixelYMin=self.GetPixelYFromRefY(RasterYMax)
		
		PixelXMin=int(PixelXMin)
		PixelYMin=int(PixelYMin)
		
		PixelXMax=PixelXMin+WidthInPixels
		PixelYMax=PixelYMin+HeightInPixels
		
		TheImage.paste(TheRasterImage, (PixelXMin, PixelYMin, PixelXMax,PixelYMax))
					
	############################################################################
	# Functions to Render rasters into a view
	############################################################################
	def RenderVectors(self,TheDataset):
		
		########################################################################
		# Crop the raster to the vewing area if needed
		TheBounds=TheDataset.GetBounds() # upper left, lower right (XMin,YMax,XMax,YMin)
		
		TheViewBounds=self.GetBounds()
		
		Index=0
		NumFeatures=TheDataset.GetNumFeatures()
		while (Index<NumFeatures):
			
			TheGeometry=TheDataset.GetGeometry(Index)
			
			self.RenderRefGeometry(TheGeometry)
				
			Index+=1
			
					
	############################################################################
	# Functions to access and save the image.
	############################################################################
	def GetImage(self):
		return(self.TheImage)

	def Save(self, FilePath):
		self.TheImage.save(FilePath)
		
	def Show(self):
		# Create the tkinter window
		window = tkinter.Tk()
	
		# Set the width and height of the window
		Width,Height=self.GetDimensions()
		window.geometry(format(Width)+"x"+format(Height)) # (optional)    
	
		# Get the image and add it to the window
		TheImage=self.GetImage()
		TheTkImage = PIL.ImageTk.PhotoImage(TheImage)
		lbl = tkinter.Label(window, image = TheTkImage).pack()
	
		# Display the window until the user clicks the close box
		window.mainloop()

############################################################################
# Oneline functions (jjg need to be comleted for different datasets)
############################################################################
def Show(TheDataset,width=800,height=800):
	
	# IF a file path is specified, load the dataset
	if (type(TheDataset) is str):
		filename, file_extension = os.path.splitext(TheDataset)
		file_extension=file_extension.lower()
		
		if (file_extension==".shp"):
			TheDataset=SpaVectors.Load(TheDataset) # load the contents of the layer
		else:
			TheDataset=SpaRasters.Load(TheDataset)
		
	# Create the view
	TheView=SpaView(width,height)
	
	# Set the bounds of the view to match the dataset
	TheBounds=TheDataset.GetBounds()
	TheView.SetBounds(TheBounds)
	
	# Render the dataset into the view
	if (isinstance(TheDataset, SpaRasters.SpaDatasetRaster)):
		
		TheView.RenderRaster(TheDataset)
		
	elif (isinstance(TheDataset, SpaVectors.SpaDatasetVector)):
		TheView.RenderVectors(TheDataset)
		
	TheView.Show()
	