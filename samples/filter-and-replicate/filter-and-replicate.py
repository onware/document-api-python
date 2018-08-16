import csv              # so we can work with our database list (in a CSV file)

############################################################
# Step 1)  Use Workbook object from the Document API
############################################################
from tableaudocumentapi import Workbook

############################################################
# Step 3)  Use a database list (in CSV), loop thru and
#          create new .twb's with their settings
############################################################
with open('databases.csv') as csvfile:
    databases = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    for row in databases:

        # Open the workbook
        sourceWB = Workbook(row['Filename'] + row['Format'])

        # Update the filters
        for datasource in sourceWB.datasources:
            for filter in datasource:
                if filter.column == '[Branch]'
                    filter.groupfilter.member = '&quot;' + row['Branch'] + '&quot;'
                    
        # Save our newly created workbook with the new file name
        sourceWB.save_as(row['Filename'] + ' - ' + row['Branch'] + row['Format'])