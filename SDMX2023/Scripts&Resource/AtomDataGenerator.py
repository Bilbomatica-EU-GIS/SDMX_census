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
root_folder= os.getcwd()
target_folder = root_folder + os.sep + '190530 PD'
zip_name = '_3035'
template_path_file = root_folder + os.sep + 'readme_template.md'
readme_name = "readme.md"
atom_file_name = 'PD'
atom_title = 'Population Distribution and Demography'
base_url = 'http://localhost:8080/ATOM/'
metadata_suffix = '_GRID_2011_MD.xml'
gml_suffix = '_GRID_2011.gml'
country_code_dict = {
    "EUROPE":"Europe",    
    "AL":"Albania",
    "AT":"Austria",
    "BE":"Belgium",
    "BG":"Bulgaria",    
    "CH":"Switzerland", 
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
    opts, args = getopt.getopt(sys.argv[1:],'hmz:i:o:',['help', 'root-folder=' , 'zip-name=', 'target-folder=', 'atom-name=', 'atom-title=', 'base-url=', 'readme-template', 'readme-name'])
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
        print('    r, optional, default-vaule:\'current working directory\', --root-folder="ROOT-FOLDER"')
        print('    t, optional, default-vaule:\'current working directory/190530 PD/\', --target-folder="target-FOLDER"')    
        print('    z, optional, default-vaule:\'[contry code]_PD_3035_GML\', --zip-name=name-sencond-part')      
        print('    a, optional, default-vaule:\'PD\', --atom-name=ATOM file name')    
        print('    m, optional, default-vaule:\'Population Distribution and Demography\', --atom-title=ATOM title')  
        print('    b, optional, default-vaule:\'http://localhost:8080/ATOM/\', --base-url=base url')     
        print('    e, optional, default-vaule:\'current working directory/readme_template.md\', --readme-template=template location')           
        print('    n, optional, default-vaule:\'readme.md\', --readme-name=readme name')   
        print('Examples:')
        print('    default usage:')
        print('        python AtomDataGenerator.py')        
        print('    set root-folder location to \"other_folder\" to locate the source directory:')
        print('        python AtomDataGenerator.py --root-folder=\"./other_folder/\"')
        print('    set target-folder location to \"other_folder\" to store the Data and Metadata generated:')
        print('        python AtomDataGenerator.py --target-folder=\"./other_folder/\"')
        print('    set zip file name to a different suffix (to replace "_PD_3035_GML" part)') 
        print('        python AtomDataGenerator.py --zip-name=\"zip_name\"')       
        print('    set the name to the *.atom file to generate.')
        print('        python AtomDataGenerator.py --atom-name=\"atom_file_name\"')  
        print('    set the title in the atom file.')
        print('        python AtomDataGenerator.py --atom-title=\"atom_title\"')  
        print('    set the base url for in generated *.atom file.')
        print('        python AtomDataGenerator.py --base-url=\"base_url\"') 
        print('    set the reame template for generating readme file in every zip file.')
        print('        python AtomDataGenerator.py --readme-template=\"template_location\"') 
        print('    set the readme name to be generated.')
        print('        python AtomDataGenerator.py --readme-name=\"readme_name\"') 
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
    elif opt in ('-e', '--readme-template'):
        template_path_file = arg
    elif opt in ('-n', '--readme-name'):
        readme_name = arg   

def check_root_dir(folder):        
    if(not os.path.isdir(folder)):        
        folder= os.getcwd()
        print("The root-folder is invalid, it is set to current working directory.")
    folder = os.path.abspath(folder)
    return folder

def check_target_dir(folder):   
    folder = os.path.abspath(folder)    
    if(os.path.isdir(folder)):
        shutil.rmtree(folder)       
    os.makedirs(folder)
    os.makedirs(folder + os.sep + 'Metadata')  
    return folder  

def generate_data(root_folder):   
    country_atom_added_list=[]
    country_zipped_list=[]
    feed_entry_object_list = {}
    file_code_name_dict = {}

    for root,dirs,files in os.walk(root_folder, topdown=True):   
        files.sort()       
        for filename in files:                       
            target_filename_country_code = root.split(os.path.sep)[-1]           
            if (filename.lower().endswith(gml_suffix.lower()) and target_filename_country_code.upper() in country_code_dict.keys() and not (target_filename_country_code in country_zipped_list)): 
                target_readme_path = os.path.join(root, readme_name)
                generate_readme(template_path_file, target_filename_country_code, target_readme_path)
                target_path_name = os.path.join(target_folder, target_filename_country_code + "_" + atom_file_name + zip_name)
                zipDir(root, (target_path_name + '.zip'))                            
                country_zipped_list.append(target_filename_country_code) 
                if (target_filename_country_code in country_atom_added_list and not file_code_name_dict[target_filename_country_code].split("_")[0] == filename.split("_")[0]):               
                    change_feed_entry (feed_entry_object_list[target_filename_country_code], target_filename_country_code, filename)
                elif not target_filename_country_code in country_atom_added_list:
                    fe = generate_feed_entry(target_filename_country_code, filename)
                    country_atom_added_list.append(target_filename_country_code)
                    feed_entry_object_list[target_filename_country_code] = fe
                    file_code_name_dict[target_filename_country_code] = filename
                    
            if (filename.lower().endswith(metadata_suffix.lower()) and (atom_file_name.upper() in filename.upper())):                   
                metadata_path_name = os.path.join((target_folder + os.sep + 'Metadata'), filename)
                root_path_name = os.path.join((root), filename)                              
                try:
                    shutil.copy2(os.path.join(root,filename), metadata_path_name)    
                    print("Copy Metadata file to metadata_path_name: " + metadata_path_name + ", from root_path_name: " + root_path_name) 
                except IOError as e:
                    print("Skipped copy as " + str(e)) 
                    pass                         
                if  (target_filename_country_code in country_atom_added_list and not file_code_name_dict[target_filename_country_code].split("_")[0] == filename.split("_")[0]):
                    change_feed_entry(feed_entry_object_list[target_filename_country_code], target_filename_country_code, filename)
                elif not target_filename_country_code in country_atom_added_list: 
                    fe = generate_feed_entry(target_filename_country_code, filename)
                    country_atom_added_list.append(target_filename_country_code)
                    feed_entry_object_list[target_filename_country_code] = fe
                    file_code_name_dict[target_filename_country_code] = filename

def zipSinglefile(target_path_name, root_path, file_to_zip):  
    zip_file = zipfile.ZipFile(target_path_name + '.zip', 'w')
    zip_file.write(os.path.join(root_path,file_to_zip), file_to_zip, compress_type=zipfile.ZIP_DEFLATED)
    zip_file.close()

def zipDir(dirPath, zipPath):
    try:
        zipf = zipfile.ZipFile(zipPath , mode='w')
        lenDirPath = len(dirPath)
        for root, _ , files in os.walk(dirPath):
            for file in files:               
                filePath = os.path.join(root, file)
                zipf.write(filePath , filePath[lenDirPath :], compress_type=zipfile.ZIP_DEFLATED )
        print("Create zip in target_path_name: " + zipPath + ", from folder: " + dirPath) 
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
    finally:
        zipf.close()   

def generate_feed_main():      
    #fg.language('es')        
    fg.title(atom_title)    
    fg.link(href=base_url + atom_file_name +'/' + atom_file_name +'.atom', rel="self", type="application/atom+xml", hreflang="en", title="This document" )
    fg.link(href=base_url + "ATOM.atom", rel="up", type="application/atom+xml", hreflang="es", title="ATOM FEED" )       
    fg.id(base_url + atom_file_name +'/' + atom_file_name +'.atom')
    fg.rights('{Copyrights}')  
    date = datetime.datetime(2019, 5, 21, 12, 0, 0, 0, pytz.UTC)
    fg.updated(date)      
    fg.link(rel="describedby", href="http://inspire.ec.europa.eu/featureconcept/StatisticalDistribution", type="text/html", title="Statistical Distribution")       
    fg.author({'name':'(Author)','email':'{Contact}'})        
    
def generate_feed_entry(country_code, filename):    
    fe = fg.add_entry(feedEntry=None, order='append')        
    fe.category(term="http://www.opengis.net/def/crs/EPSG/0/3035", label="ETRS89 / LAEA Europe")
    date = datetime.datetime(2019, 5, 21, 12, 0, 0, 0, pytz.UTC)
    fe.updated(date)
    fe.title(country_code_dict[country_code.upper()])
    entry_data = (base_url + atom_file_name +'/Data/' + filename).replace("_MD.xml",".gml")
    entry_metadata = (base_url  + atom_file_name +'/Metadata/' + filename).replace(".gml","_MD.xml")
    entry_zip = base_url + atom_file_name +'/Data/' + country_code + "_" + atom_file_name + zip_name + '.zip' 
    entry_img = base_url + 'img/'+ country_code_dict[country_code.upper()] + '.png'
    fe.id(entry_data)
    entry_title = atom_title + ' - ' + country_code     
    entry_metadata_href = 'b&gt;Metadata:&lt;/b&gt; &lt;a href="' + entry_metadata + '" target="_blank" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    fe.link(rel="alternate", href=entry_zip, type="application/gml+xml", length="0", hreflang="en", title=entry_title)   
    entry_summary = '&lt;div&gt;&lt;div&gt;ZIP file containing information about the ' + atom_title + ' in '+ country_code_dict[country_code.upper()] + '.&lt;/br&gt;&lt;div&gt;&lt;b&gt;Formats:&lt;/b&gt; &lt;i&gt;GML, Shapefile, CSV&lt;/i&gt;&lt;/div&gt;&lt;div&gt;&lt;'+ entry_metadata_href +'&lt;div&gt;&lt;a href="' + entry_zip +'" &gt; Download &lt;/a&gt;&lt;/div&gt;&lt;img width="100px" vspace="10" border="1" src="'+ entry_img + '" alt="'+ country_code_dict[country_code.upper()] +'" title="' + country_code_dict[country_code.upper()] +'"&gt;&lt;/div&gt;'
    fe.summary(entry_summary)   
    return fe

def remove_feed_entry(fe):
    fg.remove_entry(fe)

def change_feed_entry(fe, country_code, filename):  
    entry_metadata = (base_url  + atom_file_name +'/Metadata/' + filename).replace(".gml","_MD.xml")
    entry_zip = base_url + atom_file_name +'/Data/' + country_code + "_" + atom_file_name + zip_name + '.zip' 
    entry_metadata_href = 'b&gt;Metadata:&lt;/b&gt; &lt;a href="' + entry_metadata + '" target="_blank" &gt; Link &lt;/a&gt;&lt;/div&gt;'
    entry_img = base_url + 'img/'+ country_code_dict[country_code.upper()] + '.png'
    entry_summary = '&lt;div&gt;&lt;div&gt;ZIP file containing information about the ' + atom_title + ' in '+ country_code_dict[country_code.upper()] + '.&lt;/br&gt;&lt;div&gt;&lt;b&gt;Formats:&lt;/b&gt; &lt;i&gt;GML, Shapefile, CSV&lt;/i&gt;&lt;/div&gt;&lt;div&gt;&lt;'+ entry_metadata_href +'&lt;div&gt;&lt;a href="' + entry_zip +'" &gt; Download &lt;/a&gt;&lt;/div&gt;&lt;img width="100px" vspace="10" border="1" src="'+ entry_img + '" alt="'+ country_code_dict[country_code.upper()] +'" title="' + country_code_dict[country_code.upper()] +'"&gt;&lt;/div&gt;'
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

def generate_readme(template_path_file, country_code, target_file_name):
    try:
        f = open(template_path_file,'r')
        filedata = f.read()
        f.close()
        newdata = filedata.replace('{CC}', country_code).replace('{TH}', atom_file_name)
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
fg = FeedGenerator()
generate_feed_main()
generate_data(root_folder)
target_atom_file = os.path.join(target_folder, (atom_file_name + '.atom'))
fg.atom_file(target_atom_file, pretty=True)
replace_value_for_feed(target_atom_file)
print('Write ' +  atom_file_name + '.atom Finished in ' + target_folder) 
print('Execution time: ' + str((time.time() - start_time)//60) + ' minutes, ' + str(round((time.time() - start_time)%60, 3)) + ' seconds')
print('Finished.')