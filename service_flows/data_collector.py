# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode
import os
import shutil
import webbrowser
import time
from datetime import date
import csv

# START DATE: 10 FEBBRAIO 2020 - GRAPH START = 1581292860
# STEP 86400 (= SECONDI IN UN GIORNO 60*60*24)
STEP = 86400  # seconds in a day
START_DATE = date(2020,2,9)
BEGINNING_OF_TIME = 1581206460

DAY_DIFF = date.today() - START_DATE
DAYS = DAY_DIFF.days

# Everyday, catch previous day traffic
START_TIME = BEGINNING_OF_TIME + (DAYS-1) * STEP - 7200  # '7200' -> Begins two hours before to fill previous day gap
END_TIME = START_TIME + STEP + 7200

def main():

    link_url = {
        "BENL": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47771&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ams-bru", 0],
        "DENL": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=48423&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ams-fra", 0],
        "DUNL": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47927&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ams-ham", 0],
        "NLUK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=48929&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ams-lon", 1],
        "GCGR": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=36069&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ath-ath2", 0],
        "GRIT": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47977&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ath-mil", 1],
        "ATGC": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=36087&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ath2-vie", 0],
        "HUSK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=8630&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bra-bud", 0],
        "ATSK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47779&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bra-vie", 0],
        "BEUK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=9122&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bru-lon", 1],
        "HURO": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=21165&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "buc-bud", 0],
        "BGRO": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=21019&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "buc-sof", 0],
        "HUSI": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47789&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bud-lju", 1],
        "CZHU": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47791&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bud-pra", 0],
        "ATHU": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47937&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bud-vie", 0],
        "HRHU": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47787&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "bud-zag", 0],
        "IEIR": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47799&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "dub-dub", 0], ## ricontrolla! (già fatto una volta)
        "IEUK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47797&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "dub-lon", 1],
        "IRUI": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=39699&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "dub2-lon2", 1],
        "CHDE": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=48189&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "FRA-GEN", 0],
        "DEDU": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=20493&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "fra-ham", 1],
        "DEPL": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47803&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "fra-poz", 1],
        "CZDE": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=53015&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "FRA-PRA", 0],
        "CHES": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47831&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "gen-mad", 1],
        "CHFN": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=20747&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "gen-mar", 1],
        "CHIT": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=52853&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "GEN-MIL2", 1],
        "CHFR": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=48177&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "GEN-PAR", 1],
        "DUEE": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=20497&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "ham-tal", 1],
        "LNLT": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=12697&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "kau-kau", 0], ## ricontrolla!
        "LTPL": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=526&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "kau-poz", 1],
        "LNLV": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47863&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "kau-rig", 1],
        "PRPT": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47857&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "lis-lis", 0],
        "PTUK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=7450&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "lis-lon", 1],
        "ESPR": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47865&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "lis-mad", 0],
        "ITSI": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=54087&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "LJU-MIL2", 0],
        "UIUK": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=46031&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "lon-lon2", 0],
        "FRUI": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47463&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "lon2-par", 0],
        "ESFR": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47849&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "mad-par", 1],
        "ITFN": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=20737&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "mar-mil2", 0],
        "ATIT": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=52905&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "MIL2-VIE", 0],
        "ATPL": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47877&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "poz-vie", 0],
        "ATCZ": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=52961&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "PRA-VIE", 0],
        "ETLV": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47861&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "rig-tal", 0],
        "ATBG": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=21125&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "sof-vie", 0],
        "EEET": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47859&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "tal-tal", 1],
        "ATHR": ["https://tools.geant.org/portal/links/p-cacti/graph_xport.php?local_graph_id=47883&rra_id=0&view_type=tree&graph_start={}&graph_end={}".format(START_TIME, END_TIME), "vie-zag", 1],
    }

    # Create Dataset Folder
    create_folder('dataset_geant')

    # Create Today's Data Folder
    create_today_folder()

    # Download Today's Data
    download_data(link_url)

    # Move downloaded files in the correct folder
    move_downloaded_data()

    # Process downloaded data
    process_data(link_url)


def download_data(urls):
    
    for link in urls:
        webbrowser.open(urls[link][0])
        time.sleep(4)

def create_folder(folder_name):
    current_dir = os.path.dirname(__file__)
    database_path = os.path.join(current_dir, folder_name)

    if not os.path.exists(database_path):
        os.makedirs(database_path, exist_ok=True)
    
    return database_path

def create_today_folder():

    today_string = str(date.today())
    folder_name = os.path.join('geant_daily_data', today_string)

    create_folder(folder_name)

    return folder_name

def move_downloaded_data():

    source_path = '/home/' + os.getlogin() + '/Downloads'
    current_dir = os.path.dirname(__file__)
    today_string = str(date.today())
    destination_path = os.path.join(current_dir, 'geant_daily_data', today_string) 
    #destination_path = create_today_folder()
    files = os.listdir(source_path)

    for f in files:
        if f.endswith('.csv'):
            source_file = os.path.join(source_path, f)
            shutil.move(source_file, destination_path)

def process_data(urls):

    # init variable
    dataset_path = create_folder('dataset_geant')

    ## READ TODAY DATA
    current_dir = os.path.dirname(__file__)
    today_folder = create_today_folder()
    source_path = os.path.join(current_dir, today_folder)
    files = os.listdir(source_path)

    ## FIND LINK FILE 
    for link in urls:
        link_id = urls[link][1]
        for f in files:
            if link_id in f:
                # Import Data
                csvfile = os.path.join(source_path, f)
                csvdata = import_csv(csvfile)
                # Export Data to correct location
                destination_path = os.path.join(dataset_path, f)
                export_csv(destination_path, csvdata[12:])
    
    ## VALIDATE DATA
    validate_data(dataset_path, urls)
                
def import_csv(csvfilename):
    data = []
    with open(csvfilename, "r", encoding="utf-8", errors="ignore") as scraped:
        reader = csv.reader(scraped, delimiter=',')
        for row in reader:
            if row:  # avoid blank lines
                data.append(row)
    return data

def export_csv(path, data):

    # Append data to file @ path if file exists, otherwise create it.
    with open(path, 'a+') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

def validate_data(path, urls):

    files = os.listdir(path)

    for f in files:
        ## IMPORT FILE DATA
        csvfile = os.path.join(path, f)
        csvdata = import_csv(csvfile)

        ## DELETE DUPLICATE ROWS
        # Find rows with same date and time
        for i in range(len(csvdata)):
            for j in range(len(csvdata[0:i])):
                # if date is equal to previous row date
                if csvdata[i][0] == csvdata[j][0]:
                    # ...copy this row to that row
                    csvdata[j] = csvdata[i]
        # Delete all equal rows
        foo_csvdata_set = set(tuple(x) for x in csvdata)
        foo_csvdata = [list(x) for x in foo_csvdata_set]
        foo_csvdata.sort(key = lambda x: csvdata.index(x))

        csvdata = foo_csvdata.copy()

        ## SET NaN ELEMENTS TO 0
        for row in csvdata:
            for index, value in enumerate(row):
                if value == 'NaN':
                    row[index] = '0'

        ## ADD HEADING
        # Find Link
        for link in urls:
            if urls[link][1] in f:
                link_name = get_key_from_value(urls, urls[link][1])
                eman_knil = link_name[len(link)//2:] + link[:len(link)//2]
                # Check if data is coherent (straight = 1) or vice versa (reverse = 0)
                if urls[link][2] == 1:
                    heading = ['DATE', '{}'.format(link_name), '{}_peak'.format(link_name), '{}'.format(eman_knil), '{}_peak'.format(link_name) ]
                else:
                    heading = ['DATE', '{}'.format(eman_knil), '{}_peak'.format(eman_knil), '{}'.format(link_name), '{}_peak'.format(link_name) ]
                break

        # Insert heading on top
        if csvdata[0][0] != 'DATE':
            csvdata.insert(0, heading)

        ## SAVE FILE
        with open(csvfile, 'w') as csvf:
            writer = csv.writer(csvf)
            for row in csvdata:
                writer.writerow(row)

def get_key_from_value(dictionary, val):
    
    for k, v in dictionary.items():
        if v[1] == val:
            return k


if __name__ == "__main__":
    main()
