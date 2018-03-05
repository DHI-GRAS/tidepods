import click
from datetime import datetime as dt

def click_callback(f):
    return lambda _, __, x: f(x)
    
def check_date(date):
    try:
        return dt.strptime(date , "%Y%m%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date)
        raise Exception(msg)
        
@click.group()
def cli():
    """Tidal Surface Processing Tasks"""
    pass

@cli.command()
@click.option('-s','--shp', type=click.Path(dir_okay=False), required=True)
@click.option('-t', '--template', type=click.Path(dir_okay=False), required=True)
@click.option('-d', '--date', type=click.STRING, required=True, callback=click_callback(check_date))
@click.argument('pfs', type=click.Path(dir_okay=False))

def pfs(**kwargs):
    """Create pfs file for input to MIKE
    
    ------------------------------------
    
    Arguments:
    
    pfs : Path to output pfs file e.g. C:/tides/outpfs.pfs
    
    Options:
    
    -s/--shp : Path to AOI shapefile e.g. C:/tides/aoi.shp
    
    -t/--template : Path to template textfile e.g. C:/tides/template.txt
    
    -d/--date: Image acquisiton date (YYYYMMDD)
    Example use:
    
    tidepods pfs -s C:/tides/aoi.shp -t C:/tides/template.txt -d 20171031 C:/tides/outpfs.pfs
    """
    from . import write_pfs as wp
    wp.write_pfs(**kwargs)

if __name__ == '__main__':
    pfs()
    
