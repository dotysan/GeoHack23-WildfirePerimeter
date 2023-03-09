############################################################################
# Raster Test File for the Spatial (Spa) libraries.  This script will test most of the features
# of SpaRaster.py and add a bunch of files to the "Temp" folder.
#
# Copyright (C) 2023, Humboldt State University, Jim Graham
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
import webbrowser

# Open source spatial libraries
from osgeo import gdal

from SpaTestUtil import *
# Spa Libraries

from SpaPy import SpaPlot
from SpaPy import SpaView
from SpaPy import SpaRasters
from SpaPy import SpaTopo
from SpaPy import SpaRasterVectors

############################################################################
# Globals
############################################################################

StHelensPreEruption="../Data/MtStHelens/Mt St Helens PreEruption DEM Float32.tif"

StHelensPostEruption="../Data/MtStHelens/Mt St Helens Post Eruption DEM Float32.tif"

NASAFilePath="../Data/NASA/BlueMarbleNG-TB_2004-12-01_rgb_1440x720.TIFF"

OutputFolderPath="../Temp/Rasters/"
TempFolderPath=OutputFolderPath

SetupOutputFolder(OutputFolderPath)
TheHTMLFile=None
HTMLOpen(OutputFolderPath+"_SpaRasterTest.html")
HTMLHeading("Spa Referencing Test")

#########################################################################
# Raster opterations
#########################################################################

HTMLHeading("RGB Raster Info")

TheDataset =SpaRasters.SpaDatasetRaster()
TheDataset.Load(NASAFilePath)

print("____________________________________")
HTMLParagraph("Loading Raster: "+StHelensPreEruption)

HTMLParagraph(format(TheDataset.GetDriverNames()))

HTMLParagraph("Width in pixels: "+format(TheDataset.GetWidthInPixels()))

HTMLParagraph("Height in pixels: "+format(TheDataset.GetHeightInPixels()))

HTMLParagraph("Pixel Type: "+format(TheDataset.GetType()))

#print("CRS:"+format(TheDataset.GetCRS())) # returns a WKT string

TheBounds=TheDataset.GetBounds()
HTMLParagraph("TheBounds="+format(TheBounds))

TheBand=TheDataset.GetBandInfo(1) # band numbers start at 1
HTMLParagraph("TheBandInfo="+format(TheBand))

MinMax=TheDataset.GetMinMax(0)
HTMLParagraph("Min="+format(MinMax[0])+" Max="+format(MinMax[1]))

Histogram=TheDataset.GetHistogram()
HTMLParagraph("Histogram="+format(Histogram))

#######################################################################
#
HTMLHeading("Merging")

SpaRasters.Merge(StHelensPostEruption,"../Data/Cropped.tif",OutputFolderPath+"Merged.tif")
TheDataset=SpaRasters.SpaDatasetRaster()
TheDataset.Load(OutputFolderPath+"Merged.tif")
HTMLRenderDataset(TheDataset,OutputFolderPath,"Merged.png")

#######################################################################
#
HTMLHeading("Masks")

HTMLHeading("Mt St Helens with masked pixels replaced by 2000",2)
TheDataset=SpaRasters.SpaDatasetRaster()
TheDataset.Load(StHelensPostEruption)
TheDataset.SetMask(None,2000)
TheDataset.Save(OutputFolderPath +"StHelensPostEruption_NoMask.tif")
HTMLRenderDataset(TheDataset,OutputFolderPath,"StHelensPostEruption_NoMask.png")

#######################################################################
# Get information on an existing raster and save it to a new name
	
# test reclassify
if (True):
	HTMLHeading("Reclassed",1)
	
	TheDataset=SpaRasters.SpaDatasetRaster()
	TheDataset.Load(StHelensPreEruption)
	TheDataset.Save(OutputFolderPath +"StHelensPreEruption.tif")
	
	TheDataset=SpaRasters.SpaDatasetRaster()
	TheDataset.Load(StHelensPostEruption)
	TheDataset.Save(OutputFolderPath +"StHelensPostEruption.tif")
	
	HTMLHeading("Reclassed",2)
	ReclassedDataset=SpaRasters.ReclassifyRange(StHelensPreEruption,[(0,1000),(1000,2000),(2000,3000)],[100,200,255])
	ReclassedDataset.Save(TempFolderPath + "Reclassed.tif")
	HTMLRenderDataset(ReclassedDataset,OutputFolderPath,"Reclassed.png")
	MinMax=ReclassedDataset.GetMinMax(0)
	HTMLParagraph("Min="+format(MinMax[0])+" Max="+format(MinMax[1]))

	HTMLHeading("ReclassedMask",2)
	ReclassedDataset=SpaRasters.ReclassifyRange(StHelensPreEruption,[(-1,1000),(1000,2000),(2000,3000)],[None,200,255])
	ReclassedDataset.Save(TempFolderPath + "ReclassedMask.tif")
	HTMLRenderDataset(ReclassedDataset,OutputFolderPath,"ReclassedMask.png")
	
	MinMax=ReclassedDataset.GetMinMax(0)
	HTMLParagraph("Min="+format(MinMax[0])+" Max="+format(MinMax[1]))

if (True): #for toggling code on/off for debugging

	HTMLHeading("DEM Raster Info")

	TheDataset =SpaRasters.SpaDatasetRaster()
	TheDataset.Load(StHelensPreEruption)

	print("____________________________________")
	print("Loading Raster: "+StHelensPreEruption)

	print(TheDataset.GetDriverNames())

	#TheGDALDataset=TheDataset.GetGDALDataset()
	
	#print(TheGDALDataset.GetMetadata()) # empty

	print("Width in pixels: "+format(TheDataset.GetWidthInPixels()))

	print("Height in pixels: "+format(TheDataset.GetHeightInPixels()))

	print("Num Bands: "+format(TheDataset.GetNumBands()))

	print("Pixel Type: "+format(TheDataset.GetType()))

	print("Projection: "+format(TheDataset.GetCRS()))

	print("Resolution (x,y): "+format(TheDataset.GetResolution()))

	TheBounds=TheDataset.GetBounds()
	print("TheBounds (XMin,YMin,YMax,XMax): "+format(TheBounds))

	TheBandStats=TheDataset.GetBandInfo(1)
	print("TheBandStats="+format(TheBandStats))

	TheBand=TheDataset.GetBand(0)
	print("TheBands: "+format(TheBand))

	TheDataset.Save(TempFolderPath+"CopiedRaster.tif")

#######################################################################
#SpaPlot.PlotRasterHistogram(TheDataset)
TheDataset=SpaRasters.SpaDatasetRaster()
TheDataset.Load(StHelensPreEruption)

TheDataset2=SpaRasters.SpaDatasetRaster()
TheDataset2.Load(StHelensPostEruption)

#SpaPlot.PlotRasterHistogram(TheDataset)
#SpaPlot.PlotRasterHistogram(TheDataset2)

TheDataset,TheDataset2=SpaRasters.ResampleToMatch(TheDataset,TheDataset2)
#SpaPlot.PlotRasterHistogram(TheDataset)
#SpaPlot.PlotRasterHistogram(TheDataset2)

if (True):
	TheDataset.Save(TempFolderPath+"TheDataset.tif")
	TheDataset2.Save(TempFolderPath+"TheDataset2.tif")

	Difference=SpaRasters.Subtract(TheDataset,TheDataset2)
	Difference.Save(TempFolderPath+"Difference.tif")

	Difference=TheDataset-TheDataset2
	Difference.Save(TempFolderPath+"Difference2.tif")

	#SpaView.Show(Difference)
	#SpaPlot.PlotRasterHistogram(Difference)

#######################################################################
# Test writing out a new raster

if (True):
	HTMLHeading("New Raster")

	WidthInPixels=100
	HeightInPixels=100

	TheDataset=SpaRasters.SpaDatasetRaster()
	TheDataset.SetWidthInPixels(WidthInPixels)
	TheDataset.SetHeightInPixels(HeightInPixels)
	TheDataset.SetType(gdal.GDT_Float32)

	TheBands=TheDataset.AllocateArray()
	TheBands=TheBands[0]

	Row=0
	while (Row<HeightInPixels):
		Column=0
		while (Column<WidthInPixels):
			TheBands[Row][Column]=Column
			Column+=1
		Row+=1
	print(TheBands)

	TheDataset.SetUTM(10)
	TheDataset.SetNorthWestCorner(400000,4000000)
	TheDataset.SetResolution(30,30)
	TheDataset.Save(TempFolderPath+"NewRaster.tif")

#######################################################################
# Transform an existing raster
HTMLHeading("Transforms")

# Clone
if (True):
	TheDataset=SpaRasters.SpaDatasetRaster()
	TheDataset.Load(StHelensPostEruption)
	NewDataset=TheDataset.Clone()
	NewDataset.Save(TempFolderPath+"ClonedRaster.tif")

	#SpaPlot.PlotRasterHistogram(NewDataset,"Original Raster")

# Basic Math
if (True):
	HTMLHeading("Raster_Add10",2)

	NewDataset=SpaRasters.Add(TheDataset,10)
	NewDataset.Save(TempFolderPath+"Raster_Add10.tif")

	#SpaPlot.PlotRasterHistogram(NewDataset,"Original Raster Plus 10")

	HTMLHeading("Raster_SUBTRACT10",2)

	NewDataset=SpaRasters.Subtract(TheDataset,10)
	NewDataset.Save(TempFolderPath+"Raster_SUBTRACT10.tif")

	#SpaPlot.PlotRasterHistogram(NewDataset,"Original Raster Minus 10")

	HTMLHeading("Raster_MULTIPLY_10",2)

	NewDataset=SpaRasters.Multiply(TheDataset,10)
	NewDataset.Save(TempFolderPath+"Raster_MULTIPLY_10.tif")

	#SpaPlot.PlotRasterHistogram(NewDataset,"Original Raster Times 10")

	HTMLHeading("Raster_DIVIDE_10",2)

	NewDataset=SpaRasters.Divide(TheDataset,10)
	NewDataset.Save(TempFolderPath+"Raster_DIVIDE_10.tif")

	#SpaPlot.PlotRasterHistogram(NewDataset,"Original Raster Divided by 10")

if (True):
	TheDataset=SpaRasters.SpaDatasetRaster()
	TheDataset.Load(StHelensPreEruption)

	TheSampler=SpaRasters.SpaResample()

	# resize the raster
	HTMLHeading("Zoomed",2)

	NewDataset=TheSampler.Scale(TheDataset,0.2) # really fast
	NewDataset.Save(TempFolderPath+"Zoomed.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Zoomed.png")

	# extract a portion of the raster
	HTMLHeading("Extraction",2)

	NewDataset1=TheSampler.ExtractByPixels(TheDataset,15,30,30,100) # really fast
	NewDataset1.Save(TempFolderPath+"Extraction.tif")
	HTMLRenderDataset(NewDataset1,OutputFolderPath,"Extraction.png")

#Test Comparison Operators
if (True):

	HTMLHeading("LessThan 1000",2)
	NewDataset = SpaRasters.LessThan(StHelensPreEruption,1000)
	NewDataset.Save(TempFolderPath+"LessThan1000.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"LessThan1000.png")

	HTMLHeading("LessThan",2)
	NewDataset=SpaRasters.LessThan(StHelensPostEruption,StHelensPreEruption)
	HTMLRenderDataset(NewDataset,OutputFolderPath,"LessThan.png")

	NewDataset=SpaRasters.GreaterThan(StHelensPreEruption,1000)
	HTMLHeading("GreaterThan 1000",2)
	HTMLRenderDataset(NewDataset,OutputFolderPath,"GreaterThan1000.png")

	HTMLHeading("GreaterThan",2)
	NewDataset=SpaRasters.GreaterThan(StHelensPreEruption,StHelensPostEruption)
	HTMLRenderDataset(NewDataset,OutputFolderPath,"GreaterThan.png")

	HTMLHeading("LessThanOrEqual",2)
	NewDataset=SpaRasters.LessThanOrEqual(StHelensPreEruption,StHelensPostEruption)
	NewDataset.Save(TempFolderPath+"LessThanOrEqual.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"LessThanOrEqual.png")

	HTMLHeading("GreaterThanOrEqual",2)
	NewDataset=SpaRasters.GreaterThanOrEqual(StHelensPreEruption,StHelensPostEruption)
	NewDataset.Save(TempFolderPath+"GreaterThanOrEqual.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"GreaterThanOrEqual.png")

	HTMLHeading("Equal",2)
	NewDataset=SpaRasters.Equal(StHelensPreEruption,StHelensPostEruption)
	NewDataset.Save(TempFolderPath+"Equal.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Equal.png")

	HTMLHeading("Maximum",2)

	NewDataset=SpaRasters.Maximum(StHelensPreEruption, StHelensPostEruption)
	NewDataset.Save(TempFolderPath + "Maximum.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Maximum.png")

	HTMLHeading("Minimum",2)
	NewDataset=SpaRasters.Minimum(StHelensPreEruption, StHelensPostEruption)
	NewDataset.Save(TempFolderPath + "Minimum.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Minimum.png")

#Test Arthmetic Operators
if (True):

	RasterFile2=SpaRasters.Load(StHelensPostEruption)

	HTMLHeading("Add",2)
	NewDataset=SpaRasters.Add(StHelensPreEruption,RasterFile2)
	NewDataset.Save(TempFolderPath+"Add.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Add.png")
	
	HTMLHeading("Add1",2)
	NewDataset=SpaRasters.Add(StHelensPreEruption,1000)
	NewDataset.Save(TempFolderPath+"Add1.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Add1.png")
	
	HTMLHeading("Minimum",2)
	NewDataset=SpaRasters.Add(2,StHelensPreEruption)
	NewDataset.Save(TempFolderPath+"Add2.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Minimum.png")
	
	HTMLHeading("Subtract",2)
	NewDataset=SpaRasters.Subtract(StHelensPreEruption,RasterFile2)
	NewDataset.Save(TempFolderPath+"Subtract.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Subtract.png")
	
	HTMLHeading("Subtract1",2)
	NewDataset=SpaRasters.Subtract(StHelensPreEruption,2)
	NewDataset.Save(TempFolderPath+"Subtract1.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Subtract1.png")
	
	HTMLHeading("Subtract2",2)
	NewDataset=SpaRasters.Subtract(1,RasterFile2)
	NewDataset.Save(TempFolderPath+"Subtract2.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Subtract2.png")
	
	HTMLHeading("divide",2)
	NewDataset=SpaRasters.Divide(StHelensPreEruption,RasterFile2)
	NewDataset.Save(TempFolderPath+"divide.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"divide.png")
	
	HTMLHeading("divide1",2)
	NewDataset=SpaRasters.Divide(StHelensPreEruption,3)
	NewDataset.Save(TempFolderPath+"divide1.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"divide1.png")
	
	HTMLHeading("Minimum",2)
	NewDataset=SpaRasters.Divide(1,RasterFile2)
	NewDataset.Save(TempFolderPath+"divide2.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Minimum.png")
	
	HTMLHeading("Multiple",2)
	NewDataset=SpaRasters.Multiply(StHelensPreEruption,RasterFile2)
	NewDataset.Save(TempFolderPath+"Multiple.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Multiple.png")
	
	HTMLHeading("Multiple1",2)
	NewDataset=SpaRasters.Multiply(StHelensPreEruption,3)
	NewDataset.Save(TempFolderPath+"Multiple1.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Multiple1.png")
	
	HTMLHeading("Multiple2",2)
	NewDataset=SpaRasters.Multiply(1.0,RasterFile2)
	NewDataset.Save(TempFolderPath+"Multiple2.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Multiple2.png")

#Test Logical Operators
if (False):
	#create some boolean rasters to work with
	RasterFile2 =SpaRasters.LessThan(StHelensPreEruption,1000)
	BoolRaster1=SpaRasters.GreaterThan(StHelensPreEruption,StHelensPostEruption)
	BoolRaster2=SpaRasters.GreaterThan(StHelensPreEruption,2000)

	NewDataset=SpaRasters.And(BoolRaster1,BoolRaster2)
	NewDataset.Save(TempFolderPath + "And.tif")

	NewDataset=SpaRasters.Or(BoolRaster1,BoolRaster2)
	NewDataset.Save(TempFolderPath + "Or.tif")

	NewDataset=SpaRasters.Not(BoolRaster1)
	NewDataset.Save(TempFolderPath + "Not.tif")

#Test Rounding Functions:
if (True):
	#create a raster with decimal numbers
	DecimalRaster=SpaRasters.Divide(StHelensPreEruption,RasterFile2)
	DecimalRaster.Save(TempFolderPath + "Divide.tif")

	NewDataset=SpaRasters.Round(DecimalRaster, 1)
	NewDataset.Save(TempFolderPath + "Round.tif")

	NewDataset=SpaRasters.RoundInteger(DecimalRaster)
	NewDataset.Save(TempFolderPath + "Int.Tif")

	NewDataset=SpaRasters.RoundFix(DecimalRaster)
	NewDataset.Save(TempFolderPath + "Fix.tif")

	NewDataset=SpaRasters.RoundFloor(DecimalRaster)
	NewDataset.Save(TempFolderPath + "Floor.tif")

	NewDataset=SpaRasters.RoundCeiling(DecimalRaster)
	NewDataset.Save(TempFolderPath + "Ceiling.tif")

	NewDataset=SpaRasters.Truncate(DecimalRaster)
	NewDataset.Save(TempFolderPath + "Truncate.tif")

#test other math function

if (True):

	NewDataset=SpaRasters.NaturalLog(StHelensPreEruption)
	NewDataset.Save(TempFolderPath + "NatLog.tif")

	NewDataset=SpaRasters.Log(StHelensPreEruption)
	NewDataset.Save(TempFolderPath + "Log.tif")

	NewDataset=SpaRasters.Exponential(StHelensPreEruption)
	NewDataset.Save(TempFolderPath + "Exponential.tif")

	NewDataset=SpaRasters.Power(StHelensPreEruption, 2)
	NewDataset.Save(TempFolderPath + "Power.tif")

	NewDataset=SpaRasters.Square(StHelensPreEruption)
	NewDataset.Save(TempFolderPath + "Square.tif")

	NewDataset=SpaRasters.SquareRoot(StHelensPreEruption)
	NewDataset.Save(TempFolderPath + "SquareRoot.tif")

	NewDataset=SpaRasters.AbsoluteValue(StHelensPreEruption)
	NewDataset.Save(TempFolderPath + "Abs.tif")
	HTMLHeading("Abs",2)
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Abs.png")

# test resampler
if (True):
	HTMLHeading("Resampled",2)
	NewDataset=SpaRasters.Resample(StHelensPreEruption,0.5)
	NewDataset.Save(TempFolderPath + "Resampled.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Resampled.png")

# test reclassify
if (True):
	HTMLHeading("Reclassed",2)
	ReclassedDataset=SpaRasters.ReclassifyRange(StHelensPreEruption,[(0,1000),(1000,2000),(2000,3000)],[100,200,255])
	ReclassedDataset.Save(TempFolderPath + "Reclassed.tif")
	HTMLRenderDataset(ReclassedDataset,OutputFolderPath,"Reclassed.png")

#test crop
if (True):
	print("*** Performing crop tests")
	HTMLHeading("Cropped",2)
	NewDataset=SpaRasters.Crop(StHelensPreEruption,[560000,5114000,565000,5119000])
	NewDataset.Save(TempFolderPath+"Cropped.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Cropped.png")

	HTMLHeading("NumpyCropped",2)
	NewDataset=SpaRasters.NumpyCrop(StHelensPreEruption,[560000,5114000,565000,5119000])
	NewDataset.Save(TempFolderPath+"NumpyCropped.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"NumpyCropped.png")

if (True):
	print("*** Performing polygonize test")
	HTMLHeading("Polygonize",2)
	NewDataset=SpaRasterVectors.Polygonize(ReclassedDataset)
	NewDataset.Save(TempFolderPath + "Polygonize.shp")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Polygonize.png")

# topographic transforms
if (True):
	print("*** Performing topography tests")
	HTMLHeading("Topography")

	HTMLHeading("Hillshade",2)
	NewDataset=SpaTopo.Hillshade(StHelensPreEruption)
	NewDataset.Save(TempFolderPath+"Hillshade.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Hillshade.png")

	HTMLHeading("Slope",2)
	NewDataset=SpaTopo.Slope(StHelensPreEruption)
	NewDataset.Save(TempFolderPath+"Slope.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Slope.png")

	HTMLHeading("Aspect",2)
	NewDataset=SpaTopo.Aspect(StHelensPreEruption)
	NewDataset.Save(TempFolderPath+"Aspect.tif")
	HTMLRenderDataset(NewDataset,OutputFolderPath,"Aspect.png")

	HTMLHeading("Contour",2)
	SpaTopo.Contour(StHelensPreEruption,OutputFilePath=TempFolderPath+"Contour.shp")
	TheCoutours=SpaVectors.SpaDatasetVector()
	TheCoutours.Load(TempFolderPath+"Contour.shp")
	HTMLRenderDataset(TheCoutours,TempFolderPath,"Contour.png")

print("DONE")

HTMLClose()

# Open the browser to show the file
Thing=os.path.abspath("../Temp/Rasters")

WebPagePath="file:///"+Thing+"/_SpaRasterTest.html"

webbrowser.open(WebPagePath)
