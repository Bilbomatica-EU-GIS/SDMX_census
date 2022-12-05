import pandas as pd
import geopandas as gpd
from datetime import datetime
import numpy as np
from lxml import etree
import shutil

def main():
    '''Based on user input file and selected output format, it runs a different function'''
    global countryCode, start_date, inputfile,outputfile,extension
    lists()
    inputfile = input("Select a csv or SDMX file from your computer: ")
    outputfile = input("Select the export file format (gpkg/SDMX/GML):")
    extension = inputfile[-3:]
    if extension == 'csv':
        readCSV()
    elif extension == 'xml' and outputfile == 'gpkg':
        SDMX2df()
    #elif extension == 'xml'and outputfile == 'gpkg':
    #    SDMX2df()
    elif extension == 'xml' and outputfile == 'SDMX':
        SDMX2SDMX()
    else:
        print ("This is not a correct file format: " + inputfile)
        quit()

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
    read_shp = 'INPUT/JRC_POP_SHP/JRC_POPULATION_2018.shp'
    #read_shp= gpd.read_file(shp)
    shp_gpd = gpd.read_file(read_shp,
    include_fields = ['GRD_ID','CNTR_ID'])
    #Drops the undesired columns
    shp_gpd.drop(columns=['TOT_P_2018','Country','Date','Method','Shape_Leng','Shape_Area','OBJECTID','CNTR_ID'],inplace= True)
    #Set GRD_ID as index
    shp = shp_gpd.set_index('GRD_ID')
    return shp

def EU_or_Country(df):
    '''Checks the AREA_OF_DISSEMINATIOn field, if EU runs EUwide to perform the aggregation, otherwise it runs different functions depending on the output file'''
    if df['AREA_OF_DISSEMINATION'].iat[0] == 'EU':
        EUwide(df)
    else:
        if outputfile == 'gpkg':
            df['Flag'] = 0
            duplicateSTAT(df)
        if outputfile == 'SDMX':
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
    if outputfile == 'gpkg':
        df['Flag'] = 1
        duplicateSTAT(df)
    if outputfile == 'SDMX':
        #Drop SPATIAL and rename GRD_ID to spacial
        df.drop(columns=['SPATIAL'],inplace= True)
        df.rename(columns={'GRD_ID':'SPATIAL'},inplace= True)
        df2SDMX(df)

def duplicateSTAT(df):
    '''The observation fields are multiplied by STAT values before creating the geopackage'''
    #print ("Reading shapefile and creating geopackage data schema")
    if df['Flag'].iat[0] == 0:
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


def SDMX2df():
    '''Reads SDMX and creates pandas dataframe'''
    #print ("Reading SDMX file")
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
        df['Flag'] = 0
        df = df.replace('nan',np.NaN, regex=True)
        duplicateSTAT(df)


def create_gpkg(shp,df):
    '''Joins te geodataframe previously created with the dataframe, and exports the result as geopackage'''
    #print ('Joining shapefile with dataframe and exporting geopackage')
    shp2gpck = gpd.GeoDataFrame(df.merge(shp, on ='GRD_ID'))
    gpck_cntr = shp2gpck['AREA_OF_DISSEMINATION'].values[0]
    shp2gpck.to_file('OUTPUT/' + gpck_cntr + '_ESTAT_DF_CENSUS_GRID_2021_' + datetime.today().strftime('%Y%m%d%H%M%S') + '.gpkg',driver = 'GPKG')
    print ('Geopackage created')

def SDMX2SDMX():
    '''Parses XML and creates a new one in the selected destination'''
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
    df = pd.DataFrame.from_dict(columns)
    if df['AREA_OF_DISSEMINATION'].iat[0] == 'EU':
        SDMX2df()
    else:
        sdmx_country = df['AREA_OF_DISSEMINATION'].iat[0]
        filename = sdmx_country + '_sdmxoutput_ESTAT_DF_CENSUS_GRID_2021_' + datetime.today().strftime('%Y%m%d%H%M%S') + '.xml'
        destination = 'OUTPUT/'
        file = inputfile
        shutil.copy(file, destination + filename )

def df2SDMX(df):
    '''Builds a SDMX from dataframe data'''
    #print ("creating SDMX")
    try:
        xmlTemplate_filename = 'INPUT/sdmx_template.xml'
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
    file = open('OUTPUT/'  + cntr_name + '_sdmxoutput_ESTAT_DF_CENSUS_GRID_2021_' + datetime.today().strftime('%Y%m%d%H%M%S')  + '.xml','wb')
    file.write(xmlComplet)

if __name__ == "__main__":
    main()