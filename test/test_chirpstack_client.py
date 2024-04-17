import unittest
from pytest import mark
from unittest.mock import Mock, patch, MagicMock
from chirpstack_api_wrapper.client import * 
from chirpstack_api_wrapper.objects import * 
import grpc
from grpc import _channel as channel
from chirpstack_api import api
import sys

CHIRPSTACK_API_INTERFACE = "wes-chirpstack-server:8080"
CHIRPSTACK_ACT_EMAIL = "test"
CHIRPSTACK_ACT_PASSWORD = "test"

#TODO: Use sample data instead of mocking, maybe use factories lib (look at line of code with `Example` tag)

class TestLogin(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    def test_login_success(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test a successful pass through of login
        """

        # Mocking grpc login response
        mock_login_response = MagicMock(jwt='mock_jwt_token')
        mock_internal_service_stub.return_value.Login.return_value = mock_login_response

        # Creating ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Assert that the login method was called with the correct parameters
        mock_internal_service_stub.return_value.Login.assert_called_once_with(
            api.LoginRequest(email=CHIRPSTACK_ACT_EMAIL, password=CHIRPSTACK_ACT_PASSWORD)
        )

        # Assert that the auth_token is set correctly
        self.assertEqual(client.auth_token, 'mock_jwt_token')

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    def test_login_success_using_argparse(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test a successful pass through of login using argparse
        """
        #Mock argparse
        args = MagicMock()
        args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

        # Mocking grpc login response
        mock_login_response = MagicMock(jwt='mock_jwt_token')
        mock_internal_service_stub.return_value.Login.return_value = mock_login_response

        # Creating ChirpstackClient instance
        client = ChirpstackClient(args.chirpstack_account_email, args.chirpstack_account_password, args.chirpstack_api_interface)

        # Assert that the login method was called with the correct parameters
        mock_internal_service_stub.return_value.Login.assert_called_once_with(
            api.LoginRequest(email=args.chirpstack_account_email, password=args.chirpstack_account_password)
        )

        # Assert that the auth_token is set correctly
        self.assertEqual(client.auth_token, 'mock_jwt_token')

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    def test_login_failure_RpcError_grpcStatusCodeUNAVAILABLE(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test the login method with a RpcError exception with a grpc.StatusCode.UNAVAILABLE
        """
        # Mocking grpc login response
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAVAILABLE
        mock_rpc_error.details = lambda: 'unavailable'
        mock_internal_service_stub.return_value.Login.side_effect = mock_rpc_error

        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Creating ChirpstackClient instance
            with self.assertRaises(SystemExit) as cm:
                ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertIn("Service is unavailable. This might be a DNS resolution issue.", log.output[0])

        # Assert that the system exit code is 1 (indicating failure)
        self.assertEqual(cm.exception.code, 1)

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    def test_login_failure_RpcError_grpcStatusCodeOther(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test the login method with a RpcError exception with a grpc.StatusCode.UNAUTHENTICATED
        """
        # Mocking grpc login response
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'Invalid credentials'
        mock_internal_service_stub.return_value.Login.side_effect = mock_rpc_error

        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Creating ChirpstackClient instance
            with self.assertRaises(SystemExit) as cm:
                ChirpstackClient(CHIRPSTACK_ACT_EMAIL, 'wrong_password', CHIRPSTACK_API_INTERFACE)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertIn(f"An error occurred with status code {grpc.StatusCode.UNAUTHENTICATED}", log.output[0])

        # Assert that the system exit code is 1 (indicating failure)
        self.assertEqual(cm.exception.code, 1)

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    def test_login_failure_Exception(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test the login method with a general exception
        """
        # Mocking grpc login response to raise a general Exception
        e = Exception("Test exception")
        mock_internal_service_stub.return_value.Login.side_effect = e

        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Creating ChirpstackClient instance
            with self.assertRaises(SystemExit) as cm:
                ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn(f"An error occurred: {e}", log.output[0])

        # Assert that the system exit code is 1 (indicating failure)
        self.assertEqual(cm.exception.code, 1)

class TestListAllDevices(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_list_all_devices_happy_path(self, mock_insecure_channel, mock_internal_service_stub):
        """
        Test list_all_devices() method's happy path by mocking list_all_apps() reponse and List_agg_pagination()
        """

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock(return_value=["device1", "device2"]) #Example

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        with patch.object(client, 'List_agg_pagination', mock_list_agg_pagination):

            # Mock the app_resp for list_all_apps
            mock_app_resp = [Mock(id="app1"), Mock(id="app2")] #Example

            # Call list_all_devices
            devices = client.list_all_devices(mock_app_resp)

            # Assert the result
            self.assertEqual(devices, ['device1', 'device2', 'device1', 'device2'])

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_list_all_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel):
        """
        Test list_all_devices() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock()
        mock_list_agg_pagination.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        with patch.object(client, 'List_agg_pagination', mock_list_agg_pagination):

            # Mock the app_resp for list_all_apps
            mock_app_resp = [Mock(id="app1"), Mock(id="app2")] #Example

            # Mock the login method to return a dummy token
            with patch.object(client, "login", return_value="dummy_token"):

                #mock refresh token successfully logging in and retrying the method
                with patch.object(client, "refresh_token", return_value=['device1', 'device2', 'device1', 'device2']):
                    # Call the method in testing
                    result = client.list_all_devices(mock_app_resp)


        # Assert the result
        self.assertEqual(result, ['device1', 'device2', 'device1', 'device2'])

class TestListAllApps(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_list_all_apps_happy_path(self, mock_insecure_channel, mock_internal_service_stub):
        """
        Test list_all_apps() method's happy path by mocking list_tenants() reponse and List_agg_pagination()
        """

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock(return_value=["app1", "app2"]) 

        with patch.object(ChirpstackClient, 'List_agg_pagination', mock_list_agg_pagination):
            # Create a ChirpstackClient instance
            client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

            # Mock the tenant_resp for list_all_devices
            mock_tenant_resp = [Mock(id="tenant1"), Mock(id="tenant2")]

            # Call list_all_devices
            apps = client.list_all_apps(mock_tenant_resp)

            # Assert the result
            self.assertEqual(apps, ['app1', 'app2', 'app1', 'app2'])

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_list_all_apps_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel):
        """
        Test list_all_apps() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock()
        mock_list_agg_pagination.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        with patch.object(client, 'List_agg_pagination', mock_list_agg_pagination):

            # Mock the tenant_resp for list_all_devices
            mock_tenant_resp = [Mock(id="tenant1"), Mock(id="tenant2")]

            # Mock the login method to return a dummy token
            with patch.object(client, "login", return_value="dummy_token"):

                #mock refresh token successfully logging in and retrying the method
                with patch.object(client, "refresh_token", return_value=['app1', 'app2', 'app1', 'app2']):
                    # Call the method in testing
                    result = client.list_all_apps(mock_tenant_resp)

        # Assert the result
        self.assertEqual(result, ['app1', 'app2', 'app1', 'app2'])

class TestListTenants(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.InternalServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_list_all_tenants_happy_path(self, mock_insecure_channel, mock_internal_service_stub):
        """
        Test list_tenants() method's happy path by mocking List_agg_pagination()
        """

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock(return_value=["Tenant1", "Tenant1"]) 

        with patch.object(ChirpstackClient, 'List_agg_pagination', mock_list_agg_pagination):
            # Create a ChirpstackClient instance
            client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

            # Call list_tenants()
            tenants = client.list_tenants()

            # Assert the result
            self.assertEqual(tenants, ["Tenant1", "Tenant1"])

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_list_all_tenants_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel):
        """
        Test list_tenants() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock()
        mock_list_agg_pagination.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        with patch.object(client, 'List_agg_pagination', mock_list_agg_pagination):

            # Mock the login method to return a dummy token
            with patch.object(client, "login", return_value="dummy_token"):

                #mock refresh token successfully logging in and retrying the method
                with patch.object(client, "refresh_token", return_value=["Tenant1", "Tenant1"]):
                    # Call the method in testing
                    tenants = client.list_tenants()

        # Assert the result
        self.assertEqual(tenants, ["Tenant1", "Tenant1"])

class TestGetDevice(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_happy_path(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device() method's happy path
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = Mock(device_info="mock_device_info")

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call get_device
        device_info = client.get_device(mock_dev_eui)

        # Assert the result
        self.assertEqual(device_info.device_info, "mock_device_info")

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_get_device_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value="mock_device_info"):
                # Call the method in testing
                result = client.get_device(mock_dev_eui)

        # assertations
        self.assertEqual(result, "mock_device_info")

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_not_found_grpc_error(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device() when grpc error is raised for NOT_FOUND
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_rpc_error.details = lambda: 'Object does not exist'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        result = client.get_device(mock_dev_eui)

        self.assertEqual(result, {})

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_other_grpc_error(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device() when grpc error is not NOT_FOUND or UNAUTHENTICATED
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.INTERNAL
        mock_rpc_error.details = lambda: 'other'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        result = client.get_device(mock_dev_eui)

        self.assertEqual(result, {})

class TestGetDeviceProfile(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_profile_happy_path(self, mock_insecure_channel, mock_device_profile_service_stub):
        """
        Test get_device_profile() method's happy path
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceProfileServiceStub
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.return_value = Mock(device_profile_info="mock_device_profile_info")

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        device_profile_info = client.get_device_profile(mock_device_profile_id)

        # Assert the result
        self.assertEqual(device_profile_info.device_profile_info, "mock_device_profile_info")

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_get_device_profile_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_profile_service_stub):
        """
        Test get_device_profile() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceProfileServiceStub
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value="mock_device_profile_info"):
                # Call the method in testing
                device_profile_info = client.get_device_profile(mock_device_profile_id)

        # assertations
        self.assertEqual(device_profile_info, "mock_device_profile_info")

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_profile_not_found_grpc_error(self, mock_insecure_channel, mock_device_profile_service_stub):
        """
        Test get_device_profile() when grpc error is raised for NOT_FOUND
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_rpc_error.details = lambda: 'Object does not exist'

        # Mock the DeviceProfileServiceStub
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        result = client.get_device_profile(mock_device_profile_id)

        self.assertEqual(result, {})

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_other_grpc_error(self, mock_insecure_channel, mock_device_profile_service_stub):
        """
        Test get_device_profile() when grpc error is not NOT_FOUND or UNAUTHENTICATED
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.INTERNAL
        mock_rpc_error.details = lambda: 'other'

        # Mock the DeviceProfileServiceStub
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        result = client.get_device_profile(mock_device_profile_id)

        self.assertEqual(result, {})

class TestGetDeviceAppKey(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_app_key_happy_path_1(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_app_key() method's happy path with lorawan version < 5
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value

        # Create a mock for the device keys response
        mock_device_keys = Mock()
        mock_device_keys.device_keys.nwk_key = "mock_nwk_key"
        mock_device_keys.device_keys.app_key = "mock_app_key"
        
        # Set the return value for the GetKeys method
        mock_device_service_stub_instance.GetKeys.return_value = mock_device_keys

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock get_device_profile response
        deviceprofile_resp = { 
            "device_profile": {
                "id": "cf2aec2f-03e1-4a60-a32c-0faeef5730d8",
                "tenant_id": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "name": "MFR node",
                "mac_version": 4
            }
        }
        lw_v = deviceprofile_resp['device_profile']['mac_version']

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call get_device_app_key
        app_key = client.get_device_app_key(mock_dev_eui, lw_v)

        # Assert the result
        self.assertEqual(app_key, "mock_nwk_key")

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_app_key_happy_path_2(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_app_key() method's happy path with lorawan version = 5
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value

        # Create a mock for the device keys response
        mock_device_keys = Mock()
        mock_device_keys.device_keys.nwk_key = "mock_nwk_key"
        mock_device_keys.device_keys.app_key = "mock_app_key"
        
        # Set the return value for the GetKeys method
        mock_device_service_stub_instance.GetKeys.return_value = mock_device_keys

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock get_device_profile response
        deviceprofile_resp = { 
            "device_profile": {
                "id": "cf2aec2f-03e1-4a60-a32c-0faeef5730d8",
                "tenant_id": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "name": "MFR node",
                "mac_version": 5
            }
        }
        lw_v = deviceprofile_resp['device_profile']['mac_version']

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call get_device_app_key
        app_key = client.get_device_app_key(mock_dev_eui, lw_v)

        # Assert the result
        self.assertEqual(app_key, "mock_app_key")

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_app_key_failure_NOTFOUND(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test the get_device_app_key() method with a RpcError exception with a grpc.StatusCode.NOT_FOUND
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value

        # Mock the GetKeys method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_rpc_error.details = lambda: 'not found'
        mock_device_service_stub_instance.GetKeys.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock get_device_profile response
        deviceprofile_resp = { 
            "device_profile": {
                "id": "cf2aec2f-03e1-4a60-a32c-0faeef5730d8",
                "tenant_id": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "name": "MFR node",
                "mac_version": 4
            }
        }
        lw_v = deviceprofile_resp['device_profile']['mac_version']

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        with self.assertLogs(level='ERROR') as log:
            # Call get_device_app_key
            app_key = client.get_device_app_key(mock_dev_eui, lw_v)
            # Assert logs
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertIn('The device key does not exist. It is possible that the device is using ABP which does not use an application key', log.output[0])
        
        # Assert the result
        self.assertIsNone(app_key)

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_get_device_app_key_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_app_key() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.GetKeys.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock get_device_profile response
        deviceprofile_resp = { 
            "device_profile": {
                "id": "cf2aec2f-03e1-4a60-a32c-0faeef5730d8",
                "tenant_id": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "name": "MFR node",
                "mac_version": 5
            }
        }
        lw_v = deviceprofile_resp['device_profile']['mac_version']

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value="mock_nwk_key"):
                # Call the method in testing
                app_key = client.get_device_app_key(mock_dev_eui, lw_v)

        # assertations
        self.assertEqual(app_key, "mock_nwk_key")

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_app_key_failure_Other(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test the get_device_app_key() method with a RpcError exception that gets catch by else in if statement
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        # Mock the GetKeys method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.ABORTED
        mock_rpc_error.details = lambda: 'Invalid credentials'
        mock_device_service_stub_instance.GetKeys.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock get_device_profile response
        deviceprofile_resp = { 
            "device_profile": {
                "id": "cf2aec2f-03e1-4a60-a32c-0faeef5730d8",
                "tenant_id": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "name": "MFR node",
                "mac_version": 4
            }
        }
        lw_v = deviceprofile_resp['device_profile']['mac_version']

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"
    
        with self.assertLogs(level='ERROR') as log:
            # Call get_device_app_key
            app_key = client.get_device_app_key(mock_dev_eui, lw_v)
            # Assert logs
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertIn(f"An error occurred with status code {grpc.StatusCode.ABORTED}", log.output[0])
       
        # Assert the result
        self.assertIsNone(app_key)


    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_app_key_failure_Exception(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test the get_device_app_key() method with a general exception
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        # Mock the GetKeys method to raise general exception
        e = Exception("Test exception")
        mock_device_service_stub_instance.GetKeys.side_effect = e

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock get_device_profile response
        deviceprofile_resp = { 
            "device_profile": {
                "id": "cf2aec2f-03e1-4a60-a32c-0faeef5730d8",
                "tenant_id": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "name": "MFR node",
                "mac_version": 4
            }
        }
        lw_v = deviceprofile_resp['device_profile']['mac_version']

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        with self.assertLogs(level='ERROR') as log:
            # Call get_device_app_key
            app_key = client.get_device_app_key(mock_dev_eui, lw_v)
            # Assert logs
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn(f"An error occurred: {e}", log.output[0])

        # Assert the result
        self.assertIsNone(app_key)

class TestGetDeviceActivation(unittest.TestCase):
    
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_activation_happy_path(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_activation() method's happy path
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.GetActivation.return_value = Mock(activation_details="mock_activation_details")

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call get_device_app_key
        response = client.get_device_activation(mock_dev_eui)

        # Assert the result
        self.assertEqual(response.activation_details, "mock_activation_details")

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_get_device_activation_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_activation() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.GetActivation.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value="mock_activation_details"):
                # Call the method in testing
                result = client.get_device_activation(mock_dev_eui)

        # assertations
        self.assertEqual(result, "mock_activation_details")

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_activation_not_found_grpc_error(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_activation() when grpc error is raised for NOT_FOUND
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.NOT_FOUND
        mock_rpc_error.details = lambda: 'Object does not exist'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.GetActivation.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        result = client.get_device_activation(mock_dev_eui)

        self.assertEqual(result, {})

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_get_device_activation_other_grpc_error(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test get_device_activation() when grpc error is not NOT_FOUND or UNAUTHENTICATED
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the get_device method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.INTERNAL
        mock_rpc_error.details = lambda: 'other'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.GetActivation.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        result = client.get_device_activation(mock_dev_eui)

        self.assertEqual(result, {})

class TestListAggPagination(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_list_agg_pagination(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test list_agg_pagination() method's happy path
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_list_response = Mock(result=["result_page1", "result_page2"], total_count=2)
        mock_device_service_stub_instance.List.return_value = mock_list_response

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the request and metadata
        mock_req = Mock(offset=0,limit=1)
        mock_metadata = [("authorization", "Bearer mock_jwt")]

        # Call List_agg_pagination
        aggregated_records = ChirpstackClient.List_agg_pagination(mock_device_service_stub_instance, mock_req, mock_metadata)

        # Assert the result
        self.assertEqual(aggregated_records, ["result_page1", "result_page2"])

class TestCreateApp(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.ApplicationServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_app_happy_path(self, mock_insecure_channel, mock_app_service_stub):
        """
        Test create_app() method's happy path
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        #mock response
        mock_resp = MagicMock()
        mock_resp.id = "1234"

        # Mock the ApplicationServiceStub
        mock_app_service_stub_instance = mock_app_service_stub.return_value
        mock_app_service_stub_instance.Create.return_value = mock_resp

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        #Mock tags
        mock_tags = {
            "mock1": "test1",
            "mock2": "test2"
        }

        #mock app
        mock_app = Application(
            name="mock", 
            tenant_id="54f14cd5-d6a1-4fbd-8a81-1022d1d41234",
            description="mock description",
            tags=mock_tags
            )

        # Call create_app
        return_val = client.create_app(mock_app)

        # Assert the result and object
        self.assertEqual(return_val, None)
        self.assertEqual(mock_app.id, "1234")

    @patch('chirpstack_api_wrapper.api.ApplicationServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_app_typeError(self, mock_insecure_channel, mock_app_service_stub):
        """
        Test create_app() method's Application TypeError
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the ApplicationServiceStub
        mock_app_service_stub_instance = mock_app_service_stub.return_value

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock app
        mock_app = "mock" # NOT a Application Instance

        # Call create_gateway and Assert Raise
        with self.assertRaises(TypeError) as context:
            client.create_app(mock_app)

    @patch('chirpstack_api_wrapper.api.ApplicationServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_create_app_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_app_service_stub):
        """
        Test create_app() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the create_app method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the app service stub
        mock_app_service_stub_instance = mock_app_service_stub.return_value
        mock_app_service_stub_instance.Create.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        #mock app
        mock_app = Application(
            name="mock", 
            tenant_id="54f14cd5-d6a1-4fbd-8a81-1022d1d41234",
            description="mock description"
            )

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value=None):
                # Call the method in testing
                return_val = client.create_app(mock_app)

        # assertations
        self.assertEqual(return_val, None)

class TestCreateDeviceProfile(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_dp_happy_path(self, mock_insecure_channel, mock_dp_service_stub):
        """
        Test create_device_profile() method's happy path
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        #mock response
        mock_resp = MagicMock()
        mock_resp.id = "1234"

        # Mock the ApplicationServiceStub
        mock_dp_service_stub_instance = mock_dp_service_stub.return_value
        mock_dp_service_stub_instance.Create.return_value = mock_resp

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        #Mock tags
        mock_tags = {
            "mock1": "test1",
            "mock2": "test2"
        }

        #mock device profile
        mock_dp = DeviceProfile(
            name="mock_dp",
            tenant_id="54f14cd5-d6a1-4fbd-8a81-1022d1d41234", 
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_2,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            description="mock description",
            payload_codec_runtime=CodecRuntime.JS,
            payload_codec_script="mock js script",
            flush_queue_on_activate=False,
            device_status_req_interval=2,
            tags=mock_tags,
            auto_detect_measurements=False,
            allow_roaming=True,
            adr_algorithm_id=AdrAlgorithm.BOTH
            )

        # Call function in testing
        return_val = client.create_device_profile(mock_dp)

        # Assert the result and object
        self.assertEqual(return_val, None)
        self.assertEqual(mock_dp.id, "1234")

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_dp_typeError(self, mock_insecure_channel, mock_dp_service_stub):
        """
        Test create_device_profile() method's DeviceProfile TypeError
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceProfileServiceStub
        mock_dp_service_stub_instance = mock_dp_service_stub.return_value

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock app
        mock_dp = "mock" # NOT a DeviceProfile Instance

        # Call function in testing and Assert Raise
        with self.assertRaises(TypeError) as context:
            client.create_device_profile(mock_dp)

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_create_app_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_dp_service_stub):
        """
        Test create_device_profile() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the dp service stub
        mock_dp_service_stub_instance = mock_dp_service_stub.return_value
        mock_dp_service_stub_instance.Create.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        #mock device profile
        mock_dp = DeviceProfile(
            name="mock_dp",
            tenant_id="54f14cd5-d6a1-4fbd-8a81-1022d1d41234", 
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_2,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False
        )

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value=None):
                # Call the method in testing
                return_val = client.create_device_profile(mock_dp)

        # assertations
        self.assertEqual(return_val, None)

class TestCreateDevice(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_device_happy_path(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test create_device() method's happy path
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Create.return_value = None

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        #Mock tags
        mock_tags = {
            "mock1": "test1",
            "mock2": "test2"
        }

        #Mock vars
        mock_vars = {
            "mock1": "test1",
            "mock2": "test2"
        }

        # Mock device
        mock_device = Device(
            name="mock_dev",
            dev_eui="a30012969b74de70",
            application_id="mock id",
            device_profile_id="mock id",
            tags=mock_tags,
            variables=mock_vars)

        # Call method in testing
        return_val = client.create_device(mock_device)

        # Assert the result
        self.assertEqual(return_val, None)

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_device_typeError(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test create_device() method's Device TypeError
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock device
        mock_device = "mock" # NOT a Device Instance

        # Call method in testing and Assert Raise
        with self.assertRaises(TypeError) as context:
            client.create_device(mock_device)

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_create_device_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test create_device() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Create.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock device
        mock_device = Device(
            name="mock_dev",
            dev_eui="a30012969b74de70",
            application_id="mock id",
            device_profile_id="mock id")

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value=None):
                # Call the method in testing
                return_val = client.create_device(mock_device)

        # assertations
        self.assertEqual(return_val, None)

class TestCreateDeviceKeys(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_dk_happy_path(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test create_device_keys() method's happy path
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the GatewayServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.CreateKeys.return_value = None

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock device keys
        mock_dk = DeviceKeys(dev_eui="a30012969b74de70", nwk_key="0f09f1223715f93d8aa3a7101fad0f04")

        # Call method in testing
        return_val = client.create_device_keys(mock_dk)

        # Assert the result
        self.assertEqual(return_val, None)

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_create_dk_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test create_device() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.CreateKeys.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock device keys
        mock_dk = DeviceKeys(dev_eui="a30012969b74de70", nwk_key="0f09f1223715f93d8aa3a7101fad0f04")

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value=None):
                # Call the method in testing
                return_val = client.create_device_keys(mock_dk)

        # assertations
        self.assertEqual(return_val, None)

class TestCreateGateway(unittest.TestCase):
    
    @patch('chirpstack_api_wrapper.api.GatewayServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_gw_happy_path(self, mock_insecure_channel, mock_gw_service_stub):
        """
        Test create_gateway() method's happy path
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the GatewayServiceStub
        mock_gw_service_stub_instance = mock_gw_service_stub.return_value
        mock_gw_service_stub_instance.Create.return_value = None

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        #Mock tags
        mock_tags = {
            "mock1": "test1",
            "mock2": "test2"
        }

        # Mock Gateway
        mock_gw = Gateway("mock","mock_gw_id","mock_tenant_id","mock description",mock_tags,45)

        # Call create_gateway
        return_val = client.create_gateway(mock_gw)

        # Assert the result
        self.assertEqual(return_val, None)

    @patch('chirpstack_api_wrapper.api.GatewayServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_gw_typeError(self, mock_insecure_channel, mock_gw_service_stub):
        """
        Test create_gateway() method's Gateway TypeError
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the GatewayServiceStub
        mock_gw_service_stub_instance = mock_gw_service_stub.return_value

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock Gateway
        mock_gw = "mock" # NOT a Gateway Instance

        # Call create_gateway and Assert Raise
        with self.assertRaises(TypeError) as context:
            client.create_gateway(mock_gw)

    @patch("chirpstack_api_wrapper.api.GatewayServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_create_gw_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_gw_service_stub):
        """
        Test create_gateway() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the create_gateway method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the GatewayServiceStub
        mock_gw_service_stub_instance = mock_gw_service_stub.return_value
        mock_gw_service_stub_instance.Create.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock Gateway
        mock_gw = Gateway("mock","mock_gw_id","mock_tenant_id")

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value=None):
                # Call the method in testing
                return_val = client.create_gateway(mock_gw)

        # assertations
        self.assertEqual(return_val, None)

class TestDeleteDevice(unittest.TestCase):

    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_delete_device_happy_path(self, mock_insecure_channel, mock_device_service_stub):
        """
        Test delete_device() method's happy path
        """

        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the GatewayServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Delete.return_value = None

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Call method in testing
        return_val = client.delete_device("mock deveui")

        # Assert the result
        self.assertEqual(return_val, None)

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_delete_device_unauthenticated_grpc_error(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test delete_device() when grpc error is raised for UNAUTHENTICATED and token needs to be refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the method to raise grpc.RpcError()
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'ExpiredSignature'

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Delete.side_effect = mock_rpc_error

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):

            #mock refresh token successfully logging in and retrying the method in testing
            with patch.object(client, "refresh_token", return_value=None):
                # Call the method in testing
                return_val = client.delete_device("mock deveui")

        # assertations
        self.assertEqual(return_val, None)

class TestRefreshToken(unittest.TestCase):

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_refresh_token_get_device(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test refresh token's happy path when used by ChirpstackClient.get_device()
        - refresh_token() should call get_device() after token is refreshed
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = Mock(device_info="mock_device_info")

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):
            # Create a dummy gRPC error
            dummy_error = Mock()
            dummy_error.code.return_value = grpc.StatusCode.UNAUTHENTICATED
            dummy_error.details.return_value = "ExpiredSignature"

            # Call the refresh_token method
            result = client.refresh_token(dummy_error, client.get_device, mock_dev_eui)

        # assertations
        self.assertEqual(result, client.get_device(mock_dev_eui))

    @patch("chirpstack_api_wrapper.api.DeviceServiceStub")
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    @patch("chirpstack_api_wrapper.time.sleep", return_value=None) #dont time.sleep() for test case
    def test_refresh_token_get_device_not_expired(self, mock_sleep, mock_insecure_channel, mock_device_service_stub):
        """
        Test refresh token's raised exception when used by ChirpstackClient.get_device()
        - refresh_token() should raise an exception when the problem is not ExpiredSignature
        """
        # Mock the gRPC channel and login response
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = Mock(device_info="mock_device_info")

        # Create a ChirpstackClient instance
        client = ChirpstackClient(CHIRPSTACK_ACT_EMAIL, CHIRPSTACK_ACT_PASSWORD, CHIRPSTACK_API_INTERFACE)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Mock the login method to return a dummy token
        with patch.object(client, "login", return_value="dummy_token"):
            # Create a dummy gRPC error
            dummy_error = Mock()
            dummy_error.code.return_value = grpc.StatusCode.ABORTED
            dummy_error.details.return_value = "aborted"

            with self.assertRaises(Exception) as context:
                client.refresh_token(dummy_error, client.get_device, mock_dev_eui)

        # assertations
        expected_exception_message = "The JWT token failed to be refreshed"
        self.assertEqual(str(context.exception), expected_exception_message)

if __name__ == "__main__":
    unittest.main()