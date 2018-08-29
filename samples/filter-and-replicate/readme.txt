If python is not found on your path, run the command: 

$env:path="$env:Path;C:\Python27"

If the tableau libraries on not included on your python installation, then run the commands:

.\pip.exe install tableauserverclienterverclient
.\pip.exe install tableaudocumentapi

Once the environment is set up, drag and drop all tableau workbook items into Source, run the python script with the command below:

python filter-and-replicate.py --server https://10ay.online.tableau.com/ --username Craig.hindal@thorpepme.com --logging-level error --sitename thorpespecialtyservicescorporation

Type in the tableau password corresponding to the account in the command above.

The script should be completed when a message displays at the end.