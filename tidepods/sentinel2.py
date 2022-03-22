# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 10:57:13 2021

@author: vlro
"""
import pathlib
import xml.etree.ElementTree as ET
import numpy as np
from affine import Affine
from shapely.geometry import box, Point, shape, mapping
import fiona
from fiona.crs import from_epsg
import datetime
import os
import subprocess
import rasterio
from rasterio import features
import shutil
from rasterio.io import MemoryFile
import rasterio.warp
import rasterio.mask

VALID_LEVELS = ["LAT", "MSL"]


def read_meta(metafile):
    """
    Read metadata xml file of Sentinel 2 tile.

    Parameters
    ----------
    metafile : Path or str
        Path to the MTD_TL.xml file in the S2 Granule/Product subdir of the .SAFE.

    Returns
    -------
    meta : Dictionary
        Dictionary of relevant metadata used to create the tide surface.

    """
    root = ET.parse(metafile).getroot()
    meta = {}

    # get raster tile_id
    meta["tile_id"] = [x.text for x in root.iter("TILE_ID")][0]
    # get raster sensing time
    meta["sensing_time"] = [x.text for x in root.iter("SENSING_TIME")][0][0:19]

    # get raster epsg
    meta["epsg"] = [x.text for x in root.iter("HORIZONTAL_CS_CODE")][0]

    # get raster shape
    for x in root.iter("Size"):
        if x.attrib["resolution"] == "10":
            meta["nrows"] = float(x.find("NROWS").text)
            meta["ncols"] = float(x.find("NCOLS").text)

    # get raster geoposition for affine transform
    for x in root.iter("Geoposition"):
        if x.attrib["resolution"] == "10":
            meta["ulx"] = float(x.find("ULX").text)
            meta["uly"] = float(x.find("ULY").text)
            meta["xdim"] = float(x.find("XDIM").text)
            meta["ydim"] = float(x.find("YDIM").text)

    return meta


def make_profile(meta):
    """
    Create a rasterio profile based on the metadata file provided.

    Parameters
    ----------
    meta : Dictionary
        Dictionary of metadata information as returned by read_meta().

    Returns
    -------
    profile : Dictionary
        Rasterio profile.

    """
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": None,
        "width": meta["nrows"],
        "height": meta["ncols"],
        "count": 1,
        "crs": meta["epsg"],
        "transform": Affine(
            meta["xdim"], 0.0, meta["ulx"], 0.0, meta["ydim"], meta["uly"]
        ),
    }

    return profile


def make_ds_array(profile):
    """
    Create an empty numpy array of the needed shape as per the profile.

    Parameters
    ----------
    profile : Dictionary
        The rasterio profile created by make_profile().

    Returns
    -------
    ds : Array
        Empty numpy array.

    """
    ds = np.empty(
        [int(profile["width"]), int(profile["height"])], dtype=profile["dtype"]
    )
    ds = ds[np.newaxis, :, :]

    return ds


def get_dataset_outline(dataset, profile, target_epsg=4326, buffer=2):
    """
    Get the outline of the input raster dataset, reporject and buffer if wanted.

    Parameters
    ----------
    dataset : Array
        Numpy array as created by make_ds_array().
    profile : Dictionary
        The rasterio profile created by make_profile()..
    target_epsg : Integer, optional
        The target EPSG code. The default is 4326.
    buffer : Float, optional
        The wanted buffer to be added to the shape. The value should be
        consistent with the given EPSG. i.e. give buffer size in degrees for
        EPSG 4326. The default is 0.125.

    Returns
    -------
    shp : Shapely object
        Input dataset AOI bounds as a shapely polygon object.

    """
    with MemoryFile() as memfile:
        with memfile.open(**profile) as ds:
            ds.write(dataset)

    left, bottom, right, top = ds.bounds
    in_crs = ds.crs

    if target_epsg is None:
        shp = box(left, bottom, right, top)
        

    else:
        out_crs = rasterio.crs.CRS.from_epsg(target_epsg)
        minx, miny, maxx, maxy = rasterio.warp.transform_bounds(
            in_crs, out_crs, left, bottom, right, top
        )
        shp = box(minx, miny, maxx, maxy)

    if buffer:
        shp = shp.buffer(buffer, join_style=2)

    return shp


def create_pts(shp, spacing):
    """Generate fixed distance points within a polygon.

    Parameters
    ----------
    infile : str
        Path to polygon or raster AOI.

    Returns
    -------
    plist : list
        List of shapely points for points within infile.

    Raises
    ------
    ValueError
        If plist is empty as no points have been generated.

    """
    bounds = shp.bounds
    minx, miny, maxx, maxy = bounds
    plist = []
    offset = spacing / 2
    for x in np.arange(minx + offset, maxx - offset, spacing):
        for y in np.arange(miny + offset, maxy - offset, spacing):
            p = Point(x, y)
            if p.within(shp):
                plist.append(p) 

    if not plist:
        raise ValueError(
            "No points generated. Is the input file covering a large enough AOI?"
        )
  
   
    return plist


def generate_pfs(pts, meta, mikepath, tempdir):
    """Generate a pfs file using DHI.PFS.

    Parameters
    ----------
    pts : list
        List of shapely points generated by create_pts().
    meta : dictionary
        Metadata dictionary created by read_meta().
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
    date = datetime.datetime.strptime(meta["sensing_time"], "%Y-%m-%dT%H:%M:%S")
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
    pfsbuilder.AddString(str(meta["tile_id"]))
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

    for pid, p in enumerate(pts, 1):
        pfsbuilder.AddSection("Point_" + str(pid))
        pfsbuilder.AddKeyword("description")
        pfsbuilder.AddInt(pid)
        pfsbuilder.AddKeyword("y")
        pfsbuilder.AddDouble(p.coords[0][1])
        pfsbuilder.AddKeyword("x")
        pfsbuilder.AddDouble(p.coords[0][0])
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


def tide_values_from_dfs0(mikepath, meta, dfsfilepath, level):
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
        meta["sensing_time"], "%Y-%m-%dT%H:%M:%S"
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


def write_tide_values(tide_values, plist, level, outfile, outfolder):
    """Write generated points and tide values to a new shapefile.

    Parameters
    ----------
    tide_values : list
        List of tide values generated by tide_values_from_dfs0().
    plist : list
        List of shapely points generated by create_pts().
    level : str
        Click option LAT or MSL.

    Returns
    -------
    ms : Fiona collection
        Points

    """
    pts_schema = {
        "geometry": "Point",
        "properties": {"p_ID": "int", str(level): "float"},
    }

    mem_file = fiona.MemoryFile()
    ms = mem_file.open(crs=from_epsg(4326), driver="ESRI Shapefile", schema=pts_schema,)
   
    out_name_points = outfile.split('\\')[-1][:-4]+'.shp'

    for pid, (p, tv) in enumerate(zip(plist, tide_values)):
        prop = {"p_ID": int(pid + 1), str(level): float(tv)}
        ms.write({"geometry": mapping(p), "properties": prop})
    
    
    with fiona.open(outfile, 'w', crs=from_epsg(4326), driver='ESRI Shapefile',
                    schema=pts_schema) as output:
        for pid, (p, tv) in enumerate(zip(plist, tide_values)):
            prop = {"p_ID": int(pid + 1), str(level): float(tv)}
            output.write({"geometry": mapping(p), "properties": prop})

    
    return ms


def rasterize_points(pc, shp):
    """
    Rasterize the created points

    Parameters
    ----------
    pc : Fiona collection
        Points collection as created by write_tide_values().
    shp : Shapely shape
        Shapely polygon as created by get_dataset_outline().

    Returns
    -------
    image : array
        Image array.
    profile : dictionary
        Dictionary of the updated profile.

    """
    pc.mode = "r"  # set collection mode to read

    # transform for the target raster, hardcoded 0.125 deg resoution as
    # that is the resolution of the tide values
    tr = rasterio.transform.from_origin(shp.bounds[0], shp.bounds[-1], 0.125, 0.125)

    minx, miny, maxx, maxy = shp.bounds
    xsize = int((maxx - minx) / 0.125)
    ysize = int((maxy - miny) / 0.125)

    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": None,
        "width": xsize,
        "height": ysize,
        "count": 1,
        "crs": "EPSG:4326",
        "transform": tr,
    }

    image = features.rasterize(
        (
            (p["geometry"], p["properties"][[*pc.schema["properties"].keys()][1]])
            for p in pc
        ),
        out_shape=(xsize, ysize),
        transform=tr,
    )
    image = image[np.newaxis, :, :]

    return image, profile


def mask_raster(image, profile, shp, landmask):
    """
    Mask the output tides raster with the land mask.

    Parameters
    ----------
    image : Array
        The image array created by rasterize_points().
    profile : Dictionary
        The dictionary profile created by rasterize_points().
    shp : Shapely shape
        Shapely polygon as created by get_dataset_outline().
    landmask : String
        Path to the land mask shapefile.

    Returns
    -------
    out_image : Array
        Masked image array.

    """
    with fiona.open(landmask) as msk:
        shapes = [f["geometry"] for f in msk if shape(f["geometry"]).within(shp)]
    with MemoryFile() as memfile:
        with memfile.open(**profile) as ds:
            ds.write(image)
            out_image, out_transform = rasterio.mask.mask(
                ds, shapes, invert=True, crop=False
            )

    return out_image


def write_raster(src_array, src_profile, dst_array, dst_profile, outfile):
    """
    Write the final masked or unmasked raster to file.

    Parameters
    ----------
    src_array : Array
        The reprojected image array created by rasterize_points().
    src_profile : Dictionary
        The profile dictionary of the reprojected array.
    dst_array : Array
        The array created by make_ds_array().
    dst_profile : Dictionary
        The profile dictionary for the dst_array.
    outfile : String
        Path to output file.

    Returns
    -------
    None.

    """

    dst_image = rasterio.warp.reproject(
        src_array,
        dst_array,
        src_transform=src_profile["transform"],
        src_crs=src_profile["crs"],
        src_nodata=None,
        dst_transform=dst_profile["transform"],
        dst_crs=dst_profile["crs"],
        dst_nodata=None,
        resampling=0,
    )[0]

    with rasterio.open(outfile, "w", **dst_profile) as dst:
        dst.write(dst_image)


def main(safe, outfolder, level, landmask=None):
    """
    Run main function to run the Sentinel 2 command.

    Parameters
    ----------
    safe : String
        Path to the sentinel 2 safe folder.
    outfolder : String
        Path to the output folder. This will be created if it does not exist.
    level : String
        Click option LAT or MSL.
    land_mask : String, optional
        Path to the land mask to be applied. The default is None.

    Returns
    -------
    None.

    """
    if not os.path.isdir(outfolder):
        os.makedirs(outfolder)


    mikepath = os.environ['MIKE'] = "C:\Program Files (x86)\DHI"
    #ikepath = os.environ.get['MIKE']
    mikepath = pathlib.Path(mikepath)

    # mikepath = os.environ.get("MIKE")
    metafile = list(pathlib.Path(safe).glob("**/MTD_TL.xml"))[0]
    meta = read_meta(metafile)
    dst_profile = make_profile(meta)
    dst_array = make_ds_array(dst_profile)
    shp = get_dataset_outline(dst_array, dst_profile)

    pts = create_pts(shp, 0.125)

    tempfolder = os.path.join(outfolder, "temp")
    os.makedirs(tempfolder, exist_ok=True)
    generate_pfs(pts, meta, mikepath, tempfolder)

    temp_pfs_path = str(list(pathlib.Path(tempfolder).glob("*.pfs"))[0])
    make_dfs0(mikepath, temp_pfs_path)

    temp_dfs0_path = str(list(pathlib.Path(tempfolder).glob("*.dfs0"))[0])
    tv = tide_values_from_dfs0(mikepath, meta, temp_dfs0_path, level)


    outfilename = ".".join([meta["tile_id"], "tides", level, "shp"])
    outfile = os.path.join(outfolder, outfilename)

    c = write_tide_values(tv, pts, level, outfile, outfolder)

    src_array, src_profile = rasterize_points(c, shp)


    if not landmask:
        src_array, src_profile = rasterize_points(c, shp)
    else:
        unmasked_a, unmasked_p = rasterize_points(c, shp)
        src_array = mask_raster(unmasked_a, unmasked_p, shp, landmask=landmask)
        src_profile = unmasked_p

    outfilename = ".".join([meta["tile_id"], "tides_resampling_2", level, "tif"])
    outfile = os.path.join(outfolder, outfilename)

    write_raster(src_array, src_profile, dst_array, dst_profile, outfile)

    shutil.rmtree(tempfolder)
