import click
from datetime import datetime as dt


def click_callback(f):
    return lambda _, __, x: f(x)


def check_date(date):
    try:
        return dt.strptime(date, "%Y%m%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date)
        raise Exception(msg)


def check_time(time):
    try:
        return dt.strptime(time, "%H:%M")
    except ValueError:
        msg = "Not a valid timestamp: '{0}'.".format(time)
        raise Exception(msg)


@click.group()
def cli():
    """Tidal Surface Processing Tasks"""
    pass


@cli.command()
@click.option('-i', '--infile', type=click.Path(dir_okay=False), required=True)
@click.option('-t', '--template', type=click.Path(dir_okay=False), required=True)
@click.option('-d', '--date', type=click.STRING, required=True,
              callback=click_callback(check_date))
@click.option('-o', '--outfile', type=click.Path(dir_okay=False), required=True)
@click.option('-p', '--pfs', type=click.Path(dir_okay=False), required=True)
def pfs(**kwargs):
    """Create pfs file for input to MIKE

    ------------------------------------

    Options:

    -i/--infile : Path to AOI polygon shapefile e.g. C:/tides/aoi.shp

    -t/--template : Path to template textfile e.g. C:/tides/template.txt

    -d/--date : Image acquisiton date (yyyymmdd) e.g. 20150131

    -o/--outfile : Path to output points shapefile e.g. C:/tides/points.shp

    -p/--pfs : Path to output pfs file e.g. C:/tides/output.pfs

    Example use:

    tidepods pfs -s C:/tides/aoi.shp -t C:/tides/template.txt -d 20170131
    -o C:/tides/outpts.shp -p C:/tides/outpfs.pfs
    """
    from . import pfs_shp as ps
    ps.write_pfs(**kwargs)
    ps.write_pts(**kwargs)


@cli.command()
@click.option('-i', '--infile', type=click.Path(dir_okay=False), required=True)
@click.option('-d', '--date', type=click.STRING, required=True,
              callback=click_callback(check_date))
@click.option('-t', '--timestamp', type=click.STRING, required=True,
              callback=click_callback(check_time))
@click.option('-s', '--shapefile', type=click.Path(dir_okay=False), required=True)
@click.option('-o', '--outfile', type=click.Path(dir_okay=False), required=True)
def tides(**kwargs):
    """Extract tide values from dfs0 file to a point shapefile

    ------------------------------------

    Options:

    -i/--infile : Path to dfs0 file created using tidepods pfs e.g. C:/tides/aoi.dfs0

    -d/--date : Image acquisiton date (yyyymmdd) e.g. 20150131)

    -t/--timestamp : Image acquisition time (HH:MM) e.g. 12:34

    -s/--shapefile : Path to input points shapefile created using tidepods pfs
    e.g. C:/tides/points.shp

    -o/--outfile : Path to output points shapefile containign the tidal values

    Example use:

    tidepods tides -i C:/tides/aoi.dfs0 -d 20150131 tt-t 12:34 -s C:/tides/points.shp
    -o C:/tide/tidal_points.shp
    """
    from . import write_tides as wt
    wt.write_tide_values(**kwargs)
