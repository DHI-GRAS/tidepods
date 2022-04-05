import click
from datetime import datetime as dt

@click.group()
def cli():
    """Tidal Surface Processing Tasks."""
    pass


@cli.command()
@click.option(
    "-s",
    "--safe",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    required=True,
    help="Path to Sentinel 2 SAFE folder for tide surface creation e.g. C:/S2A_MSIL1C_20180524T023551_N0206_R089_T50QQM_20180524T051356.SAFE",
)
@click.option(
    "-o",
    "--outfolder",
    type=click.Path(dir_okay=True, file_okay=False),
    required=True,
    help="Path to output folder where tidepods will create the tidal surface raster "
    "e.g. C:/tides",
)
@click.option(
    "-l",
    "--level",
    type=click.Choice(["LAT", "MSL"]),
    required=True,
    help="Tide value return type, LAT (Lowest Astronomical Tide) "
    "or MSL (Mean Sea Level)",
)
@click.option(
    "-m",
    "--landmask",
    type=click.Path(dir_okay=False, file_okay=True),
    help="Path to land mask shapefile. e.g. C:/land_mask.shp",
)
def s2(**kwargs):
    """Create a tidal surface for a Sentinel 2 acquisition.

    Example use:

    tidepods s2 -s C:/path-to-sentinel-folder/S2B_MSIL1C_XXX.SAFE 
    -l MSL -o C:/user/path-to-output-folder/
    
    """
    from tidepods import sentinel2

    sentinel2.main(**kwargs)


@cli.command()
@click.option(
    "-s",
    "--shapefile",
    type=click.Path(dir_okay=False, file_okay=True),
    required=True,
    help="Path to input shapefile " "e.g. C:/tides/processed_icesat_pts.shp",
)
@click.option(
    "-o",
    "--outfolder",
    type=click.Path(dir_okay=True, file_okay=False),
    required=True,
    help="Path to output folder where tidepods will create the updated shapefile "
    "e.g. C:/tides",
)
@click.option(
    "-l",
    "--level",
    type=click.Choice(["LAT", "MSL"]),
    required=True,
    help="Tide value return type, LAT (Lowest Astronomical Tide) "
    "or MSL (Mean Sea Level)",
)
def icesat2(**kwargs):
    """Extract tide levels at icesat_2 acquisition points.

    Example use:

    tidepods icesat2 -s A:/user/path-to-shapefile-folder/ICESat-2/Tidepods.shp
     -l MSL -o A:/user/path-to-output-folder/ICESat-2/Tidepods.shp

    """
    from tidepods import icesat2

    icesat2.main(**kwargs)
    


# Andrea parts

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


@cli.command()
@click.option(
    "-i",
    "--infile",
    type=click.Path(dir_okay=False, file_okay=True),
    required=True,
    help="Path to AOI raster (.tif) or shapefile for points creation e.g. C:/tides/aoi.tif",
)
@click.option(
    "-d", 
    "--date",
    type=DATEIN,
    required=False,
    help="Image acquisiton date (yyyymmdd) e.g. 20150131",
)
@click.option(
    "-t",
    "--timestamp",
    type=TIMEIN,
    required=False,
    help="Image acquisition time (HH:MM) e.g. 10:30",
)
@click.option(
    "-o",
    "--outfolder",
    type=click.Path(dir_okay=True, file_okay=False),
    required=False,
    help="Path to output points shapefile containing the tidal values e.g. C:/tides",
)
@click.option(
    "-l",
    "--level",
    type=click.Choice(["LAT", "MSL"]),
    required=True,
    help="Tide value return type, LAT (Lowest Astronomical Tide) "
    "or MSL (Mean Sea Level)",
)
@click.option(
    "-r",
    "--resolution",
    type=float,
    required=False,
    help="Resolution of tif file ",    
    
)

def vhr(**kwargs):
    """Create a point shp containing tide values over AOI (VHR image).
    
    Example use:
    tidepods vhr -i A:/user/path-to-vhrfile/vhr.tif -d 20200815 -t 15:45 -l MSL
    """
    from tidepods import vhr_imdfile
    vhr_imdfile.main(**kwargs)


TIMEIN = TimeType()
DATEIN = DateType()


@cli.command()
@click.option('-i', '--infile', type=click.Path(dir_okay=False, exists=True), required=True,
              help='Path to AOI raster or shapefile for points creation e.g. C:/tides/aoi.tif')

@click.option('-d', '--date', type=DATEIN, required=True,
              help='Image acquisiton date (yyyymmdd) e.g. 20150131')

@click.option('-t', '--timestamp', type=TIMEIN, required=True,
              help='Image acquisition time (HH:MM) e.g. 10:30')

@click.option('-o', '--outfolder', type=click.Path(dir_okay = True), required=True,
              help='Path to output points shapefile containing the tidal values '
              'e.g. C:/tides')

@click.option('-l', '--level', type=click.Choice(['LAT', 'MSL']), required=True,
              help='Tide value return type, LAT (Lowest Astronomical Tide) '
              'or MSL (Mean Sea Level)')

def points(**kwargs):
    """Create a point shapefile containing tide values over an AOI

    Example use:
    tidepods points -i A:/user/path-to-tif-file/mosaic.tif -l MSL 
    -o A:/user/path-to-output-folder/points.shp -d 20200407 -t 10:40

    """

    from tidepods import points
   
    points.main(**kwargs)


 # Timeseries
 
@cli.command()
@click.option('-i', '--infile', type=click.Path(dir_okay=False, exists=True), required=True,
              help='Path to AOI raster or shapefile for points creation e.g. C:/tides/aoi.tif')

@click.option('-d', '--date', type=DATEIN, required=True,
              help='Image acquisiton date (yyyymmdd) e.g. 20150131')

@click.option('-t', '--timestamp', type=TIMEIN, required=True,
              help='Image acquisition time (HH:MM) e.g. 10:30')

@click.option('-o', '--outfolder', type=click.Path(dir_okay = True), required=True,
              help='Path to output points shapefile containing the tidal values '
              'e.g. C:/tides')
              

def timeseries(**kwargs):
    """Create a tide timeseries csv file over an AOI, 
    shapefile containing MSL, HAT and LAT tide values and
    rasters containg MSL, HAT and LAT tide values.

    Example use:
    tidepods timeseries -i A:/user/path-to-tif-file/AOI.tif  
    -o A:/user/path-to-output-folder/timeseries -d 20200407 -t 10:40

    """

    from tidepods import points_timeseries
   
    points_timeseries.main(**kwargs)   

