import pandas as pd
import geopandas as gpd
from datetime import datetime
import numpy as np
from lxml import etree
import os
import shutil
import html
import re
import zipfile
import argparse


# --- Entry parameters --- #
inputfile = "./INPUT/CSV/DK_ESTAT_DF_CENSUS_GRID_2021_2.0.csv"
# Metadata parameters
inputMetadataFile = "./INPUT/Metadata/CENSUS_INS21ES_A_DK_2021_0000.sdmx.xml"
countriesBoundingBox = "./INPUT/JRC_COUN_EXTENTS/JRC_COUNTRIES_extent.xml"
metadataTemplate_filename = "./INPUT/Templates/CENSUS_Countries_Metadata_template.xml"
metadataTemplateEUWide_filename = "./INPUT/Templates/CENSUS_EUWIDE_Metadata_template.xml"
base_url = "https://gisco-services.ec.europa.eu/pub/census/"
output_filename = "CENSUS_INS21ES_A_{country_code}_2021_0000"
#ZIP global variables
zipped_filenames = []
#ATOM feed parameters
atomTemplate_filename = "./INPUT/Templates/CENSUS_ATOMFeed_template.atom"

def main():
    '''Based on user input file and selected output format, it runs a different function'''
    global countryCode, start_date, extension
    lists()
    # Creates output files
    extension = inputfile[-3:]
    if extension == 'csv': #INPUT CSV
        readCSV()
    elif extension == 'xml': #INPUT SDMX
        readSDMX()
    else:
        print ("This is not a correct file format: " + inputfile)
        quit()
    if (df):
        # Creates metadata file
        if df['AREA_OF_DISSEMINATION'].iat[0] == 'EU':
            createMetadataEUWide()
        else:
            createMetadataCountries(df)
        # Compressing output file
        zipAllFiles(df)
        # Creates ATOM feed file
        createAtomFeed(df)


def lists():
    '''This function stores the different lists'''
    global observations,dataset,float_fields,stat_values
    #Fields listed as observations according to documentation
    observations = ['NOT_COUNTED_PROPORTION','GENERAL_STATUS','OBS_STATUS','STATUS','LAND_SURFACE','SPECIAL_VALUE','APPROXIMATELY_LOCATED_POPULATION_PROPORTION','OBS_NOTE','CONVENTIONALLY_LOCATED_PROPORTION','OBS_VALUE']
    #Fields listed as dataset according to documentation
    dataset = ['FREQ','NOT_COUNTED_PROPORTION','GENERAL_STATUS','MEASURE','MEASUREMENT_METHOD','UNIT_MEASURE','UNIVERSE','AREA_OF_DISSEMINATION','TIME_PERIOD','dataflowAgencyID','dataflowID','action','INSPIREID']
    #Fields listes as type = double according to documentation
    float_fields = ['NOT_COUNTED_PROPORTION','LAND_SURFACE', 'APPROXIMATELY_LOCATED_POPULATION_PROPORTION','CONVENTIONALLY_LOCATED_PROPORTION']
    # List of accepted STAT values
    stat_values = ['T_','M_','F_','Y_LT15_','Y15-64_','Y_GE65_','EMP_','NAT_','EU_OTH_','OTH_','SAME_','CHG_IN_','CHG_OUT_']

def readCSV():
    '''Reads the CSV and creates the pandas dataframe'''
    global df
    csv = pd.read_csv(inputfile,sep= ';')
    #Creates the pandas dataframe
    df = pd.DataFrame(csv)
    for o in observations:
        if o in df.columns:
            df[o] =df[o].astype(str)
    for d in dataset:
        if d in df.columns:
            df[d] =df[d].astype(str)
    #Changes fields in double list from str to float
    for f in float_fields:
        if f in df.columns:
            df[f] = df[f].astype(float)
    df['OBS_VALUE'] = df['OBS_VALUE'].astype(int)
    EU_or_Country(df)
    '''
    here we will need CSV2GML
    '''

def getShapefile():
    '''Reads Shapefile and converts it into a pandas geodataframe'''
    read_shp = 'INPUT/JRC_POP_SHP/JRC_POPULATION_2021.shp'
    #read_shp= gpd.read_file(shp)
    shp_gpd = gpd.read_file(read_shp,
    include_fields = ['GRD_ID','CNTR_ID'])
    #Drops the undesired columns
    shp_gpd.drop(columns=['TOT_P_2018','Country','Date','Method','Shape_Leng','Shape_Area','OBJECTID','CNTR_ID'],inplace= True)
    #Set GRD_ID as index
    shp = shp_gpd.set_index('GRD_ID')
    print ("Shapefile readed")
    return shp

def EU_or_Country(df):
    '''Checks the AREA_OF_DISSEMINATIOn field, if EU runs EUwide to perform the aggregation, otherwise it runs different functions depending on the output file'''
    if df['AREA_OF_DISSEMINATION'].iat[0] == 'EU':
        EUwide(df)
    else:
        # Creates geopackage file
        df['Flag'] = 0 #value 0 for countries
        duplicateSTAT(df)
        # Creates SDMX file
        df2SDMX(df)

def EUwide(df):
    '''Groups the rows based on SPATIAL id, among others. Sums up the float and int values, and join the string values'''
    #Remove the country Prefix from SPATIAL  fields, and create a new field called GRD_ID
    df['GRD_ID'] = df['SPATIAL'].str.split('_').str[1]
    #Replace "nan" values for empty cells
    df = df.replace('nan','', regex=True)
    #Depending on the source, we group by certain values, as not all values in CSV exist in SDMX, and viceversa
    if extension == 'csv':
        df = df.groupby(['AREA_OF_DISSEMINATION','FREQ','MEASURE','MEASUREMENT_METHOD','UNIT_MEASURE','DATAFLOW','TIME_PERIOD','POPULATED','GRD_ID','STAT', 'INSPIREID','UNIVERSE'],as_index=False).agg(lambda x : x.sum() if x.dtype=='int32' or x.dtype=='int64' or x.dtype == 'float64' or x.dtype == 'float32' else ' '.join(x))
    if extension == 'xml':
        df = df.groupby(['AREA_OF_DISSEMINATION','FREQ','MEASURE','MEASUREMENT_METHOD','UNIT_MEASURE','action','dataflowAgencyID','dataflowID','TIME_PERIOD','POPULATED','GRD_ID','STAT'],as_index=False).agg(lambda x : x.sum() if x.dtype=='int32' or x.dtype == 'float64' else ' '.join(x))
    #We join and sort string values
    df['OBS_STATUS'] = df['OBS_STATUS'].apply(lambda x: "".join(sorted(set(x))))
    #Remove space before string
    df['OBS_STATUS'] = df['OBS_STATUS'].str.strip()
    #In string values, if the string joined are different, then we substitute it for "D"
    df['OBS_STATUS'] = df['OBS_STATUS'].apply(lambda x : x if len(x) <2 else "D")
    #Recreate POPULATED field, as is a int, but we did not wanted to sum up it before.
    df['POPULATED'] = 1
    # Creates geopackage file
    df['Flag'] = 1 #value 1 for EU Wide
    duplicateSTAT(df)
    # Creates SDMX file
    #Drop SPATIAL and rename GRD_ID to spacial
    df.drop(columns=['SPATIAL'],inplace= True)
    df.rename(columns={'GRD_ID':'SPATIAL'},inplace= True)
    df2SDMX(df)

#Function to read shapefile and then creates the geopackage file
def duplicateSTAT(df):
    '''The observation fields are multiplied by STAT values before creating the geopackage'''
    print ("Reading shapefile...")
    if df['Flag'].iat[0] == 0: #1 for EU, and 0 for countries
        df['GRD_ID'] = df['SPATIAL'].str.split('_').str[1]
    df['STAT_'] = df['STAT'] + '_'
    df = df.replace('',np.nan, regex=True)
    #The OBS_VALUE is placed in the STAT + observation field, depending on the value of STAT
    df =  pd.concat([df, pd.DataFrame(data={s+o: np.where(df['STAT_'] == s , df[o], np.NaN) for s in stat_values for o in observations})], axis = 1)
    df.drop(['STAT_','STAT'],axis = 1, inplace= True)
    #Drop observation fields, SPATIAL and flag fields
    df.drop(observations,axis = 1, inplace= True)
    df.drop(columns=['SPATIAL'],inplace= True)
    df.drop(columns=['Flag'],inplace= True)
    #Replace empty cells with NULLs
    df = df.replace(' ',np.nan, regex=True)
    create_gpkg(getShapefile(),df)


def readSDMX():
    '''Reads SDMX and creates pandas dataframe'''
    global df
    #Parse XML
    xmldata = etree.parse(inputfile)
    root = xmldata.getroot()
    urn = '{urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=ESTAT:CENSUS_GRID_2021(2.0):cross}'
    columns = []
    #Iterates through Dataset childs, converts it to dictionary and appends it to columns list
    for child in root.findall('.//'):
        if child.tag == urn + 'DataSet':
            childs = child.iter()
            for c in childs:
                attributes = c.attrib
                attributes_dict = dict(attributes)
                columns.append(attributes_dict)
    #Creates dataframe
    df = pd.DataFrame.from_dict(columns)
    df = df.replace('', np.nan)
    #Fills with previous value all columns that exist in dataset list
    for d in dataset:
        if d in df.columns:
            df[d].fillna(method='ffill',inplace= True)
        else:
            df[d] = np.nan
    #Rename value column to OBS_VALUE
    df.rename(columns= {'value':'OBS_VALUE'},inplace= True)
    # Observation fields only exist in SDMX file when having a value, we insert a new column if field does not exist in SDMX
    for o in observations:
        if o not in df.columns:
            df[o] = np.nan
    # Removes rows where SPATIAL values is null
    df = df[df['SPATIAL'].notna()]
    for o in observations:
        if o in df.columns:
            df[o] =df[o].astype(str)
    for d in dataset:
        if d in df.columns:
            df[d] =df[d].astype(str)
    #Changes fields in double list from str to float
    for f in float_fields:
        if f in df.columns:
            df[f] = df[f].astype(float)
    #Changes OBS_VALUE from str to int
    df['OBS_VALUE'] = df['OBS_VALUE'].astype(int)
    #Resets index and drops previous index
    df.reset_index(inplace=True)
    df.drop(columns=['index'],inplace= True)
    if df['AREA_OF_DISSEMINATION'].iat[0] == 'EU':
        EUwide(df)
    else:
        # Creates geopackage file
        df['Flag'] = 0 #value 0 for countries
        df = df.replace('nan',np.NaN, regex=True)
        duplicateSTAT(df)
        # Creates SDMX file
        SDMX2SDMX(df)


def create_gpkg(shp,df):
    '''Joins te geodataframe previously created with the dataframe, and exports the result as geopackage'''
    print ("Creating geopackage file...")
    shp2gpck = gpd.GeoDataFrame(df.merge(shp, on ='GRD_ID'))
    gpck_cntr = shp2gpck['AREA_OF_DISSEMINATION'].values[0]
    outputGeopackage_filename = './OUTPUT/' + gpck_cntr + '_ESTAT_DF_CENSUS_GRID_2021_' + datetime.today().strftime('%Y%m%d%H%M%S') + '.gpkg'
    zipped_filenames.append(outputGeopackage_filename) #zip this file
    shp2gpck.to_file(outputGeopackage_filename,driver = 'GPKG')
    print ('Geopackage file created')
        

def df2SDMX(df):
    '''Builds a SDMX from dataframe data'''
    print ("Creating SDMX file...")
    try:
        xmlTemplate_filename = './INPUT/Templates/CENSUS_SDMX_template.xml'
        tree = etree.parse(xmlTemplate_filename)
        root = tree.getroot()
        NAMESPACES = root.nsmap
    except IOError:
        print ("File not found: " + xmlTemplate_filename)
        quit()
    SDMXHeaderString = '<message:CrossSectionalData xmlns:message="http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message" xmlns:common="http://www.SDMX.org/resources/SDMXML/schemas/v2_0/common" xmlns:ns1="urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=ESTAT:CENSUS_GRID_2021(2.0):cross" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"></message:CrossSectionalData>'
    populated = df['POPULATED'].tolist()
    spatial = df['SPATIAL'].tolist()
    stat = df['STAT'].tolist()
    obs_value = df['OBS_VALUE'].tolist()
    not_counted_proportion = df['NOT_COUNTED_PROPORTION'].tolist()
    general_status = df['GENERAL_STATUS'].tolist()
    obs_status = df['OBS_STATUS'].tolist()
    status = df['STATUS'].tolist()
    land_surface = df['LAND_SURFACE'].tolist()
    special_value = df['SPECIAL_VALUE'].tolist()
    app_loc_pp = df['APPROXIMATELY_LOCATED_POPULATION_PROPORTION'].tolist()
    obs_note = df['OBS_NOTE'].tolist()
    conv_loc_p = df['CONVENTIONALLY_LOCATED_PROPORTION'].tolist()
    
    roota = etree.fromstring(SDMXHeaderString)
    valueContainer = roota.xpath('//message:CrossSectionalData',namespaces=NAMESPACES)
    valueNode1 = etree.Element("{"+NAMESPACES.get('ns1')+"}Dataset")
    valueNode1.attrib['AREA_OF_DISSEMINATION'] = df['AREA_OF_DISSEMINATION'].iat[0]
    valueNode1.attrib['FREQ'] = df['FREQ'].iat[0]
    valueNode1.attrib['MEASURE'] = df['MEASURE'].iat[0]
    valueNode1.attrib['MEASUREMENT_METHOD'] = df['MEASUREMENT_METHOD'].iat[0]
    valueNode1.attrib['UNIT_MEASURE'] = df['UNIT_MEASURE'].iat[0]
    valueNode2 = etree.Element("{"+NAMESPACES.get('ns1')+"}Group")
    valueNode2.attrib['TIME_PERIOD'] = str(df['TIME_PERIOD'].iat[0])
    valueNode3 = etree.Element("{"+NAMESPACES.get('ns1')+"}Section")
    for (p,sp,st,ov,ncp,gs,obs_st,sts,ls,spval,alpp,on,clp) in zip(populated,spatial,stat,obs_value,not_counted_proportion,general_status,obs_status,status,land_surface,special_value,app_loc_pp,obs_note,conv_loc_p):
        valueNode4 = etree.Element("{"+NAMESPACES.get('ns1')+"}OBS_VALUE")
        valueNode4.attrib['POPULATED'] = str(p)
        valueNode4.attrib['SPATIAL'] = str(sp)
        valueNode4.attrib['STAT'] = str(st)
        valueNode4.attrib['NOT_COUNTED_PROPORTION'] = str(ncp)
        valueNode4.attrib['GENERAL_STATUS'] = str(gs)
        valueNode4.attrib['OBS_STATUS'] = str(obs_st)
        valueNode4.attrib['STATUS'] = str(sts)
        valueNode4.attrib['LAND_SURFACE'] = str(ls)
        valueNode4.attrib['SPECIAL_VALUE'] = str(spval)
        valueNode4.attrib['APPROXIMATELY_LOCATED_POPULATION_PROPORTION'] = str(alpp)
        valueNode4.attrib['OBS_NOTE'] = str(on)
        valueNode4.attrib['CONVENTIONALLY_LOCATED_PROPORTION'] = str(clp)
        valueNode4.attrib['value'] = str(ov)
        valueNode3.append(valueNode4)
    valueContainer[0].append(valueNode1)
    valueNode1.append(valueNode2)  
    valueNode2.append(valueNode3)
    xmlComplet = etree.tostring(roota, pretty_print=True)
    cntr_name = df['AREA_OF_DISSEMINATION'].iat[0]
    sdmxOutput_filename = './OUTPUT/'  + cntr_name + '_sdmxoutput_ESTAT_DF_CENSUS_GRID_2021_' + datetime.today().strftime('%Y%m%d%H%M%S') + '.xml'
    zipped_filenames.append(sdmxOutput_filename) #zip this file
    file = open(sdmxOutput_filename,'wb')
    file.write(xmlComplet)
    print ("SDMX file created")


# Creates SDMX file
def SDMX2SDMX(df):
    '''Builds a SDMX from SDMX'''
    print ("Creating SDMX file...")
    sdmx_country = df['AREA_OF_DISSEMINATION'].iat[0]
    sdmxOutput_filename = './OUTPUT/' + sdmx_country + '_sdmxoutput_ESTAT_DF_CENSUS_GRID_2021_' + datetime.today().strftime('%Y%m%d%H%M%S') + '.xml'
    zipped_filenames.append(sdmxOutput_filename) #zip this file
    file = inputfile
    shutil.copy(file, sdmxOutput_filename )
    print ("SDMX file created")


# Function to create the metadata per country
def createMetadataCountries(df):
    country_code = df['AREA_OF_DISSEMINATION'].iat[0]
    print ("Creating metadata file for "+country_code+"...")
    metadata_input = getXMLRoot(inputMetadataFile)
    countriesBoundBox = getXMLRoot(countriesBoundingBox)
    metadata_temp = getXMLRoot(metadataTemplate_filename)
    NAMESPACES_input = metadata_input.nsmap
    if (None in NAMESPACES_input.keys()):
        NAMESPACES_input.pop(None) #to remove all None namespaces
    NAMESPACES_temp = metadata_temp.nsmap
    if (None in NAMESPACES_temp.keys()):
        NAMESPACES_temp.pop(None) #to remove all None namespaces

    # Adding values to Metadata
    #File Identifier
    identifier_node = metadata_input.xpath("//*[local-name() = 'ID']")
    identifier_value = ""
    if (len(identifier_node) > 0):
        identifier_value = identifier_node[0].text
    else:
        print("File Identifier node not found")
    identifier_temp = metadata_temp.xpath('//gmd:fileIdentifier/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(identifier_temp) > 0):
        identifier_temp[0].text = identifier_value
    #Metadata point of contact
    contactOrgan_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='CONTACT_ORGANISATION']/genericmetadata:Value", namespaces=NAMESPACES_input)
    organUnit_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='ORGANISATION_UNIT']/genericmetadata:Value", namespaces=NAMESPACES_input)
    contactOrgan_value = ""
    organUnit_value = ""
    if (len(contactOrgan_node) > 0):
        contactOrgan_value = cleanMetadataValues(contactOrgan_node[0].text,"String",None)
    else:
        print("Metadata point of contact node not found")
    if (len(organUnit_node) > 0):
        organUnit_value = cleanMetadataValues(organUnit_node[0].text,"String",None)
    else:
        print("Metadata point of contact node not found")
    pointContact_temp = metadata_temp.xpath('//gmd:contact//gmd:organisationName/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(pointContact_temp) > 0):
        pointContact_temp[0].text = contactOrgan_value + ", " + organUnit_value
    #Metadata point of contact email
    contactMail_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='CONTACT_EMAIL']/genericmetadata:Value", namespaces=NAMESPACES_input)
    contactMail_value = ""
    if (len(contactMail_node) > 0):
        contactMail_value = cleanMetadataValues(contactMail_node[0].text,"Email",1)
    else:
        print("Metadata point of contact email node not found")
    contactMail_temp = metadata_temp.xpath('//gmd:contact//gmd:electronicMailAddress/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(contactMail_temp) > 0):
        contactMail_temp[0].text = contactMail_value
    #Metadata date
    metadataDate_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='META_LAST_UPDATE']/genericmetadata:Value", namespaces=NAMESPACES_input)
    metadataDate_value = ""
    if (len(metadataDate_node) > 0):
        metadataDate_value = cleanMetadataValues(metadataDate_node[0].text,"Date",None)
    else:
        print("Metadata date node not found")
    metadataDate_temp = metadata_temp.xpath('//gmd:dateStamp/gco:DateTime', namespaces=NAMESPACES_temp)
    if (len(metadataDate_temp) > 0):
        metadataDate_temp[0].text = metadataDate_value+"T09:00:00"
    #Resource title
    resourceTitle_node = metadata_input.xpath("//*[local-name() = 'Name']")
    resourceTitle_value = ""
    if (len(resourceTitle_node) > 0):
        resourceTitle_value = cleanMetadataValues(resourceTitle_node[0].text,"String",None)
    else:
        print("Resource title node not found")
    resourceTitle_temp = metadata_temp.xpath('//gmd:identificationInfo//gmd:title/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(resourceTitle_temp) > 0):
        resourceTitle_temp[0].text = resourceTitle_value
    #Date of creation
    dateCreation_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='REF_DATE']/genericmetadata:Value", namespaces=NAMESPACES_input)
    dateCreation_value = ""
    if (len(dateCreation_node) > 0):
        dateCreation_value = cleanMetadataValues(dateCreation_node[0].text,"Date",None)
    else:
        print("Date of creation node not found")
    dateCreation_temp = metadata_temp.xpath('//gmd:identificationInfo//gmd:date//gco:Date', namespaces=NAMESPACES_temp)
    if (len(dateCreation_temp) > 0):
        dateCreation_temp[0].text = dateCreation_value
    #Unique identifier
    uniqueIdentifier_value = base_url + output_filename.replace("{country_code}",country_code)
    uniqueIdentifier_temp = metadata_temp.xpath('//gmd:identificationInfo//gmd:RS_Identifier//gmd:code//gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(uniqueIdentifier_temp) > 0):
        uniqueIdentifier_temp[0].text = uniqueIdentifier_value
    #Resource abstract
    resourceAbstract_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='DATA_DESCR']/genericmetadata:Value", namespaces=NAMESPACES_input)
    resourceAbstract_value = ""
    if (len(resourceAbstract_node) > 0):
        resourceAbstract_value = cleanMetadataValues(resourceAbstract_node[0].text,"String",None)
    else:
        print("Resource abstract node not found")
    resourceAbstract_temp = metadata_temp.xpath('//gmd:abstract/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(resourceAbstract_temp) > 0):
        resourceAbstract_temp[0].text = resourceAbstract_value
    #Resource point of contact
    resourcecontactOrgan_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='CONTACT_ORGANISATION']/genericmetadata:Value", namespaces=NAMESPACES_input)
    resourceorganUnit_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='ORGANISATION_UNIT']/genericmetadata:Value", namespaces=NAMESPACES_input)
    resourcecontactOrgan_value = ""
    resourceorganUnit_value = ""
    if (len(resourcecontactOrgan_node) > 0):
        resourcecontactOrgan_value = cleanMetadataValues(resourcecontactOrgan_node[0].text,"String",None)
    else:
        print("Resource point of contact node not found")
    if (len(resourceorganUnit_node) > 0):
        resourceorganUnit_value = cleanMetadataValues(resourceorganUnit_node[0].text,"String",None)
    else:
        print("Resource point of contact node not found")
    resourcepointContact_temp = metadata_temp.xpath('//gmd:pointOfContact//gmd:organisationName/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(resourcepointContact_temp) > 0):
        resourcepointContact_temp[0].text = resourcecontactOrgan_value + ", " + resourceorganUnit_value
    #Resource point of contact email
    resourcecontactMail_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='CONTACT_EMAIL']/genericmetadata:Value", namespaces=NAMESPACES_input)
    resourcecontactMail_value = ""
    if (len(resourcecontactMail_node) > 0):
        resourcecontactMail_value = cleanMetadataValues(resourcecontactMail_node[0].text,"Email",2)
    else:
        print("Resource point of contact email node not found")
    resourcecontactMail_temp = metadata_temp.xpath('//gmd:pointOfContact//gmd:electronicMailAddress/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(resourcecontactMail_temp) > 0):
        resourcecontactMail_temp[0].text = resourcecontactMail_value
    #Use constraints
    useConstraitPolicy_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='CONF_POLICY']/genericmetadata:Value", namespaces=NAMESPACES_input)
    useConstraitDataTR_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='CONF_DATA_TR']/genericmetadata:Value", namespaces=NAMESPACES_input)
    useConstraitPolicy_value = ""
    useConstraitDataTR_value = ""
    if (len(useConstraitPolicy_node) > 0):
        useConstraitPolicy_value = cleanMetadataValues(useConstraitPolicy_node[0].text,"String",None)
    else:
        print("Use constraints node not found")
    if (len(useConstraitDataTR_node) > 0):
        useConstraitDataTR_value = cleanMetadataValues(useConstraitDataTR_node[0].text,"String",None)
    else:
        print("Use constraints node not found")
    useConstrait_temp = metadata_temp.xpath('//gmd:useConstraints//following-sibling::gmd:otherConstraints/gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(useConstrait_temp) > 0):
        useConstrait_temp[0].text = useConstraitPolicy_value + useConstraitDataTR_value
    #Geographic bounding box
    xMin_node = countriesBoundBox.xpath("//CountryId[text()='"+country_code+"']//following-sibling::xMin")
    xMax_node = countriesBoundBox.xpath("//CountryId[text()='"+country_code+"']//following-sibling::xMax")
    yMin_node = countriesBoundBox.xpath("//CountryId[text()='"+country_code+"']//following-sibling::yMin")
    yMax_node = countriesBoundBox.xpath("//CountryId[text()='"+country_code+"']//following-sibling::yMax")
    xMin_value = ""
    xMax_value = ""
    yMin_value = ""
    yMax_value = ""
    if (len(xMin_node) > 0):
        xMin_value = xMin_node[0].text
    else:
        print("West longitude node not found")
    if (len(xMax_node) > 0):
        xMax_value = xMax_node[0].text
    else:
        print("East longitude node not found")
    if (len(yMin_node) > 0):
        yMin_value = yMin_node[0].text
    else:
        print("South latitude node not found")
    if (len(yMax_node) > 0):
        yMax_value = yMax_node[0].text
    else:
        print("North latitude node not found")
    westLong_temp = metadata_temp.xpath('//gmd:westBoundLongitude/gco:Decimal', namespaces=NAMESPACES_temp)
    if (len(westLong_temp) > 0):
        westLong_temp[0].text = xMin_value
    eastLong_temp = metadata_temp.xpath('//gmd:eastBoundLongitude/gco:Decimal', namespaces=NAMESPACES_temp)
    if (len(eastLong_temp) > 0):
        eastLong_temp[0].text = xMax_value
    southLat_temp = metadata_temp.xpath('//gmd:southBoundLatitude/gco:Decimal', namespaces=NAMESPACES_temp)
    if (len(southLat_temp) > 0):
        southLat_temp[0].text = yMin_value
    northLat_temp = metadata_temp.xpath('//gmd:northBoundLatitude/gco:Decimal', namespaces=NAMESPACES_temp)
    if (len(northLat_temp) > 0):
        northLat_temp[0].text = yMax_value
    #Temporal extent begin
    temporalExtent_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='REF_PERIOD']/genericmetadata:Value", namespaces=NAMESPACES_input)
    temporalExtent_value = ""
    if (len(temporalExtent_node) > 0):
        temporalExtent_value = cleanMetadataValues(temporalExtent_node[0].text,"Date",None)
    else:
        print("Temporal extent begin node not found")
    temporalExtentBegin_temp = metadata_temp.xpath('//gml:beginPosition', namespaces=NAMESPACES_temp)
    if (len(temporalExtentBegin_temp) > 0):
        temporalExtentBegin_temp[0].text = temporalExtent_value
    #Resource locator
    resourceLocator_value = base_url + output_filename.replace("{country_code}",country_code) + ".zip"
    resourceLocator_temp = metadata_temp.xpath('//gmd:linkage//gmd:URL', namespaces=NAMESPACES_temp)
    if (len(resourceLocator_temp) > 0):
        resourceLocator_temp[0].text = resourceLocator_value
    #Lineage
    lineageDoc_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='DOC_METHOD']/genericmetadata:Value", namespaces=NAMESPACES_input)
    lineageColl_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='COLL_METHOD']/genericmetadata:Value", namespaces=NAMESPACES_input)
    lineageDataVal_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='DATA_VALIDATION']/genericmetadata:Value", namespaces=NAMESPACES_input)
    lineageAccuOverall_node = metadata_input.xpath("//genericmetadata:ReportedAttribute[@conceptID='ACCURACY_OVERALL']/genericmetadata:Value", namespaces=NAMESPACES_input)
    lineageDoc_value = ""
    lineageColl_value = ""
    lineageDataVal_value = ""
    lineageAccuOverall_value = ""
    if (len(lineageDoc_node) > 0):
        lineageDoc_value = cleanMetadataValues(lineageDoc_node[0].text,"String",None)
    else:
        print("Lineage doc node not found")
    if (len(lineageColl_node) > 0):
        lineageColl_value = cleanMetadataValues(lineageColl_node[0].text,"String",None)
    else:
        print("Lineage coll node not found")
    if (len(lineageDataVal_node) > 0):
        lineageDataVal_value = cleanMetadataValues(lineageDataVal_node[0].text,"String",None)
    else:
        print("Lineage data val node not found")
    if (len(lineageAccuOverall_node) > 0):
        lineageAccuOverall_value = cleanMetadataValues(lineageAccuOverall_node[0].text,"String",None)
    else:
        print("Lineage accu overall node not found")
    lineage_temp = metadata_temp.xpath('//gmd:lineage//gco:CharacterString', namespaces=NAMESPACES_temp)
    if (len(lineage_temp) > 0):
        lineages_value = lineageDoc_value + lineageColl_value + lineageDataVal_value + lineageAccuOverall_value
        lineages_value = html.unescape(lineages_value)
        lineage_temp[0].text = lineages_value

    # Metadata completed
    metadataComplet = etree.tostring(metadata_temp, pretty_print=True, encoding='UTF-8')
    outputMetadataFile = "./OUTPUT/" + output_filename.replace("{country_code}",country_code) + "_metadataINSPIRE.xml"
    with open(outputMetadataFile, "wb") as f:
        f.write(metadataComplet)
        zipped_filenames.append(outputMetadataFile) #zip this file
        print ("Metadata file for "+country_code+ " created")
    #Copy SDMX metadata
    outputMetadataSDMXFile = "./OUTPUT/" + output_filename.replace("{country_code}",country_code) + "_metadata.sdmx.xml"
    shutil.copy(inputMetadataFile, outputMetadataSDMXFile)
    zipped_filenames.append(outputMetadataSDMXFile) #zip this file

# Function to create the metadata for EU Wide
def createMetadataEUWide():
    print ("Creating metadata file for EU Wide...")
    metadataEU_temp = getXMLRoot(metadataTemplateEUWide_filename)
    NAMESPACESEU_temp = metadataEU_temp.nsmap
    if (None in NAMESPACESEU_temp.keys()):
        NAMESPACESEU_temp.pop(None) #to remove all None namespaces

    # Adding values to Metadata EU
    #Metadata date of creation
    dateCreation_value = datetime.today().strftime('%Y-%m-%d') + "T09:00:00"
    dateCreation_temp = metadataEU_temp.xpath('//gmd:dateStamp//gco:DateTime', namespaces=NAMESPACESEU_temp)
    if (len(dateCreation_temp) > 0):
        dateCreation_temp[0].text = dateCreation_value
    #Resource date of creation
    resDateCreation_value = datetime.today().strftime('%Y-%m-%d')
    resDateCreation_temp = metadataEU_temp.xpath('//gmd:identificationInfo//gmd:date//gco:Date', namespaces=NAMESPACESEU_temp)
    if (len(resDateCreation_temp) > 0):
        resDateCreation_temp[0].text = resDateCreation_value
    #Unique identifier
    uniIdent_value = base_url + "CENSUS_EU-WIDE_2021_0000"
    uniIdent_temp = metadataEU_temp.xpath('//gmd:identifier//gmd:code//gco:CharacterString', namespaces=NAMESPACESEU_temp)
    if (len(uniIdent_temp) > 0):
        uniIdent_temp[0].text = uniIdent_value
    #Temporal begin extent
    tempBegin_temp = metadataEU_temp.xpath('//gml:beginPosition', namespaces=NAMESPACESEU_temp)
    if (len(tempBegin_temp) > 0):
        tempBegin_temp[0].text = resDateCreation_value
    #Resource locator
    resLocator_value = base_url + "CENSUS_EU-WIDE_2021_0000.zip"
    resLocator_temp = metadataEU_temp.xpath('//gmd:linkage//gmd:URL', namespaces=NAMESPACESEU_temp)
    if (len(resLocator_temp) > 0):
        resLocator_temp[0].text = resLocator_value

    # Metadata completed
    metadataEUComplet = etree.tostring(metadataEU_temp, pretty_print=True, encoding="utf-8")
    outputMetadataFile = "./OUTPUT/" + output_filename.replace("{country_code}","EU_WIDE") + "_metadataINSPIRE.xml"
    with open(outputMetadataFile, "wb") as f:
        f.write(metadataEUComplet)
        print ("Metadata file for EU Wide created")
        zipped_filenames.append(outputMetadataFile) #zip this file


# Function to clean metadata values, removing <p> tags and converting date to the correct format
def cleanMetadataValues(meta_value,value_format,email_order):
    meta_value = meta_value.replace('&lt;p&gt;','').replace('<p>','') #removing <p> tag
    meta_value = meta_value.replace('&lt;/p&gt;','').replace('</p>','') #removing </p> tag
    if (value_format == "Date"):
        try:
            d = pd.to_datetime(meta_value)
            meta_value = d.strftime('%Y-%m-%d')
        except:
            meta_value = "2021-01-01" #default value in case of there is not a valid date
    elif (value_format == "Email"):
        matchMails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', meta_value)
        if (len(matchMails) > 0):
            meta_value = matchMails[0]
            if (email_order == 2 and len(matchMails) == email_order):
                meta_value = matchMails[1]
    return meta_value

# Function to get the xml root
def getXMLRoot(xml_filename):
    try:
        xmldata = etree.parse(xml_filename)
    except IOError:
        print ("File not found: " + xml_filename)
        quit()
    root_xmlTemp = xmldata.getroot()
    return root_xmlTemp

# Function to create a ZIP file adding all generated files
def zipAllFiles(df):
    print("Compressing all output files...")
    country_code = df['AREA_OF_DISSEMINATION'].iat[0]
    zip_filename = output_filename.replace("{country_code}",country_code)
    # create a ZipFile object
    zipObj = zipfile.ZipFile('./OUTPUT/'+zip_filename+'.zip', 'w')
    # Add multiple files to the zip
    for zfilename in zipped_filenames:
        zipObj.write(zfilename, arcname=zfilename.replace("./OUTPUT/",""))
        #remove initial output file
        os.remove(zfilename)
    # close the Zip File
    zipObj.close()
    print("ZIP file created")

# Function to create the ATOM feed
def createAtomFeed(df):
    print("Creating ATOM feed...")
    atomRoot_temp = getXMLRoot(atomTemplate_filename)
    NAMESPACESAtom_temp = atomRoot_temp.nsmap
    if (None in NAMESPACESAtom_temp.keys()):
        NAMESPACESAtom_temp.pop(None) #to remove all None namespaces
    #ATOM feed values
    country_code = df['AREA_OF_DISSEMINATION'].iat[0]
    actualDate_atom = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    url_atom = base_url + output_filename.replace("{country_code}",country_code)

    # Completing ATOM feed
    #ATOM date
    atomDate_temp = atomRoot_temp.xpath("//*[local-name() = 'updated']")
    if (len(atomDate_temp) > 0):
        atomDate_temp[0].text = actualDate_atom
    #Entry date
    entryDate_temp = atomRoot_temp.xpath("//*[local-name() = 'updated']")
    if (len(entryDate_temp) > 1):
        entryDate_temp[1].text = actualDate_atom
    #ATOM id
    atomId_temp = atomRoot_temp.xpath("//*[local-name() = 'id']")
    if (len(atomId_temp) > 0):
        atomId_temp[0].text = url_atom
    #Entry id
    entryId_temp = atomRoot_temp.xpath("//*[local-name() = 'id']")
    if (len(entryId_temp) > 1):
        entryId_temp[1].text = url_atom
    #Entry title
    entryTitle_temp = atomRoot_temp.xpath("//*[local-name() = 'title']")
    if (len(entryTitle_temp) > 1):
        entryTitle_temp[1].text = "CENSUS - " + country_code
    #ATOM link
    atomLink_temp = atomRoot_temp.xpath("//*[local-name() = 'link']")
    if (len(atomLink_temp) > 0):
        atomLink_temp[0].set('href', base_url + "ATOMFeed_"+country_code+".atom")
    #Entry link
    entryLink_temp = atomRoot_temp.xpath("//*[local-name() = 'link']")
    if (len(entryLink_temp) > 1):
        entryLink_temp[1].set('href', url_atom + ".zip")
        entryTitleLink_value = entryLink_temp[1].get('title')
        entryTitleLink_value = entryTitleLink_value.replace("{country_code}",country_code)
        entryLink_temp[1].set('title', entryTitleLink_value)
    #Entry summary
    entrySummary_temp = atomRoot_temp.xpath("//*[local-name() = 'summary']")
    if (len(entrySummary_temp) > 0):
        entrySummary_value = entrySummary_temp[0].text
        entrySummary_value = entrySummary_value.replace("{country_code}",country_code)
        entrySummary_value = entrySummary_value.replace("{url_zip}",url_atom + ".zip")
        entrySummary_temp[0].text = entrySummary_value
    # ATOM feed completed
    atomFeedComplet = etree.tostring(atomRoot_temp, xml_declaration=True, encoding="utf-8")
    outputAtomFile = "./OUTPUT/ATOMFeed_"+country_code+".atom"
    with open(outputAtomFile, "wb") as f:
        f.write(atomFeedComplet)
        print ("ATOM feed created")


if __name__ == "__main__":
    main()

