# ATOM
This folder contains the content for the Tomcat deployment in order to display ATOM feed data of the following two parts:
* Population Distribution - Demography and Coordinate Reference Systems. 
* Statistical Units

## Deployment 
* Install JAVA and Tomcat 8.5 (64-bits) or above.
* Unzip the file "quercus.rar" in "Scripts&Resource" directory from this project repository. It is a free software to execute PHP scripts in Tomcat.
    * Rename the file quercus.war by ATOM.war (or the name you want to appear in the URL)
    * Display the war in Tomcat and wait for the "ATOM" folder (or the name you have chosen) to appear
* Copy the content of  this "ATOM" folder into the decompress ATMO directory in Tomcat.
    
## Content explanation
* Atom.atom - Top Feed of ATOM
* opensearchdescription.xml - XML that describes the search engine
* search.php - PHP scripts that do the searches
* PD - Folder for Population Distribution and Demography
    * PD.atom - Feed for Population Distribution and Demography
    * Data - Folder that contains:
       * Files of information to download (en ZIP)
       * *.gml files for the metadata links
* SU - Folder for Statistical Units
    * SU.atom - Feed of Dataset
    * Data - Folder that contains 
        *  Files of the information to download (en ZIP)
        *  *.xml files for the metadata links
* img - Folder for all countries' flags and other images
* notFound.html - HTML that is displayed when the search engine does not find any results

* In the Feeds and in the XML of the search description data that were put between "{}":
    * Conditions of access
    * Author
    * Contact email
    * URL to metadata
    * Code and Namespace of the data (data that is extracted from the metadata)
* All the URLs are pointing to localhost: 8080, so you will have to modify them to point to your server.
* The search engine is a simple PHP script to cover the two operations requested by INSPIRE:
    * Get Spatial Dataset: http://localhost:8080/ATOM/search.php?Spatial_dataset_identifier_code=AAA&spatial_dataset_identifier_namespace=PD&crs=3035&language=en&country=CH
    * Get Describe Dataset: http://localhost:8080/ATOM/search.php?Spatial_dataset_identifier_code=AAA&spatial_dataset_identifier_namespace=PD&crs=3035&language=en
* To enter the ATOM, you have to access the main feed: http://localhost:8080/ATOM/ATOM.atom
* Internet Explorer is able to display them natively.

## Requirements
* Java Development Kit (JDK) version 7 or above
* Tomcat 8.5 (64-bits) or above


