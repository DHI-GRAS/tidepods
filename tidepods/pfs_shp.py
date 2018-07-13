from string import Template

import fiona
from fiona.transform import transform_geom
from fiona.crs import from_epsg
import numpy as np
from shapely.geometry import mapping, shape, Point

POINT_FMT = (
    '''[Point_{pid}]
description = {pid}
y = {coords[0]}
x = {coords[1]}
EndSect // Point_{pid}
''')


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


def write_pfs(infile, template, date, pfs, **kwargs):
    """Creates pfs file for input to MIKE

    Parameters
    ----------
    infile : str
        File path to polygon.
    template : str
        File path to template textfile.
    img_date : datetime
        Image acquisiton date (YYYYMMDD).
    pfs : str
        File path to pfs file.

    """
    plist = generate_pts(infile)
    formatted_pts = []

    for pid, p in enumerate(plist, 1):
        points_str = POINT_FMT.format(pid=pid, coords=p.coords[0])
        formatted_pts.append(points_str)

    with open(template) as infile, open(pfs, 'w') as outfile:
        d = {'REPLACE_YEAR': date.year, 'REPLACE_OUTFILE_NAME': pfs[:-4],
             'REPLACE_NUM_PTS': len(plist), 'REPLACE_POINTS': '\n'.join(formatted_pts)}
        src = Template(infile.read())
        replacement = src.substitute(d)
        outfile.write(replacement)


def write_pts(infile, outfile, **kwargs):
    """Writes points to new shapefile

    Parameters
    ----------
    infile : str
        File path to polygon.
    outfile : str
        File path to output point shapefile.
    """
    plist = generate_pts(infile)
    pts_schema = {'geometry': 'Point',
                  'properties': {'p_ID': 'int'}}

    with fiona.open(outfile, 'w', crs=from_epsg(4326), driver='ESRI Shapefile',
                    schema=pts_schema) as output:
        for pid, p in enumerate(plist):
            prop = {'p_ID': int(pid+1)}
            output.write({'geometry': mapping(p), 'properties': prop})
