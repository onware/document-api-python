import csv              # so we can work with our database list (in a CSV file)
############################################################
# Step 1) Use Workbook object from the Document API
############################################################
import argparse
import getpass
import logging
import zipfile
import tableauserverclient as TSC
import os
from tableauserverclient import ConnectionCredentials, ConnectionItem
from tableaudocumentapi import Workbook


############################################################
# Step 3) Use a database list (in CSV), loop thru and
#          create new .twb's with their settings
############################################################

#https://stackoverflow.com/questions/19932130/iterate-through-folders-then-subfolders-and-print-filenames-with-path-to-text-f
def list_files(dir):                                                                                                  
    r = []                                                                                                            
    subdirs = [x[0] for x in os.walk(dir)]                                                                            
    for subdir in subdirs:                                                                                            
        files = os.walk(subdir).next()[2]                                                                             
        if (len(files) > 0):                                                                                          
            for file in files:                                                                                        
                r.append(subdir + "/" + file)                                                                         
    return r   

def main():

    parser = argparse.ArgumentParser(description='Publish a workbook to server.')
    parser.add_argument('--server', '-s', required=True, help='server address')
    parser.add_argument('--username', '-u', required=True, help='username to sign into server')
    parser.add_argument('--sitename','-sn',required=True, help='site name to sign into')
    parser.add_argument('--logging-level', '-l', choices=['debug', 'info', 'error'], default='error',
                        help='desired logging level (set to error by default)')
    parser.add_argument('--as-job', '-a', help='Publishing asynchronously', action='store_true')
    
    args = parser.parse_args()
    
    password = getpass.getpass("Password: ") 


    # Set logging level based on user input, or error by default
    logging_level = getattr(logging, args.logging_level.upper())
    logging.basicConfig(level=logging_level)
    
    # Step 1: Sign in to server.
    tableau_auth = TSC.TableauAuth(args.username, password, args.sitename)
    server = TSC.Server(args.server)
    
    overwrite_true = TSC.Server.PublishMode.Overwrite
    
    with server.auth.sign_in(tableau_auth):
        with open('databases.csv') as csvfile:
            databases = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in databases:   		
                # Open the workbook
                   
                   dir_name = "Zip"
                   originaltableauworkbook = zipfile.ZipFile(row['Workbook'] + ".twbx")                  
                   originaltableauworkbook.extractall(dir_name)
                   test = os.listdir(dir_name)

                   for item in test:
                       if item.endswith(".twb"):
                           sourceWB = Workbook(os.path.join(dir_name, item))

                        # Update the filters
                           for datasource in reversed(sourceWB.datasources):
                               for children in datasource._datasourceTree._root._children:
                                   if "column" in children.attrib and "class" in children.attrib:
                                       if children.attrib["column"] == "[Branch]" and children.attrib["class"] == "categorical":
                                           for subchildren in children._children:
                                               if "member" in subchildren.attrib:
                                                   subchildren.attrib["member"] = '&quot;' + row['Branch'] + '&quot;'
                                    
                        # Save our newly created workbook with the new file name
                           sourceWB.save_as(row['Workbook'] + ' - ' + row['Branch'] + row['Format']) 
                           z = zipfile.ZipFile(row['Workbook'] + ' - ' + row['Branch']+ ".twbx",mode='w')
                           z.write(row['Workbook'] + ' - ' + row['Branch'] + row['Format'])
                           for item in list_files(dir_name):
                               if item.endswith(".twb") != True:
                                   z.write(item,item.replace("Zip",""))
                           z.close()

                       #all_projects, pagination_item = server.projects.get()
                       #default_project = next((project for project in all_projects if project.name == row['Project']), None)
                       #
                       #
                       #connection = ConnectionItem()
                       #connection.server_address = "10ay.online.tableau.com"
                       #connection.server_port = "443"
                       #connection.connection_credentials = ConnectionCredentials(args.username, password, True)
                       #
                       #all_connections = list()
                       #all_connections.append(connection)
                       #
                       #if default_project is not None:
                       #    new_workbook = TSC.WorkbookItem(default_project.id)
                       #    if args.as_job:
                       #        new_job = server.workbooks.publish(new_workbook,row['Workbook'] +".twbx", overwrite_true)
                       #        print("Workbook published. JOB ID: {0}".format(new_job.id))
                       #    else:
                       #        new_workbook = server.workbooks.publish(new_workbook, row['Workbook'] +".twbx", overwrite_true)
                       #        print("Workbook published. ID: {0}".format(new_workbook.id))
                       #else:
                       #    error = "The default project could not be found."
                       #    raise LookupError(error)




if __name__ == '__main__':
    main()





