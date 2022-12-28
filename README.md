# Project Title

SDMX Infrastructure - CENSUS script conversion

## Description

Development of script to convert SDMX CSV datasources into a INSPIRE compliant Atom feed (output files: geopackage, SDMX and GML).
The output files are produced by joining the EU 2021 population grid provided by EUROSTAT(https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/grids) with the census data sent by the different EU countries at national level.
INSPIRE Metadata files are also created for all countries and at a EU Wide.

## Getting Started

### Dependencies

* Python version 3.0 or more
* Python libraries: pandas, geopandas, lxml, zipfile, argparse, ...

### Installing

* Download all the repository clicking "Download ZIP" button
* The code is inside "./src/" folder
* Install all required python libraries. For example, this line of code is to install the geopandas library:
```
python -m pip install geopandas
```

### Executing program

* There are 3 arguments to run the python script (2 required arguments and 1 optional):
    * '-d','--inputData': Path to input file. The input file can be a CSV or SDMX file (required)
    * '-m','--inputMetaData': Path to input metadata file (required)
    * '-b','--baseURL': Url where dissemination packages will be stored after creating them (optional)
These are two examples to execute python script with the arguments:
```
python SDMX_census_.py -d ./INPUT/CSV/CENSUS_GRID_N_DK_2021_0000_V0001.csv -m ./INPUT/Metadata/CENSUS_INS21ES_A_DK_2021_0000.sdmx.xml
```
```
python SDMX_census_.py -d ./INPUT/CSV/CENSUS_GRID_N_DK_2021_0000_V0001.csv -m ./INPUT/Metadata/CENSUS_INS21ES_A_DK_2021_0000.sdmx.xml -b https://gisco-services.ec.europa.eu/pub/census/
```

## Help

If you need more information about the arguments, run this python: 
```
python SDMX_census_.py -h
```

## Version History

* 1.0
    * Initial Release

## License

This project is licensed under the GISCO Eurostat, European Commission License [estat-gisco@ec.europa.eu](estat-gisco@ec.europa.eu)
