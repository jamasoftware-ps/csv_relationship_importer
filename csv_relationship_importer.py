import configparser
import getpass
import os
import sys
import time
import csv

from py_jama_rest_client.client import JamaClient, APIException


def init_jama_client():
    # do we have credentials in the config?
    credentials_dict = {}
    if 'CREDENTIALS' in config:
        credentials_dict = config['CREDENTIALS']
    try:
        instance_url = get_instance_url(credentials_dict)
        oauth = get_oauth(credentials_dict)
        username = get_username(credentials_dict)
        password = get_password(credentials_dict)
        jama_client = JamaClient(instance_url, credentials=(username, password), oauth=oauth)
        jama_client.get_available_endpoints()
        return jama_client
    except APIException:
        # we cant do things without the API so lets kick out of the execution.
        print('Error: invalid Jama credentials, check they are valid in the config.ini file.')
    except Exception as e:
        print('Failed to authenticate to <' + get_instance_url(credentials_dict) + '>')

    response = input('\nWould you like to manually enter server credentials?\n')
    response = response.lower()
    if response == 'y' or response == 'yes' or response == 'true':
        config['CREDENTIALS'] = {}
        return init_jama_client()
    else:
        sys.exit()


def get_instance_url(credentials_object):
    if 'instance url' in credentials_object:
        instance_url = str(credentials_object['instance url'])
        instance_url = instance_url.lower()
        # ends with a slash? lets remove this
        if instance_url.endswith('/'):
            instance_url = instance_url[:-1]
        # user forget to put the "https://" bit?
        if not instance_url.startswith('https://') or instance_url.startswith('http://'):
            # if forgotten then ASSuME that this is an https server.
            instance_url = 'https://' + instance_url
        # also allow for shorthand cloud instances
        if '.' not in instance_url:
            instance_url = instance_url + '.jamacloud.com'
        return instance_url
    # otherwise the user did not specify this in the config. prompt the user for it now
    else:
        instance_url = input('Enter the Jama Instance URL:\n')
        credentials_object['instance url'] = instance_url
        return get_instance_url(credentials_object)


def get_username(credentials_object):
    if 'username' in credentials_object:
        username = str(credentials_object['username'])
        return username.strip()
    else:
        username = input('Enter the username (basic auth) or client ID (oAuth):\n')
        credentials_object['username'] = username
        return get_username(credentials_object)


def get_password(credentials_object):
    if 'password' in credentials_object:
        password = str(credentials_object['password'])
        return password.strip()
    else:
        password = getpass.getpass(prompt='Enter your password (basic auth) or client secret (oAuth):\n')
        credentials_object['password'] = password
        return get_password(credentials_object)


def get_oauth(credentials_object):
    if 'using oauth' in credentials_object:
        # this is user input here so lets be extra careful
        user_input = credentials_object['using oauth'].lower()
        user_input = user_input.strip()
        return user_input == 'true' or user_input == 'yes' or user_input == 'y'
    else:
        oauth = input('Using oAuth to authenticate?\n')
        credentials_object['using oauth'] = oauth
        return get_oauth(credentials_object)

def get_custom_field():
    custom_field = config['PARAMETERS']['custom field']
    return custom_field


def get_using_doc_key():
    doc_key = config['PARAMETERS']['using doc key'].lower()
    if doc_key == 'false' or doc_key == 'no':
        return False
    else:
        return True

def get_using_custom_field():
    doc_key = config['PARAMETERS']['using custom field'].lower()
    if doc_key == 'false' or doc_key == 'no':
        return False
    else:
        return True

def get_import_directory():
    import_dir = config['PARAMETERS']['import directory']
    if import_dir is None or import_dir is '':
        print('No import directory provided. please specify one in the config.ini')
        sys.exit()
    if not os.path.isdir(import_dir):
        print('Invalid import directory [' + str(import_dir) + ']. Please confirm the import directory provided in the '
              'config.ini file.')
        sys.exit()

    contains_csv_file = False
    for filename in os.listdir(import_dir):
        if filename.lower().endswith('.csv'):
            contains_csv_file = True
            break

    if not contains_csv_file:
        print('Import directory provided does not contain any CSV files. please confirm the import directory in the '
              'config.ini file.')
        sys.exit()

    return import_dir


def get_jama_id_from_doc_key(doc_key, map):
    if doc_key not in map:
        items = client.get_abstract_items(None, None, doc_key, None, None, None, None, None, None)
        item_id = items[0].get('id')
        map[doc_key] = item_id
    return map[doc_key]


def get_jama_id_from_custom_field(field_value, field_name, map):
    if field_value not in map:
        lucene_query = field_name + ':\"' + field_value + '\"'
        items = client.get_abstract_items(None, None, None, None, None, None, None, lucene_query, None)
        if items is None or len(items) == 0:
            return None
        item_id = items[0].get('id')
        map[field_value] = item_id
    return map[field_value]


if __name__ == '__main__':
    start_time = time.time()
    config = configparser.ConfigParser()
    config.read('config.ini')
    client = init_jama_client()

    # do work
    relationships = []
    key_to_item_id = {}

    relationship_type = 4
    total_line_count = 0
    file_count = 0
    using_doc_key = get_using_doc_key()
    using_custom_field = get_using_custom_field()

    import_directory = get_import_directory()

    for filename in os.listdir(import_directory):

        # we only want to process csv files here, so skip non csv files.
        if not filename.lower().endswith('.csv'):
            continue

        file_count += 1
        with open(import_directory + filename, encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            file_count += 1
            for row in csv_reader:
                line_count += 1
                if using_doc_key:
                    from_item = get_jama_id_from_doc_key(row[0], key_to_item_id)
                    to_item = get_jama_id_from_doc_key(row[1], key_to_item_id)
                elif using_custom_field:
                    custom_field = get_custom_field()
                    from_item = get_jama_id_from_custom_field(row[0], custom_field, key_to_item_id)
                    to_item = get_jama_id_from_custom_field(row[1], custom_field, key_to_item_id)
                else:
                    from_item = row[0]
                    to_item = row[1]

                relationship = {
                    'fromItem': from_item,
                    'toItem': to_item,
                    'relationshipType': relationship_type
                }
                relationships.append(relationship)

            print('Processed ' + str(line_count) + ' lines in CSV File ' + filename)
            total_line_count += line_count

    print('Processed ' + str(total_line_count) + ' across ' + str(file_count) + ' files.')

    for relationship in relationships:
        from_item = relationship.get('fromItem')
        to_item = relationship.get('toItem')
        relationship_type = relationship.get('relationshipType')

        # is this a relationship to self?
        if from_item == to_item:
            continue
        try:
            client.post_relationship(from_item, to_item, relationship_type)
        except APIException as error:
            if error == 'Entity already Exists.':
                continue
            print(error)

    elapsed_time = '%.2f' % (time.time() - start_time)
    print('total execution time: ' + elapsed_time + ' seconds')