import os

###################################################################################################
#    Jama Connect Connection settings
###################################################################################################
# Jama Base URL EX: https://instance.jamacloud.com
base_url = os.environ.get('JAMA_BASE_URL')

# BASIC AUTH:
# Jama Username
username = os.environ.get('JAMA_USERNAME')

# Jama Password
password = os.environ.get('JAMA_PASSWORD')

# OAuth:
oauth = False   # Set this to True to use OAuth instead of basic auth.

# Client ID
client_id = os.environ.get('JAMA_CLIENT_ID')

# Client Secret
client_secret = os.environ.get('JAMA_CLIENT_SECRET')


###################################################################################################
#    CSV settings
###################################################################################################
# csv_location can be set to a specific csv file or a directory of csv file to import multiple files at once.
# NOTE: if using import by directory, all files will be imported with the same configuration.
csv_location = './simple_csv_with_headers.csv'

# Set to True if the file has headers, False otherwise; If CSV file does not have headers,header names must be supplied.
csv_has_headers = True
# If the CSV file does not have headers, please give a description of each column in order they occur in the file.
csv_headers = []

# The CSV column that contains the data to match the source item
csv_source_column = 'SourceGuiID'
# THe CSV column that contains the data to match the target item
csv_target_column = 'DestGuiID'

# Optional: This column can set the type of relationship to be created.
# Set to None if relationship type does not need to be imported
csv_relationship_type_column = 'Connector_Type'


###################################################################################################
#    Import settings
###################################################################################################
# Setting match on custom field to False will tell the program to expect raw API ID's, this improves performance.
match_on_custom_field = False

# The name's of the custom fields to do lookup's.  This is a field on a jama item
source_item_custom_field_name = 'ea_legacy_id'
target_item_custom_field_name = 'ea_legacy_id'

# Items will only be matched against items in the projects in the following lists, leave empty to match all projects.
source_project_list = [1279]
target_project_list = [1279]

# Default relationship type
default_relationship_type = 4


###################################################################################################
#    Logging settings
###################################################################################################
# Logging directory
log_directory = './logs/'
# Log file name prefix prefix
log_file_name_prefix = 'csv_relationship_importer'
# Logging date time format
log_date_time_format = "%Y-%m-%d %H_%M_%S"
