import datetime
import os
import shutil
import sys
import tempfile

import fiona
from fiona.crs import from_epsg
from shapely.geometry import mapping

from . import generate_pts as gp, make_pfs as mp


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

    sdkpath = os.path.join(mikepath, r'MIKE SDK\bin')

    import clr

    clr.AddReference('System')

    import System

    try:
        sys.path.insert(0, sdkpath)

    except System.IO.FileNotFoundException as exception:
        msg = "Reference not found. Is the path to the sdk correct: '{0}'?".format(sdkpath)
        raise ValueError(msg) from exception

    clr.AddReference(r'DHI.Generic.MikeZero.DFS')

    import DHI.Generic.MikeZero.DFS

    sys.path.pop(0)

    dfs_img_datetime = date

    dfsfilepath = mp.make_dfs0(infile, date, mikepath, tempdir)

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
        acq_value = dfsfile.ReadItemTimeStep(i+1, img_timestep).Data[0]  # Value c.f. MSL

        if level == 'LAT':
            lat_value = acq_value - min_value  # Value above LAT
            tide_values.append(lat_value)
        else:
            tide_values.append(acq_value)

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

    plist = gp.generate_pts(infile)

    pts_schema = {'geometry': 'Point',
                  'properties': {'p_ID': 'int',
                                 'tide_value': 'float'}}

    with fiona.open(outfile, 'w', crs=from_epsg(4326), driver='ESRI Shapefile',
                    schema=pts_schema) as output:
        for pid, (p, tv) in enumerate(zip(plist, tide_values)):
            prop = {'p_ID': int(pid+1), 'tide_value': float(tv)}
            output.write({'geometry': mapping(p), 'properties': prop})


def main(infile, date, mikepath, outfile, **kwargs):
    dirpath, filepath = os.path.split(infile)
    tempdir = tempfile.mkdtemp(dir=dirpath)
    write_tide_values(infile, date, mikepath, outfile, tempdir, **kwargs)
    shutil.rmtree(tempdir)
