import os.path
from datetime import datetime
import sqlite3
import tanium
import tanium.sensor_io.sensor_input
#
# Copyright (c) 2024 Tanium
#
# DIRECTORIES
TC_ROOT = tanium.client.get_client_dir()
NORM_INDEX_DIR = os.path.normpath('Tools/SoftwareManagement/data')
MONITOR_DB = os.path.join(TC_ROOT, NORM_INDEX_DIR)
# FILES
CORE_DB = os.path.join(MONITOR_DB, 'software-management.db')
# Sensor input
from tanium.sensor_io import sensor_input
inputs = sensor_input.SensorInputs()
inputs.add_param('NumDays', '||NumDays||')
NumDays = inputs.get_param('NumDays')

def getContentsFromDB():
    try:
        conn = sqlite3.connect('file:' + CORE_DB + '?mode=ro', uri=True)
    except:
        tanium.results.add("ERROR: Failed to connect to the Software Management database. Confirm Deploy is installed.")
        exit()
    cursor = conn.cursor()
    # Get scan details
    try:
        SQL_Query = "SELECT software_package_id,software_package_edit_id,software_package_name,operation,start_time,was_successful,error FROM Software_Package_history WHERE start_time >= datetime('now', '-" + str(NumDays) + " days');"
        cursor.execute(SQL_Query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except:
        tanium.results.add("ERROR: \'Software_Package_history\' table missing from SoftwareManagementDB")
        #import traceback
        #print(traceback.format_exc())

try:
    data=getContentsFromDB()
    if len(data) == 0:
        tanium.results.add("No software packages were found.")
    else:
        for item in data:
            install_date = datetime.fromisoformat(item[4])
            install_date_clean = install_date.replace(microsecond=0, tzinfo=None)
            string_out = str(item[0]) + "|" + str(item[1]) + "|" + str(item[2]) + "|" + str(item[3]) + "|" + str(install_date_clean) + "|" + str(item[5])+ "|" + str(item[6])
            tanium.results.add(string_out)
          
except:
    #import traceback
    #print(traceback.format_exc())
    tanium.results.add("TSE Error review if Deploy tools are installed.")