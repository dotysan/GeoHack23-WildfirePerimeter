import geopandas
import os
from matplotlib import pyplot
import rasterio
import shapely
import numpy as np
shp = geopandas.read_file(r"C:\Users\RICLO\OneDrive - Ørsted\Desktop\Geopython\last\GeoHack23-WildfirePerimeter-main\data\HeatPoly_utm.shp")


#dissolved
dissolved = shapely.unary_union(shp.geometry)


print(type(dissolved))

#Concave hull
new_shp = shapely.concave_hull(dissolved,ratio=0.01,allow_holes=False)
new_gdp = geopandas.GeoDataFrame(geometry=[new_shp])
new_gdp.to_file(r"C:\Users\RICLO\OneDrive - Ørsted\Desktop\Geopython\last\GeoHack23-WildfirePerimeter-main\data\afterDissolve_shp2",crs=shp.crs)

new_gdp.plot()



dataset = rasterio.open(r"C:\Users\RICLO\OneDrive - Ørsted\Desktop\Geopython\last\GeoHack23-WildfirePerimeter-main\data\LWIR_QuickMosaic_16-bit_9327.tiff")
band1 = dataset.read(1)



print(np.max(band1))
pyplot.imshow(band1, cmap='Reds')
pyplot.show()

from scipy.signal import find_peaks

a = band1.flatten()
print(a)
b = find_peaks(a)

import matplotlib.pyplot as plt
plt.plot(a)
