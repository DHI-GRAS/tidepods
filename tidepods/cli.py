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
              help='Path to AOI raster file for points creation e.g. C:/tides/aoi.tif')
@click.option('-d', '--date', type=DATEIN, required=True,
              help='Image acquisiton date (yyyymmdd) e.g. 20150131')
@click.option('-t', '--timestamp', type=TIMEIN, required=True,
              help='Image acquisition time (HH:MM) e.g. 10:30')
@click.option('-o', '--outfile', type=click.Path(dir_okay=False), required=True,
              help='Path to output points shapefile containing the tidal values '
              'e.g. C:/tides/pts_tides.shp')
@click.option('-l', '--level', type=click.Choice(['LAT', 'MSL']), required=True,
              help='Tide value return type, LAT (Lowest Astronomical Tide) '
              'or MSL (Mean Sea Level)')
@click.option('-p', '--mikepath', type=click.Path(dir_okay=True, file_okay=False),
              default=r'C:\Program Files (x86)\DHI\2016', show_default=True,
              help='Path to DHI MIKE version install root directory')
def points(date, timestamp, **kwargs):
    """Create a point shapefile containing tide values over an AOI

    Example use:

    tidepods points -p "C:/Program Files (x86)/DHI/2016/MIKE SDK/bin" -i C:/tides/aoi.tif
    -d 20150131 -t 10:30 -o C:/tides/pts_tides.shp
    """
    kwargs.update(date=dt.combine(date, timestamp))
    from tidepods import create_tides as ct
    ct.main(**kwargs)
