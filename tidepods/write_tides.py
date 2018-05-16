import datetime
import sys

import clr
import System
import fiona
from shapely.geometry import mapping, shape


def read_dfs0(infile, date, sdkpath, **kwargs):
    """Reads dfs0 file and returns tide values as value above LAT at desired time

    Parameters
    ----------
    infile : str
        File path to dfs0 file.
    date : datetime.datetime
        Image acquisition date and time

    Returns
    -------
    tide_values : list
        List of tide values

    """
    dfs_img_datetime = date
    try:
        sys.path.insert(0, sdkpath)
        clrpath = 'DHI.Generic.MikeZero.DFS'
        clr.AddReference(clrpath)

    except System.IO.FileNotFoundException as exception:
        msg = "Reference not found. Is the path to the sdk correct: '{0}'?".format(sdkpath)
        raise ValueError(msg) from exception

    import DHI.Generic.MikeZero.DFS

    sys.path.pop(0)

    dfsfile = DHI.Generic.MikeZero.DFS.DfsFileFactory.DfsGenericOpen(infile)
    tide_values = []
    # read timestep in seconds, convert to minutes
    timestep = int(dfsfile.FileInfo.TimeAxis.TimeStep / 60)
    sdt = dfsfile.FileInfo.TimeAxis.StartDateTime
    dfs_start_datetime = datetime.datetime(*(getattr(sdt, n) for n in ['Year', 'Month', 'Day',
                                             'Hour', 'Minute']))

    diff = dfs_img_datetime - dfs_start_datetime
    img_timestep = int(((diff.days * 24 * 60) + (diff.seconds / 60)) / timestep)

    for i in range(dfsfile.ItemInfo.Count):
        min_value = float(dfsfile.ItemInfo[i].MinValue)
        acq_value = dfsfile.ReadItemTimeStep(i+1, img_timestep).Data[0]
        img_value = acq_value - min_value
        tide_values.append(img_value)

    return tide_values


def write_tide_values(infile, shapefile, outfile, date, sdkpath, **kwargs):
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
    tide_values = read_dfs0(infile, date, sdkpath)

    with fiona.open(shapefile, 'r') as src:
        crs = src.crs.copy()
        schema = src.schema.copy()
        schema['properties'].update({'tide_value': 'float'})

        with fiona.open(outfile, 'w', crs=crs, driver='ESRI Shapefile', schema=schema) as dst:
            for idx, (elem, tv) in enumerate(zip(src, tide_values)):
                prop = {'p_ID': int(idx+1), 'tide_value': float(tv)}
                dst.write({'properties': prop, 'geometry': mapping(shape(elem['geometry']))})
