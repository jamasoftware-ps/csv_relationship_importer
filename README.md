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
#### Config:
 * Open the config.py file in a text editor and set the relevant settings for your environment.
 
 * Connections Settings:  These are the settings required to connect to Jama Connect via the REST API
   * base_url: this is the URL of your Jama Instance ex: https://example.jamacloud.com
   * username: The username of the user
   * password: The password of the user
   * oauth: Set to True or False.  If set to True, the client_id and client_secret variables will be used to log into 
   Jama connect via OAuth
   * client_id:  The Client ID of the user
   * client_secret: The Client Secret of the user
   * NOTE: the unused set of credentials (username and password) or (client_id and client_secret) 
   should be set to None, or an empty string "".  They should not be removed from the config file, 
   this may cause errors.
 
 * CSV Settings: These settings inform the script about the structure of the CSV file and its data.
   * csv_location: This can be set to a specific CSV file or a Directory containing multiple CSV files to be processed.
   * csv_has_headers: Boolean True or False, Set to True if the CSV file has headers, Set to False if the CSV file has
   no headers and provide the headers manually in the csv_headers setting
   * csv_headers: a list of header names to be used.  this setting is only used if csv_has_headers is set to False.
   * csv_source_column: The name of the column that contains source item data.
   * csv_target_column: The name of the column that contains target item data.
   * csv_relationship_type_column: The name of the column that contains relationship type data.
   
 * Import Settings:  These Settings inform the script how the data should be imported to Jama.
   * match_on_custom_field: Boolean True or False. Setting this to False will tell the script to expect the CSV file to 
   contain API ID's using API ID's instead of a custom field data will result in improved performance.
   * source_item_custom_field_name: This is the field name to match on for the source items
   * target_item_custom_field_name: This is the field name to match on for the target items.
   * source_project_list: This is a list of project ID's that the script will look in to match source items.
   Set to an empty list [] to match all projects
   * target_project_list: This is a list of project ID's that the script will look in to match target items.
   Set to an empty list [] to match all projects
   * default_relationship_type: this is the API id of the relationship type to use as a default
#### Execution:
 * Open the terminal to the directory the script is in and execute the following:   
 ``` 
 pipenv run python csv_relationship_importer.py
 ```