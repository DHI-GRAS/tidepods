# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 12:00:18 2021

@author: vlro
"""

import rasterio
import geopandas as gpd
import rasterio.mask
import numpy as np
import os

import numpy as np
from shapely.geometry import box, Point, shape


def transform_shape_raster(infile):
    """Reads raster AOI bounds and reprojects to EPSG:4326. Returns bounds as shapely polygon.

    Parameters
    ----------
    infile : str
        Path to raster AOI.

    Returns
    -------
    shp : shapely object.

    """
    import rasterio
    import rasterio.warp

    with rasterio.open(infile) as src:
        left, bottom, right, top = src.bounds
        in_crs = src.crs
        out_crs = rasterio.crs.CRS.from_epsg(4326)
        minx, miny, maxx, maxy = rasterio.warp.transform_bounds(in_crs, out_crs,
                                                                left, bottom, right, top)
        shp = box(minx, miny, maxx, maxy)
        shp = shp.buffer(0.125)
    return shp


def transform_shape_vector(infile):
    """Reads vector AOI bounds and reprojects to EPSG:4326. Returns bounds as shapely polygon.

    Parameters
    ----------
    infile : str
        Path to vector AOI.

    Returns
    -------
    shp : shapely object
        Infile AOI bounds as a shapely polygon object.

    Raises
    -------
    ValueError
        If the input vector file is not a polygon.

    """
    import fiona
    from fiona.transform import transform_geom

    with fiona.open(infile, encoding='utf-8') as c:
        shp_geom = c.schema['geometry']

        if shp_geom != 'Polygon':
            raise ValueError('Shapefile not accepted. Only polygons may be used as input.')

        infile_4326 = transform_geom(c.crs.get("init"), 'epsg:4326', c[0]['geometry'])
        shp = shape(infile_4326)
        shp = shp.buffer(0.125)

        return shp


def transform_shape(infile):
    """Transforms input file to EPSG:4326.

    Parameters
    ----------
    infile : str
        Path to polygon or raster AOI.

    Returns
    -------
    shp : shapely object
        Infile AOI bounds as a shapely polygon object.

    Raises
    -------
    ValueError
        If the input file is not an accepted raster of vector format.

    """
    raster_exts = ['.tif']
    vector_exts = ['.shp', '.geojson', '.json']
    ext = os.path.splitext(infile)[1].lower()

    if ext in raster_exts:
        return transform_shape_raster(infile)

    if ext in vector_exts:
        return transform_shape_vector(infile)

    raise ValueError(f'File not accepted. Acceptable raster formats are {raster_exts} and '
                     f'acceptable vector formats are {vector_exts}')

def create_pts(infile):
    """Generates fixed distance points within a polygon.

    Parameters
    ----------
    infile : str
        Path to polygon or raster AOI.

    Returns
    -------
    plist : list
        List of shapely points for points within infile.

    Raises
    -------
    ValueError
        If plist is empty as no points have been generated.

    """
    shp = transform_shape(infile)
    bounds = shp.bounds
    minx, miny, maxx, maxy = bounds
    plist = []
    for x in np.arange(minx, maxx, 0.125):
        for y in np.arange(miny, maxy, 0.125):
            p = (Point(x, y))
            if p.within(shp):
                plist.append(p)

    if not plist:
        raise ValueError('No points generated. Is the input file covering a large enough AOI?')

    return plist

inf = r'C:\tidepods-dev\data\s2\S2A_MSIL1C_20180524T023551_N0206_R089_T50QQM_20180524T051356.SAFE\GRANULE\L1C_T50QQM_A015244_20180524T025016\IMG_DATA\RGB.tif'

x = create_pts(inf)

r = rasterio.open(inf)
r.height
r.meta
r.
new_arr = np.random.randint(0, 100, size=r.shape)
new_arr = new_arr[np.newaxis, :, :]
new_arr.shape
with rasterio.Env():
    profile = r.profile
    profile.update(count=1, dtype=rasterio.float32)
    with rasterio.open(r'C:\tidepods-dev\random2.tif', 'w', **profile) as dst:
        dst.write(new_arr)

x[0].coords

from shapely.ops import transform

import pandas as pd
df = pd.DataFrame([p for p in x])
df
gdf = geopandas.GeoDataFrame(df, geometry=df[0])
gdf.plot()

gdf.crs = 'EPSG:4326'
gdf = gdf.to_crs(r.crs)
gdf
r.bounds

rd = r.read()
r.index(812294.163, 2714985.598)
r.shape

pl = [(x[1]['geometry'].x, x[1]['geometry'].y) for x in gdf.iterrows()]

for j in pl:
    print(r.index(j[0], j[1]))

len(pl)

for p in pl:
    if p[0] < 0:
        pl.

x = gpd.read_file(r'C:\tidepods-dev\test_output.shp')


p = gpd.read_file(r'C:\tidepods-dev\test.shp')

li = []
for _, r in x.iterrows():
    if p['geometry'][0].contains(r['geometry']):
        li.append(r['geometry'])

len(li)
len(x)

from rasterio.transform import from_origin

arr = np.zeros((100, 100), dtype=rasterio.float32)
transform = from_origin(-86.97364545, 34.7075079, 0.0125, 0.0125)

arr
gdf
gdf["value"] = 1
gdf
import random

randoms = [random.randrange(1, 11, 1) for _ in range(100)]
randoms
gdf["values"] = randoms
gdf
new_arr

for _, row in gdf.iterrows():
    ab = (row['geometry'].x, row['geometry'].y)
    idx = r.index(ab[0], ab[1])
    if 0 <= idx[0] <= r.shape[0] and 0 <= idx[1] <= r.shape[1]:
        print(idx)
        new_arr[idx[0], idx[1]] = row['values']

r.index(0,0)

r.index(813216.035, 2673426.199)
r.shape
r
new_arr = np.zeros(r.shape, dtype=rasterio.float32)
np.minimum(new_arr)
new_arr = new_arr[np.newaxis, :, :]

new_arr.max()
(0, 0) < ab < r.shape
r.shape
