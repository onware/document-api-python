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
from dateutil.parser import parse
import platform
import datetime
import time
import sys
import shutil

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
    parser.add_argument('--sitename','-sn', required=True, help='site name to sign into')
    parser.add_argument('--password', '-p', required=True, help='Publishing Password')
    parser.add_argument('--logging-level', '-l', choices=['debug', 'info', 'error'], default='error',
                        help='desired logging level (set to error by default)')
    parser.add_argument('--as-job', '-a', help='Publishing asynchronously', action='store_true')

    
    args = parser.parse_args()
    
    password = args.password


    # Set logging level based on user input, or error by default
    logging_level = getattr(logging, args.logging_level.upper())
    logging.basicConfig(level=logging_level)
    
    # Step 1: Sign in to server.
    tableau_auth = TSC.TableauAuth(args.username, password, args.sitename)
    server = TSC.Server(args.server)
    count = 1
    overwrite_true = TSC.Server.PublishMode.Overwrite

    # Open the workbook
    source = "Source"
    zip = "Zip"
    export = "Export"
    columns = ['Workbook', 'Format', 'Project', 'Branch', 'Directory', 'PublishDate','ModifiedDate' ]
    oldworkbookname = ""
    with server.auth.sign_in(tableau_auth):
        with open('databases.csv',mode='r') as csvfile:
            total = sum(1 for line in open('databases.csv'))
            print("Total file count: " + str(total-1))
            databases = csv.DictReader(csvfile, delimiter=',', quotechar='"')    
            outfile = open('databases_new.csv',mode='wb') 
            writer = csv.DictWriter(outfile,fieldnames=columns)
            writer.writeheader()
            for row in databases:               
                if any(row):
                    if(row['Workbook'] != oldworkbookname):
                        shutil.rmtree('Export', ignore_errors=True, onerror=None)
                        os.makedirs('Export')
                        shutil.rmtree('Zip', ignore_errors=True, onerror=None)
                        os.makedirs('Zip')

                    print ("working on item: "+ str(count)+" \n")
                    mtime = parse(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getmtime(os.path.join(source, row['Workbook'] + ".twbx")))))
                    ptime = parse(row['PublishDate'])          
                    count = count +1 
                    if(mtime>ptime):                             
                        if(row['Format'] == ".twbx"):
                            originaltableauworkbook = zipfile.ZipFile(os.path.join(source, row['Workbook'] + ".twbx"))                  
                            originaltableauworkbook.extractall(zip)
                            test = os.listdir(zip)

                            for item in test:
                                if item.endswith(".twb") :
                                    sourceWB = Workbook(os.path.join(zip, item))
                                    for datasource in reversed(sourceWB.datasources):
                                        # Update the filters
                                        for children in datasource._datasourceXML._children:
                                            if "column" in children.attrib and "class" in children.attrib:
                                                if "Branch" in children.attrib["column"] and children.attrib["class"] == "categorical":
                                                    for subchildren in children._children:
                                                        if "member" in subchildren.attrib:
                                                            subchildren.attrib["member"] = '"' + row['Branch'] + '"'

                                             
                                    # Save our newly created workbook with the new file name
                                    outputpath = os.path.join(export, row['Workbook'] + ' - ' + row['Branch'] + ".twb")
                                    sourceWB.save_as(outputpath) 
                                    
                                    z = zipfile.ZipFile(os.path.join(export, row['Workbook'] + ' - ' + row['Branch'] + row['Format']),mode='w',compression=zipfile.ZIP_DEFLATED) 
                                    z.write(os.path.join(export, row['Workbook'] + ' - ' + row['Branch'] + ".twb"),item.replace("Export",""))                                    
                                    for item in list_files(zip):                                          
                                        if item.endswith(".twb") != True:   
                                            z.write(item,item.replace("Zip",""))   
                                      
                                    z.close()
                                       

                        elif (row['Format'] ==".twb"):
                            sourceWB = Workbook(os.path.join(source, row['Workbook'] + ".twb"))                        
                            # Update the filters
                            for datasource in reversed(sourceWB.datasources):
                                for children in datasource._datasourceTree._root._children:
                                    if "column" in children.attrib and "class" in children.attrib:
                                        if children.attrib["column"] == "[Branch]" and children.attrib["class"] == "categorical":
                                            for subchildren in children._children:
                                                if "member" in subchildren.attrib:
                                                   subchildren.attrib["member"] = '"' + row['Branch'] + '"'
                                     
                        # Save our newly created workbook with the new file name
                        outputpath = os.path.join(export, row['Workbook'] + ' - ' + row['Branch'] + ".twb")
                        sourceWB.save_as(outputpath) 
                        oldworkbookname = row['Workbook']

                        all_projects, pagination_item = server.projects.get()
                        default_project = next((project for project in all_projects if project.name == row['Project']), None)              
                        
                        if default_project is not None:
                            new_workbook = TSC.WorkbookItem(default_project.id,show_tabs= True)
                            if args.as_job:
                                new_job = server.workbooks.publish(new_workbook,os.path.join(export, row['Workbook'] + ' - ' + row['Branch'] + row['Format']), overwrite_true)
                                row['PublishDate'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                writer.writerow(row)
                                print("Workbook published. JOB ID: {0}".format(new_job.id))
                            else:
                                row['PublishDate'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                writer.writerow(row)
                                new_workbook = server.workbooks.publish(new_workbook, os.path.join(export, row['Workbook'] + ' - ' + row['Branch'] + row['Format']), overwrite_true)
                                print("Workbook published. ID: {0}".format(new_workbook.id))

                        else:
                            error = "The default project could not be found."
                            raise LookupError(error)
    print ("Done!!!!!!!!!!!!!!!!!!")
    outfile.close()
    statinfo = os.stat('databases_new.csv')
    if(statinfo.st_size>67):
        os.remove('databases.csv')
        os.rename('databases_new.csv','databases.csv')
    else:
         os.remove('databases_new.csv')





    
if __name__ == '__main__':
    main()




