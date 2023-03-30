import os
import sys
import getopt
import time
import ntpath
from pathlib import Path
import datetime
from os import walk, path
import os,string
import shutil
from feedgen.feed import FeedGenerator
import pytz
import zipfile

# Default variables values
start_time = time.time()
#root_folder= os.getcwd()
#target_folder = root_folder + os.sep + '190530 PD'
root_folder = os.getcwd() + os.sep +'INPUT'
target_folder = os.getcwd() + os.sep +'OUTPUT'

zip_name = '_3035'
#template_path_file = os.getcwd() + os.sep + 'readme_template.md'
template_path = os.getcwd() + os.sep + 'Templates'
template_path_file_csv = template_path + os.sep + 'readme_template_csv.md'
template_path_file_gpkg = template_path + os.sep + 'readme_template_gpkg.md'
template_path_file_gml = template_path + os.sep + 'readme_template_gml.md'
template_path_file_sdmx = template_path + os.sep + 'readme_template_sdmx.md'
readme_name = "readme.md"
atom_file_name = 'PD'
atom_title = 'Population Distribution and Demography'
#base_url = 'http://localhost:8080/ATOM/'
base_url = 'https://gisco-services.ec.europa.eu/pub/census/'
metadata_suffix = '.xml'
suffix = ['.gml', '.gpkg']

country_code_dict = {
    "EUROPE":"Europe",    
    "AL":"Albania",
    "AT":"Austria",
    "BE":"Belgium",
    "BG":"Bulgaria",    
    "CH":"Switzerland", 
    "CY":"Cyprus", 
    "CZ":"Czechia",
    "DE":"Germany",
    "DK":"Denmark",
    "EE":"Estonia",
    "EL":"Greece",
    "ES":"Spain",
    "FI":"Finland",
    "FR":"France",
    "HR":"Croatia",
    "HU":"Hungary",
    "IE":"Ireland",
    "IT":"Italy",
    "LI":"Liechtenstein",
    "LT":"Lithuania",
    "LU":"Luxembourg",
    "LV":"Latvia",
    "MT":"Malta",
    "NL":"Netherlands",
    "NO":"Norway",
    "PL":"Poland",
    "PT":"Portugal",
    "RO":"Romania",
    "SE":"Sweden",
    "SI":"Slovenia",
    "SK":"Slovakia",
    "UK":"United Kingdom",
    "XK":"Kosovo"
}

try:
    opts, args = getopt.getopt(sys.argv[1:],'hmz:i:o:',['help', 'root-folder=' , 'zip-name=', 'target-folder=', 'atom-name=', 'atom-title=', 'base-url=', 'readme-template-csv=', 'readme-template-gpkg=', 'readme-template-gml=', 'readme-template-sdmx='])
except getopt.GetoptError as err:
    print(err)
    print('python AtomDataGenerator.py --help')
    sys.exit(2)
for opt, arg in opts:
    if opt in ('-h', '--help'):
        print('AtomDataGenerator\n')
        print('Utility to compress the *.gml file into zip file under a directory recusivley, and generate the *.atom, then save zip files, metadata, *.atom in to a specified folder.\n')
        print('python AtomDataGenerator.py [options]\n')
        print('Options:')
        print('    h, optional, --help')
        print('    r, optional, default-value:\'current working directory/INPUT\', --root-folder="ROOT-FOLDER"')
        print('    t, optional, default-value:\'current working directory/OUTPUT\', --target-folder="target-FOLDER"')    
        print('    z, optional, default-value:\'[contry code]_PD_3035_GML\', --zip-name=name-second-part')      
        print('    a, optional, default-value:\'PD\', --atom-name=ATOM file name')    
        print('    m, optional, default-value:\'Population Distribution and Demography\', --atom-title=ATOM title')  
        print('    b, optional, default-value:\'https://gisco-services.ec.europa.eu/pub/census/\', --base-url=base url')     
        print('    rc, optional, default-value:\'current working directory/Templates/readme_template_csv.md\', --readme-template-csv=template location csv')
        print('    rk, optional, default-value:\'current working directory/Templates/readme_template_gpkg.md\', --readme-template-gpkg=template location gpkg')
        print('    rg, optional, default-value:\'current working directory/Templates/readme_template_gml.md\', --readme-template-gml=template location gml')
        print('    rs, optional, default-value:\'current working directory/Templates/readme_template_sdmx.md\', --readme-template-sdmx=template location sdmx')
        print('Examples:')
        print('    default usage:')
        print('        python AtomDataGenerator.py')        
        print('    set root-folder location to \"other_input_folder\" to locate the source directory:')
        print('        python AtomDataGenerator.py --root-folder=\"./other_input_folder/\"')
        print('    set target-folder location to \"other_output_folder\" to store the Data and Metadata generated:')
        print('        python AtomDataGenerator.py --target-folder=\"./other_output_folder/\"')
        print('    set zip file name to a different suffix (to replace "_PD_3035_GML" part)') 
        print('        python AtomDataGenerator.py --zip-name=\"zip_name\"')       
        print('    set the name to the *.atom file to generate.')
        print('        python AtomDataGenerator.py --atom-name=\"atom_file_name\"')  
        print('    set the title in the atom file.')
        print('        python AtomDataGenerator.py --atom-title=\"atom_title\"')  
        print('    set the base url for in generated *.atom file.')
        print('        python AtomDataGenerator.py --base-url=\"base_url\"') 
        print('    set the readme template for generating readme file in every csv zip file.')
        print('        python AtomDataGenerator.py --readme-template-csv=\"template_location_csv\"') 
        print('    set the readme template for generating readme file in every gpkg zip file.')
        print('        python AtomDataGenerator.py --readme-template-gpkg=\"template_location_gpkg\"') 
        print('    set the readme template for generating readme file in every gml zip file.')
        print('        python AtomDataGenerator.py --readme-template-gml=\"template_location_gml\"') 
        print('    set the readme template for generating readme file in every sdmx zip file.')
        print('        python AtomDataGenerator.py --readme-template-sdmx=\"template_location_sdmx\"') 
        sys.exit()
    elif opt in ('-r', '--root-folder'):
        root_folder = arg
    elif opt in ('-z', '--zip-name'):
        zip_name = arg
    elif opt in ('-t', '--target-folder'):
        target_folder = arg
    elif opt in ('-a', '--atom-name'):
        atom_file_name = arg
    elif opt in ('-m', '--atom-title'):
        atom_title = arg
    elif opt in ('-b', '--base-url'):
        base_url = arg  
    elif opt in ('-rc', '--readme-template-csv'):
        template_path_file_csv = arg  
    elif opt in ('-rk', '--readme-template-gpkg'):
        template_path_file_gpkg = arg  
    elif opt in ('-rg', '--readme-template-gml'):
        template_path_file_gml = arg  
    elif opt in ('-rs', '--readme-template-sdmx'):
        template_path_file_sdmx = arg          

def check_root_dir(folder):     
    if(not os.path.isdir(folder)):        
        folder= os.getcwd() + os.sep +'INPUT'
        print("The root-folder is invalid, it is set to the default INPUT directory.")
    folder = os.path.abspath(folder)
    return folder

def check_target_dir(folder):   
    folder = os.path.abspath(folder)    
    if(os.path.isdir(folder)):
        shutil.rmtree(folder)       
    os.makedirs(folder)
    return folder  

def generate_data(root_folder): 
    print("CALL generate_data")
    country_atom_added_list=[]
    country_zipped_list=[]
    feed_entry_object_list = {}
    file_code_name_dict = {}

    for root,dirs,files in os.walk(root_folder, topdown=True):   
        files.sort()       
        for filename in files: 
            split_tup=os.path.splitext(filename)
            target_filename_country_code = root.split(os.path.sep)[-1]           
            if (split_tup[1].lower() in suffix and target_filename_country_code.upper() in country_code_dict.keys() and not (target_filename_country_code in country_zipped_list)):
                target_readme_path = os.path.join(root, readme_name)
                target_path_name = os.path.join(target_folder, target_filename_country_code + "_" + atom_file_name + zip_name)       
                suffix_list = ['.gml', '.gpkg', '.xml', '.csv']
                readme_paths = [template_path_file_gml, template_path_file_gpkg, template_path_file_sdmx, template_path_file_csv]
                generate_readme(readme_paths, root, target_filename_country_code)
                zipDir(root, target_path_name, suffix_list)   
                country_zipped_list.append(target_filename_country_code) 
                if (target_filename_country_code in country_atom_added_list and not file_code_name_dict[target_filename_country_code].split("_")[0] == filename.split("_")[0]):               
                    change_feed_entry (feed_entry_object_list[target_filename_country_code], target_filename_country_code, filename)
                elif not target_filename_country_code in country_atom_added_list:
                    fe = generate_feed_entry(target_filename_country_code, filename)
                    country_atom_added_list.append(target_filename_country_code)
                    feed_entry_object_list[target_filename_country_code] = fe
                    file_code_name_dict[target_filename_country_code] = filename
      
           

def zipSinglefile(target_path_name, root_path, file_to_zip): 
    zip_file = zipfile.ZipFile(target_path_name + '.zip', 'w')
    zip_file.write(os.path.join(root_path,file_to_zip), file_to_zip, compress_type=zipfile.ZIP_DEFLATED)
    zip_file.close()


def zipDir(dirPath, zipPath, suffix):
    print("CALL zipDir")
    print(str(zipPath))
    try:
        #new script
        readme_files=[]
        zipPaths=[]
        zipfs=[]
        zippedfiles=[]
        lenDirPath = len(dirPath)
        for s in suffix:
            if (s =='.xml'):
                zipPaths.append(zipPath +'_SDMX.zip')
                zipfs.append(zipfile.ZipFile(zipPaths[-1] , mode='w'))
                zippedfiles.append(False)
                readme_files.append('readme_sdmx.md')
            else:
                zipPaths.append(zipPath + s.replace(".", "_").upper() + '.zip')
                zipfs.append(zipfile.ZipFile(zipPaths[-1] , mode='w'))
                zippedfiles.append(False)
                readme_files.append("readme_"+s.replace('.','')+'.md')
        for root, _ , files in os.walk(dirPath):
            for file in files:  
                split_tup=os.path.splitext(file) 
                split_file=os.path.split(file) 
                index = suffix.index(split_tup[1]) if split_tup[1] in suffix else -1
                if (index != -1):
                    if (split_tup[1]!='.xml'):
                        zippedfiles[index] = True
                        filePath = os.path.join(root, file) 
                        zipfs[index].write(filePath , filePath[lenDirPath :], compress_type=zipfile.ZIP_DEFLATED )
                    else:
                        if (split_file[1].lower().find("sdmx") != -1):
                            zippedfiles[index] = True
                            filePath = os.path.join(root, file)    
                            zipfs[index].write(filePath , filePath[lenDirPath :], compress_type=zipfile.ZIP_DEFLATED )
                        elif (split_file[1].lower().find("metadata") != -1):
                            filePath = os.path.join(root, file)
                            for zfs in range(len(zipfs)):
                                zipfs[zfs].write(filePath , filePath[lenDirPath :], compress_type=zipfile.ZIP_DEFLATED )
                
                elif (split_tup[1]=='.md'):
                    index2 = readme_files.index(split_file[1]) if split_file[1] in readme_files else -1
                    if (index2 != -1):
                        filePath = os.path.join(root, file)
                        zipfs[index2].write(filePath , filePath[lenDirPath :], compress_type=zipfile.ZIP_DEFLATED )
        for zfs in range(len(zipfs)):
            zipfs[zfs].close()
        for zp in range(len(zipPaths)):
            if (not(zippedfiles[zp])) and os.path.exists(zipPaths[zp]):
                os.remove(zipPaths[zp])   
            
        if os.path.exists(os.path.join(root, 'readme_csv.md')):
            os.remove(os.path.join(root, 'readme_csv.md'))
        if os.path.exists(os.path.join(root, 'readme_gml.md')):
            os.remove(os.path.join(root, 'readme_gml.md'))
        if os.path.exists(os.path.join(root, 'readme_gpkg.md')):
            os.remove(os.path.join(root, 'readme_gpkg.md'))
        if os.path.exists(os.path.join(root, 'readme_sdmx.md')):
            os.remove(os.path.join(root, 'readme_sdmx.md'))           
    except IOError as e:
        print("Skipped zip as " + str(e)) 
        pass
    except OSError as e:
        print("Skipped zip as " + str(e)) 
        pass
    except zipfile.BadZipfile as e:
        print("Skipped zip as " + str(e)) 
        pass       
    except:
        print("Skipped zip as unexpected error:", sys.exc_info()[0]) 
        pass
    print("RETURN zipDir\n")        

def generate_feed_main():      
    #fg.language('es') 
    print("CALL generate_feed_main")
    fg.title(atom_title)    
    #fg.link(href=base_url + atom_file_name +'/' + atom_file_name +'.atom', rel="self", type="application/atom+xml", hreflang="en", title="This document" )     
    fg.link(href=base_url + atom_file_name +'.atom', rel="self", type="application/atom+xml", hreflang="en", title="This document" ) 
    #fg.id(base_url + atom_file_name +'/' + atom_file_name +'.atom')
    fg.id(base_url + atom_file_name +'.atom')
    fg.rights('{Copyrights}')  
    date = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day, 0, 0, 0, 0, pytz.UTC)
    fg.updated(date)      
    fg.link(rel="describedby", href="http://inspire.ec.europa.eu/featureconcept/StatisticalDistribution", type="text/html", title="Statistical Distribution")       
    fg.author({'name':'(Author)','email':'{Contact}'})        
    
def generate_feed_entry(country_code, filename):
    print("CALL generate_feed_entry")
    fe = fg.add_entry(feedEntry=None, order='append')        
    fe.category(term="http://www.opengis.net/def/crs/EPSG/0/3035", label="ETRS89 / LAEA Europe")
    date = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day, 0, 0, 0, 0, pytz.UTC)
    fe.updated(date)
    fe.title(country_code_dict[country_code.upper()])
    print ("Country: " + str(country_code.upper()))
    #entry_data = base_url + atom_file_name +'/Data/' +country_code.upper()+'_'+ atom_file_name + zip_name
    entry_data = base_url +'Data/' +country_code.upper()+'_'+ atom_file_name + zip_name
    entry_metadata = (base_url  + '/.xml')    
    target_path_name = os.path.join(target_folder, country_code.upper() + "_" + atom_file_name + zip_name)
    entry_sdmx= entry_data+'_SDMX.zip'
    entry_gml= entry_data+'_GML.zip'
    entry_gpkg= entry_data+'_GPKG.zip'
    entry_csv= entry_data+'_CSV.zip'
    entry_img = base_url + 'img/'+ country_code_dict[country_code.upper()] + '.png'
    fe.id(entry_data)
    entry_title = atom_title + ' - ' + country_code     
    entry_metadata_href = 'b&gt;Metadata:&lt;/b&gt; &lt;a href="' + entry_metadata + '" target="_blank" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    if os.path.exists(target_path_name + "_SDMX.zip"):
        fe.link(rel="alternate", href=entry_sdmx, type="application/sdmx", length="0", hreflang="en", title=entry_title)
    if os.path.exists(target_path_name + "_GML.zip"):
        fe.link(rel="alternate", href=entry_gml, type="application/gml", length="0", hreflang="en", title=entry_title)
    if os.path.exists(target_path_name + "_GPKG.zip"):    
        fe.link(rel="alternate", href=entry_gpkg, type="application/gpkg", length="0", hreflang="en", title=entry_title)
    if os.path.exists(target_path_name + "_CSV.zip"):
        fe.link(rel="alternate", href=entry_csv, type="application/csv", length="0", hreflang="en", title=entry_title)
    entry_summary = '&lt;div&gt;&lt;div&gt;ZIP file containing information about the ' + atom_title + ' in '+ country_code_dict[country_code.upper()] + '.&lt;/br&gt;'
    if os.path.exists(target_path_name + "_SDMX.zip"):
        entry_summary += '&lt;div&gt;&lt;b&gt;SDMX: &lt;/b&gt; &lt;a href="' + entry_sdmx +'" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    if os.path.exists(target_path_name + "_GML.zip"):
        entry_summary += '&lt;div&gt;&lt;b&gt;GML: &lt;/b&gt; &lt;a href="' + entry_gml +'" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    if os.path.exists(target_path_name + "_GPKG.zip"): 
        entry_summary += '&lt;div&gt;&lt;b&gt;GEOPACKAGE: &lt;/b&gt; &lt;a href="' + entry_gpkg +'" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    if os.path.exists(target_path_name + "_CSV.zip"):
        entry_summary += '&lt;div&gt;&lt;b&gt;CSV: &lt;/b&gt; &lt;a href="' + entry_csv +'" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    entry_summary += '&lt;div&gt;&lt;img width="100px" vspace="10" border="1" src="'+ entry_img + '" alt="'+ country_code_dict[country_code.upper()] +'" title="' + country_code_dict[country_code.upper()] +'"&gt;&lt;/div&gt;'
    fe.summary(entry_summary)   
    print("RETURN generate_feed_entry\n")
    return fe    
    


def remove_feed_entry(fe):
    print("CALL remove_feed_entry")
    fg.remove_entry(fe)

def change_feed_entry(fe, country_code, filename): 
    entry_metadata = (base_url  + '/.xml')
    entry_zip = base_url + entry_data+'.zip' 
    entry_metadata_href = 'b&gt;Metadata:&lt;/b&gt; &lt;a href="' + entry_metadata + '" target="_blank" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    entry_img = base_url + 'img/'+ country_code_dict[country_code.upper()] + '.png'
    entry_summary = '&lt;div&gt;&lt;div&gt;ZIP file containing information about the ' + atom_title + ' in '+ country_code_dict[country_code.upper()] + '.&lt;/br&gt;&lt;div&gt;&lt;b&gt;Formats:&lt;/b&gt; &lt;i&gt;GML, Shapefile, CSV, Geopackage&lt;/i&gt;&lt;/div&gt;&lt;div&gt;&lt;'+ entry_metadata_href +'&lt;div&gt;&lt;a href="' + entry_zip +'" &gt; Download &lt;/a&gt;&lt;/div&gt;&lt;img width="100px" vspace="10" border="1" src="'+ entry_img + '" alt="'+ country_code_dict[country_code.upper()] +'" title="' + country_code_dict[country_code.upper()] +'"&gt;&lt;/div&gt;'
    fe.summary(entry_summary)   
    print("Change the feed entry for " + country_code)

def replace_value_for_feed(original_file):
    try:
        f = open(original_file,'r')
        filedata = f.read()   
        newdata = filedata.replace('<feed xmlns="http://www.w3.org/2005/Atom">', '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:georss="http://www.georss.org/georss" xmlns:gml="http://www.opengis.net/gml" xml:lang="es">').replace('2019-05-21T12:00:00+00:00','2019-05-21T12:00:00').replace('<summary','<summary type="html"').replace('&amp;','&').replace('<generator uri="http://lkiesow.github.io/python-feedgen" version="0.7.0">python-feedgen</generator>','')
        f = open(original_file,'w')
        f.write(newdata)
        f.close() 
    except IOError as e:
        print("Not replacing Atom entry as " + str(e)) 
        pass
    except FileNotFoundError as e:
        print("Not replacing Atom entry as " + str(e)) 
        pass
    except:
        print("Not replacing Atom entry as unexpected error:", sys.exc_info()[0]) 
        pass
    finally: 
        f.close()

def generate_readme(template_path_files, target_file_path, country_code ):
    filename = ''
    filename_metadata = ''
    for file in os.listdir(target_file_path):
        if (file.lower().find("inspire") != -1):
            filename_metadata = file
    for template in template_path_files:
        target_file_name = ''
        cur_file= ''
        readme_name = os.path.split(template)[1]
        if (readme_name.lower().find("sdmx") != -1):
            target_file_name = target_file_path + os.sep + 'readme_sdmx.md'
            cur_file='sdmx'
        elif (readme_name.lower().find("gpkg") != -1):
            target_file_name = target_file_path + os.sep + 'readme_gpkg.md'
            cur_file='gpkg'
        elif (readme_name.lower().find("gml") != -1):
            target_file_name = target_file_path + os.sep + 'readme_gml.md'
            cur_file='gml'
        elif (readme_name.lower().find("csv") != -1):
            target_file_name = target_file_path + os.sep + 'readme_csv.md'
            cur_file='csv'
        else: 
            target_file_name = target_file_path + os.sep + 'readme_test.md'
            cur_file='test'
        filename = ''
        try:
            for file in os.listdir(target_file_path):
                if ((file.lower().find("readme") == -1) and (file.lower().find(cur_file) != -1 and template.lower().find(cur_file) != -1)):
                    filename = file
            f = open(template,'r')
            filedata = f.read()
            f.close()
            newdata = filedata.replace('{CC}', country_code).replace('{TH}', atom_file_name).replace('{FILENAME}', filename).replace ('{FILENAME_METADATA}', filename_metadata)
            f = open(target_file_name,'w')
            f.write(newdata)
            f.close()
        except IOError as e:
            print("Not generating readme as " + str(e)) 
            pass
        except FileNotFoundError as e:
            print("Not generating readme as " + str(e)) 
            pass
        except:
            print("Not generating readme as unexpected error:", sys.exc_info()[0]) 
            pass
        finally: 
            f.close()



root_folder = check_root_dir(root_folder)
target_folder = check_target_dir(target_folder)
print("target folder is: " + target_folder)
fg = FeedGenerator()
generate_feed_main()
generate_data(root_folder)
target_atom_file = os.path.join(target_folder, (atom_file_name + '.atom'))
fg.atom_file(target_atom_file, pretty=True)
replace_value_for_feed(target_atom_file)
print('Write ' +  atom_file_name + '.atom Finished in ' + target_folder) 
print('Execution time: ' + str((time.time() - start_time)//60) + ' minutes, ' + str(round((time.time() - start_time)%60, 3)) + ' seconds')
print('Finished.')