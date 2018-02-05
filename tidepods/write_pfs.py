import fiona
import numpy as np
from shapely.geometry import shape, Point
from fiona.transform import transform_geom
from string import Template

def transform_shape(infile):
    """Reprojects polygon to EPSG:4326 and return as shapely object

    Parameters
    ----------
    infile: str
        path to polygon

    Returns
    -------
    shapely object : polygon
    """
    with fiona.open(infile) as c:
        infile_4326 = transform_geom(c.crs.get("init"), 'epsg:4326', c[0]['geometry'])
        shp = shape(infile_4326)
    return (shp)

def generate_pts(infile):
    """Generates fixed distance points within a polygon

    Parameters
    ----------
    infile: str
        path to polygon

    Returns
    -------
    list : list of shapely points for points within infile
    """
    shp = transform_shape(infile)
    bounds = shp.bounds
    minx, miny, maxx, maxy = bounds
    plist=[]
    for x in np.arange(minx, maxx, 0.125):
        for y in np.arange(miny, maxy, 0.125):
            p = (Point(x,y))
            if p.within(shp):
                plist.append(p)
    return (plist)

def write_pfs(shp, template, acq_date, pfs):
    """Creates pfs file for input to MIKE

    Parameters
    ----------
    shp: str
        path to input shapefile
    
    template: str
        path to template textfile

    acq_date: int
        image acquisiton date (yyyymmdd)
        
    pfs: str
        path to pfs file

    Returns
    -------
    pfs file: a .pfs file for input to MIKE
    """
    acq_date_str = str(acq_date)
    acq_year = acq_date_str[:4]
    plist = generate_pts(shp)
    formatted_pts = []
    pid = 1
    for p in plist:
        formatted_pts.append(r'[Point_' + str(pid) + ']\n' +
                        r'description = ' + str(pid) + '\n' +
                        r'y = ' + str(p.coords[0][0]) + '\n' +
                        r'x = ' + str(p.coords[0][1]) + '\n' +
                        r'EndSect // Point_' + str(pid) + '\n'
            )
        pid +=1
    
    with open(template) as infile, open(pfs, 'w') as outfile:
        d = {'REPLACE_YEAR': acq_year, 'REPLACE_OUTFILE_NAME': pfs, 'REPLACE_NUM_PTS': len(plist), 'REPLACE_POINTS':'\n'.join(formatted_pts)}
        src = Template(infile.read())
        replacement = src.substitute(d)
        outfile.write(replacement)