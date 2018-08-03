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
