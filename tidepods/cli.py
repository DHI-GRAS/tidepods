import click


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

    tidepods s2 -s C:/S2A_MSIL1C_20180524T023551_N0206_R089_T50QQM_20180524T051356.SAFE -o C:/tides_output -l MSL -m C:/tides_input/land_mask.shp
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

    tidepods icesat2 -s C:/tides/processed_icesat_pts.shp -o C:/tides_output -l MSL
    """
    from tidepods import icesat2

    icesat2.main(**kwargs)
