# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 08:06:48 2021

@author: vlro
"""
import pathlib
import os
import shutil
import subprocess
import datetime
import fiona

VALID_LEVELS = ["LAT", "MSL"]


def read_shapefile_pts(shape):
    c = fiona.open(shape)
    pts = [p for p in c]

    return pts


def read_shapefile_props(shape):
    c = fiona.open(shape)

    crs = c.crs
    driver = c.driver
    schema = c.schema

    return crs, driver, schema


def write_pts(pts, tv, crs, driver, schema, outfile):

    for p, t in zip(pts, tv):
        p["properties"]["tide_level"] = t

    schema["properties"].update({"tide_level": "float:24.15"})

    with fiona.open(outfile, "w", crs=crs, driver=driver, schema=schema) as o:
        for p in pts:
            o.write(p)


def generate_pfs(pts, mikepath, tempdir):
    """Generate a pfs file using DHI.PFS.

    Parameters
    ----------
    pts : list
        List of shapely points generated by create_pts().
    mikepath : pathlib Path
        Path to MIKE installation directory.
    tempdir : str
        Path to the temporary working directory.

    Raises
    ------
    ValueError
        If DHI.PFS could not be imported or is not found in the mike folder.
    ValueError
        If the PFS file could not be created.

    """
    one_date = pts[0]["properties"]["time"]
    date = datetime.datetime.strptime(one_date, "%Y-%m-%d %H:%M")
    temppfs = os.path.join(tempdir, "temp.pfs")

    dhi_pfs_path = list(mikepath.glob("**/Mike SDK/**/*DHI.PFS.dll"))[0]
    constituents_path = list(
        mikepath.glob("**/global_tide_constituents_height_0.125deg.dfs2")
    )[0]
    prepack_path = list(mikepath.glob("**/Tide_Constituents/prepack.dat"))[0]

    import clr
    import System

    try:
        clr.AddReference(str(dhi_pfs_path))
        import DHI.PFS

    except (ImportError, System.IO.FileNotFoundException) as exception:
        msg = f'DHI.PFS not found. Is the path correct: "{dhi_pfs_path}"?'
        raise ValueError(msg) from exception

    # Begin PFS Generation Parameters using DHI.PFS.PFSBuilder

    pfsbuilder = DHI.PFS.PFSBuilder()

    pfsbuilder.AddTarget("TidePredictor")  # First Section

    pfsbuilder.AddKeyword("Name")
    pfsbuilder.AddString("Icesat2-Points")
    pfsbuilder.AddKeyword("constituent_file_name")
    pfsbuilder.AddString(str(constituents_path))
    pfsbuilder.AddKeyword("prepack_file_name")
    pfsbuilder.AddString(str(prepack_path))
    pfsbuilder.AddKeyword("start_date")
    DHI.PFS.PFSExtensions.AddDate(pfsbuilder, System.DateTime(date.year, 1, 1))
    pfsbuilder.AddKeyword("end_date")
    DHI.PFS.PFSExtensions.AddDate(pfsbuilder, System.DateTime(date.year, 12, 31))
    pfsbuilder.AddKeyword("timestep")
    pfsbuilder.AddDouble(0.5)
    pfsbuilder.AddKeyword("number_of_files")
    pfsbuilder.AddInt(1)
    pfsbuilder.AddKeyword("ShowGeographic")
    pfsbuilder.AddInt(1)

    pfsbuilder.AddSection("File_1")  # File Section
    pfsbuilder.AddKeyword("format")
    pfsbuilder.AddInt(0)
    pfsbuilder.AddKeyword("file_name")
    pfsbuilder.AddFileName("temp.dfs0")
    pfsbuilder.AddKeyword("description")
    pfsbuilder.AddString("Predicted Tide Level")
    pfsbuilder.AddKeyword("number_of_points")
    pfsbuilder.AddInt(len(pts))

    # Points section enumerated for each point generated within shapefile

    for p in pts:
        pid = int(p["id"]) + 1
        pfsbuilder.AddSection("Point_" + (str(pid)))
        pfsbuilder.AddKeyword("description")
        pfsbuilder.AddInt(pid)
        pfsbuilder.AddKeyword("y")
        pfsbuilder.AddDouble(p["properties"]["lat"])
        pfsbuilder.AddKeyword("x")
        pfsbuilder.AddDouble(p["properties"]["lon"])
        pfsbuilder.EndSection()

    pfsbuilder.EndSection()
    pfsbuilder.EndSection()
    pfsbuilder.Write(temppfs)

    if not os.path.exists(temppfs):
        raise ValueError("PFS file not created. Recheck creation options.")


def make_dfs0(mikepath, pfsfile):
    """Generate a dfs0 file from the input PFS in the same directory.

    Parameters
    ----------
    mikepath : str
        Path to MIKE installation directory.
    pfsfile : str
        Path to PFS file.

    Raises
    ------
    ValueError
        If the DFS file could not be created.
    """
    tp = str(list(mikepath.glob("**/TidePredictor.exe"))[0])
    cmd = [tp, pfsfile]
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output
            )
        )
    dfsfile = pfsfile.replace(".pfs", ".dfs0")

    if not os.path.exists(dfsfile):
        raise ValueError(
            f"DFS file not created. Please check that you are connected to the VPN and that the path to the tide predictor is correct: {tp}."
        )


def tide_values_from_dfs0(mikepath, pts, dfsfilepath, level):
    """Read and extract values from dfs0 file using DHI.Generic.MikeZero.DFS.

    Parameters
    ----------
    mikepath : str
        Path to MIKE installation directory.
    meta : dictionary
        Metadata dictionary created by read_meta().
    dfsfilepath : str
        Path to the dfs file created by make_dfs0().
    level : str
        Click option LAT or MSL.

    Returns
    -------
    tide_values : list
        List of tide values for image acquisiton date and time.

    Raises
    ------
    ValueError
        If an invalid level type was provided.
    ValueError
        If DHI.Generic could not be imported or is not found in the sdkpath folder.
    ValueError
        If no tide values could be generated.

    """
    if level not in VALID_LEVELS:
        raise ValueError(f"Level should be one of {VALID_LEVELS}, not {level}.")

    import clr

    clr.AddReference("System")
    import System

    generic_mike_zero_path = list(
        mikepath.glob("**/Mike SDK/**/*DHI.Generic.MikeZero.DFS.dll")
    )[0]
    try:
        clr.AddReference(str(generic_mike_zero_path))
        import DHI.Generic.MikeZero.DFS

    except (ImportError, System.IO.FileNotFoundException) as exception:
        msg = f'DHI.Generic not found. Is the path to the mike installation directory correct: "{mikepath}"?'
        raise ValueError(msg) from exception

    dfs_img_datetime = datetime.datetime.strptime(
        pts[0]["properties"]["time"], "%Y-%m-%d %H:%M"
    )

    dfsfile = DHI.Generic.MikeZero.DFS.DfsFileFactory.DfsGenericOpen(dfsfilepath)
    tide_values = []

    # read timestep in seconds, convert to minutes
    timestep = int(dfsfile.FileInfo.TimeAxis.TimeStep / 60)
    sdt = dfsfile.FileInfo.TimeAxis.StartDateTime
    dfs_start_datetime = datetime.datetime(
        *(getattr(sdt, n) for n in ["Year", "Month", "Day", "Hour", "Minute", "Second"])
    )

    diff = dfs_img_datetime - dfs_start_datetime
    img_timestep = int(((diff.days * 24 * 60) + (diff.seconds / 60)) / timestep)

    for i in range(len(dfsfile.ItemInfo)):
        min_value = float(dfsfile.ItemInfo[i].MinValue)
        acq_value = dfsfile.ReadItemTimeStep(i + 1, img_timestep).Data[
            0
        ]  # Value c.f. MSL

        if level == "LAT":
            lat_value = acq_value - min_value  # Value above LAT
            tide_values.append(lat_value)
        elif level == "MSL":
            tide_values.append(acq_value)
        else:
            raise ValueError("Invalid level.")

    dfsfile.Dispose()

    if not tide_values:
        raise ValueError("No tide values generated, recheck AOI")

    return tide_values


def main(shapefile, outfolder, level):

    # mikepath = os.environ['MIKE'] = "C:\Program Files (x86)\DHI"
    mikepath = os.environ.get("MIKE")
    mikepath = pathlib.Path(mikepath)

    if not os.path.isdir(outfolder):
        os.makedirs(outfolder)

    shapefile_path = pathlib.Path(shapefile)
    shapefile_name = shapefile_path.stem
  
    pts = read_shapefile_pts(shapefile)

    tempfolder = os.path.join(outfolder, "temp")
    os.makedirs(tempfolder, exist_ok=True)
    generate_pfs(pts, mikepath, tempfolder)

    temp_pfs_path = str(list(pathlib.Path(tempfolder).glob("*.pfs"))[0])
    make_dfs0(mikepath, temp_pfs_path)

    temp_dfs0_path = str(list(pathlib.Path(tempfolder).glob("*.dfs0"))[0])
    tv = tide_values_from_dfs0(mikepath, pts, temp_dfs0_path, level)

    outfilename = "_".join([shapefile_name, level, "tides.shp"])
    outfile = os.path.join(outfolder, outfilename)

    crs, driver, schema = read_shapefile_props(shapefile)
    write_pts(pts, tv, crs, driver, schema, outfile)

    shutil.rmtree(tempfolder)
