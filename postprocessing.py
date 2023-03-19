import os
import shapely
import geopandas
from geopandas import GeoDataFrame
import tomllib
import numpy as np


def postprocessing(input_path: str, intermediate: bool) -> bool:
    """
    Function for postprocessing the classification results.

    Args:
        input_path (str): Path to heatpoly-Shapefile
        intermediate (bool): Export of intermediate results to shapefiles (True/False)

    Returns:
        Returns boolean value, if function runs successfully or not.    
    
    Example:
        postprocessing(path='./data/LWIR_QuickMosaic_16-bit_9327_heatpoly.shp', intermediate=True)
    
    """
    print(f'Extract the file name from path: {input_path}')
    file_name = os.path.splitext(os.path.basename(input_path))[0]

    print(f'Load configuration file.')
    with open("config.toml", "rb") as f:
        configdata = tomllib.load(f)

    print(f'Read the input shapefile into a GeoDataFrame.')
    gdf = geopandas.read_file(input_path)
    coord_sys = gdf.crs

    print(f'Dissolve and generate a concave hull around classified area')
    concavratio = configdata['postprocessing']['concave_ratio']
    gdf_dissolve = shapely.unary_union(gdf.geometry)
    concave = shapely.concave_hull(gdf_dissolve, ratio=concavratio, allow_holes=False)
    gdf_concave = geopandas.GeoDataFrame(index=[0], crs=coord_sys, geometry=[concave])
    gdf_concave.to_file(f'./data/{file_name}_00_concave.shp', crs=coord_sys)

    print(f'Select the distance_out_buffer from config-file.')
    distance_out_buffer = configdata['postprocessing']['distance_out_buffer']

    print(f'Create a buffer around each polygon using the distance_out_buffer: {distance_out_buffer}')
    buffered_out = gdf.geometry.buffer(distance_out_buffer)

    print(f'Group buffered polygons that intersect with each other.')
    groups_1 = buffered_out.unary_union

    print(f'Convert the grouped polygons back to a GeoDataFrame.')
    if isinstance(groups_1, shapely.geometry.MultiPolygon):
        polygons_list = [polygon for polygon in groups_1.geoms]
    else:
        polygons_list = [groups_1]

    grouped_polygons = geopandas.GeoDataFrame(
        {'geometry': polygons_list},
        crs=coord_sys
    )

    if intermediate == True:
        shp_agg = f'./data/{file_name}_01_aggregated.shp'
        print(f'Save the aggregated polygons to shapefile: {shp_agg}')
        grouped_polygons.to_file(shp_agg)

    print(f'Select the min_area_interior_polygons from config-file.')
    min_area_interior_polygons = configdata['postprocessing']['min_area_interior_polygons']

    area_before_filtering = np.sum(grouped_polygons['geometry'].area)
    print(f'Area before filtering the polygons: {area_before_filtering}')
    fc = []
    for index, row in grouped_polygons.iterrows():
        # Get the exterior and interior polygons
        exterior = row.geometry.exterior
        interiors = row.geometry.interiors

        # Filter out small interior polygons
        interiors_filtered = [interior for interior in interiors if shapely.Polygon(interior.coords).area > min_area_interior_polygons]
        
        # Create a new polygon with the filtered interiors
        filtered_polygon = type(row.geometry)(exterior, interiors_filtered)
        
        # Replace the original geometry with the filtered geometry
        fc.append(filtered_polygon)
 
    filtered_polygons = geopandas.GeoDataFrame(
        {'geometry': fc},
        crs=coord_sys
    )

    area_after_filtering = np.sum(filtered_polygons['geometry'].area)
    print(f'Area after filtering the polygons: {area_after_filtering}')

    if intermediate == True:
        shp_buff = f'./data/{file_name}_02_buff.shp'
        print(f'Save the aggregated polygons to shapefile: {shp_buff}')
        filtered_polygons.to_file(shp_buff)

    print(f'Select the distance_in_buffer from config-file.')
    distance_in_buffer = configdata['postprocessing']['distance_in_buffer']

    print(f'Create a buffer around each polygon using the distance_in_buffer: {distance_in_buffer}')
    buffered_in = filtered_polygons.geometry.buffer(distance_in_buffer)

    print(f'Group buffered polygons that intersect with each other')
    groups_2 = buffered_in.unary_union

    print(f'Area before applying minimum area treshold: {groups_2.area}')
    print(f'Select the min_area from config-file.')
    min_area_polygons = configdata['postprocessing']['min_area_polygons']
    poly_list=[]
    print(f'Convert the grouped polygons back to a GeoDataFrame')
    if isinstance(groups_2, shapely.geometry.MultiPolygon):
        for polygon in groups_2.geoms:
            if polygon.area > min_area_polygons:
                poly_list.append(polygon)
    else:
        if groups_2.area > min_area_polygons:
                poly_list.append(groups_2)

    grouped_polygons_2 = geopandas.GeoDataFrame(
        {'geometry': poly_list},
        crs=coord_sys
    )

    area_after_min_area = np.sum(grouped_polygons_2['geometry'].area)
    print(f'Area after minimum area: {area_after_min_area}')

    if intermediate == True:
        shp_negbuff = f'./data/{file_name}_03_negbuff.shp'
        print(f'Save the aggregated polygons to shapefile: {shp_negbuff}')
        grouped_polygons_2.to_file(shp_negbuff)

    print(f'Dissolve the polygons')
    dissolved_polygons = grouped_polygons_2.dissolve()

    shp_dissolve = f'./data/{file_name}_dissolve.shp'
    print(f'Save the dissolved polygons to the final shapefile: {shp_dissolve}')
    dissolved_polygons.to_file(shp_dissolve)

    return dissolved_polygons


### Debugging
#postprocessing(input_path='./data/LWIR_QuickMosaic_16-bit_9327_heatpoly.shp', intermediate=True)
