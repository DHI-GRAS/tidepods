# tidepods

Extract gridded tide values from MIKE for a given area of interest and create a tidal surface.

Usage requires MIKE Zero(default: 2021) and the MIKE SDK

## Installation

### 1. Setup

1. Download and install [Miniconda](https://conda.io/miniconda.html) (Python 3).
   If you already have Anaconda or Miniconda installed, you can skip this step.


2. Install [MIKE Zero and the MIKE SDK](https://www.mikepoweredbydhi.com/). This version of tidepods has been tested and works with the 2021 versions of MIKE. Default install directory is:
	```
	C:\Program Files (x86)\DHI\2021
	```
2. Ensure MIKE Zero and the MIKE SDK are installed. Tidepods relies on certain files within these directories, thus the installation directory tree needs to be consistent. Default installation locations are:
	```
	C:\Program Files (x86)\DHI\Mike SDK\2021
	C:\Program Files (x86)\DHI\Mike Zero\2021
	```
3. Make sure the MIKE applications have access to a valid license.
4. Add the root MIKE installation directory to the environment variables, naming it "MIKE" e.g.:
	```
	Variable: MIKE
	Value: C:\Program Files (x86)\DHI\
	```

### 2. The tidepods environment

1. [Download the most recent environment.yml file](https://github.com/DHI-GRAS/tidepods/raw/master/environment.yml) (right-click, `save-as`) and run:
    ```
    conda env create -f /path/to/environment.yml
    ```
   This creates the **tidepods environment**

## Usage

After installation, the **tidepods environment** will contain the `tidepods` command-line interface.

#### 1. Activate the **tidepods environment**
```
activate tidepods
```

#### 2. Get information about the `tidepods` CLI with:
```
tidepods --help
```
```
Usage: tidepods [OPTIONS] COMMAND [ARGS]...

  Tidal Surface Processing Tasks.

Options:
  --help  Show this message and exit.

Commands:
  icesat2  Extract tide levels at icesat_2 acquisition points.
  s2       Create a tidal surface for a Sentinel 2 acquisition.
  vhr      Create a point shp containing tide values over AOI (VHR image).
```

### Individual Commands

The individual commands available within tidepods are: `icesat2, s2, vhr`
e.g. 
```
tidepods icesat2 --help
```
```
Usage: tidepods icesat2 [OPTIONS]

  Extract tide levels at icesat_2 acquisition points.

  Example use:

  tidepods icesat2 -s C:/tides/processed_icesat_pts.shp -o C:/tides_output
  -l MSL

Options:
  -s, --shapefile FILE       Path to input shapefile e.g.
                             C:/tides/processed_icesat_pts.shp  [required]

  -o, --outfolder DIRECTORY  Path to output folder where tidepods will create
                             the updated shapefile e.g. C:/tides  [required]

  -l, --level [LAT|MSL]      Tide value return type, LAT (Lowest Astronomical
                             Tide) or MSL (Mean Sea Level)  [required]

  --help                     Show this message and exit.
```

