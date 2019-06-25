import mock
import pytest
import re
from user_sync.rules import RuleProcessor


@pytest.fixture
def rule_processor(caller_options):
    return RuleProcessor(caller_options)


@pytest.fixture
def caller_options():
    return {'adobe_group_filter': None, 'after_mapping_hook': None, 'default_country_code': 'US',
            'delete_strays': False, 'directory_group_filter': None, 'disentitle_strays': False, 'exclude_groups': [],
            'exclude_identity_types': ['adobeID'], 'exclude_strays': False, 'exclude_users': [],
            'extended_attributes': None, 'process_groups': True, 'max_adobe_only_users': 200,
            'new_account_type': 'federatedID', 'remove_strays': True, 'strategy': 'sync',
            'stray_list_input_path': None, 'stray_list_output_path': None,
            'test_mode': True, 'update_user_info': False, 'username_filter_regex': None,
            'adobe_only_user_action': ['remove'], 'adobe_only_user_list': None,
            'adobe_users': ['all'], 'config_filename': 'tests/fixture/user-sync-config.yml',
            'connector': 'ldap', 'encoding_name': 'utf8', 'user_filter': None,
            'users': None, 'directory_connector_type': 'csv',
            'directory_connector_overridden_options': {'file_path': ''},
            'adobe_group_mapped': False, 'additional_groups': []}


@mock.patch('user_sync.helper.CSVAdapter.read_csv_rows')
def test_stray_key_map(csv_reader, rule_processor):
    csv_mock_data = [{'type': 'adobeID', 'username': 'removeuser2@example.com', 'domain': 'example.com'},
                     {'type': 'federatedID', 'username': 'removeuser@example.com', 'domain': 'example.com'},
                     {'type': 'enterpriseID', 'username': 'removeuser3@example.com', 'domain': 'example.com'}]
    csv_reader.return_value = csv_mock_data
    rule_processor.read_stray_key_map('')
    actual_value = rule_processor.stray_key_map
    expected_value = {None: {'federatedID,removeuser@example.com,': None,
                             'enterpriseID,removeuser3@example.com,': None,
                             'adobeID,removeuser2@example.com,': None}}

    assert expected_value == actual_value

    # Added secondary umapi value
    csv_mock_data = [{'type': 'adobeID', 'username': 'remo@sample.com', 'domain': 'sample.com', 'umapi': 'secondary'},
                     {'type': 'federatedID', 'username': 'removeuser@example.com'},
                     {'type': 'enterpriseID', 'username': 'removeuser3@example.com', 'domain': 'example.com'}]
    csv_reader.return_value = csv_mock_data
    rule_processor.read_stray_key_map('')
    actual_value = rule_processor.stray_key_map
    expected_value = {'secondary': {'adobeID,remo@sample.com,': None},
                      None: {'federatedID,removeuser@example.com,': None,
                             'enterpriseID,removeuser3@example.com,': None,
                             'adobeID,removeuser2@example.com,': None}}
    assert expected_value == actual_value


def test_log_after_mapping_hook_scope(log_stream):
    stream, logger = log_stream

    state = {
        'source_attributes': {
            'email': 'bsisko@example.com',
            'identity_type': None,
            'username': None,
            'domain': None,
            'givenName': 'Benjamin',
            'sn': 'Sisko',
            'c': 'CA'},
        'source_groups': set(),
        'target_attributes': {
            'email': 'bsisko@example.com',
            'username': 'bsisko@example.com',
            'domain': 'example.com',
            'firstname': 'Benjamin',
            'lastname': 'Sisko',
            'country': 'CA'},
        'target_groups': set(),
        'log_stream': logger,
        'hook_storage': None}

    ruleprocessor = RuleProcessor({})
    ruleprocessor.logger = logger
    ruleprocessor.after_mapping_hook_scope = state
    ruleprocessor.log_after_mapping_hook_scope(before_call=True)

    expected = """.
Source attrs, before: {'email': 'bsisko@example.com', 'identity_type': None, 'username': None, 'domain': None, 'givenName': 'Benjamin', 'sn': 'Sisko', 'c': 'CA'}
Source groups, before: set()
Target attrs, before: {'email': 'bsisko@example.com', 'username': 'bsisko@example.com', 'domain': 'example.com', 'firstname': 'Benjamin', 'lastname': 'Sisko', 'country': 'CA'}
Target groups, before: set()
"""

    expected = []
    expected.append(["'email': 'bsisko@example.com'", "'identity_type': None", "'username': None", "'domain': None", "'givenName': 'Benjamin'", "'sn': 'Sisko'", "'c': 'CA'"])
    expected.append("Source groups, before: set()")
    expected.append(["'email': 'bsisko@example.com'", "'username': 'bsisko@example.com'", "'domain': 'example.com'", "'firstname': 'Benjamin'", "'lastname': 'Sisko'", "'country': 'CA'"])
    expected.append("Target groups, before: set()")

    stream.flush()
    ac = stream.getvalue().split("\n")
    zz = re.split('[{}]',ac[1])[1].split(",")

    exc = expected[0].replace(" ", "")
    acc = ac[1].replace(" ", "")

    result = all(elem in expected[0] for elem in zz)



    assert stream.getvalue() == expected

    state['target_groups'] = {'One'}
    state['target_attributes'] = {'firstname': 'John'}
    state['source_attributes'] = {'sn': 'David'}
    state['source_groups'] = {'One'}

    ruleprocessor.after_mapping_hook_scope = state
    ruleprocessor.log_after_mapping_hook_scope(after_call=True)

    expected=""".
Source attrs, before: {'email': 'bsisko@example.com', 'identity_type': None, 'username': None, 'domain': None, 'givenName': 'Benjamin', 'sn': 'Sisko', 'c': 'CA'}
Source groups, before: set()
Target attrs, before: {'email': 'bsisko@example.com', 'username': 'bsisko@example.com', 'domain': 'example.com', 'firstname': 'Benjamin', 'lastname': 'Sisko', 'country': 'CA'}
Target groups, before: set()
Target attrs, after: {'firstname': 'John'}
Target groups, after: {'One'}
Hook storage, after: None
"""

    stream.flush()
    assert stream.getvalue() == expected
