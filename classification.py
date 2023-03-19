import os
import rasterio
from rasterio import features
import numpy as np
import shapely
from geopandas import GeoSeries, GeoDataFrame

def classification_image(path: str, treshold: int, export_raster: bool, local_crs: int) -> str:
    '''
    Classifies a single-band, near-infrared image based on a given treshold to a shapefile in a local
    coordinate system.

    Args:
        path (str): Path to the TIF-image
        treshold (int): Integer value for image classification
        export_raster (bool): Export of classified raster (True/False)
        local_crs (int): EPSG integer value for local coordinate system

    Returns:
        Returns the path of the exported Shapefile.

    Example:
        classification_image(path="./data/LWIR_QuickMosaic_16-bit_9327.tiff", \
            treshold=33332, export_raster=True, local_crs=26910)
    
    '''
    # Extract the file name from path
    file_name = os.path.splitext(os.path.basename(path))[0]

    with rasterio.open(path) as img:
        print(f'Read the first band of image {path}')
        raster_data = img.read(1)
        raster_meta = img.meta

    print(f'Classification of raster {path} based on treshold value "{treshold}"')
    classified_data  = np.where(raster_data < treshold, 0, 1)

    # Update the metadata with the new data type and nodata value
    raster_meta.update(dtype=rasterio.uint8, nodata=None)

    if export_raster == True:
        print(f'Write the classified raster to file {file_name}_class.tif')
        with rasterio.open(f'./data/{file_name}_class.tif', 'w', **raster_meta) as dst:
            dst.write(classified_data, 1)

    polygon_list = []
    value_list = []
    print(f'Convert the classified raster to polygons')
    shapes = features.shapes(classified_data, transform=raster_meta['transform'])
    for shape in shapes:
        value = shape[1]
        if value > 0:
            polygon_list.append(shapely.geometry.shape(shape[0]))
            value_list.append(shape[1])
  
    print('Project the polygons to local coordinate system {local_crs}')
    gdf_wgs84 = GeoDataFrame({'value': value_list, 'geometry': GeoSeries(polygon_list)}, crs="epsg:4326")
    gdf_local = gdf_wgs84.to_crs(epsg=local_crs)
    shpfile = f'./data/{file_name}_heatpoly.shp'
    gdf_local.to_file(shpfile, driver='ESRI Shapefile')

    return shpfile


### Debugging
#shp = classification_image(path='./data/LWIR_QuickMosaic_16-bit_9327.tiff', \
#                           treshold=33332, \
#                           export_raster=False, \
#                           local_crs=26910)
#print(shp)