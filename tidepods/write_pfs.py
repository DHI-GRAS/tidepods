from string import Template

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
    with fiona.open(infile) as c:
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


def write_pfs(shp, template, date, pfs):
    """Creates pfs file for input to MIKE

    Parameters
    ----------
    shp : str
          File path to polygon.

    template : str
               File path to template textfile.

    date : datetime
           Image acquisiton date (YYYYMMDD).

    pfs : str
          File path to pfs file.

    """
    date_str = str(date)
    acq_year = date_str[:4]
    plist = generate_pts(shp)
    formatted_pts = []
    POINT_FMT = (
        '''[Point_{pid}]
        description = {pid}
        y = {coords[0]}
        x = {coords[1]}
        EndSect // Point_{pid}\n''')

    for pid, p in enumerate(plist, 1):
        points_str = POINT_FMT.format(pid=pid, coords=p.coords[0])
        formatted_pts.append(points_str)

    with open(template) as infile, open(pfs, 'w') as outfile:
        d = {'REPLACE_YEAR': acq_year, 'REPLACE_OUTFILE_NAME': pfs[:-4],
             'REPLACE_NUM_PTS': len(plist), 'REPLACE_POINTS': '\n'.join(formatted_pts)}
        src = Template(infile.read())
        replacement = src.substitute(d)
        outfile.write(replacement)
