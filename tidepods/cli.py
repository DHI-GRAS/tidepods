import click

@click.group()
def cli():
    """Tidal Surface Processing Tasks"""
    pass

@cli.command()
@click.argument('shp', type=click.Path(dir_okay=False))
@click.argument('template', type=click.Path(dir_okay=False))
@click.argument('acq_date', type=click.INT)
@click.argument('pfs', type=click.Path(dir_okay=False))

def pfs(**kwargs):
    """Create pfs file for input to MIKE
    
    ------------------------------------
    
    Arguments:
    
    shp : Path to AOI shapefile e.g. C:/tides/aoi.shp
    
    template : Path to template textfile e.g. C:/tides/template.txt
    
    acq_date : Image acquisiton date (YYYYMMDD)
    
    pfs : Path to output pfs file e.g. C:/tides/outpfs.pfs
    
    Example use:
    
    tidepods pfs C:/tides/aoi.shp C:/tides/template.txt 20171031 C:/tides/outpfs.pfs
    """
    from . import write_pfs as wp
    wp.write_pfs(**kwargs)
    
