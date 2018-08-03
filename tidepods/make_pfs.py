import os
import subprocess
import sys

from tidepods import generate_pts


def generate_pfs(infile, date, mikepath, tempdir):
    """Generates a pfs file using DHI.PFS.

    Parameters
    ----------
    infile : str
        Path to polygon or raster AOI.
    date : datetime.datetime
        Image acqusition date and time.
    mikepath : str
        Path to MIKE installation directory.
    tempdir : str
        Path to temporary directory.

    Returns
    -------
    temppfs : str
        Path to the generated pfs file within the tempdir.

    Raises
    -------
    ValueError
        If the path to the MIKESDK does not exist.
    ValueError
        If DHI.PFS could not be imported or is not found in the sdkpath folder.
    ValueError
        If the PFS file could not be created.

    """
    plist = generate_pts.create_pts(infile)

    temppfs = os.path.join(tempdir, 'temp.pfs')
    sdkpath = os.path.join(mikepath, r'MIKE SDK\bin')
    constituents_path = os.path.join(mikepath,
                                     r'MIKE Zero\Application Data\Tide_Constituents\global_tide'
                                     '_constituents_0.125deg.dfs2')
    prepack_path = os.path.join(mikepath,
                                r'MIKE Zero\Application Data\Tide_Constituents\prepack.dat')

    import clr
    clr.AddReference('System')
    import System

    if not os.path.isdir(sdkpath):
        raise ValueError(f'SDK Path folder not found. Is the path to the sdk correct: "{sdkpath}"?')

    sys.path.insert(0, sdkpath)

    try:
        clr.AddReference('DHI.PFS')
        import DHI.PFS

    except (ImportError, System.IO.FileNotFoundException) as exception:
        msg = f'DHI.PFS not found. Is the path to the sdk correct: "{sdkpath}"?'
        raise ValueError(msg) from exception

    finally:
        sys.path.pop(0)

    # Begin PFS Generation Parameters using DHI.PFS.PFSBuilder

    pfsbuilder = DHI.PFS.PFSBuilder()

    pfsbuilder.AddTarget('TidePredictor')  # First Section

    pfsbuilder.AddKeyword('Name')
    pfsbuilder.AddString(str(infile))
    pfsbuilder.AddKeyword('constituent_file_name')
    pfsbuilder.AddString(str(constituents_path))
    pfsbuilder.AddKeyword('prepack_file_name')
    pfsbuilder.AddString(str(prepack_path))
    pfsbuilder.AddKeyword('start_date')
    DHI.PFS.PFSExtensions.AddDate(pfsbuilder, System.DateTime(date.year, 1, 1))
    pfsbuilder.AddKeyword('end_date')
    DHI.PFS.PFSExtensions.AddDate(pfsbuilder, System.DateTime(date.year, 12, 31))
    pfsbuilder.AddKeyword('timestep')
    pfsbuilder.AddDouble(0.5)
    pfsbuilder.AddKeyword('number_of_files')
    pfsbuilder.AddInt(1)
    pfsbuilder.AddKeyword('ShowGeographic')
    pfsbuilder.AddInt(1)

    pfsbuilder.AddSection('File_1')  # File Section
    pfsbuilder.AddKeyword('format')
    pfsbuilder.AddInt(0)
    pfsbuilder.AddKeyword('file_name')
    pfsbuilder.AddFileName('temp.dfs0')
    pfsbuilder.AddKeyword('description')
    pfsbuilder.AddString('Predicted Tide Level')
    pfsbuilder.AddKeyword('number_of_points')
    pfsbuilder.AddInt(len(plist))

    # Points section enumerated for each point generated within shapefile

    for pid, p in enumerate(plist, 1):
        pfsbuilder.AddSection('Point_' + str(pid))
        pfsbuilder.AddKeyword('description')
        pfsbuilder.AddInt(pid)
        pfsbuilder.AddKeyword('y')
        pfsbuilder.AddDouble(p.coords[0][1])
        pfsbuilder.AddKeyword('x')
        pfsbuilder.AddDouble(p.coords[0][0])
        pfsbuilder.EndSection()

    pfsbuilder.EndSection()
    pfsbuilder.EndSection()
    pfsbuilder.Write(temppfs)

    if not os.path.exists(temppfs):
        raise ValueError('PFS file not created. Recheck creation options.')

    return temppfs


def make_dfs0(infile, date, mikepath, tempdir):
    """Generates a dfs0 file from the above PFS.

    Parameters
    ----------
    infile : str
        Path to polygon or raster AOI.
    date : datetime.datetime
        Image acqusition date and time.
    mikepath : str
        Path to MIKE installation directory.
    tempdir : str
        Path to temporary directory.

    Returns
    -------
    dfsfile : str
        Path to the generated dfs0 file within the tempdir.

    Raises
    -------
    ValueError
        If the DFS file could not be created.
    """

    pfsfile = generate_pfs(infile, date, mikepath, tempdir)
    tp = os.path.join(mikepath, r'bin\x64\TidePredictor.exe')
    cmd = [tp, pfsfile]

    subprocess.check_call(cmd)
    dfsfile = pfsfile.replace('.pfs', '.dfs0')

    if not os.path.exists(dfsfile):
        raise ValueError(f'DFS file not created. Is the path to the tide predictor correct:"{tp}"?')

    return dfsfile
