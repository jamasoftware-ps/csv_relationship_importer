import datetime
import os
import sys
import time
import csv
import logging

from py_jama_rest_client.client import JamaClient, APIException

import config
import project_utils as utils


class CSVRelationshipImporter:
    """
    This class exposes a set of functions that allow the import of relationship data from a CSV file to Jama Connect.
    """

    logger = logging.getLogger('CSVRelationshipImporter')

    def __init__(self, j_client: JamaClient, ):
        """
        Initialize the CSV Relationships Importer
        :param j_client:
        """
        self.j_client = j_client
        self.raw_relationship_data = []
        self.prepped_relationship_data = []
        self.source_item_map = {}  # Stores custom field -> item id info
        self.target_item_map = {}  # Stores custom field -> item id info
        self.relationship_map = {}  # Stores Relationship name -> relationship id
        self._build_relationship_map()
        self._csv_line_count = 0  # Stores the number of lines read in from csv

    def load_csv_data(self,
                      csv_file: str,
                      has_headers: bool,
                      headers: list,
                      source_item_column: str,
                      target_item_column: str,
                      relationship_type_column: str):
        """
        This method will load data from a CSV file into a list of relationships to be processed and posted.

        By using a CSV Dict reader, we allow for the consumption of non standardized CSV files,  All we need is the
        name of the relevant columns to perform our operations.

        :param csv_file: The path to the file to be read
        :param has_headers: A boolean that denotes if the CSV file has headers
        :param headers: A list of header names, or None if the file already has headers
        :param source_item_column: A string describing the column name that contains the source item data
        :param target_item_column: A string describing the column name that contains the target item data
        :param relationship_type_column: None or a str describing the column name with the relationship type item data
        :return: None
        :raise ValueError: If one of the provided column names cannot be located in the CSV dictreader.fieldnames var
        """
        # Create log entry about the loading of this file.
        CSVRelationshipImporter.logger.info('Loading CSV Data from: {}'.format(csv_file))

        # Clear out any possible old data.
        self.raw_relationship_data.clear()

        # Keep track of how many lines are read.
        csv_lines_read = 0

        # Open the CSV file for reading, use the utf-8-sig encoding to deal with excel file type outputs.
        with open(csv_file, encoding='utf-8-sig') as open_csv_file:
            # We need to get a dict reader, if the CSV file has headers, we dont need to supply them
            if has_headers:
                csv_dict_reader = csv.DictReader(open_csv_file)
            # If the CSV doesn't have headers, we must supply headers or the first row will be consumed as header names.
            else:
                csv_dict_reader = csv.DictReader(open_csv_file, fieldnames=headers)

            # Validate that our header values exist and are valid.
            CSVRelationshipImporter._validate_header_values(csv_dict_reader,
                                                            source_item_column,
                                                            target_item_column,
                                                            relationship_type_column)

            # Begin processing the data in the CSV file.
            for row_number, row_data in enumerate(csv_dict_reader):
                # For each row in the CSV file we will append an object to a list for later processing.
                # First get source and target data.  These are mandatory, a missing data point here is an error.
                csv_lines_read += 1
                current_row_rel_data = {
                    'row_number': row_number,
                    'source_data': row_data[source_item_column],
                    'target_data': row_data[target_item_column],
                }

                # Now get the relationship data string if it exists.
                if relationship_type_column is not None:
                    relationship_info = row_data.get(relationship_type_column)
                    current_row_rel_data['rel_type_data'] = relationship_info

                # Append the data from this row to a list for processing.
                self.raw_relationship_data.append(current_row_rel_data)

                # Create a log entry about the row we just read.
                CSVRelationshipImporter.logger.debug('Read row {}, data: {} '.format(row_number, current_row_rel_data))

            # Log number of lines read
            CSVRelationshipImporter.logger.info('Read {} lines from file'.format(csv_lines_read))
            self._csv_line_count = csv_lines_read

    def process_relationships(self,
                              using_custom_field: bool,
                              source_projects: list,
                              target_projects: list,
                              source_lookup_field_name: str,
                              target_lookup_field_name: str,
                              default_relationship_type_id: int):
        """
        This function will process the relationships after they have been loaded,  It will prepare each relationship for
        posting to Jama Connect.

        :return: None
        """
        # Create a log entry that we are going to prepare the relationship data for posting.
        CSVRelationshipImporter.logger.info('Preparing relationship data for posting.')

        # If source and target project lists are equal, we can use one lookup table to reduce the amount of network work
        if set(source_projects) == set(target_projects):
            self.target_item_map = self.source_item_map

        # Clear our prepped data list.
        self.prepped_relationship_data.clear()

        # Begin processing relationsihps
        for relationship in self.raw_relationship_data:
            prepared_relationship = {}
            # here we may need to do a lookup to get the Item ID if we are using custom field information.
            if using_custom_field:
                # we must do a lookup to find the item ID of the matching item.
                try:
                    # Lookup source item id
                    source_item_id = self._get_item_id_by_custom_field(relationship.get('source_data'),
                                                                       source_lookup_field_name,
                                                                       self.source_item_map,
                                                                       source_projects)
                    # Lookup target item id
                    target_item_id = self._get_item_id_by_custom_field(relationship.get('target_data'),
                                                                       target_lookup_field_name,
                                                                       self.target_item_map,
                                                                       target_projects)
                    if source_item_id is None or target_item_id is None:
                        CSVRelationshipImporter.logger.warning('Unable to find items for: {}'.format(relationship))
                        continue
                    # Lookup Relationship item id
                    try:
                        relationship_type_id = self.relationship_map.get(relationship.get('rel_type_data'))
                        if relationship_type_id is None:
                            relationship_type_id = default_relationship_type_id
                    except KeyError:
                        relationship_type_id = default_relationship_type_id

                except ValueError as ve:
                    CSVRelationshipImporter.logger.error("SKIPPING ROW: {}".format(relationship))
                    CSVRelationshipImporter.logger.error(ve)
                    continue

                # Build up the prepared relationship object for posting.
                prepared_relationship['fromItem'] = source_item_id
                prepared_relationship['toItem'] = target_item_id
                prepared_relationship['relationshipType'] = relationship_type_id

            else:
                # Assume the field already contains the item ID's this is faster to process and minimizes network time
                prepared_relationship['fromItem'] = relationship['source_data']
                prepared_relationship['toItem'] = relationship['target_data']
                try:
                    prepared_relationship['relationshipType'] = relationship['rel_type_data']
                except KeyError:
                    prepared_relationship['relationshipType'] = default_relationship_type_id
            # Append the prepared relationship to the list to be posted.
            self.prepped_relationship_data.append(prepared_relationship)

    def post_relationships(self, ):
        """
        This Method will post each relationship and log the results.
        :param default_relationship_type: The API ID of the default relationship type to use.
        :return: None
        """
        # Log beggining of posting phase:
        CSVRelationshipImporter.logger.info("Beginning to post relationships")
        # Keep track of successful and failed posts
        posted_relationship_count = 0
        failed_posts_count = 0
        # Post each prepared relationship
        for relationship in self.prepped_relationship_data:
            try:
                created_rel_id = self.j_client.post_relationship(relationship['fromItem'],
                                                                 relationship['toItem'],
                                                                 relationship['relationshipType'])
                CSVRelationshipImporter.logger.info('Posted NEW relationship {}'.format(created_rel_id))
                posted_relationship_count += 1

            # Handle any errors
            except APIException as e:
                CSVRelationshipImporter.logger.error('Error while posting relationship. {} : {}'.format(relationship,
                                                                                                        e))
                failed_posts_count += 1

        # Log a summary
        CSVRelationshipImporter.logger.info('{} relationship were read from CSV.  {} relationships posted successful.'
                                            ' {} Failed during post.'.format(self._csv_line_count,
                                                                             posted_relationship_count,
                                                                             failed_posts_count))

    @staticmethod
    def _validate_header_values(csv_dict_reader,
                                source_item_coloumn,
                                target_item_coloumn,
                                relationship_type_coloumn):
        """
        This helper method checks to ensure that the fields passed are in the CSV file fieldnames list.
        :param csv_dict_reader: A instanciated CSV dictreader object
        :param source_item_coloumn: A string that contains the Source Column header name
        :param target_item_coloumn: A string that contains the Target Column header name
        :param relationship_type_coloumn: A string that contains the Relationship type info Column header name
        :return:
        """

        # We need to ensure the expected columns are present.
        source_data_present = source_item_coloumn is not None and source_item_coloumn in csv_dict_reader.fieldnames
        target_data_present = target_item_coloumn is not None and target_item_coloumn in csv_dict_reader.fieldnames
        if not source_data_present or not target_data_present:
            missing_header_error_message = 'Please ensure CSV file settings are configured correctly with header ' \
                                           'names.  These are the supplied header values.  source_item_column: {}' \
                                           '   target_item_column: {}'.format(source_item_coloumn,
                                                                              target_item_coloumn)
            CSVRelationshipImporter.logger.critical(missing_header_error_message)
            raise ValueError(missing_header_error_message)

            # Now determine if we are using relationship type fields and verify the field exists.
        if relationship_type_coloumn is not None:
            relationship_data_present = relationship_type_coloumn in csv_dict_reader.fieldnames
            if not relationship_data_present:
                missing_relationship_header_message = 'You have specified a relationship type header but no ' \
                                                      'matching column was found. The ' \
                                                      'specified relationship_type_column (' \
                                                      '{}) will be set to the ' \
                                                      'default value.'.format(relationship_type_coloumn)
                CSVRelationshipImporter.logger.warning(missing_relationship_header_message)

    @staticmethod
    def _get_item_id_by_custom_field(field_value, field_name, lookup_table, project_list):
        """
        This method will take in a string from a custom field, and return the ID of the matching jama item.
        :return: the ID of the matching jama item.
        """
        # If we already know the ID then use it
        if field_value in lookup_table:
            return lookup_table[field_value]
        # Otherwise we must look it up.
        else:
            # Build the lucene query
            lucene_query = '"{}: "{}""'.format(field_name, field_value)

            # Make call to Jama API
            try:
                items = client.get_abstract_items(contains=lucene_query, project=project_list)
            # Deal with any API Bananas
            except APIException as e:
                CSVRelationshipImporter.logger.error("Error trying to lookup item with custom field <{}> containing "
                                                     "<{}> API Error message: {}".format(field_name, field_value, e))
                raise e

            # Validate we have one and only one result.
            if items is None or len(items) == 0:
                return None
            if len(items) > 1:
                CSVRelationshipImporter.logger.error("Found multiple items matching the "
                                                     "lookup value: <{}>.".format(field_value))
                raise ValueError("Too many matching items for {}".format(field_value))

            # Get the result, store it, return it.
            item_id = items[0].get('id')
            lookup_table[field_value] = item_id
            return item_id

    def _build_relationship_map(self):
        """
        Pull relationship Data from the API and build a dictionary to lookup relationship ID's by name.
        :return: None
        """
        # Get the relationship types from the PAI
        try:
            relationship_types = self.j_client.get_relationship_types()
        except APIException as e:
            CSVRelationshipImporter.logger.error("Error while fetching relationship type information. "
                                                 "Message from API: {}".format(e))
            raise e

        # Add each type to the lookup table
        for relationship_type in relationship_types:
            self.relationship_map[relationship_type.get('name')] = relationship_type.get('id')


def do_import(filename):
    """
    Run one iteration of the CSVRealationshipImporter
    :param filename:  the file to import
    :return: None
    """
    # Instantiate a new relationship importer
    rel_creator = CSVRelationshipImporter(client)

    # Load CSV from file into memory
    rel_creator.load_csv_data(filename,
                              config.csv_has_headers,
                              config.csv_headers,
                              config.csv_source_column,
                              config.csv_target_column,
                              config.csv_relationship_type_column)

    # Process the relationship data
    rel_creator.process_relationships(config.match_on_custom_field,
                                      config.source_project_list,
                                      config.target_project_list,
                                      config.source_item_custom_field_name,
                                      config.target_item_custom_field_name,
                                      config.default_relationship_type)

    # Post the relationships
    rel_creator.post_relationships()


if __name__ == '__main__':
    # INIT LOGGING
    try:
        os.mkdir('logs')
    except FileExistsError:
        pass
    current_date_time = datetime.datetime.now().strftime(config.log_date_time_format)
    log_file = '{}/{}_{}.log'.format(config.log_directory, config.log_file_name_prefix, str(current_date_time))
    logging.basicConfig(filename=log_file, level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    # Keep track of execution time.
    start_time = time.perf_counter()

    # Get a Jama Client.
    client = utils.init_jama_client()

    # Keep track of the number of files processed.
    file_count = 0

    csv_location = config.csv_location

    if os.path.isdir(csv_location):
        # Process all the CSV files in this directory.
        for file in filter(lambda x: x.lower().endswith('.csv'), os.listdir(csv_location)):
            # Increment number of .csv files found.
            file_count += 1
            # Run the CSV importer
            do_import(file)
    else:
        # We are just processing a single file.
        file_count += 1
        do_import(csv_location)

    # Measure execution time and print a log about it
    elapsed_time = '%.2f' % ((time.perf_counter() - start_time) / 60)
    logging.info('Process Complete: Imported: {} csv files.  total execution time: {} minutes'.format(file_count,
                                                                                                      elapsed_time))
