# from textwrap import dedent
# from unittest.mock import patch
#
# import pytest
#
# from utils.helm import *
#
# version = '0.0.1'
#
#
# class TestHelm:
#
#     @pytest.fixture
#     def mock_helm_result_blue(self):
#         return dedent("""\
#                 ---
#                 kind: Deployment
#                 ---
#                 kind: DestinationRule
#                 spec:
#                   subsets:
#                     - name: test-destination-rule-0.0.1
#                       labels:
#                         version: 0.0.1
#                 ---""").encode('utf-8')
#
#     @pytest.fixture
#     def mock_helm_result_green(self):
#         return dedent("""\
#                 ---
#                 kind: Deployment
#                 ---
#                 kind: DestinationRule
#                 spec:
#                   subsets:
#                     - name: test-destination-rule-0.0.1-green
#                       labels:
#                         version: 0.0.1
#                 ---""").encode('utf-8')
#
#     @pytest.fixture
#     def mock_helm_result_blue_green(self):
#         return dedent("""\
#                 ---
#                 kind: Deployment
#                 ---
#                 kind: DestinationRule
#                 spec:
#                   subsets:
#                     - name: test-destination-rule-0.0.1-green
#                       labels:
#                         version: 0.0.1
#                     - name: test-destination-rule-0.0.1
#                       labels:
#                         version: 0.0.1
#                 ---""").encode('utf-8')
#
#     class TestIsVersionGreen:
#         def test_is_version_green_should_return_false_when_running_locally(self):
#             os.environ['ENVIRONMENT'] = 'local'
#             actual_result = is_version_green(version)
#             assert not actual_result
#
#         def test_is_version_green_should_return_false_when_dd_env_is_local(self):
#             os.environ.pop('ENVIRONMENT', None)
#             os.environ['DD_ENV'] = 'local'
#             actual_result = is_version_green(version)
#             assert not actual_result
#
#         def test_is_version_green_should_return_false_when_dd_env_is_not_set(self):
#             os.environ.pop('ENVIRONMENT', None)
#             os.environ.pop('DD_ENV', None)
#             actual_result = is_version_green(version)
#             assert not actual_result
#
#         @patch('subprocess.check_output')
#         def test_is_version_green_should_return_true_when_green(self, mock_check_output, mock_helm_result_green):
#             os.environ['ENVIRONMENT'] = 'test'
#             os.environ['DD_ENV'] = 'test'
#             mock_check_output.return_value = mock_helm_result_green
#             actual_result = is_version_green(version)
#             assert actual_result
#             mock_check_output.assert_called_once()
#
#         @patch('subprocess.check_output')
#         def test_is_version_green_should_return_false_when_blue(self, mock_check_output, mock_helm_result_blue):
#             os.environ['ENVIRONMENT'] = 'test'
#             os.environ['DD_ENV'] = 'test'
#             mock_check_output.return_value = mock_helm_result_blue
#             actual_result = is_version_green(version)
#             assert not actual_result
#             mock_check_output.assert_called_once()
#
#         @patch('subprocess.check_output')
#         def test_is_version_green_should_return_true_when_blue_green(self, mock_check_output,
#                                                                      mock_helm_result_blue_green):
#             os.environ['ENVIRONMENT'] = 'test'
#             os.environ['DD_ENV'] = 'test'
#             mock_check_output.return_value = mock_helm_result_blue_green
#             actual_result = is_version_green(version)
#             assert actual_result
#             mock_check_output.assert_called_once()
#
#         @patch('subprocess.check_output')
#         def test_is_version_green_should_return_false_when_exception(self, mock_check_output):
#             os.environ['ENVIRONMENT'] = 'test'
#             os.environ['DD_ENV'] = 'test'
#             mock_check_output.side_effect = Exception()
#             actual_result = is_version_green(version)
#             assert not actual_result
#             assert len(mock_check_output.mock_calls) == 10
#
#     class TestGetApplicationVersionBlueGreenState:
#
#         @patch('subprocess.check_output')
#         def test_get_application_version_blue_green_state_blue(self, mock_check_output, mock_helm_result_green):
#             mock_check_output.return_value = mock_helm_result_green
#             expected_dict = {version: True}
#             actual_dict = get_application_version_blue_green_state()
#             assert expected_dict == actual_dict
#             mock_check_output.assert_called_once()
#
#         @patch('subprocess.check_output')
#         def test_get_application_version_blue_green_state_green(self, mock_check_output, mock_helm_result_blue):
#             mock_check_output.return_value = mock_helm_result_blue
#             expected_dict = {version: False}
#             actual_dict = get_application_version_blue_green_state()
#             assert expected_dict == actual_dict
#             mock_check_output.assert_called_once()
#
#         @patch('subprocess.check_output')
#         def test_get_application_version_blue_green_state_blue_green(self, mock_check_output,
#                                                                      mock_helm_result_blue_green):
#             mock_check_output.return_value = mock_helm_result_blue_green
#             expected_dict = {version: True}
#             actual_dict = get_application_version_blue_green_state()
#             assert expected_dict == actual_dict
#             mock_check_output.assert_called_once()
