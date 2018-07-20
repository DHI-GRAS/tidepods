import fiona
from fiona.transform import transform_geom
import numpy as np
from shapely.geometry import shape, Point


def transform_shape(infile):
    """Reprojects polygon to EPSG:4326 and return as shapely object

    Parameters
    ----------
    infile : str
        File path to polygon.

    Returns
    -------
    shp : shapely object

    """
    with fiona.open(infile, encoding='utf-8') as c:
        infile_4326 = transform_geom(c.crs.get("init"), 'epsg:4326', c[0]['geometry'])
        shp = shape(infile_4326)
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
