# Jama Software

## CSV Relationship Importer Script

This script will allow the user to import relationship data from a csv file to Jama. 

#### Supported features:
* Create relationships within a single project or that span projects
* Allows matching items based on the contents of any text field.
* Allows the type of relationship to be specified

# Requirements
* [python 3.7+](https://www.python.org/downloads/)
* [Pipenv](https://docs.pipenv.org/en/latest/) 

## Installing dependencies 
 * Download and unzip the package contents into a clean directory.
 * execute pipenv install from the commandline.
 
## Usage
 * Open the config.py file in a text editor and set the relevant settings for your environment.
 * Open the terminal to the directory the script is in and execute the following:   
 ``` 
 pipenv run python csv_relationship_importer.py
 ```