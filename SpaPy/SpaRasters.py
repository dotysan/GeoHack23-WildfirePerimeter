############################################################################
# Classes and functions for working with spatially referenced raster data.
# The GDAL libraries are heavily relied upon for this and the data can be
# maintained in file (as a GDAL dataset) or in numpy arrays.
#
# Note, the GDAL documentation at: https://www.gdal.org/gdal_tutorial.html
# is not update to date with the Python gdal reelases.  The standard
# Python documentation is closer:
# https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
#
# Supports the following gdal types:
# gdal.GDT_Byte
# gdal.GDT_UInt16
# gdal.GDT_Int16
# gdal.GDT_UInt32
# gdal.GDT_Int32
# gdal.GDT_Float32
# gdal.GDT_Float64
#
# The GDAL bindings return numpy arrays of the data so this was helpful:
# https://gis.stackexchange.com/questions/150300/how-to-place-an-numpy-array-into-geotiff-image-using-python-gdal
#
# Data is available using numpy arrays.  numpy masked arrays are not implemented for all numpy functions so a separate mask
# is maintained as a numpy array of booleans were True means masked and False means not masked.  This allows a numpy masked
# array to be created where needed for speed such as min/max and histogram operations.  The mask may be ingored except when:
# - Changing the resolution or shape of the raster
# - When combining rasters together that may be different masks
# Also, pixels that are masked can be ignored to improve speed if desired.
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
from osgeo_utils import gdal_merge

# Spa Libraries
from SpaPy import SpaBase

############################################################################
# Globals
############################################################################

class SpaDatasetRaster:
	"""
	Class to manage the data associated with a spatial layer.  The data can be in any combination of the
	following locations:
	- A file
	- In numpy arrays 
	- In a GDALDataset Mem (memory) object
	
	Reading and write large rasters from and to files can take a great deal of time so we need to minimize
	how often this occurs.
	
	Some transforms can perform file to file operations.  This means we should not load the data all the time.
	Other transforms require the data to be in numpy arrays which means the data will have to be loaded
	into the arrays.  Also, new rasters can be created and held in memory (GDAL object or numpy arrays) and
	not written to a file.
	
	For these reasons, data is only read or written when requested.  
	
	Load() - loads the attributes of the raster into the object but not the data
	GetGDALDataset() - loads the data from a file or creates it from existing numpy arrays.
	GetBands() - returns numpy arrays with the data or reads the data from the file.
	
	Attributes:

		GDALDataType: See file header for supported types

		WidthInPixels: an integer representing the number of pixels along the x-axis

		HeightInPixels: an integer representing the number of pixels along the x-axis

		NumBands: an integer representing the number of bands

		NoDataValue: Value used for transparent pixels when reading and writing data to formats that do not support masks.

		TheMask: SpaRaster uses a mask internally to avoid problems with performing math on NoDataValues

		TheBands: Array of bands where each entry has a 2D grid of pixel values

		XMin: typically the x coordinate value for the left-most pixel in the raster
		YMin: typically the y coordinate value for the bottom pixel in the raster

		PixelWidth: Width of a pixel in reference units
		PixelHeight: Height of a pixel in reference units

		SpatialReference: Spatial reference (CRS)
		GCS: GCS but not used yet
		UTMZone
		UTMSouth

	"""
	def __init__(self):
		""""
		Initializes an empty instance of SpaDatasetRasters
		"""

		self.FilePath=None
		self.WidthInPixels=100
		self.HeightInPixels=100
		self.NumBands=1

		# mask, if NoDataValue is not None, then TheMask contains 1 where there is data, 0 otherwise
		self.NoDataValue=None
		self.TheMask=None # Optional numpy array used as a mask

		# the actual data for each band as numpy arrays
		self.TheBands=None # list with one entry for each band

		# 
		self.GDALDataset=None
		self.GDALDataType=None
		# reference coordinates for the raster
		self.XMin=0
		self.YMax=0
		self.PixelWidth=1
		self.PixelHeight=1

		# projection information
		self.SpatialReference=None
		self.GCS="WGS84"
		self.UTMZone=None # if the zone is set, it takes over
		self.UTMSouth=False

	def CopyPropertiesButNotData(self,RasterDataset):
		"""
		Copy all attributes pertaining to metadata from another instance of SpaDatasetRasters into this instance

		Parameters:
			RasterDataset: A SpaDasetRaster object (cannot take a path name, at this point)

		Returns:
			None
		"""
		self.GDALDataset=None
		self.GDALDataType=RasterDataset.GDALDataType

		self.WidthInPixels=RasterDataset.WidthInPixels
		self.HeightInPixels=RasterDataset.HeightInPixels
		self.NumBands=RasterDataset.NumBands

		self.NoDataValue=RasterDataset.NoDataValue
		#self.TheMask=None

		self.TheBands=None

		self.XMin=RasterDataset.XMin
		self.YMax=RasterDataset.YMax
		self.PixelWidth=RasterDataset.PixelWidth
		self.PixelHeight=RasterDataset.PixelHeight

		self.SpatialReference=None
		
		if (RasterDataset.SpatialReference is not None):
			self.SpatialReference=RasterDataset.SpatialReference.Clone()
			
		self.GCS=RasterDataset.GCS
		self.UTMZone=RasterDataset.UTMZone
		self.UTMSouth=RasterDataset.UTMSouth

	def Clone(self):
		"""
		Duplicates this instance of SpaDatasetRaster

		Parameters:
			None
		Returns:
			SpaDatasetRaster object that is an exact copy of the inputted SpaDatasetRaster object
		"""
		NewDataset=SpaDatasetRaster()
		NewDataset.CopyPropertiesButNotData(self)

		# copy the bands of data
		NewDataset.TheBands=[]
		for SourceArray in self.TheBands:
			DestinArray = numpy.array(SourceArray)
			NewDataset.TheBands.append(DestinArray)

		# make a copy of the mask, if there is one
		if (self.NoDataValue is not None) and (self.TheMask is not None):
			NewDataset.TheMask=numpy.array(self.TheMask)
		else:
			NewDataset.TheMask=None

		return(NewDataset)

	############################################################################
	# General Information functions
	############################################################################
	def GetDriverNames(self):
		"""
		Retrieves driver names for provided SpaDatasetRaster

		Parameters:
			None
		Returns:
			driver information for provided SpaDatasetRaster
		"""		
		return(self.GDALDataset.GetDriver().ShortName, self.GDALDataset.GetDriver().LongName)

	def GetWidthInPixels(self):
		"""
		Retrieves width in pixels for provided SpaDatasetRaster

		Parameters:
			None
		Returns:
			Width (in pixels) of provided SpaDatasetRaster
		"""		
		return(self.WidthInPixels)

	def SetWidthInPixels(self,New):
		"""
		Redefines width (in pixels) of provided SpaDatasetRaster

		Parameters:
			New: Value of desired raster width
		Returns:
			none
		"""		
		self.WidthInPixels=New

	def GetHeightInPixels(self):
		"""
		Retrieves height for provided SpaDatasetRaster

		Parameters:
			None
		Returns:
			Height (in pixels) of provided raster
		"""	
		return(self.HeightInPixels)

	def SetHeightInPixels(self,New):
		"""
		Redefines height of provided SpaDatasetRaster

		Parameters:
			New: Value of desired raster height (in pixels)
		Returns:
			none
		"""				
		self.HeightInPixels=New

	def GetNumBands(self):
		"""
		Retrieves number of bands in provided SpaDatasetRaster

		Parameters:
			None
		Returns:
			number of bands found in provided raster
		"""			
		return(self.NumBands)

	def SetNumBands(self,NumBands): 
		"""
		Sets new value for number of bands in this SpaDatasetRaster

		Parameters:
			NumBands: Insert value of desired band amount found in raster
		Returns:
			none
		"""		
		self.NumBands=NumBands

	def GetCRS(self):
		"""
		Retrieves coordinate reference system/spatial reference of this SpaDatasetRaster

		Parameters:
			None
		Returns:
			Projection information for provided raster formatted into a list that includes projection, geographic coordinate system, spheroid, etc.
		"""					
		return(self.SpatialReference)


	def GetEPSGCode(self):
		"""
		Gets the EPSG Code for the current raster if available.

		Parameters:
			None
		Returns:
			EPSG Code for the current raster or None if the code is not available.
		"""				
		Result=None
		if (self.SpatialReference is not None): self.SpatialReference.GetAttrValue("AUTHORITY", 1)
		return(Result)

	def SetEPSGCode(self,EPSGCode):
		"""
		Sets the spatial refrence for the current raster based on an EPSG Code.

		Parameters:
			EPSG Code as a number or strng
		"""				
		srs = osr.SpatialReference()
		srs.ImportFromEPSG(format(EPSGCode))
	

	def GetResolution(self):
		""" 
		Returns the resolution of the raster as a tuple with (X,Y) 

		Parameters: 
			none
		Returns:
			the resolution of the raster as a tuple with (X,Y)

		"""
		return((self.PixelWidth,self.PixelHeight))

	def SetResolution(self,PixelWidth,PixelHeight=None):
		"""
		Redefines resolution of provided SpaDatasetRaster

		Parameters:
			PixelWidth: Value of desired pixel width in pixel units
		Returns:
			none
		"""				
		if (PixelHeight is None): PixelHeight=PixelWidth
		self.PixelWidth=PixelWidth
		self.PixelHeight=PixelHeight


	def GetBounds(self):
		"""
		Retreives bounds of provided SpaDatasetRaster formatted as (XMin,YMin,YMax,XMax)

		Parameters:
			None
		Returns:
			Bound information for provided raster
		"""
		Result=None

		Resolution=self.GetResolution()

		XMax=self.XMin+(self.WidthInPixels*Resolution[0])
		YMin=self.YMax+(self.HeightInPixels*Resolution[1]) # The resolution will be negative so we add the height 

		Result=(self.XMin,YMin,XMax,self.YMax)

		return(Result)

	def GetRefXFromPixelX(self,PixelX):
		#Need additional information to complete notes (function of tool-inputs, outputs, etc.)
		"""
		Converts from Pixel (view/raster) coordinates to Reference (map) coordinates in the horizontal direction

		Parameters:
			PixelX= pixel coordinates in the horizontal direction (x-coordinate)
		Returns:
			Reference coordinates in the horizontal direction
		"""		
		Resolution=self.GetResolution()
		RefX=self.XMin+(PixelX*Resolution[0])
		return(RefX)

	def GetRefYFromPixelY(self,PixelY):
		#Need additional information to complete notes (function of tool-inputs, outputs, etc.)
		"""
		Converts from Pixel (view/raster) coordinates to Reference (map) coordinates in the vertical direction

		Parameters:
			PixelY= pixel coordinates in the vertical direction (y-coordinate)
		Returns:
			Reference point information for listed pixel from SPDatatsetRaster 
		"""				
		Resolution=self.GetResolution()
		RefY=self.YMax-(PixelY*Resolution[1])
		return(RefY)

	def GetPixelXFromRefX(self,RefX):
		"""
		Converts from Reference (map) coordinates to Pixel (view/raster) coordinates in the horizontal direction

		Parameters:
			RefX= Reference coordinates in the horizontal direction (x-coordinate)
		Returns:
			Pixel coordinates in the horizontal direction
		"""								
		Resolution=self.GetResolution()
		PixelX=0+((RefX-self.XMin)// Resolution[0])
		return(int(PixelX))

	def GetPixelYFromRefY(self,RefY):
		"""
		This function converts from Reference (map) coordinates to Pixel (view/raster) coordinates in the vertical direction

		Parameters:
			RefY= Reference coordinates in the vertical direction (y-coordinate)
		Returns:
			Pixel coordinates in the horizontal direction
		"""						
		Resolution=self.GetResolution()
		PixelY=0-((self.YMax-RefY) //Resolution[1])
		return(int(PixelY))

	def SetNorthWestCorner(self,X,Y):
		""""
		Sets northwest corner of raster to desired coordinates (x,y)

		Parameters:
			X= insert desired x-coordinate here
			Y= insert desired y-coordinate here
		Returns:
			a SpaDatasetRaster object

		"""		
		self.XMin=X 
		self.YMax=Y

	def GetBand(self,Index):
		"""
		Retreive band information for selected band

		Parameters:
			Index: format as a tuple.
		Returns:
			Band information for selected band

		"""
		if (self.TheBands is None): throw("Error")

		return(self.TheBands[Index])

	def SetBands(self,TheBands):
		# Need more information about format of TheBands
		"""
		Sets the band values in SpaRaster object equal to those specified

		Parameters:
			TheBands=desired band values
		Returns:
			none

		"""	
		self.TheBands=TheBands
		self.GDALDataset=None # have to recreate the GDAL dataset if the bands are replaced
		
	def SetMask(self,TheMask,NewValue=None):
		"""
		Sets a new mask.  The mask can be None or a new array.  If a NewValue is specified, the current
		mask values will be replaced by the NewValue.  If TheMask is None, the NoDataValue will be set to None
		"""
		if (NewValue is not None):
			TheBands=self.GetBands()
			NewBands=[]
			
			Index=0
			while (Index<len(TheBands)):
				TheBand=TheBands[Index]
				
				NewBand=numpy.where(self.TheMask,NewValue,TheBand)
				NewBands.append(NewBand)
				
				Index+=1
				
			self.SetBands(NewBands)
			
		self.TheMask=TheMask
		
	def GetMask(self):
		return(self.TheMask)

		
	def GetBands(self):
		"""
		Retreive band information for SpaRaster object

		Parameters:
			none
		Returns:
			Band information for SpaRaster object

		"""		
		if (self.TheBands is None):
			if (self.GDALDataset is not None):
				# Get the first band to see if we have a mask (NoDataValue)
				TheMask=None
				FirstBand = self.GDALDataset.GetRasterBand(1)
				self.NoDataValue=FirstBand.GetNoDataValue()
	
				# this is ugly but GDAL returns 0 for a no data value that is missing
				if (self.NoDataValue==0): self.NoDataValue=None 
				
				# Load the bands of data
				self.TheBands =[]
				Count=0
				while (Count<self.NumBands):
					# Read the band from the file and get the numpy array
					TheBand=self.GDALDataset.GetRasterBand(Count+1)
					TheBand=TheBand.ReadAsArray()
					
					if (self.NoDataValue is not None) and (TheMask is None): # have to create the mask
						
						# Find where pixels match the no data value (note that in numpy, False indicates a valid pixel (i.e. not masked))
						TheMask=numpy.equal(TheBand,self.NoDataValue)
						
					self.TheBands.append(TheBand)
					
					Count+=1
	
				self.TheMask=TheMask
					
		return(self.TheBands)

			
	def GetMinMax(self,Index=0):
		"""
		Returns the min and max values for the specified band

		Parameters:
			Index: insert specified band here 
		Return:
			Returns a tuple (static list) with the minimum and maximum raster values for the specific band index
		"""
		TheBand=self.TheBands[Index]
		
		Min=None
		Max=None
				
		if (self.TheMask is not None): # if there is a mask, use it
			TheBand=numpy.ma.masked_array(TheBand,self.TheMask)
			Min=numpy.ma.MaskedArray.min(TheBand)
			Max=numpy.ma.MaskedArray.max(TheBand)
			
		else: # no mask
			
			Min=numpy.amin(TheBand)
			Max=numpy.amax(TheBand)
		
		return(Min,Max)

	# Results additional information for each band.
	# Not sure what to do with this function in the future
	def GetBandInfo(self,Index):
		"""
		Retreive band info from SpaDatasetRaster object for selected band
		Note: This function uses GDAL directly and should only be used if required.
		
		Parameters:
			Index: Input desired band here
		Returns:
			Selcted band information for SpaDatasetRaster object

		"""				
		srcband = self.GDALDataset.GetRasterBand(Index)
		Result=None
		if (srcband is not None):
			Result={
				"Scale":srcband.GetScale(),
				"UnitType":srcband.GetUnitType(),
				"ColorTable":srcband.GetColorTable()
			}
		return(Result)

	def GetType(self):
		"""
		returns the GDAL types, these are shown in the GetNumPyType() function

		Parameters:
			none
		Returns:
		        SpaDatasetRaster object type information

		"""		
		return(self.GDALDataType)

	def SetType(self,GDALDataType):
		"""
		Set GDAL type for SpaDatasetRaster object.  If the current raster data does not match the type,
		the data will be converted to match the specified type.

		Parameters:
			Desired data type
		Returns:
			none

		"""		
		self.GDALDataType=GDALDataType

		if (self.GDALDataset is not None):
			self.GDALDataset = gdal.Translate('', GDALDataset, format="MEM",outputType=GDALDataType)

	def GetNoDataValue(self):
		"""
		Returns the current NoDataValue that is used for transparent data in the raster.  

		Returns:
			NoDataValue
		"""
		return(self.NoDataValue)
	
	def GetHistogram(self,BandIndex=0,NumBins=10):
		"""
		Returns a histogram with the specified number of bins

		Parameters:
		    BandIndex: Index to the desired band or 0 if not specified
			NumBins: Number of bins in the histogram or 10 if not specified
			
		Returns:
			An array of arrays where each array contains a histogram and then another array with the edges of the bins.
			See https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
		"""

		# setup the return value as an array of all zeros
		Result=[]
		
		# Go through the data adding 1 to each bin that a pixel falls into
		TheBand=self.TheBands[BandIndex]
		
		if (self.TheMask is not None): # if there is a mask, use it
			Result=numpy.histogram(TheBand, bins=NumBins, weights=self.TheMask)
		else:
			Result=numpy.histogram(TheBand, bins=NumBins)

		return(Result)
	############################################################################
	# Functions to manage spatial references
	############################################################################
	def SetUTM(self,Zone,South=False):
		"""
		Set SpaDatadetRaster object to UTM zone specified

		Parameters:
			Zone: insert zone number here
		Returns:
			none

		"""		
		self.UTMZone=Zone
		self.UTMSouth=South

	############################################################################
	# Functions to setup the arrays of data
	############################################################################
	def AllocateArray(self):
		""" 
		Allocates the numpy array for the raster.
		NumPyType - uint8, int16, int32, float32 are supported.   
		 (see https://docs.scipy.org/doc/numpy-1.13.0/user/basics.types.html)
		Parameters:
			none
		Returns:
			An array of values
		"""
		#self.NumPyType=NumPyType
		NumPyType=self.GetNumPyType()

		self.TheBands=[]

		Count=0
		while (Count<self.NumBands):
			self.TheBands.append(numpy.zeros((self.HeightInPixels,self.WidthInPixels), dtype=NumPyType))
			Count+=1

		return(self.TheBands)

	############################################################################
	# Functions to interact with files (shapefiles and CSVs)
	############################################################################
	def GetNumPyType(self):
		"""
		Returns with NumPy Type of SpaDatasetRaster object

		Parameters:
			none
		Returns:
			Numpy Type of SpaDatasetRaster object

		"""				
		NumPyType=None
		if (self.GDALDataType==gdal.GDT_Byte): NumPyType="uint8"
		elif (self.GDALDataType==gdal.GDT_Byte): NumPyType="int8"
		elif (self.GDALDataType==gdal.GDT_UInt16): NumPyType="uint16"
		elif (self.GDALDataType==gdal.GDT_Int16): NumPyType="int16"
		elif (self.GDALDataType==gdal.GDT_UInt32): NumPyType="uint32"
		elif (self.GDALDataType==gdal.GDT_Int32): NumPyType="int32"
		elif (self.GDALDataType==gdal.GDT_Float32): NumPyType="float32"
		elif (self.GDALDataType==gdal.GDT_Float64): NumPyType="float64"
		elif (self.GDALDataType==gdal.GDT_CFloat64): NumPyType="complex64"
		return(NumPyType)

	def Load(self,FilePathOrDataset):
		"""
		Loads raster file (this enables us to later perform operations on the raster)
		Parameters:
			FilePathOrDataset: A SpaDatasetRaster object OR a string representing the path to the raster file
		Returns:
			none

		"""				

		if isinstance(FilePathOrDataset,gdal.Dataset): # A dataset was specified, set it as the current GDALDataset
			self.GDALDataset=FilePathOrDataset
		else:
			self.FilePath=FilePathOrDataset
			self.GDALDataset=gdal.Open(FilePathOrDataset)
			
		if (self.GDALDataset is None):
			raise Exception("Sorry, the file "+FilePathOrDataset+" could not be opened.  Please, make sure the file path is correct and is of a supported file type.")
		else:
			# get the desired band
			FirstBand = self.GDALDataset.GetRasterBand(1)

			# Get the GDAL data type and convert it to a numpy datatype

			self.GDALDataType=FirstBand.DataType

			# get the dimensions in pixels and the number of bands
			self.WidthInPixels=self.GDALDataset.RasterXSize
			self.HeightInPixels=self.GDALDataset.RasterYSize

			self.NumBands=self.GDALDataset.RasterCount

			####################################
			# Get the spatial location of the raster data
			# adfGeoTransform[0] /* top left x */
			# adfGeoTransform[1] /* w-e pixel resolution */
			# adfGeoTransform[2] /* 0 */
			# adfGeoTransform[3] /* top left y */
			# adfGeoTransform[4] /* 0 */
			# adfGeoTransform[5] /* n-s pixel resolution (negative value) */

			TheGeoTransform=self.GDALDataset.GetGeoTransform()

			self.XMin=TheGeoTransform[0]
			self.YMax=TheGeoTransform[3]

			self.PixelWidth=TheGeoTransform[1]
			self.PixelHeight=TheGeoTransform[5]

			# Get the spatial reference
			self.SpatialReference=self.GDALDataset.GetSpatialRef()
			
			self.GetBands()

	def GetGDALDataset(self):
		
		if (self.GDALDataset is None):
			self.GDALDataset=self.GetGDALDataset2()
			
		return(self.GDALDataset)
	
	def GetGDALDataset2(self,TheFilePath=None):
		"""
		Private function to either return an existing GDALDataset or create a new one from the existing numpy arrays
		
		TheFilePath - for creating a dataset wth a file path to write to.  The file extension will determine the file type
		DriverName - " MEM " for memory, gdal.GetDriverByName(  " MEM " )
		"""
		OutputGDALDataset=None
		
		if (self.GDALDataset is None) or (True): # if the data was not loaded using a GDALDataset, then create a new one and copy the data to the specifed file and/or memory
			
			DriverName="MEM"
			
			if (TheFilePath is not None):
				FileName,Extension=os.path.splitext(TheFilePath)
		
				Extension=Extension.lower()
	
				if (Extension==".tif") or (Extension==".tiff"):
					DriverName="GTiff"
				elif (Extension==".png"):
						DriverName="PNG"
				elif (Extension==".jpg"):
					DriverName="JPG" 
				elif (Extension==".asc"):
					DriverName="AAIGrid"
				elif (Extension==".img"):
					DriverName="HFA"
			else:
				TheFilePath="" # required by GDAL
				
			# Create the file
			
			TheDriver = gdal.GetDriverByName(DriverName)
	
			OutputGDALDataset = TheDriver.Create(TheFilePath, self.WidthInPixels, self.HeightInPixels, self.NumBands,self.GDALDataType)
			
			if (OutputGDALDataset == None): raise Exception("Can't ind File Path");
			
			# This has to be done before the GDAL Dataset is written out
			OutputGDALDataset.SetGeoTransform((self.XMin, self.PixelWidth, 0, self.YMax, 0, self.PixelHeight))
	 
			if (OutputGDALDataset is None): raise Exception("Sorry, there was a problem creating the file at "+TheFilePath)
	
			# write out the data
			Count=0
			while (Count<self.NumBands):
				OutputBand = OutputGDALDataset.GetRasterBand(Count+1)
	
				TheBand=self.TheBands[Count]
				
				if (self.NoDataValue is not None): # Restore the no data values
					
					OutputBand.SetNoDataValue(self.NoDataValue)
										
					# Use the NoDateValue where masked, the valid data otherwise
					TheBand=numpy.where(self.TheMask,self.NoDataValue,TheBand)
					
				OutputBand.WriteArray(TheBand)
				OutputBand.FlushCache()
	
				Count+=1
			
			#self.GDALDataset=OutputGDALDataset
			
		return(OutputGDALDataset)
		
	def Save(self,TheFilePath):
		""" 
		Creates a new raster in the layer.
		TheFilePath - Fill file path with the file extension (tif, jpg, png, or asc)
		Common file formats include: GTiff, PNG, JPEG, HFA (ERDAS Imagine or img), AAIGrid (Esri ASCII Ggrid)
		All FileFormats are listed at: https://www.gdal.org/formats_list.html 

		Parameters:
			TheFilePath: A string representing the path to the folder where file is to be stored
		Returns:
			none
		"""
		self.FilePath=TheFilePath
		
		# make sure the data is loaded
		self.GetBands() 
		
		# Reset the GDAL dataset to create another one
		#self.GDALDataset=None
		
		# Getting the new GDAL dataset with a filepath will save it to a file
		OutputGDALDataset=self.GetGDALDataset2(TheFilePath)
		
		###########################################
		
		#OutputGDALDataset.SetGeoTransform((self.XMin, self.PixelWidth, 0, self.YMax, 0, self.PixelHeight))
		
		#Setup the spatial reference
		if (self.UTMZone is not None):
			# setup the spatial reference
			srs = osr.SpatialReference()

			North=1
			if (self.UTMSouth): North=0
			srs.SetUTM(self.UTMZone,North)

			srs.SetWellKnownGeogCS(self.GCS)

			OutputGDALDataset.SetProjection(srs.ExportToWkt())
			
		elif (self.SpatialReference is not None):
			OutputGDALDataset.SetProjection(self.SpatialReference.ExportToWkt())


	#def Warp(self,DestinFilePath):
		#"""
		#Works but only writes to disk
		#"""
		#drv = ogr.GetDriverByName("ESRI Shapefile")
		#dst_ds = drv.CreateDataSource( DestinFilePath + ".shp" )
		#dst_layer = dst_ds.CreateLayer(DestinFilePath, srs = None )

		#srcband=self.GDALDataset.GetRasterBand(1)

	def Math(self,Operation,Input2):
		"""
		Handles all raster math operations using numPy arrays - called by one-line functions

		Parameters:
			Operation: An integer specifying which numpy function to call
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster file OR a constant value as a float
		Returns:
			SpaRasterDataset object
		"""

		BandIndex=0
		NewDataset=None #self.Clone()
		NewBands=None #[]

		if (isinstance(Input2, numbers.Number)==False): # input is another dataset
			# jjg - add checks for same number of bands, convertion to save width, height, and data type
			
			Input2=SpaBase.GetInput(Input2) # get the input as a dataset
			
			if (self.GetNumBands()!=Input2.GetNumBands()): raise Exception("Sorry, the number of bands in the two rasters must match")
			
			# resample the inputs if needed
			Input1,Input2=ResampleToMatch(self,Input2)
			
			# this could change the dimensions of the raster bands and mask so we need to clone them here
			NewDataset=Input1.Clone()
			NewBands=[]
			
			for TheBand in Input1.TheBands: # add each of the bands from each of the datasets
				Band2=Input2.GetBand(BandIndex)

				if (Operation==SPAMATH_ADD): NewBands.append(numpy.add(TheBand,Band2))
				elif (Operation==SPAMATH_SUBTRACT): NewBands.append(numpy.subtract(TheBand,Band2))
				elif (Operation==SPAMATH_MULTIPLY): NewBands.append(numpy.multiply(TheBand,Band2))
				elif (Operation==SPAMATH_DIVIDE): NewBands.append(numpy.divide(TheBand,Band2))
				elif (Operation==SPAMATH_EQUAL): NewBands.append(numpy.equal(TheBand,Band2))
				elif (Operation==SPAMATH_NOT_EQUAL): NewBands.append(numpy.not_equal(TheBand,Band2))
				elif (Operation==SPAMATH_GREATER): NewBands.append(numpy.greater(TheBand,Band2))
				elif (Operation==SPAMATH_LESS): NewBands.append(numpy.less(TheBand,Band2))
				elif (Operation==SPAMATH_GREATER_OR_EQUAL): NewBands.append(numpy.greater_equal(TheBand,Band2))
				elif (Operation==SPAMATH_LESS_OR_EQUAL): NewBands.append(numpy.less_equal(TheBand,Band2))
				elif (Operation==SPAMATH_AND): NewBands.append(numpy.logical_and(TheBand,Band2))
				elif (Operation==SPAMATH_OR): NewBands.append(numpy.logical_or(TheBand,Band2))
				elif (Operation==SPAMATH_MAX): NewBands.append(numpy.maximum(TheBand, Band2))
				elif (Operation==SPAMATH_MIN): NewBands.append(numpy.minimum(TheBand, Band2))

				# if the operation resulted in a Boolean raster, convert the raster to integer and type it as byte
				if (Operation==SPAMATH_EQUAL) or (Operation==SPAMATH_NOT_EQUAL) or (Operation==SPAMATH_GREATER) or (Operation==SPAMATH_LESS) or \
				   (Operation==SPAMATH_GREATER_OR_EQUAL) or (Operation==SPAMATH_LESS_OR_EQUAL) or (Operation==SPAMATH_AND) or (Operation==SPAMATH_OR) or \
				   (Operation==SPAMATH_MAX) or (Operation==SPAMATH_MIN): 
					NewBands[BandIndex]=NewBands[BandIndex].astype(int)
					NewDataset.GDALDataType=gdal.GDT_Byte

				BandIndex+=1

		else: # input is a scalar value ... all unary operators are in here
			
			NewDataset=self.Clone()
			NewBands=[]
			
			for TheBand in self.TheBands:
				if (Operation==SPAMATH_ADD): NewBands.append(numpy.add(TheBand,Input2))
				elif (Operation==SPAMATH_SUBTRACT): NewBands.append(numpy.subtract(TheBand,Input2))
				elif (Operation==SPAMATH_MULTIPLY): NewBands.append(numpy.multiply(TheBand,Input2))
				elif (Operation==SPAMATH_DIVIDE): NewBands.append(numpy.divide(TheBand,Input2))
				elif (Operation==SPAMATH_EQUAL): NewBands.append(numpy.equal(TheBand,Input2))
				elif (Operation==SPAMATH_NOT_EQUAL): NewBands.append(numpy.not_equal(TheBand,Input2))
				elif (Operation==SPAMATH_GREATER): NewBands.append(numpy.greater(TheBand,Input2))
				elif (Operation==SPAMATH_LESS): NewBands.append(numpy.less(TheBand,Input2))
				elif (Operation==SPAMATH_GREATER_OR_EQUAL): NewBands.append(numpy.greater_equal(TheBand,Input2))
				elif (Operation==SPAMATH_LESS_OR_EQUAL): NewBands.append(numpy.less_equal(TheBand,Input2))
				elif (Operation==SPAMATH_AND): NewBands.append(numpy.logical_and(TheBand,Input2))
				elif (Operation==SPAMATH_OR): NewBands.append(numpy.logical_or(TheBand,Input2))
				elif (Operation==SPAMATH_NOT): NewBands.append(numpy.logical_not(TheBand))
				elif (Operation==SPAMATH_ROUND): NewBands.append(numpy.around(TheBand,Input2))
				elif (Operation==SPAMATH_ROUND_INTEGER): NewBands.append(numpy.rint(TheBand))
				elif (Operation==SPAMATH_ROUND_FIX): NewBands.append(numpy.fix(TheBand))
				elif (Operation==SPAMATH_ROUND_FLOOR): NewBands.append(numpy.floor(TheBand))
				elif (Operation==SPAMATH_ROUND_CEIL): NewBands.append(numpy.ceil(TheBand))
				elif (Operation==SPAMATH_ROUND_TRUNC): NewBands.append(numpy.trunc(TheBand))
				elif (Operation==SPAMATH_NATURAL_LOG): NewBands.append(numpy.log(TheBand))
				elif (Operation==SPAMATH_LOG): NewBands.append(numpy.log10(TheBand))
				elif (Operation==SPAMATH_EXPONENT): NewBands.append(numpy.exp(TheBand))
				elif (Operation==SPAMATH_POWER): NewBands.append(numpy.power(TheBand, Input2))
				elif (Operation==SPAMATH_SQUARE): NewBands.append(numpy.square(TheBand))
				elif (Operation==SPAMATH_SQUARE_ROOT): NewBands.append(numpy.sqrt(TheBand))
				elif (Operation==SPAMATH_ABSOLUTE): NewBands.append(numpy.absolute(TheBand))
				#elif (Operation==SPAMATH_CLIP_TOP): NewBands.append(numpy.clip(TheBand,0,Input2))
				#elif (Operation==SPAMATH_CLIP_BOTTOM): NewBands.append(numpy.clip(TheBand,Input2,10000))

				# if the operation resulted in a Boolean raster, convert the raster to integer and type it as byte
				if (Operation==SPAMATH_EQUAL) or (Operation==SPAMATH_NOT_EQUAL) or (Operation==SPAMATH_GREATER) or (Operation==SPAMATH_LESS) or \
				   (Operation==SPAMATH_GREATER_OR_EQUAL) or (Operation==SPAMATH_LESS_OR_EQUAL) or (Operation==SPAMATH_AND) or (Operation==SPAMATH_OR) or \
				   (Operation==SPAMATH_MAX) or (Operation==SPAMATH_MIN): 
					NewBands[BandIndex]=NewBands[BandIndex].astype(int)
					NewDataset.GDALDataType=gdal.GDT_Byte

				BandIndex+=1


		NewDataset.SetBands(NewBands)
		return(NewDataset)

	#######################################################################
	# Common math operators that are overloaded
	#######################################################################
	def __add__(self, Input2): 
		"""
		Performs pixel-wise addition of two rasters OR of one raster and a constant

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster file OR 
			a constant value as a float
		Returns:
			A SpaDatasetRaster object where the value of each cell is equal to the sum of the values 
			of the corresponding cells in each of the two inputs
		"""
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_ADD,Input2))

	def __sub__(self, Input2): 
		"""
		Performs pixel-wise subtraction of two rasters OR of one raster and a constant

		Parameters:
			Input2:A SpaDatasetRaster object OR a string representing the path to the raster file 
				OR a constant value as a float
		Returns:
			A SpaDatasetRaster object where the value of each cell is equal to the difference between 
			the provided SPRasterDatasetObject and Input2
		"""		
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_SUBTRACT,Input2))

	def __mul__(self, Input2): 
		"""
		Performs pixel-wise multiplication of two rasters OR of one raster and a constant

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster file 
			OR a constant value as a float
		Returns:
			A SpaDatasetRaster object where the value of each cell is equal to the product of the values of 
			the corresponding cells in each of the two raster dataset objects
		"""		
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_MULTIPLY,Input2))

	def __truediv__(self, Input2): 
		"""
		Performs function for pixel-wise division two rasters OR of one raster and a constant

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster file 
			OR a constant value as a float
		Returns:
			A SpaDatasetRaster object where the value of each cell is equal to the quotient 
			of the values on the corresponding cells
		"""				
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_DIVIDE,Input2))

	# Common comparison operators
	def __lt__(self, Input2): # less than
		"""
		Performs  pixel-wise comparison between two rasters OR between one raster and a constant.

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster 
			file OR a constant value as a float
		Returns:
			A SpaDatasetRaster object with values of 1 for cells where self is less than Input2 and 0 for cells where it is not
		"""				
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_LESS,Input2))

	def __le__(self, Input2): # less than or equal
		"""
		Performs  pixel-wise comparison between two rasters OR between one raster and a constant.

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster 
			file OR a constant value as a float
		Returns:
			A SpaDatasetRaster object with values of 1 for cells where self is less than or equal to Input2 and 0 for cells where it is not
		"""		
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_LESS_OR_EQUAL,Input2))

	def __eq__(self, Input2): # equal
		"""
		Performs  pixel-wise comparison between two rasters OR between one raster and a constant.

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster 
			file OR a constant value as a float
		Returns:
			A SpaDatasetRaster object with values of 1 for cells where self is equal to Input2 and 0 for cells where it is not
		"""					
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_EQUAL,Input2))

	def __ne__(self, Input2): # not equal
		"""
		Performs  pixel-wise comparison between two rasters OR between one raster and a constant.

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster 
			file OR a constant value as a float
		Returns:
			A SpaDatasetRaster object with values of 1 for cells where self is not equal to Input2
			and 0 for cells where it is not
		"""							
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_NOT_EQUAL,Input2))

	def __ge__(self, Input2): # greater than or equal
		"""
		Performs  pixel-wise comparison between two rasters OR between one raster and a constant.

		Parameters:
			Input2: A SpaDatasetRaster object OR a string representing the path to the raster 
			file OR a constant value as a float
		Returns:
			A SpaDatasetRaster object with values of 1 for cells where self is greater than or equal to 
			Input2 and 0 for cells where it is not
		"""			
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_GREATER_OR_EQUAL,Input2))

	def __gt__(self, Input2): # greater than
		"""
		Performs  pixel-wise comparison between two rasters OR between one raster and a constant.

		Parameters:
			Input2: 
			A SpaDatasetRaster object OR a string representing the path to the raster 
			file OR a constant value as a float
		Returns:
			A SpaDatasetRaster object with values of 1 for cells where self is greater than 
			Input2 and 0 for cells where it is not
		"""			
		Input1=SpaBase.GetInput(self)
		return(Input1.Math(SPAMATH_GREATER,Input2))

	# Common boolean operators (jjg boolean operators cannot be overriden in Python, we have to use And())
	#def __and__(self, Input2):# greater than 
		#"""
		#One-line function for logical operation between two boolean rasters OR between one boolean raster and a constant boolean value. The order of the parameters does not matter.

		#Parameters:
			#Input2: SpaDatasetRaster object OR a string representing the path to the raster file OR a boolean consta
		#Returns:
			#A SpaDatasetRaster object where each cell true if the corresponding cells in both inputs are true. 
		#"""			
		#Input1=SpaBase.GetInput(self)
		#return(Input1.Math(SPAMATH_AND,Input2))
	#def __or__(self, Input2): # greater than
		## need more info on function
		#"""
		#One-line function for logical operation between two boolean rasters OR between one boolean raster and a constant boolean value. The order of the parameters does not matter.

		#Parameters:
			#Input2: SpaDatasetRaster object OR a string representing the path to the raster file OR a boolean constant

		#Returns:
			#A SpaDatasetRaster object where each cell true if the corresponding cells in either inputs are true. 
		#"""				
		#Input1=SpaBase.GetInput(self)
		#return(Input1.Math(SPAMATH_OR,Input2))

	#def __inv__(self, Input2): # greater than
		## need more info
		#"""
		#Returns with a SpaDatasetRaster object containing only values...
		#Parameters:
			#Input2: A SpaDatasetRaster object OR a string representing the path to the raster file OR a constant value as a float
		#Returns:
			#A SpaDatasetRaster object
		#"""			
		#Input1=SpaBase.GetInput(self)
		#return(Input1.Math(SPAMATH_NOT,Input2))

	#######################################################################
	# 
	#######################################################################
	def Reclassify(self,InputClasses,OutputClasses,mode):
		"""
		Reclassify a raster dataset using numpy

		Parameters:
			InputClasses: if the mode is "discrete" then the InputClasses is a simple array that includes
			values that will be set to their matching values in OutputClasses[].
			If the mode is "range", then the InputClasses contains an array of arrays where each secondary
			array contains a minimum and maximum value for each range that will be reclassed to its
			corresponding OutputClass.
			OutputClasses: An array of values for the reclassed pixels.
			mode: The format of the values which will be used for reclassification (either range or discrete)

		Returns:
			A SpaRasterDataset object reclassified to the parameters outlined in mode
		"""

		NewDataset=None
		
		#if mode=="discrete":
			#NewDataset = SpaDatasetRaster()
			#NewDataset = self.Clone()
			#NewBands=[]
			#condlist=[]
			#choicelist=[]
			
			#for TheBand in self.TheBands:
				#for cond in InputClasses:
					#condlist.append(TheBand==cond)
				#for choice in OutputClasses:
					#choicelist.append(numpy.ones_like(TheBand)*choice)
				#NewBand=numpy.select(condlist,choicelist)
				#NewBands.append(NewBand)
				
			#NewDataset.SetBands(NewBands)

		#elif mode=="range":
		NewDataset = SpaDatasetRaster()
		NewDataset = self.Clone()
		NewBands=[]
		TheMask=self.TheMask
		
		# If the user specified None for an output value, we need to add those pixels to the raster's mask
		TheBand=self.TheBands[0]
			
		Index=0
		while (Index<len(InputClasses)):
			
			OutputValue=OutputClasses[Index]
			
			if (OutputValue is None):
				Range=InputClasses[Index]
				
				if mode=="discrete":
					# Get an array with 1s where pixels are within the range and 0s otherwise
					BooleanArray=(TheBand==Range)
				else:
					# Get an array with 1s where pixels are within the range and 0s otherwise
					BooleanArray=numpy.logical_and(TheBand>Range[0],TheBand<=Range[1])
			
				# Or in any new pixels that should be added as NoData
				if (TheMask is not None):
					TheMask=numpy.logical_or(BooleanArray,TheMask)
				else:
					TheMask=BooleanArray
					
			Index+=1
			
		# Reclassify the bands
		for TheBand in self.TheBands:
			
			# For each input class, replace the pixels within the range with the matching output value
			Index=0
			while (Index<len(InputClasses)):
				Range=InputClasses[Index]
			
				OutputValue=OutputClasses[Index]
				
				# If the output value is None, mask the desired pixels, otherwise, convert the desired pixels to the output value
				if (OutputValue is not None):
					
					if mode=="discrete":
						# Get an array with 1s where pixels are within the range and 0s otherwise
						BooleanArray=(TheBand==Range)
					else:
						BooleanArray=numpy.logical_and(TheBand>Range[0],TheBand<=Range[1])
					
					TheBand=numpy.where(BooleanArray,OutputValue,TheBand) # removes the mask!
					
				Index+=1
			
			NewBands.append(TheBand)
			
		NewDataset.SetBands(NewBands)
		NewDataset.SetMask(TheMask)
		
		return(NewDataset)

#######################################################################
# additional core transforms
#######################################################################

class SpaResample(SpaBase.SpaTransform):
	"""
	Abstract class to define projectors
	"""
	def __init__(self):
		super().__init__()

		self.SetSettings(Resample,{
			"RowRate":10,
			"ColumnRate":10,
		})

	def Crop(Self,InputRasterDataset,Bounds):
		"""
		Crops a raster to a specified extent
		Parameters:
			InputRasterDataset: A SpaDatasetRaster object OR a string representing the path to the raster file
			Bounds: new extent formatted as [x1,y1,x2,y2] 
		Return:
			A cropped SpaRasterDataset object 

		"""
		NewDataset=SpaDatasetRaster()
		NewDataset.CopyPropertiesButNotData(InputRasterDataset)

		GDALDataset = InputRasterDataset.GDALDataset
		
		# Format for the bounds for gdal is [ulx uly lrx lry] which is [xmin,ymax,xmax,ymin]
		NewBounds=[Bounds[0],Bounds[3],Bounds[2],Bounds[1]] 
		
		GDALDataset = gdal.Translate('', GDALDataset, format="MEM", projWin = NewBounds)
		NewDataset.Load(GDALDataset)
		GDALDataset = None
		
		return(NewDataset)

	def NumpyCrop(self,InputRasterDataset,Bounds):
		"""
		Crops a raster using extract by pixel
		Parameters:
			InputRasterDataset: A SpaDatasetRaster object
			Bounds: A list representing UpperLeftX, UpperLeftY, LowerRightX, and LowerRightY coordinates, in map units.
		Returns:
			A SpaDatsetRasterObject
		"""
		NewDataset=SpaDatasetRaster()
		NewDataset.CopyPropertiesButNotData(InputRasterDataset)

		UpperLeftRefX=Bounds[0]
		UpperLeftRefY=Bounds[3]
		LowerRightRefX=Bounds[2]
		LowerRightRefY=Bounds[1]

		UpperLeftPixelX=InputRasterDataset.GetPixelXFromRefX(UpperLeftRefX)
		UpperLeftPixelY=InputRasterDataset.GetPixelYFromRefY(UpperLeftRefY)
		LowerRightPixelX=InputRasterDataset.GetPixelXFromRefX(LowerRightRefX)
		LowerRightPixelY=InputRasterDataset.GetPixelYFromRefY(LowerRightRefY)

		NewDataset = self.ExtractByPixels(InputRasterDataset, UpperLeftPixelX, UpperLeftPixelY, LowerRightPixelX, LowerRightPixelY)

		return(NewDataset)

	def Scale(self,InputRasterDataset,ZoomFactor,order=3):
		"""
		Resamples the raster based on the specified ZoomFactor.
		This appears to work well.
		Parameters:
			InputRasterDataset: A SpaDatasetRaster object OR a string representing the path to the raster file
			ZoomFactor: 
		Return:
			A SpaRasterDataset object scaled to the specified extent
		"""
		#check to see if input is a str or a SpaDatasetRaster object

		InputRasterDataset = SpaBase.GetInput(InputRasterDataset)

		OutputDataset=SpaDatasetRaster()
		OutputDataset.CopyPropertiesButNotData(InputRasterDataset)

		OutputBands=[]
		InputBands=InputRasterDataset.GetBands()

		NumBands=OutputDataset.GetNumBands()

		OutputDataset.PixelHeight=InputRasterDataset.PixelHeight/ZoomFactor
		OutputDataset.PixelWidth=InputRasterDataset.PixelWidth/ZoomFactor

		# go through each of the rows in the output raster sampling data from the input rows
		BandIndex=0
		while (BandIndex<NumBands):

			InputBand=InputBands[BandIndex]

			#OutputBand=scipy.ndimage.zoom(InputBand, ZoomFactor, order=order, mode='constant', cval=0.0, prefilter=True)
			# jjg - we need another way to deal with no data values - convert them to zeros on load and then convert back on save?
			super_threshold_indices = InputBand<0.00000001
			InputBand[super_threshold_indices] = 0
			OutputBand=scipy.ndimage.zoom(InputBand, ZoomFactor)

							 
			OutputBands.append(OutputBand)

			OutputDataset.HeightInPixels=numpy.size(OutputBand,0)
			OutputDataset.WidthInPixels=numpy.size(OutputBand,1)

			BandIndex+=1

		# add the new band to the output dataset
		OutputDataset.TheBands=OutputBands

		# the zoom function strips off the mask and returns a regular numpy array so we have to get the mask, zoom it, and put it back
		TheMask = InputRasterDataset.TheMask
		if (TheMask is not None):
			OutputMask = scipy.ndimage.zoom(TheMask,ZoomFactor,order=1,mode='nearest') # Must be order=1 for boolean values
#			OutputMask = scipy.ndimage.zoom(TheMask,ZoomFactor,output=None,order=order,cval=0.0,prefilter=True)
			OutputDataset.TheMask=OutputMask
		else: 
			OutputDataset.TheMask=None

		return(OutputDataset)

	def ExtractByPixels(self,InputRasterDataset,StartColumn,StartRow,EndColumn,EndRow):
		"""
		Extracts a portion of the raster image using pixel locations.

		Parameters:
			InputRasterDataset: 
				A SpaDatasetRaster object OR a string representing the path to the raster file
			StartColumn: 
				input first column of input raster to be extracted into new layer
			StartRow: 
				input first row of input raster to be extracted into new layer
			EndColumn: 
				input last column of input raster to be extracted inot new layer
			EndRow: 
				input last column of input raster to be extracted into new layer
		Returns:
		        A SpaRastserDataset object extracted to the outlined extent
		"""
		OutputDataset=SpaDatasetRaster()
		OutputDataset.CopyPropertiesButNotData(InputRasterDataset)

		OutputBands=[]
		InputBands=InputRasterDataset.GetBands()

		OutputDataset.HeightInPixels=EndRow-StartRow+1
		OutputDataset.WidthInPixels=EndColumn-StartColumn+1

		OutputDataset.XMin=OutputDataset.XMin+(StartColumn*OutputDataset.PixelWidth)
		OutputDataset.YMax=OutputDataset.YMax+(StartRow*OutputDataset.PixelHeight)

		NumBands=OutputDataset.GetNumBands()

		# go through each of the rows in the output raster sampling data from the input rows
		BandIndex=0
		while (BandIndex<NumBands):

			InputBand=InputBands[BandIndex]

			OutputBand=InputBand[StartRow:EndRow+1,StartColumn:EndColumn+1]

			OutputBands.append(OutputBand)

			BandIndex+=1

		# add the new band to the output dataset
		OutputDataset.TheBands=OutputBands

		return(OutputDataset)

	def NearestNeighbor(self,InputRasterDataset):
		"""
		Creates a sampled version of the specified raster
		This uses NumPy arrays with Python to sample pixel by
		pixel and is really slow.

		Parameters:
			InputRasterDataset: 
				A SpaDatasetRaster object OR a string representing the path to the raster file
		Returns:
			A SpaDatasetRaster resampled using Nearest Neighbor resampling method
		"""
		#check to see if input is a str or a SpaDatasetRaster object

		InputRasterDataset = SpaBase.GetInput(InputRasterDataset)

		OutputDataset=SpaDatasetRaster()
		OutputDataset.CopyPropertiesButNotData(InputRasterDataset)

		NumPyType=OutputDataset.GetNumPyType()

		# get information from the rasters
		InputWidthInPixels=InputRasterDataset.GetWidthInPixels()
		InputHeightInPixels=InputRasterDataset.GetHeightInPixels()

		# get settings
		TheSettings=self.GetSettings(Resample)
		RowRate=TheSettings["RowRate"]
		ColumnRate=TheSettings["ColumnRate"]

		# these will move to settings

		OutputRowStart=0
		OutputColumnStart=0

		InputColumnStart=0
		InputRowStart=0

		# can specify either a sample rate or a width and height in pixels for the output
		# below is specifying the sample rate

		OutputRowEnd=math.floor(InputHeightInPixels/RowRate)
		OutputColumnEnd=math.floor(InputWidthInPixels/ColumnRate)

		OutputDataset.HeightInPixels=OutputRowEnd
		OutputDataset.WidthInPixels=OutputColumnEnd

		# Need to call this function to resample the mask
		OutputMask=None
		InputMask=None

		# output the output bands
		OutputBands=[]
		InputBands=InputRasterDataset.GetBands()

		NumBands=OutputDataset.GetNumBands()

		# go through each of the rows in the output raster sampling data from the input rows
		BandIndex=0
		while (BandIndex<NumBands):

			OutputBands.append(numpy.zeros((OutputDataset.HeightInPixels,OutputDataset.WidthInPixels), dtype=NumPyType))

			BandIndex+=1

		# go through each row sampling data
		OutputRowIndex=OutputRowStart
		while (OutputRowIndex<OutputRowEnd):

			print("Processing row "+format(OutputRowIndex))

			# find the row in the input to get a sample for the output
			InputRowIndex=math.floor(OutputRowIndex*RowRate+InputRowStart)

			if ((InputRowIndex>=0) and (InputRowIndex<InputHeightInPixels)):

				OutputColumnIndex=OutputColumnStart
				while (OutputColumnIndex<OutputColumnEnd):

					InputColumnIndex=math.floor(OutputColumnIndex*ColumnRate+InputColumnStart)

					# Copy each of pixels into the input raster from the nearest output raster pixel
					if ((InputColumnIndex>=0) and (InputColumnIndex<InputWidthInPixels)):

						# only copy the data if there is no mask or the mask pixel is non-zero
						if ((InputMask is None) or (InputMask[InputRowIndex][InputColumnIndex]!=0)):

							# if there is a mask, set it to opaque
							if (OutputMask is not None):

								TheOutputMask[OutputRowIndex][OutputColumnIndex]=100

							BandIndex=0
							while (BandIndex<NumBands):
								OutputBand=OutputBands[BandIndex]
								InputBand=InputBands[BandIndex]

								OutputBand[OutputRowIndex][OutputColumnIndex]=InputBand[InputRowIndex][InputColumnIndex]

								BandIndex+=1

					OutputColumnIndex+=1

			OutputRowIndex+=1

		# add the new band to the output dataset
		OutputDataset.TheBands=OutputBands

		return(OutputDataset)

############################################################################################
# One-line functions
############################################################################################
def Load(Path1):

	TheDataset=SpaDatasetRaster()
	TheDataset.Load(Path1)
	return(TheDataset)

def Resample(Input1, ZoomFactor):
	"""
	Resamples a raster based based on a specific zoom factor

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file

		ZoomFactor: A float representing the resample rate. Values <1 will 'zoom in', values >1 will 'zoom out'

	Returns:
		A SpaDatasetRaster object resampled to the given parameters

	"""
	Input1=SpaBase.GetInput(Input1)
	TheResampler=SpaResample()
	return(TheResampler.Scale(Input1, ZoomFactor))

def ReclassifyDiscrete(Input1,InputClasses,OutputClasses):
	"""
	Resamples a raster into classes which represent a discrete set of values

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file

		Input classes: A discrete set of values ex:(10,20,30)

		Output classes: The desired classes ex:(1,2,3)

	Returns:
		A SpaDatasetRaster object

	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Reclassify(InputClasses,OutputClasses,"discrete"))

def ReclassifyRange(Input1,InputClasses,OutputClasses):

	"""
	Resamples a raster into classes which represent a range of values

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file

		Input classes: the range of values to be reclassified ex:[(-1000,1),(1,3),(3,10000)]

		Output classes: The desired classes  ex:(1,2,3)
	Returns:
		A SpaDatasetRaster object

	"""		
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Reclassify(InputClasses,OutputClasses,"range"))

def Crop(Input1,Bounds):
	"""
	Crops a raster to a specified extent using gdal.Translate()

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file

		Bounds: The desired extent formatted as [x1,y1,x2,y2]
	Returns:
		A SpaDatasetRaster object
	"""
	Input1=SpaBase.GetInput(Input1)
	TheResampler=SpaResample()
	return(TheResampler.Crop(Input1,Bounds))

def NumpyCrop(Input1,Bounds):
	"""
	Crops a raster to a specified extent without using gdal

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file

		Bounds: The desired extent formatted as [x1,y1,x2,y2]
	Returns:
		A SpaDatasetRaster object
	"""
	Input1=SpaBase.GetInput(Input1)
	TheResampler=SpaResample()
	return(TheResampler.NumpyCrop(Input1,Bounds))

############################################################################
# Constants
############################################################################
# Basic Arithmatic
SPAMATH_ADD=1
SPAMATH_SUBTRACT=2
SPAMATH_MULTIPLY=3
SPAMATH_DIVIDE=4

# Rounding
SPAMATH_ROUND=100
SPAMATH_ROUND_INTEGER=101
SPAMATH_ROUND_FIX=102
SPAMATH_ROUND_FLOOR=103
SPAMATH_ROUND_CEIL=104
SPAMATH_ROUND_TRUNC=105

# Logical
SPAMATH_AND=201
SPAMATH_OR=202
SPAMATH_NOT=203
SPAMATH_LESS=204
SPAMATH_LESS_OR_EQUAL=205
SPAMATH_EQUAL=206
SPAMATH_NOT_EQUAL=207
SPAMATH_GREATER=208
SPAMATH_GREATER_OR_EQUAL=209

# Othermath
SPAMATH_NATURAL_LOG=300
SPAMATH_LOG=301
SPAMATH_EXPONENT=302
SPAMATH_SQUARE=303
SPAMATH_SQUARE_ROOT=304
SPAMATH_ABSOLUTE=305
SPAMATH_MAX=306
SPAMATH_MIN=307
SPAMATH_POWER=309
SPAMATH_CLIP_TOP=308
SPAMATH_CLIP_BOTTOM=309
# Trig

#######################################################################
# one line raster transforms
#######################################################################

#######################################################################
# Basic math
def Add(Input1,Input2):
	"""
	Performs pixel-wise addition of two rasters OR of one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object where the value of each cell is equal to the sum of the values of the corresponding cells in each of the two inputs.
	"""
	#allows for parameters to be in any order
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1 #switches the values of Input1 and Input2

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ADD,Input2))

def Subtract(Input1,Input2):
	"""
	One-line function for pixel-wise subtraction of two rasters OR of one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object where the value of each cell is equal to the difference of the values of the corresponding cells in each of the two inputs.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1 

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_SUBTRACT,Input2))

def Multiply(Input1,Input2):
	"""
	One-line function for pixel-wise multiplication of two rasters OR of one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object where the value of each cell is equal to the product of the values of the corresponding cells in each of the two inputs.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_MULTIPLY,Input2))

def Divide(Input1,Input2):
	"""
	One-line function for pixel-wise division two rasters OR of one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object where the value of each cell is equal to the quotient of the values on the corresponding cells in each of the two inputs.
	"""
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_DIVIDE,Input2))


#######################################################################
# Logical
def Equal(Input1,Input2):
	"""
	One-line function for pixel-wise comparison between two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object with values of 1 for cells where Input1 is equal to Input2 and 0 for cells where it is not.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_EQUAL,Input2))

def NotEqual(Input1,Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object with values of 1 for cells where Input1 is not equal to Input2 and 0 for cells where it is.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1    
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_NOT_EQUAL,Input2))


def LessThan(Input1,Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object with values of 1 for cells where Input1 is less than Input2 and 0 for cells where it is not.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1 

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_LESS,Input2))

def GreaterThan(Input1,Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object with values of 1 for cells where Input1 is greater than Input2 and 0 for cells where it is not
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_GREATER,Input2))

def LessThanOrEqual(Input1,Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object with values of 1 for cells where Input1 is less than or equal to Input2 and 0 for cells where it is not.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_LESS_OR_EQUAL,Input2))

def GreaterThanOrEqual(Input1,Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object with values of 1 for cells where Input1 is greater than or equal to Input2 and 0 for cells where it is not.
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_GREATER_OR_EQUAL,Input2))


def Maximum(Input1, Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: A SpaDatasetRaster object OR a string represening the path to the raster file.

		Input2: Same as above OR a constant value as an integer or a float.

	Returns
		A SpaDatasetRaster object where each cell is equal to the greater value of the corresponding cells in each of the two inputs
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1    
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_MAX,Input2))

def Minimum(Input1, Input2):
	"""
	One-line function for pixel-wise comparison of two rasters OR between one raster and a constant. The order of the parameters does not matter.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

		Input2: SpaDatasetRaster object OR a string representing the path to the raster file OR a number as a float.

	Returns
		A SpaDatasetRaster object where each cell is equal to lesser of the corresponding cells in each of the two inputs
	"""	
	if isinstance(Input1,(int,float)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_MIN,Input2))

def And(Input1,Input2):
	"""
	One-line function for logical operation between two boolean rasters OR between one boolean raster and a constant boolean value. The order of the parameters does not matter.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

		Input2: Same as above, or a boolean or an int.

	Returns
		A SpaDatasetRaster object where each cell true if the corresponding cells in both inputs are true. 
	"""	
	if isinstance(Input1,(bool,int)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_AND,Input2))

def Or(Input1,Input2):
	"""
	One-line function for logical operation between two boolean rasters OR between one boolean raster and a constant boolean value. The order of the parameters does not matter.

	Parameters:
	    Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

		Input2: Same as above, or a boolean or an int.

	Returns
		A SpaDatasetRaster object where each cell true if the corresponding cells in either inputs are true. 
	"""	
	if isinstance(Input1,(bool,int)):
		Input1, Input2 = Input2, Input1

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_OR,Input2))

def Not(Input1):
	"""
	One-line function for logical operation between two boolean rasters OR between one boolean raster and a constant boolean value. The order of the parameters does not matter.

	Parameters:
	    Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

		Input2: Same as above, or a boolean or an int.

	Returns
		A SpaDatasetRaster object where each cell has the opposite value of the input. 
	"""	  

	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_NOT,0))


#######################################################################
# Rounding
def Round(Input1, Precision):
	"""
	One-line function for rounding a raster to a specified precision.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.
		Precision: An integer representing the number of decimal places to be rounded too (dafualt = 0)
	Returns
		A SpaDatasetRaster object where each cell has been rounded to the specified degree of precision.
	"""		
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ROUND, Precision))

def RoundInteger(Input1):
	"""
	One-line function for rounding a raster. 

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object where each cell has been rounded to the nearest integer.
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ROUND_INTEGER,0))

def RoundFix(Input1):
	"""
	One-line function for rounding a raster 

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object where each cell has been rounded to the nearest integer torwards zero.
	"""		
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ROUND_FIX,0))
def RoundFloor(Input1):
	"""
	One-line function for rounding a raster 

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object where each cell has been rounded to the nearest integer less than or equal to the input.
	"""		
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ROUND_FLOOR,0))
def RoundCeiling(Input1):
	"""
	One-line function for rounding a raster 

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object where each cell has been rounded to the nearest integer greater than or equal to the input.
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ROUND_CEIL,0))
def Truncate(Input1):
	"""
	One-line function for rounding a raster 

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object where the decimal portion of the input has been discarded	
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ROUND_TRUNC,0))

#######################################################################
#Unary Math

def NaturalLog(Input1):
	"""
	Computes the natural logarithm of a raster.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_NATURAL_LOG,0))

def Log(Input1):
	"""
	Computes the base ten logarithm of a raster.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_NATURAL_LOG,0))

def Exponential(Input1):
	"""
	Computes the exponential of a raster.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_EXPONENT,0))

def Power(Input1, Power):
	"""
	Raises the raster to the specified power.

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

		Power: The power to be raised to, as a float (or integer)

	Returns
		A SpaDatasetRaster object
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_POWER, Power))

def Square(Input1):
	"""
	Computes the square of a raster

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns
		A SpaDatasetRaster object
	"""
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_SQUARE,0))

def SquareRoot(Input1):
	"""
	Computes the square root of a raster

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns:
		A SpaDatasetRaster object
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_SQUARE_ROOT,0))

def AbsoluteValue(Input1):
	"""
	Computes the absolute value of a raster

	Parameters:
		Input1: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns:
		A SpaDatasetRaster object
	"""	
	Input1=SpaBase.GetInput(Input1)
	return(Input1.Math(SPAMATH_ABSOLUTE,0))
####################################################################
# Public utility functions
####################################################################
def ResampleToMatch(TheDataset1,TheDataset2):
	"""
	Resamples the specified datasets to create rasters that have the same pixel and
	reference bounds as each other.  This function is typically used to prepare rasters
	for raster math.  The bounds will be the area of overlap of the two rasters while 
	the pixel dimensions will be the lower resolution of the two.

	Parameters:
		TheDataset1: SpaDatasetRaster object OR a string representing the path to the raster file.
		TheDataset2: SpaDatasetRaster object OR a string representing the path to the raster file.

	Returns:
		A tuple with two SpaDatasetRaster objects ordered as (NewData1,NewData2)
	"""
	TheDataset1=SpaBase.GetInput(TheDataset1)
	TheDataset2=SpaBase.GetInput(TheDataset2)
	
	Resolution1=TheDataset1.GetResolution()
	TheBounds1=TheDataset1.GetBounds()  
	
	#TheDataset2=SpaRasters.SpaDatasetRaster()  
	#TheDataset2.Load(RasterFilePath2)      
	
	Resolution2=TheDataset2.GetResolution()
	TheBounds2=TheDataset2.GetBounds()  
	
	# make sure the two rasters represent the same spatial area
	if (TheBounds1!=TheBounds2):
		XMin=TheBounds1[0]
		YMin=TheBounds1[1]
		XMax=TheBounds1[2]
		YMax=TheBounds1[3]
		
		if (TheBounds2[0]>XMin): XMin=TheBounds2[0]
		if (TheBounds2[1]>YMin): YMin=TheBounds2[1]
		if (TheBounds2[2]<XMax): XMax=TheBounds2[2]
		if (TheBounds2[3]<YMax): YMax=TheBounds2[3]
		
		TheBounds=[XMin,YMin,XMax,YMax]
		
		TheDataset1=Crop(TheDataset1,TheBounds)
		TheDataset2=Crop(TheDataset2,TheBounds)
		
		#print("Width in pixels: "+format(TheDataset1.GetWidthInPixels())) 
		#print("Height in pixels: "+format(TheDataset1.GetHeightInPixels())) 
		
		#print("Width in pixels: "+format(TheDataset2.GetWidthInPixels())) 
		#print("Height in pixels: "+format(TheDataset2.GetHeightInPixels())) 
		
	# Make sure the rasters have the same resolution
	Resolution1=Resolution1[0]
	Resolution2=Resolution2[0]
	
	if (Resolution1<Resolution2): 
		TheDataset2=Resample(TheDataset2,Resolution2/Resolution1)
	elif (Resolution1>Resolution2): 
		TheDataset1=Resample(TheDataset1,Resolution1/Resolution2)
	
	# Make sure the masks only cover areas that are masked in both rasters
	#if (TheDataset1.TheMask is not None):
		#if (TheDataset2.TheMask is not None): # both have masks, combine them
			
			#TheDataset1.TheMask=numpy.logical_or(TheDataset1.TheMask,TheDataset2.TheMask)
			#TheDataset2.TheMask=numpy.copy(TheDataset1.TheMask)
		
		#else: # Only TheDataset1 has a mask
			#TheDataset2.TheMask=numpy.copy(TheDataset1.TheMask)
	
	#elif (TheDataset2.TheMask is not None):
		#TheDataset1.TheMask=numpy.copy(TheDataset2.TheMask)
		
	#print("Width in pixels: "+format(TheDataset1.GetWidthInPixels())) 
	#print("Height in pixels: "+format(TheDataset1.GetHeightInPixels())) 
	
	#print("Width in pixels: "+format(TheDataset2.GetWidthInPixels())) 
	#print("Height in pixels: "+format(TheDataset2.GetHeightInPixels())) 

	return(TheDataset1,TheDataset2)

def Merge(InputFilePath1,InputFilePath2,OutputFilePath):
	"""
	Merges two rasters.
	Parameters:
		InputRasterDataset: A SpaDatasetRaster object OR a string representing the path to the raster file
		Bounds: new extent formatted as [x1,y1,x2,y2] 
	Return:
		A cropped SpaRasterDataset object 

	"""
	
	args=[]
	args.append("") # First entry is call to python
	args.append("-o")
	args.append(OutputFilePath)
	args.append(InputFilePath1)
	args.append(InputFilePath2)
	
	gdal_merge.main(args)
