"""
This file contains a collection of Utilities that are of frequent use in scripts that connect to the Jama API.
"""

import getpass
import sys
import config
import logging
from py_jama_rest_client.client import JamaClient, APIException

util_logger = logging.getLogger('util_logger')


def prompt_credentials():
    get_instance_url()
    get_oauth()
    if config.oauth:
        get_client_id()
        get_client_secret()
    else:
        get_username()
        get_password()


def get_instance_url():
    # Prompt the user for the Base URL
    instance_url = input('Enter the Jama Instance URL: ')
    config.base_url = validate_base_url(instance_url)


def get_username():
    """
    Prompt the user for their username
    :return:
    """
    config.username = input('Enter your Username: ')


def get_password():
    """
    prompt the user for their password
    :return:
    """
    config.password = getpass.getpass(prompt='Enter your password: ')


def get_client_id():
    """
    Prompt the user for their Client ID
    :return:
    """
    config.client_id = input('Please enter your Client ID: ')


def get_client_secret():
    """
    Prompt the user for their Client Secret
    :return:
    """
    config.client_secret = getpass.getpass(prompt='Please enter your Client Secret: ')


def get_oauth():
    """
    Prompt the user to find out if they are using OAuth.
    :return:
    """
    oauth = input('Using oAuth to authenticate?[y/n]: ')
    oauth = oauth.lower()
    # check response
    if oauth == 'y':
        config.oauth = True
    else:
        config.oauth = False


def validate_base_url(base_url):
    """
    Validate the URL entered by the user
    :param base_url: the raw url entered by the user
    :return: the checked and cleaned URL
    """
    instance_url = base_url
    instance_url = instance_url.lower()

    # ends with a slash? lets remove this
    if instance_url.endswith('/'):
        instance_url = instance_url[:-1]

    # user forget to put the "https://" bit?
    if not instance_url.startswith('https://') or instance_url.startswith('http://'):
        # if forgotten then ASSuME that this is an https server.
        instance_url = 'https://' + instance_url

    # also allow for shorthand cloud instances, this could cause unintended consequences....
    if '.' not in instance_url:
        instance_url = instance_url + '.jamacloud.com'
    return instance_url


def init_jama_client():
    while True:
        # See if this set of credentials works.
        try:
            instance_url = validate_base_url(config.base_url)
            oauth = config.oauth
            if not oauth:
                username = config.username
                password = config.password
            else:
                username = config.client_id
                password = config.client_secret

            # Try to make the client
            jama_client = JamaClient(instance_url, credentials=(username, password), oauth=oauth)
            jama_client.get_available_endpoints()
            return jama_client
        # Catch any exception from the API
        except APIException as e:
            # we cant do things without the API so lets kick out of the execution.
            util_logger.warning('Error: invalid Jama credentials, check they are valid in the config.py file.')

        # Catch unexpected things here
        except Exception as e:
            util_logger.warning('Failed to authenticate to <' + config.base_url + '> Error: ' + str(e))

        response = input('\nWould you like to manually enter server credentials?[y/n]: ')
        response = response.lower()
        if response == 'y' or response == 'yes' or response == 'true':
            prompt_credentials()
        else:
            sys.exit()
