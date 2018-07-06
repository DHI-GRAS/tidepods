import click
from datetime import datetime as dt


class TimeType(click.ParamType):
    name = 'time'

    def convert(self, time, _, __):
        try:
            return dt.strptime(time, "%H:%M").time()
        except ValueError as exception:
            msg = "Not a valid timestamp: '{0}'.".format(time)
            raise ValueError(msg) from exception


class DateType(click.ParamType):
    name = 'date'

    def convert(self, date, _, __):
        try:
            return dt.strptime(date, "%Y%m%d").date()
        except ValueError as exception:
            msg = "Not a valid date: '{0}'.".format(date)
            raise ValueError(msg) from exception


TIMEIN = TimeType()
DATEIN = DateType()


@click.group()
def cli():
    """Tidal Surface Processing Tasks"""
    pass


@cli.command()
@click.option('-i', '--infile', type=click.Path(dir_okay=False, exists=True), required=True,
              help='Path to AOI polygon shapefile e.g. C:/tides/aoi.shp')
@click.option('-t', '--template', type=click.Path(dir_okay=False, exists=True), required=True,
              help='Path to template textfile e.g. C:/tides/template.txt')
@click.option('-d', '--date', type=DATEIN, required=True,
              help='Image acquisiton date (yyyymmdd) e.g. 20150131')
@click.option('-o', '--outfile', type=click.Path(dir_okay=False), required=True,
              help='Path to output points shapefile e.g. C:/tides/pts.shp')
@click.option('-p', '--pfs', type=click.Path(dir_okay=False), required=True,
              help='Path to output pfs file e.g. C:/tides/output.pfs')
def pfs(**kwargs):
    """Create pfs file for input to MIKE

    Example use:

    tidepods pfs -i C:/tides/aoi.shp -t C:/tides/template.txt -d 20170131
    -o C:/tides/pts.shp -p C:/tides/outpfs.pfs
    """
    from . import pfs_shp as ps
    ps.write_pfs(**kwargs)
    ps.write_pts(**kwargs)


@cli.command()
@click.option('-i', '--infile', type=click.Path(dir_okay=False, exists=True), required=True,
              help='Path to dfs0 file created using tidepods pfs e.g. C:/tides/aoi.dfs0')
@click.option('-d', '--date', type=DATEIN, required=True,
              help='Image acquisiton date (yyyymmdd) e.g. 20150131')
@click.option('-t', '--timestamp', type=TIMEIN, required=True,
              help='Image acquisition time (HH:MM) e.g. 12:34')
@click.option('-s', '--shapefile', type=click.Path(dir_okay=False, exists=True), required=True,
              help='Path to input pts shapefile created using tidepods pfs e.g. C:/tides/pts.shp')
@click.option('-o', '--outfile', type=click.Path(dir_okay=False), required=True,
              help='Path to output points shapefile containing the tidal values e.g. C:/tides/pts_tides.shp')
@click.option('-p', '--sdkpath', type=click.Path(dir_okay=True, file_okay=False),
              default=r'C:\Program Files (x86)\DHI\2016\MIKE SDK\bin', show_default=True,
              help='Path to DHI SDK install directory')
def tides(date, timestamp, **kwargs):
    """Extract tide values from dfs0 file to a point shapefile

    Example use:

    tidepods tides -p "C:/Program Files (x86)/DHI/2016/MIKE SDK/bin" -i C:/tides/aoi.dfs0
    -d 20150131 -t 12:34 -s C:/tides/pts.shp -o C:/tides/pts_tides.shp
    """
    kwargs.update(date=dt.combine(date, timestamp))
    from . import write_tides as wt
    wt.write_tide_values(**kwargs)
