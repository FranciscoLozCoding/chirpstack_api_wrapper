import unittest
from pytest import mark
from unittest.mock import Mock, patch, MagicMock
from app.chirpstack_client import ChirpstackClient
import grpc
from grpc import _channel as channel
from chirpstack_api import api
import sys

CHIRPSTACK_API_INTERFACE = "wes-chirpstack-server:8080"
CHIRPSTACK_ACT_EMAIL = "test"
CHIRPSTACK_ACT_PASSWORD = "test"

#TODO: Use sample data instead of mocking, maybe use factories lib (look at line of code with `Example` tag)

class TestLogin(unittest.TestCase):

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch('app.chirpstack_client.api.InternalServiceStub')
    def test_login_success(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test a succesful pass through of login
        """
        args = MagicMock()
        args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

        # Mocking grpc login response
        mock_login_response = MagicMock(jwt='mock_jwt_token')
        mock_internal_service_stub.return_value.Login.return_value = mock_login_response

        # Creating ChirpstackClient instance
        client = ChirpstackClient(args)

        # Assert that the login method was called with the correct parameters
        mock_internal_service_stub.return_value.Login.assert_called_once_with(
            api.LoginRequest(email=args.chirpstack_account_email, password=args.chirpstack_account_password)
        )

        # Assert that the auth_token is set correctly
        self.assertEqual(client.auth_token, 'mock_jwt_token')

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch('app.chirpstack_client.api.InternalServiceStub')
    def test_login_failure_RpcError_grpcStatusCodeUNAVAILABLE(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test the login method with a RpcError exception with a grpc.StatusCode.UNAVAILABLE
        """
        args = MagicMock()
        args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

        # Mocking grpc login response
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAVAILABLE
        mock_rpc_error.details = lambda: 'unavailable'
        mock_internal_service_stub.return_value.Login.side_effect = mock_rpc_error

        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Creating ChirpstackClient instance
            with self.assertRaises(SystemExit) as cm:
                ChirpstackClient(args)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertIn("Service is unavailable. This might be a DNS resolution issue.", log.output[0])

        # Assert that the system exit code is 1 (indicating failure)
        self.assertEqual(cm.exception.code, 1)

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch('app.chirpstack_client.api.InternalServiceStub')
    def test_login_failure_RpcError_grpcStatusCodeOther(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test the login method with a RpcError exception with a grpc.StatusCode.UNAUTHENTICATED
        """
        args = MagicMock()
        args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        args.chirpstack_account_password = 'wrong_password'

        # Mocking grpc login response
        mock_rpc_error = grpc.RpcError()
        mock_rpc_error.code = lambda: grpc.StatusCode.UNAUTHENTICATED
        mock_rpc_error.details = lambda: 'Invalid credentials'
        mock_internal_service_stub.return_value.Login.side_effect = mock_rpc_error

        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Creating ChirpstackClient instance
            with self.assertRaises(SystemExit) as cm:
                ChirpstackClient(args)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertIn(f"An error occurred with status code {grpc.StatusCode.UNAUTHENTICATED}", log.output[0])

        # Assert that the system exit code is 1 (indicating failure)
        self.assertEqual(cm.exception.code, 1)

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch('app.chirpstack_client.api.InternalServiceStub')
    def test_login_failure_Exception(self, mock_internal_service_stub, mock_insecure_channel):
        """
        Test the login method with a general exception
        """
        args = MagicMock()
        args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

        # Mocking grpc login response to raise a general Exception
        e = Exception("Test exception")
        mock_internal_service_stub.return_value.Login.side_effect = e

        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Creating ChirpstackClient instance
            with self.assertRaises(SystemExit) as cm:
                ChirpstackClient(args)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn(f"An error occurred: {e}", log.output[0])

        # Assert that the system exit code is 1 (indicating failure)
        self.assertEqual(cm.exception.code, 1)

class TestListAllDevices(unittest.TestCase):

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.InternalServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
    def test_list_all_devices_happy_path(self, mock_insecure_channel, mock_internal_service_stub):
        """
        Test list_all_devices() method's happy path by mocking list_all_apps() reponse and List_agg_pagination()
        """

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock(return_value=["device1", "device2"]) #Example

        # Create a ChirpstackClient instance
        client = ChirpstackClient(self.mock_args)

        with patch.object(client, 'List_agg_pagination', mock_list_agg_pagination):

            # Mock the app_resp for list_all_apps
            mock_app_resp = [Mock(id="app1"), Mock(id="app2")] #Example

            # Call list_all_devices
            devices = client.list_all_devices(mock_app_resp)

            # Assert the result
            self.assertEqual(devices, ['device1', 'device2', 'device1', 'device2'])

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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
    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.InternalServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
    def test_list_all_apps_happy_path(self, mock_insecure_channel, mock_internal_service_stub):
        """
        Test list_all_apps() method's happy path by mocking list_tenants() reponse and List_agg_pagination()
        """

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock(return_value=["app1", "app2"]) 

        with patch.object(ChirpstackClient, 'List_agg_pagination', mock_list_agg_pagination):
            # Create a ChirpstackClient instance
            client = ChirpstackClient(self.mock_args)

            # Mock the tenant_resp for list_all_devices
            mock_tenant_resp = [Mock(id="tenant1"), Mock(id="tenant2")]

            # Call list_all_devices
            apps = client.list_all_apps(mock_tenant_resp)

            # Assert the result
            self.assertEqual(apps, ['app1', 'app2', 'app1', 'app2'])

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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
    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.InternalServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
    def test_list_all_tenants_happy_path(self, mock_insecure_channel, mock_internal_service_stub):
        """
        Test list_tenants() method's happy path by mocking List_agg_pagination()
        """

        # Mock List_agg_pagination
        mock_list_agg_pagination = Mock(return_value=["Tenant1", "Tenant1"]) 

        with patch.object(ChirpstackClient, 'List_agg_pagination', mock_list_agg_pagination):
            # Create a ChirpstackClient instance
            client = ChirpstackClient(self.mock_args)

            # Call list_tenants()
            tenants = client.list_tenants()

            # Assert the result
            self.assertEqual(tenants, ["Tenant1", "Tenant1"])

    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

        with patch.object(client, 'List_agg_pagination', mock_list_agg_pagination):

            # Mock the login method to return a dummy token
            with patch.object(client, "login", return_value="dummy_token"):

                #mock refresh token successfully logging in and retrying the method
                with patch.object(client, "refresh_token", return_value=["Tenant1", "Tenant1"]):
                    # Call the method in testing
                    tenants = client.list_tenants()

        # Assert the result
        self.assertEqual(tenants, ["Tenant1", "Tenant1"])

class TestGetDeviceProfile(unittest.TestCase):

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.DeviceProfileServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        device_profile_info = client.get_device_profile(mock_device_profile_id)

        # Assert the result
        self.assertEqual(device_profile_info.device_profile_info, "mock_device_profile_info")

    @patch('app.chirpstack_client.api.DeviceProfileServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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

class TestGetDeviceAppKey(unittest.TestCase):

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

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

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

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

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

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

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

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


    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

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

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD
    
    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call get_device_app_key
        response = client.get_device_activation(mock_dev_eui)

        # Assert the result
        self.assertEqual(response.activation_details, "mock_activation_details")

    @patch("app.chirpstack_client.api.DeviceServiceStub")
    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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

class TestListAggPagination(unittest.TestCase):

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

        # Mock the request and metadata
        mock_req = Mock(offset=0,limit=1)
        mock_metadata = [("authorization", "Bearer mock_jwt")]

        # Call List_agg_pagination
        aggregated_records = ChirpstackClient.List_agg_pagination(mock_device_service_stub_instance, mock_req, mock_metadata)

        # Assert the result
        self.assertEqual(aggregated_records, ["result_page1", "result_page2"])

class TestGetDevice(unittest.TestCase):

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch('app.chirpstack_client.api.DeviceServiceStub')
    @patch('app.chirpstack_client.grpc.insecure_channel')
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
        client = ChirpstackClient(self.mock_args)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call get_device
        device_info = client.get_device(mock_dev_eui)

        # Assert the result
        self.assertEqual(device_info.device_info, "mock_device_info")

    @patch("app.chirpstack_client.api.DeviceServiceStub")
    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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

class TestRefreshToken(unittest.TestCase):

    def setUp(self):
        # Mock the arguments
        self.mock_args = Mock()
        self.mock_args.chirpstack_api_interface = CHIRPSTACK_API_INTERFACE
        self.mock_args.chirpstack_account_email = CHIRPSTACK_ACT_EMAIL
        self.mock_args.chirpstack_account_password = CHIRPSTACK_ACT_PASSWORD

    @patch("app.chirpstack_client.api.DeviceServiceStub")
    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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

    @patch("app.chirpstack_client.api.DeviceServiceStub")
    @patch('app.chirpstack_client.grpc.insecure_channel')
    @patch("app.chirpstack_client.time.sleep", return_value=None) #dont time.sleep() for test case
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
        client = ChirpstackClient(self.mock_args)

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