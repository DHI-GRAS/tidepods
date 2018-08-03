# tidepods

Extract gridded tide values from MIKE for a given area of interest

Usage requires MIKE Zero(default: 2016) and the MIKE SDK

## Installation

### 1. Miniconda Python

1. Download and install [Miniconda](https://conda.io/miniconda.html) (Python 3).
   If you already have Anaconda or Miniconda installed, you can skip this step.

2. Make sure that Miniconda is in the system environment variables under Path. Commonly under:
    ```
    C:\Users\<USER>\AppData\Local\Continuum\miniconda3\Scripts
    C:\Users\<USER>\AppData\Local\Continuum\miniconda3
    ```

### 2. The GDAL_DATA System Environment Variable

1. Go to 'System Properties' to edit the 'Environment Variables'

2. Add / verify 'GDAL_DATA' points to 'C:\OSGeo4W64\share\gdal' (assuming standard install of OSGeo4W 64-bit)

### 3. MIKE Zero and the MIKE SDK

1. Install [MIKE Zero and the MIKE SDK](https://www.mikepoweredbydhi.com/) (within DHI from winserv). Default install directory is:
	```
	C:\Program Files (x86)\DHI\[YEAR]
	```
2. Ensure MIKE Zero and the MIKE SDK are installed. Tidepods relies on the following files being installed (assuming default installation location):
	```
	C:\Program Files (x86)\DHI\2016\MIKE Zero\Application Data\Tide_Constituents\global_tide_constituents_0.125deg.dfs2
	C:\Program Files (x86)\DHI\2016\MIKE Zero\Application Data\Tide_Constituents\prepack.dat
	C:\Program Files (x86)\DHI\2016\MIKE SDK\bin\DHI.PFS.dll
	C:\Program Files (x86)\DHI\2016\MIKE SDK\bin\DHI.Generic.MikeZero.DFS.xml
	C:\Program Files (x86)\DHI\2016\bin\x64\TidePredictor.exe
	```

### 4. The tidepods environment

1. [Download the most recent environment.yml file](https://github.com/DHI-GRAS/tidepods/raw/master/environment.yml) (right-click, 'save-as') and run:
    ```
    conda config --add channels conda-forge
    conda env create -f /path/to/environment.yml
    ```
   This creates the **tidepods environment**

## Usage

After installation, the **tidepods environment** will contain the `tidepods` command-line interface.

1. Activate the **tidepods environment**
```
activate tidepods
```

2. Get information about the `tidepods` CLI with:
```
tidepods --help
```
```
Usage: tidepods [OPTIONS] COMMAND [ARGS]...

  Tidal Surface Processing Tasks

Options:
  --help  Show this message and exit.

Commands:
  points  Create a point shapefile containing tide...
```

### Individual Commands

The individual commands available within tidepods are: `points`

```
tidepods points --help
```
```
Usage: tidepods points [OPTIONS]

  Create a point shapefile containing tide values over an AOI

  Example use:

  tidepods points -p "C:/Program Files (x86)/DHI/2016/MIKE SDK/bin" -i
  C:/tides/aoi.tif -d 20150131 -t 10:30 -o C:/tides/pts_tides.shp

Options:
  -i, --infile PATH         Path to AOI raster file for points creation e.g.
                            C:/tides/aoi.tif  [required]
  -d, --date DATE           Image acquisiton date (yyyymmdd) e.g. 20150131
                            [required]
  -t, --timestamp TIME      Image acquisition time (HH:MM) e.g. 10:30
                            [required]
  -o, --outfile PATH        Path to output points shapefile containing the
                            tidal values e.g. C:/tides/pts_tides.shp
                            [required]
  -l, --level [LAT|MSL]     Tide value return type, LAT (Lowest Astronomical
                            Tide) or MSL (Mean Sea Level)  [required]
  -p, --mikepath DIRECTORY  Path to DHI MIKE version install root directory
                            [default: C:\Program Files (x86)\DHI\2016]
  --help                    Show this message and exit.
```

**infile** is a raster or shapefile covering the AOI

<p align="center">
<img src="https://rawgit.com/DHI-GRAS/tidepods/master/img_src/aoi_bounds.png" width=600px height=600px />
</p>

Points are then generated at every 0.125 degrees covering the AOI, plus a 0.125 degree buffer. These contain the tide level (MSL or LAT depending on the user input)

<p align="center">
<img src="https://rawgit.com/DHI-GRAS/tidepods/master/img_src/points.png" width=600px height=600px />
</p>
