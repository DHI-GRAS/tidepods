import numpy as np
import rasterio
import rasterio.warp
from shapely.geometry import box, Point


def transform_shape(infile):
    """Reads AOI bounds and reprojects to EPSG:4326. Returns bounds as shapely polygon

    Parameters
    ----------
    infile : str
        File path to raster AOI.

    Returns
    -------
    shp : shapely object

    """
    with rasterio.open(infile) as src:
        left, bottom, right, top = src.bounds
        in_crs = src.crs
        out_crs = rasterio.crs.CRS.from_epsg(4326)
        minx, miny, maxx, maxy = rasterio.warp.transform_bounds(in_crs, out_crs,
                                                                left, bottom, right, top)
        shp = box(minx, miny, maxx, maxy)
        shp = shp.buffer(0.125)

    return shp


def generate_pts(infile):
    """Generates fixed distance points within a polygon

    Parameters
    ----------
    infile : str
        File path to polygon.

    Returns
    -------
    plist : list
        List of shapely points for points within infile

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

    return plist
