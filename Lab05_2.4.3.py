############################################################
# 2.4.3 Raster Tutorials / Fire Analysis
#
#Provides functions to:
# 2.4.3 Identify High/Med/Low Heat Thresholds of Mills Fire
#     > Raster Information
#     > Clip To Specified Bounds
#     > Downsample
#     > Descriminate
#     > Combine
#
#Information:
#     Fire intensity models have utility for various industries.    
#     Cal Fire Intel uses these inputs to generate predictive
#     models that assist in the determination of where the fire
#     will grow, and how fast. Post fire damage assesment teams
#     may use this data to plan rehabilitation of devistated
#     areas based on burn intensity upon exposed flora.
#     
# By: Tony Ramos
# Date: 02/19/2023
#
############################################################

import sys

# Open source spatial libraries
import shapely
import numpy as np
from osgeo import gdal
import math
import random
import os

# SpaPy libraries
from SpaPy import SpaBase
from SpaPy import SpaPlot
from SpaPy import SpaVectors
from SpaPy import SpaView
from SpaPy import SpaReferencing
from SpaPy import SpaDensify
from SpaPy import SpaView
from SpaPy import SpaRasters
from SpaPy import SpaTopo
from SpaPy import SpaRasterVectors


######################################################################

# File Paths

# A DEM of Mt St Helens before the eruption
HotspotHighlight="SpaPyTests/Data/MillsFire/LWIR_QuickMosaic_Hotspot_Highlight_9327_4x.tiff"

# A DEM of Mt St Helens after the eruption
LWIRFullRez="SpaPyTests/Data/MillsFire/LWIR_QuickMosaic_16-bit_9327.tiff"

# A temporary folder for outputs
TempFolderPath3="SpaPyTests/Temp3/"
os.makedirs(TempFolderPath3)

######################################################################

# RASTER INFORMATION

# Define TheDataset with our SpaDatasetRaster function
LWIR_Raster=SpaRasters.SpaDatasetRaster()  

# Load our raster file in as TheDataset     
LWIR_Raster.Load(LWIRFullRez)      

# Get the dimensions of the raster in pixels
print("Width in pixels: "+format(LWIR_Raster.GetWidthInPixels()))

print("Height in pixels: "+format(LWIR_Raster.GetHeightInPixels()))

# Get the number of bands of data in the raster (e.g. DEMs have 1, RGB data has 3)
print("Number of Bands: "+format(LWIR_Raster.GetNumBands()))

# Get the GDAL type of pixels which includes GDT_Int16, GDT_Int32, GDT_Float32 and GDT_Float64
print("Pixel Type: "+format(LWIR_Raster.GetType()))

# Get the spatial reference
print("Coordinate Reference System/Spatial Reference: "+format(LWIR_Raster.GetCRS()))

# Get the resolution or dimensions of each pixel in the raster
print("Resolution (x,y): "+format(LWIR_Raster.GetResolution()))

# Get the spatial bounds of the raster
TheBounds=LWIR_Raster.GetBounds()
print("TheBounds (XMin,YMin,XMax,YMax): "+format(TheBounds))

# Get additional information on the raster
TheBandStats=LWIR_Raster.GetBandInfo(1)
print("TheBandStats="+format(TheBandStats))

# Get one band of data from the raster
TheBand=LWIR_Raster.GetBand(0)
print("TheBands: "+format(TheBand))

SpaView.Show(LWIR_Raster) # View original raster


#####################################################################

# CLIP TO SPECIFIED BOUNDS

# Use SpaRaster Crop tool and input raster for clip and desired bounds
ClippedRaster=SpaRasters.Crop(LWIR_Raster,[-122.415767,41.40831,-122.37479,41.5014]) # Bounds set for SpaView. Actual bounds dont view properly and are set later.
ClippedRaster.Save(TempFolderPath3+"Cropped.tif") # Save Result
SpaView.Show(ClippedRaster) # View Fire Area


#####################################################################

# DOWNSAMPLE

# Resample (Resample variable is the denominator, Original resolution is the numerator. Resolution is devided by the input value)
DownSample=SpaRasters.Resample(ClippedRaster,0.28) # Downsample raster to 5 meter spatial resolution.
DownSample.Save(TempFolderPath3 + "DownSampledRaster.tif") # Save Result


#####################################################################

# DESCRIMINATE

# select for high, medium, low heat thresholds.
LowHeat=SpaRasters.GreaterThanOrEqual(TempFolderPath3 + "DownSampledRaster.tif",33000) # Values below 33000 16-Bit Radiometric Resolution are no fire (0).
MediumHeat=SpaRasters.GreaterThanOrEqual(TempFolderPath3 + "DownSampledRaster.tif",39000) # Values between 39000-53000 are medium heat.
HighHeat=SpaRasters.GreaterThanOrEqual(TempFolderPath3 + "DownSampledRaster.tif",53000) # Values between 53000-65536(Max) are high heat


#####################################################################

# COMBINE

# Raster math to combine descriminated values.
FireClass = HighHeat + MediumHeat + LowHeat # Sum of all heats where 0 = NoHeat; 0.001-1 = LowHeat; 1.001-2 = MediumHeat; 2.001-3 = HighHeat
FireClass.Save(TempFolderPath3 + "Fire_Class.tif") # Save Result

FireClassCrop = SpaRasters.Crop(TempFolderPath3 + "Fire_Class.tif",[-122.415767,41.43,-122.37479,41.5014]) # Re-Cropped for actual bound
FireClassCrop.Save(TempFolderPath3 + "Fire_Class_Final.tif") # Saved Final Output

SpaView.Show(FireClass) # View heat classes.
SpaView.Show(FireClassCrop) # View to illustrate that corrected bounds doesn't render right in SpaView. Output raster bounds are correct.

######################################################################
    # END



