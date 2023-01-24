import re
import glob
from lxml import etree
from datetime import datetime
import argparse

# --- Arguments parser --- #
parser = argparse.ArgumentParser(description='An input argument is optional to run this script.')
parser.add_argument('-b','--baseURL', help='Url where dissemination packages will be stored after creating them (optional)', default='https://gisco-services.ec.europa.eu/pub/census/')
args = parser.parse_args()

# --- Entry parameters --- #
base_url = args.baseURL
path = './INPUT'
allFiles = glob.glob(path + "/*.zip")
outputAtomFile = "./OUTPUT/CENSUS_ATOMFeed.atom"

#ATOM feed parameters
atomTemplate_filename = "./Templates/CENSUS_ATOMFeed_template.atom"


def main():
    print("Creating ATOM feed...")
    atomRoot_temp = getXMLRoot(atomTemplate_filename)
    NAMESPACESAtom_temp = atomRoot_temp.nsmap
    if (None in NAMESPACESAtom_temp.keys()):
        NAMESPACESAtom_temp.pop(None) #to remove all None namespaces
    #ATOM feed values
    actualDate_atom = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    url_atomGeneric = base_url + "ATOM/"

    #ATOM feed
    atomFeed_temp = atomRoot_temp.xpath("//*[local-name() = 'feed']")
    createAtomFeedFirst(atomRoot_temp,actualDate_atom,url_atomGeneric)
    for filename in allFiles:
        #get country code for each ZIP file
        countryCodeResult = re.search('CENSUS_INS21ES_A_(.*)_2021_0000.zip', filename)
        if (countryCodeResult):
            countryCode = countryCodeResult.group(1)
            atomEntry = createAtomFeedEntry(countryCode,url_atomGeneric,actualDate_atom)
            atomFeed_temp[0].append(atomEntry)
    createAtomFeedFinal(atomRoot_temp)

# Function to create the ATOM feed
def createAtomFeedFirst(atomRoot_temp,actualDate_atom,url_atom):
    # Completing ATOM feed
    #ATOM date
    atomDate_temp = atomRoot_temp.xpath("//*[local-name() = 'updated']")
    if (len(atomDate_temp) > 0):
        atomDate_temp[0].text = actualDate_atom
    #ATOM id
    atomId_temp = atomRoot_temp.xpath("//*[local-name() = 'id']")
    if (len(atomId_temp) > 0):
        atomId_temp[0].text = url_atom + "ATOM"
     #ATOM link
    atomLink_temp = atomRoot_temp.xpath("//*[local-name() = 'link']")
    if (len(atomLink_temp) > 0):
        atomLink_temp[0].set('href', base_url + "CENSUS_ATOMFeed.atom")

def createAtomFeedEntry(country_code,url_atom,actualDate_atom):
    valueNodeEntry = etree.Element('entry')
    #Entry id
    valueNodeEntry_id = etree.SubElement(valueNodeEntry, 'id')
    valueNodeEntry_id.text = url_atom + country_code
    #Entry title
    valueNodeEntry_title = etree.SubElement(valueNodeEntry, 'title')
    valueNodeEntry_title.text = "CENSUS - " + country_code
    #Entry date
    valueNodeEntry_date = etree.SubElement(valueNodeEntry, 'updated')
    valueNodeEntry_date.text = actualDate_atom
    #Entry link
    valueNodeEntry_link = etree.SubElement(valueNodeEntry, 'link')
    valueNodeEntry_link.attrib['href'] = url_atom + country_code + ".zip"
    valueNodeEntry_link.attrib['rel'] = "alternate"
    valueNodeEntry_link.attrib['type'] = "application/gml+xml"
    valueNodeEntry_link.attrib['hreflang'] = "en"
    valueNodeEntry_link.attrib['title'] = "Statistical Units - "+country_code
    valueNodeEntry_link.attrib['length'] = "0"
    #Entry summary
    valueNodeEntry_summary = etree.SubElement(valueNodeEntry, 'summary')
    valueNodeEntry_summary.attrib['type'] = "html"
    valueNodeEntry_summary.text = "&lt;div&gt;&lt;div&gt;ZIP file storing a geopackage, SDMX and GML with information about the Statistical Units in "+country_code+"&lt;/div&gt;&lt;div&gt;&lt;b&gt;Metadata:&lt;/b&gt; ZIP file also stores the metadata file&lt;/div&gt;&lt;div&gt;&lt;a href=\""+(url_atom + country_code + ".zip")+"\" &gt; Download &lt;/a&gt;&lt;/div&gt;&lt;/div&gt;"
    return valueNodeEntry

def createAtomFeedFinal(atomRoot_temp):
    # ATOM feed completed
    atomFeedComplet = etree.tostring(atomRoot_temp, xml_declaration=True, encoding="utf-8")
    with open(outputAtomFile, "wb") as f:
        f.write(atomFeedComplet)
        print ("ATOM feed created")

# Function to get the xml root
def getXMLRoot(xml_filename):
    try:
        xmldata = etree.parse(xml_filename)
    except IOError:
        print ("File not found: " + xml_filename)
        quit()
    root_xmlTemp = xmldata.getroot()
    return root_xmlTemp


if __name__ == "__main__":
    main()
