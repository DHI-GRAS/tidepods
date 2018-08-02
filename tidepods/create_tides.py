import datetime
import os
import sys
import tempfile

import fiona
from fiona.crs import from_epsg
from shapely.geometry import mapping

from tidepods import generate_pts
from tidepods import make_pfs

VALID_LEVELS = ['LAT', 'MSL']


def read_dfs0(infile, date, mikepath, tempdir, level):
    """Read and extract values from dfs0 file using DHI.Generic.MikeZero.DFS

    Parameters
    ----------
    infile : str
        Path to AOI polygon.

    date : datetime.datetime
        Image acqusition date and time

    mikepath : str
        Path to MIKE installation directory

    tempdir : str
        Path to temporary directory

    level : str
        Click option LAT or MSL

    Returns
    -------
    tide_values :  list
        List of tide values above LAT for image acquisiton date and time

    """
    if level not in VALID_LEVELS:
        raise ValueError(f'Level should be one of {VALID_LEVELS}, not {level}.')

    sdkpath = os.path.join(mikepath, r'MIKE SDK\bin')
    dfsfilepath = make_pfs.make_dfs0(infile, date, mikepath, tempdir)

    import clr
    clr.AddReference('System')
    import System

    if os.path.isdir(sdkpath):
        sys.path.insert(0, sdkpath)
    
    else:
        raise ValueError(f'SDK Path folder not found. Is the path to the sdk correct: "{sdkpath}"?')
        
    try:
        clr.AddReference(r'DHI.Generic.MikeZero.DFS')
        import DHI.Generic.MikeZero.DFS

    except (ImportError, System.IO.FileNotFoundException) as exception:
        msg = f'DHI.Generic not found. Is the path to the sdk correct: "{sdkpath}"?'
        raise ValueError(msg) from exception

    finally:
        sys.path.pop(0)

    dfs_img_datetime = date

    
    dfsfile = DHI.Generic.MikeZero.DFS.DfsFileFactory.DfsGenericOpen(dfsfilepath)
    tide_values = []
    # read timestep in seconds, convert to minutes
    timestep = int(dfsfile.FileInfo.TimeAxis.TimeStep / 60)
    sdt = dfsfile.FileInfo.TimeAxis.StartDateTime
    dfs_start_datetime = datetime.datetime(*(getattr(sdt, n) for n in ['Year', 'Month', 'Day',
                                             'Hour', 'Minute', 'Second']))

    diff = dfs_img_datetime - dfs_start_datetime
    img_timestep = int(((diff.days * 24 * 60) + (diff.seconds / 60)) / timestep)

    for i in range(dfsfile.ItemInfo.Count):
        min_value = float(dfsfile.ItemInfo[i].MinValue)
        acq_value = dfsfile.ReadItemTimeStep(i + 1, img_timestep).Data[0]  # Value c.f. MSL

        if level == 'LAT':
            lat_value = acq_value - min_value  # Value above LAT
            tide_values.append(lat_value)
        elif level == 'MSL':
            tide_values.append(acq_value)
        else:
            raise ValueError('Invalid level.')

    dfsfile.Dispose()

    return tide_values


def write_tide_values(infile, date, mikepath, outfile, tempdir, level):
    """Writes points to new shapefile

    Parameters
    ----------
    infile : str
        File path to dfs0 file.
    shapefile : str
        File path to existing point shapefile.
    outfile : str
        File path to output point shapefile.
    """
    tide_values = read_dfs0(infile, date, mikepath, tempdir, level)

    plist = generate_pts.create_pts(infile)

    pts_schema = {'geometry': 'Point',
                  'properties': {'p_ID': 'int',
                                 'tide_value': 'float'}}

    with fiona.open(outfile, 'w', crs=from_epsg(4326), driver='ESRI Shapefile',
                    schema=pts_schema) as output:
        for pid, (p, tv) in enumerate(zip(plist, tide_values)):
            prop = {'p_ID': int(pid + 1), 'tide_value': float(tv)}
            output.write({'geometry': mapping(p), 'properties': prop})


def main(infile, date, mikepath, outfile, **kwargs):
    dirpath, filepath = os.path.split(infile)
    with tempfile.TemporaryDirectory(dir=dirpath) as tempdir:
        write_tide_values(infile, date, mikepath, outfile, tempdir, **kwargs)
