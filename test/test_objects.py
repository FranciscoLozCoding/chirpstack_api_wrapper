import unittest
from pytest import mark
from unittest.mock import Mock, patch, MagicMock
from chirpstack_api_wrapper.objects import *

class TestGateway(unittest.TestCase):
    def test_tags_ValueError(self):
        """
        Test Gateway's tags ValueError in init 
        """
        mock_tags = {
            "mock1": 1, # NOT a str
            "mock2": "test2"
        }
        # Init Gateway and Assert Raise
        with self.assertRaises(ValueError) as context:
            Gateway("mock_name", "mock_gateway_id", "mock_tenant_id",tags=mock_tags)

    def test_str_method(self):
        """
        Test Gateway's conversion to string
        """
        mock_gateway = Gateway(name="mock", gateway_id="mock_gw_id", tenant_id="mock_tenant_id")

        # Assertations
        self.assertEqual(str(mock_gateway), "mock_gw_id")

    def test_init_with_location_object(self):
        """Test Gateway initialization with Location object."""
        location = Location(40.7128, -74.0060, 100.0, "GPS", 5.0)
        gateway = Gateway(
            name="test_gateway",
            gateway_id="test_gw_id",
            tenant_id="test_tenant_id",
            location=location
        )
        self.assertEqual(gateway.location["latitude"], 40.7128)
        self.assertEqual(gateway.location["longitude"], -74.0060)
        self.assertEqual(gateway.location["altitude"], 100.0)

    def test_init_with_location_dict(self):
        """Test Gateway initialization with location dictionary."""
        location_dict = {"latitude": 40.7128, "longitude": -74.0060, "altitude": 100.0}
        gateway = Gateway(
            name="test_gateway",
            gateway_id="test_gw_id",
            tenant_id="test_tenant_id",
            location=location_dict
        )
        self.assertEqual(gateway.location, location_dict)

    def test_to_dict(self):
        """Test Gateway to_dict method."""
        gateway = Gateway(
            name="test_gateway",
            gateway_id="test_gw_id",
            tenant_id="test_tenant_id",
            description="Test gateway",
            tags={"env": "test"},
            stats_interval=60
        )
        gateway_dict = gateway.to_dict()
        expected = {
            'gateway_id': 'test_gw_id',
            'name': 'test_gateway',
            'description': 'Test gateway',
            'tenant_id': 'test_tenant_id',
            'tags': {'env': 'test'},
            'stats_interval': 60,
            'location': {},
            'metadata': {}
        }
        self.assertEqual(gateway_dict, expected)

    def test_from_grpc(self):
        """Test Gateway from_grpc method."""
        mock_grpc_gateway = Mock()
        mock_grpc_gateway.name = "test_gateway"
        mock_grpc_gateway.gateway_id = "test_gw_id"
        mock_grpc_gateway.tenant_id = "test_tenant_id"
        mock_grpc_gateway.description = "Test gateway"
        mock_grpc_gateway.tags = {"env": "test"}
        mock_grpc_gateway.stats_interval = 60
        mock_grpc_gateway.metadata = {"key": "value"}
        
        # Mock location
        mock_location = Mock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060
        mock_location.altitude = 100.0
        mock_location.source = "GPS"
        mock_location.accuracy = 5.0
        mock_grpc_gateway.location = mock_location
        
        gateway = Gateway.from_grpc(mock_grpc_gateway)
        self.assertEqual(gateway.name, "test_gateway")
        self.assertEqual(gateway.gateway_id, "test_gw_id")
        self.assertEqual(gateway.location["latitude"], 40.7128)

class TestApplication(unittest.TestCase):
    def test_tags_ValueError(self):
        """
        Test App's tags ValueError in init 
        """
        mock_tags = {
            "mock1": 1, # NOT a str
            "mock2": "test2"
        }
        # Init Application and Assert Raise
        with self.assertRaises(ValueError) as context:
            Application("mock_name","mock_tenant_id",tags=mock_tags)

    def test_str_method(self):
        """
        Test Apps's conversion to string
        """
        mock_app = Application("mock_name","mock_tenant_id",id="mock_id")

        # Assertations
        self.assertEqual(str(mock_app), "mock_id")

    def test_str_method_no_id(self):
        """
        Test Apps's conversion to string when the id is empty
        """
        mock_app = Application("mock_name","mock_tenant_id")

        #Assert Raise
        with self.assertRaises(RuntimeError) as context:
            str(mock_app)

    def test_to_dict(self):
        """Test Application to_dict method."""
        app = Application(
            name="test_app",
            tenant_id="test_tenant_id",
            id="test_app_id",
            description="Test application",
            tags={"env": "test"}
        )
        app_dict = app.to_dict()
        expected = {
            'id': 'test_app_id',
            'name': 'test_app',
            'tenant_id': 'test_tenant_id',
            'description': 'Test application',
            'tags': {'env': 'test'}
        }
        self.assertEqual(app_dict, expected)

    def test_from_grpc(self):
        """Test Application from_grpc method."""
        mock_grpc_app = Mock()
        mock_grpc_app.name = "test_app"
        mock_grpc_app.tenant_id = "test_tenant_id"
        mock_grpc_app.id = "test_app_id"
        mock_grpc_app.description = "Test application"
        mock_grpc_app.tags = {"env": "test"}
        
        app = Application.from_grpc(mock_grpc_app)
        self.assertEqual(app.name, "test_app")
        self.assertEqual(app.id, "test_app_id")
        self.assertEqual(app.tags, {"env": "test"})

class TestUser(unittest.TestCase):
    """Test cases for User class."""
    
    def test_user_init(self):
        """Test User initialization with all parameters."""
        user = User("test@example.com", "password123", True, False, "Test user", "user123")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.password, "password123")
        self.assertEqual(user.id, "user123")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertEqual(user.note, "Test user")
    
    def test_user_str_method(self):
        """Test User string representation."""
        user = User("test@example.com", "password123", "user123")
        self.assertEqual(str(user), "test@example.com")
    
    def test_user_to_dict(self):
        """Test User to_dict method."""
        user = User("test@example.com", "password123", True, False, "Test user", "user123")
        user_dict = user.to_dict()
        expected = {
            'id': 'user123',
            'email': 'test@example.com',
            'password': 'password123',
            'is_active': True,
            'is_admin': False,
            'note': 'Test user'
        }
        self.assertEqual(user_dict, expected)

    def test_from_grpc(self):
        """Test User from_grpc method."""
        mock_grpc_user = Mock()
        mock_grpc_user.email = "test@example.com"
        mock_grpc_user.is_active = True
        mock_grpc_user.is_admin = False
        mock_grpc_user.note = "Test user"
        mock_grpc_user.id = "user123"
        
        user = User.from_grpc(mock_grpc_user)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.password, "")  # Password not returned by API
        self.assertEqual(user.id, "user123")

class TestTenant(unittest.TestCase):
    """Test cases for Tenant class."""
    
    def test_tenant_init(self):
        """Test Tenant initialization with all parameters."""
        tenant = Tenant("Test Tenant", "Test Description", "tenant123", tags={"env": "test"})
        self.assertEqual(tenant.name, "Test Tenant")
        self.assertEqual(tenant.description, "Test Description")
        self.assertEqual(tenant.id, "tenant123")
        self.assertEqual(tenant.tags, {"env": "test"})
    
    def test_tenant_str_method_with_id(self):
        """Test Tenant string representation with ID."""
        tenant = Tenant("Test Tenant", "Test Description", "tenant123")
        self.assertEqual(str(tenant), "tenant123")
    
    def test_tenant_str_method_no_id(self):
        """Test Tenant string representation without ID raises error."""
        tenant = Tenant("Test Tenant", "Test Description")
        with self.assertRaises(RuntimeError):
            str(tenant)
    
    def test_tenant_to_dict(self):
        """Test Tenant to_dict method."""
        tenant = Tenant("Test Tenant", "Test Description", "tenant123", tags={"env": "test"})
        tenant_dict = tenant.to_dict()
        expected = {
            'name': 'Test Tenant',
            'description': 'Test Description',
            'id': 'tenant123',
            'can_have_gateways': False,
            'max_device_count': 0,
            'max_gateway_count': 0,
            'private_gateways_down': False,
            'private_gateways_up': False,
            'tags': {'env': 'test'}
        }
        self.assertEqual(tenant_dict, expected)
    
    def test_tenant_tags_validation(self):
        """Test Tenant tags validation raises ValueError for non-string values."""
        with self.assertRaises(ValueError):
            Tenant("Test Tenant", "Test Description", tags={"env": 123})

    def test_from_grpc(self):
        """Test Tenant from_grpc method."""
        mock_grpc_tenant = Mock()
        mock_grpc_tenant.name = "Test Tenant"
        mock_grpc_tenant.description = "Test Description"
        mock_grpc_tenant.id = "tenant123"
        mock_grpc_tenant.can_have_gateways = True
        mock_grpc_tenant.max_gateway_count = 10
        mock_grpc_tenant.max_device_count = 100
        mock_grpc_tenant.private_gateways_up = True
        mock_grpc_tenant.private_gateways_down = False
        mock_grpc_tenant.tags = {"env": "test"}
        
        tenant = Tenant.from_grpc(mock_grpc_tenant)
        self.assertEqual(tenant.name, "Test Tenant")
        self.assertEqual(tenant.id, "tenant123")
        self.assertTrue(tenant.can_have_gateways)

class TestMulticastGroup(unittest.TestCase):
    """Test cases for MulticastGroup class."""
    
    def test_multicast_group_init(self):
        """Test MulticastGroup initialization with all parameters."""
        group = MulticastGroup(
            name="Test Group",
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            mc_timeout=3600,
            application_id="app123",
            id="group123",
            description="Test multicast group",
            tags={"env": "test"}
        )
        self.assertEqual(group.name, "Test Group")
        self.assertEqual(group.mc_addr, "01020304")
        self.assertEqual(group.id, "group123")
        self.assertEqual(group.description, "Test multicast group")
        self.assertEqual(group.tags, {"env": "test"})
    
    def test_multicast_group_str_method_with_id(self):
        """Test MulticastGroup string representation with ID."""
        group = MulticastGroup(
            name="Test Group",
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            mc_timeout=3600,
            application_id="app123",
            id="group123"
        )
        self.assertEqual(str(group), "group123")
    
    def test_multicast_group_str_method_no_id(self):
        """Test MulticastGroup string representation without ID raises error."""
        group = MulticastGroup(
            name="Test Group",
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            mc_timeout=3600,
            application_id="app123"
        )
        with self.assertRaises(RuntimeError):
            str(group)
    
    def test_multicast_group_to_dict(self):
        """Test MulticastGroup to_dict method."""
        group = MulticastGroup(
            name="Test Group",
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            mc_timeout=3600,
            application_id="app123",
            id="group123",
            description="Test multicast group",
            tags={"env": "test"}
        )
        group_dict = group.to_dict()
        expected = {
            'id': 'group123',
            'name': 'Test Group',
            'mc_addr': '01020304',
            'mc_nwk_s_key': 'nwk_key_123',
            'mc_app_s_key': 'app_key_123',
            'f_cnt': 1,
            'group_type': MulticastGroupType.CLASS_C.value,
            'mc_timeout': 3600,
            'application_id': 'app123',
            'description': 'Test multicast group',
            'tags': {'env': 'test'}
        }
        self.assertEqual(group_dict, expected)
    
    def test_multicast_group_tags_validation(self):
        """Test MulticastGroup tags validation raises ValueError for non-string values."""
        with self.assertRaises(ValueError):
            MulticastGroup(
                name="Test Group",
                mc_addr="01020304",
                mc_nwk_s_key="nwk_key_123",
                mc_app_s_key="app_key_123",
                f_cnt=1,
                group_type=MulticastGroupType.CLASS_C,
                mc_timeout=3600,
                application_id="app123",
                tags={"env": 123}
            )

    def test_from_grpc(self):
        """Test MulticastGroup from_grpc method."""
        mock_grpc_group = Mock()
        mock_grpc_group.name = "Test Group"
        mock_grpc_group.mc_addr = "01020304"
        mock_grpc_group.mc_nwk_s_key = "nwk_key_123"
        mock_grpc_group.mc_app_s_key = "app_key_123"
        mock_grpc_group.f_cnt = 1
        mock_grpc_group.group_type = MulticastGroupType.CLASS_C
        mock_grpc_group.mc_timeout = 3600
        mock_grpc_group.application_id = "app123"
        mock_grpc_group.id = "group123"
        mock_grpc_group.description = "Test multicast group"
        mock_grpc_group.tags = {"env": "test"}
        
        group = MulticastGroup.from_grpc(mock_grpc_group)
        self.assertEqual(group.name, "Test Group")
        self.assertEqual(group.id, "group123")
        self.assertEqual(group.group_type, MulticastGroupType.CLASS_C.value)

class TestAppLayerParams(unittest.TestCase):
    """Test cases for AppLayerParams class."""
    
    def test_app_layer_params_init(self):
        """Test AppLayerParams initialization."""
        params = AppLayerParams(
            ts003_version=Ts003Version.V1_1,
            ts003_f_port=1,
            ts004_version=Ts004Version.V1_1,
            ts004_f_port=2,
            ts005_version=Ts005Version.V1_1,
            ts005_f_port=3
        )
        self.assertEqual(params.ts003_version, Ts003Version.V1_1.value)
        self.assertEqual(params.ts003_f_port, 1)
        self.assertEqual(params.ts004_version, Ts004Version.V1_1.value)
        self.assertEqual(params.ts004_f_port, 2)
        self.assertEqual(params.ts005_version, Ts005Version.V1_1.value)
        self.assertEqual(params.ts005_f_port, 3)

    def test_app_layer_params_str(self):
        """Test AppLayerParams string representation."""
        params = AppLayerParams(
            ts003_version=Ts003Version.V1_1,
            ts003_f_port=1,
            ts004_version=Ts004Version.V1_1,
            ts004_f_port=2,
            ts005_version=Ts005Version.V1_1,
            ts005_f_port=3
        )
        expected = "TS003:1(F1), TS004:1(F2), TS005:1(F3)"
        self.assertEqual(str(params), expected)

    def test_app_layer_params_to_dict(self):
        """Test AppLayerParams to_dict method."""
        params = AppLayerParams(
            ts003_version=Ts003Version.V1_1,
            ts003_f_port=1,
            ts004_version=Ts004Version.V1_1,
            ts004_f_port=2,
            ts005_version=Ts005Version.V1_1,
            ts005_f_port=3
        )
        params_dict = params.to_dict()
        expected = {
            'ts003_version': 1,
            'ts003_f_port': 1,
            'ts004_version': 1,
            'ts004_f_port': 2,
            'ts005_version': 1,
            'ts005_f_port': 3
        }
        self.assertEqual(params_dict, expected)

    def test_from_grpc(self):
        """Test AppLayerParams from_grpc method."""
        mock_grpc_params = Mock()
        mock_grpc_params.ts003_version = 1
        mock_grpc_params.ts003_f_port = 1
        mock_grpc_params.ts004_version = 1
        mock_grpc_params.ts004_f_port = 2
        mock_grpc_params.ts005_version = 1
        mock_grpc_params.ts005_f_port = 3
        
        params = AppLayerParams.from_grpc(mock_grpc_params)
        self.assertEqual(params.ts003_version, 1)
        self.assertEqual(params.ts003_f_port, 1)
        self.assertEqual(params.ts004_version, 1)

class TestLocation(unittest.TestCase):
    """Test cases for Location class."""
    
    def test_location_init(self):
        """Test Location initialization."""
        location = Location(40.7128, -74.0060, 100.0, "GPS", 5.0)
        self.assertEqual(location.latitude, 40.7128)
        self.assertEqual(location.longitude, -74.0060)
        self.assertEqual(location.altitude, 100.0)
        self.assertEqual(location.source, "GPS")
        self.assertEqual(location.accuracy, 5.0)

    def test_location_str(self):
        """Test Location string representation."""
        location = Location(40.7128, -74.0060, 100.0)
        # The actual output depends on how Python formats the float, so we'll check it contains the expected parts
        location_str = str(location)
        self.assertIn("40.7128", location_str)
        self.assertIn("-74.006", location_str)  # Python might truncate trailing zeros
        self.assertIn("100.0m", location_str)

    def test_location_to_dict(self):
        """Test Location to_dict method."""
        location = Location(40.7128, -74.0060, 100.0, "GPS", 5.0)
        location_dict = location.to_dict()
        expected = {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'altitude': 100.0,
            'source': 'GPS',
            'accuracy': 5.0
        }
        self.assertEqual(location_dict, expected)

class TestDeviceKeys(unittest.TestCase):
    """Test cases for DeviceKeys class."""
    
    def test_device_keys_init(self):
        """Test DeviceKeys initialization."""
        keys = DeviceKeys("dev_eui_123", "nwk_key_123", "app_key_123")
        self.assertEqual(keys.dev_eui, "dev_eui_123")
        self.assertEqual(keys.nwk_key, "nwk_key_123")
        self.assertEqual(keys.app_key, "app_key_123")

    def test_device_keys_to_dict(self):
        """Test DeviceKeys to_dict method."""
        keys = DeviceKeys("dev_eui_123", "nwk_key_123", "app_key_123")
        keys_dict = keys.to_dict()
        expected = {
            'dev_eui': 'dev_eui_123',
            'nwk_key': 'nwk_key_123',
            'app_key': 'app_key_123'
        }
        self.assertEqual(keys_dict, expected)

    def test_device_keys_repr(self):
        """Test DeviceKeys __repr__ method."""
        keys = DeviceKeys("dev_eui_123", "nwk_key_123", "app_key_123")
        expected = "{'dev_eui': 'dev_eui_123', 'nwk_key': 'nwk_key_123', 'app_key': 'app_key_123'}"
        self.assertEqual(repr(keys), expected)

class TestDeviceActivation(unittest.TestCase):
    """Test cases for DeviceActivation class."""
    
    def test_device_activation_init(self):
        """Test DeviceActivation initialization."""
        activation = DeviceActivation(
            dev_eui="dev_eui_123",
            dev_addr="dev_addr_123",
            app_s_key="app_s_key_123",
            nwk_s_enc_key="nwk_s_enc_key_123",
            s_nwk_s_int_key="s_nwk_s_int_key_123",
            f_nwk_s_int_key="f_nwk_s_int_key_123",
            f_cnt_up=1,
            n_f_cnt_down=2,
            a_f_cnt_down=3
        )
        self.assertEqual(activation.dev_eui, "dev_eui_123")
        self.assertEqual(activation.dev_addr, "dev_addr_123")
        self.assertEqual(activation.app_s_key, "app_s_key_123")
        self.assertEqual(activation.f_cnt_up, 1)
        self.assertEqual(activation.n_f_cnt_down, 2)
        self.assertEqual(activation.a_f_cnt_down, 3)

    def test_device_activation_str(self):
        """Test DeviceActivation string representation."""
        activation = DeviceActivation(
            dev_eui="dev_eui_123",
            dev_addr="dev_addr_123",
            app_s_key="app_s_key_123",
            nwk_s_enc_key="nwk_s_enc_key_123",
            s_nwk_s_int_key="s_nwk_s_int_key_123",
            f_nwk_s_int_key="f_nwk_s_int_key_123"
        )
        expected = "DeviceActivation(dev_eui=dev_eui_123, dev_addr=dev_addr_123)"
        self.assertEqual(str(activation), expected)

    def test_device_activation_to_dict(self):
        """Test DeviceActivation to_dict method."""
        activation = DeviceActivation(
            dev_eui="dev_eui_123",
            dev_addr="dev_addr_123",
            app_s_key="app_s_key_123",
            nwk_s_enc_key="nwk_s_enc_key_123",
            s_nwk_s_int_key="s_nwk_s_int_key_123",
            f_nwk_s_int_key="f_nwk_s_int_key_123",
            f_cnt_up=1,
            n_f_cnt_down=2,
            a_f_cnt_down=3
        )
        activation_dict = activation.to_dict()
        expected = {
            'dev_eui': 'dev_eui_123',
            'dev_addr': 'dev_addr_123',
            'app_s_key': 'app_s_key_123',
            'nwk_s_enc_key': 'nwk_s_enc_key_123',
            's_nwk_s_int_key': 's_nwk_s_int_key_123',
            'f_nwk_s_int_key': 'f_nwk_s_int_key_123',
            'f_cnt_up': 1,
            'n_f_cnt_down': 2,
            'a_f_cnt_down': 3
        }
        self.assertEqual(activation_dict, expected)

    def test_from_grpc(self):
        """Test DeviceActivation from_grpc method."""
        mock_grpc_activation = Mock()
        mock_grpc_activation.dev_eui = "dev_eui_123"
        mock_grpc_activation.dev_addr = "dev_addr_123"
        mock_grpc_activation.app_s_key = "app_s_key_123"
        mock_grpc_activation.nwk_s_enc_key = "nwk_s_enc_key_123"
        mock_grpc_activation.s_nwk_s_int_key = "s_nwk_s_int_key_123"
        mock_grpc_activation.f_nwk_s_int_key = "f_nwk_s_int_key_123"
        mock_grpc_activation.f_cnt_up = 1
        mock_grpc_activation.n_f_cnt_down = 2
        mock_grpc_activation.a_f_cnt_down = 3
        
        activation = DeviceActivation.from_grpc(mock_grpc_activation)
        self.assertEqual(activation.dev_eui, "dev_eui_123")
        self.assertEqual(activation.f_cnt_up, 1)

class TestFuotaDeployment(unittest.TestCase):
    """Test cases for FuotaDeployment class."""
    
    def test_fuota_deployment_init(self):
        """Test FuotaDeployment initialization."""
        deployment = FuotaDeployment(
            name="Test Deployment",
            application_id="app123",
            device_profile_id="dp123",
            multicast_group_id="mg123",
            multicast_group_type=MulticastGroupType.CLASS_C,
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            dr=5,
            frequency=868000000,
            class_c_timeout=30,
            id="deployment123",
            description="Test FUOTA deployment",
            tags={"env": "test"}
        )
        self.assertEqual(deployment.name, "Test Deployment")
        self.assertEqual(deployment.id, "deployment123")
        self.assertEqual(deployment.description, "Test FUOTA deployment")
        self.assertEqual(deployment.tags, {"env": "test"})

    def test_fuota_deployment_str_method_with_id(self):
        """Test FuotaDeployment string representation with ID."""
        deployment = FuotaDeployment(
            name="Test Deployment",
            application_id="app123",
            device_profile_id="dp123",
            multicast_group_id="mg123",
            multicast_group_type=MulticastGroupType.CLASS_C,
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            dr=5,
            frequency=868000000,
            class_c_timeout=30,
            id="deployment123"
        )
        self.assertEqual(str(deployment), "deployment123")

    def test_fuota_deployment_str_method_no_id(self):
        """Test FuotaDeployment string representation without ID raises error."""
        deployment = FuotaDeployment(
            name="Test Deployment",
            application_id="app123",
            device_profile_id="dp123",
            multicast_group_id="mg123",
            multicast_group_type=MulticastGroupType.CLASS_C,
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            dr=5,
            frequency=868000000,
            class_c_timeout=30
        )
        with self.assertRaises(RuntimeError):
            str(deployment)

    def test_fuota_deployment_to_dict(self):
        """Test FuotaDeployment to_dict method."""
        deployment = FuotaDeployment(
            name="Test Deployment",
            application_id="app123",
            device_profile_id="dp123",
            multicast_group_id="mg123",
            multicast_group_type=MulticastGroupType.CLASS_C,
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            dr=5,
            frequency=868000000,
            class_c_timeout=30,
            id="deployment123",
            description="Test FUOTA deployment",
            tags={"env": "test"}
        )
        deployment_dict = deployment.to_dict()
        expected = {
            'id': 'deployment123',
            'name': 'Test Deployment',
            'application_id': 'app123',
            'device_profile_id': 'dp123',
            'multicast_group_id': 'mg123',
            'multicast_group_type': MulticastGroupType.CLASS_C.value,
            'mc_addr': '01020304',
            'mc_nwk_s_key': 'nwk_key_123',
            'mc_app_s_key': 'app_key_123',
            'f_cnt': 1,
            'group_type': MulticastGroupType.CLASS_C.value,
            'dr': 5,
            'frequency': 868000000,
            'class_c_timeout': 30,
            'description': 'Test FUOTA deployment',
            'tags': {'env': 'test'}
        }
        self.assertEqual(deployment_dict, expected)

    def test_fuota_deployment_tags_validation(self):
        """Test FuotaDeployment tags validation raises ValueError for non-string values."""
        with self.assertRaises(ValueError):
            FuotaDeployment(
                name="Test Deployment",
                application_id="app123",
                device_profile_id="dp123",
                multicast_group_id="mg123",
                multicast_group_type=MulticastGroupType.CLASS_C,
                mc_addr="01020304",
                mc_nwk_s_key="nwk_key_123",
                mc_app_s_key="app_key_123",
                f_cnt=1,
                group_type=MulticastGroupType.CLASS_C,
                dr=5,
                frequency=868000000,
                class_c_timeout=30,
                tags={"env": 123}
            )

    def test_from_grpc(self):
        """Test FuotaDeployment from_grpc method."""
        mock_grpc_deployment = Mock()
        mock_grpc_deployment.name = "Test Deployment"
        mock_grpc_deployment.application_id = "app123"
        mock_grpc_deployment.device_profile_id = "dp123"
        mock_grpc_deployment.multicast_group_id = "mg123"
        mock_grpc_deployment.multicast_group_type = MulticastGroupType.CLASS_C
        mock_grpc_deployment.mc_addr = "01020304"
        mock_grpc_deployment.mc_nwk_s_key = "nwk_key_123"
        mock_grpc_deployment.mc_app_s_key = "app_key_123"
        mock_grpc_deployment.f_cnt = 1
        mock_grpc_deployment.group_type = MulticastGroupType.CLASS_C
        mock_grpc_deployment.dr = 5
        mock_grpc_deployment.frequency = 868000000
        mock_grpc_deployment.class_c_timeout = 30
        mock_grpc_deployment.id = "deployment123"
        mock_grpc_deployment.description = "Test FUOTA deployment"
        mock_grpc_deployment.tags = {"env": "test"}
        
        deployment = FuotaDeployment.from_grpc(mock_grpc_deployment)
        self.assertEqual(deployment.name, "Test Deployment")
        self.assertEqual(deployment.id, "deployment123")

class TestDeviceProfileTemplate(unittest.TestCase):
    """Test cases for DeviceProfileTemplate class."""
    
    def test_device_profile_template_init(self):
        """Test DeviceProfileTemplate initialization."""
        template = DeviceProfileTemplate(
            name="Test Template",
            vendor="Test Vendor",
            firmware="1.0.0",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            adr_algorithm_id="default",
            payload_codec_runtime=CodecRuntime.NONE,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="template123",
            description="Test device profile template",
            tags={"env": "test"}
        )
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.id, "template123")
        self.assertEqual(template.description, "Test device profile template")
        self.assertEqual(template.tags, {"env": "test"})

    def test_device_profile_template_str_method_with_id(self):
        """Test DeviceProfileTemplate string representation with ID."""
        template = DeviceProfileTemplate(
            name="Test Template",
            vendor="Test Vendor",
            firmware="1.0.0",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            adr_algorithm_id="default",
            payload_codec_runtime=CodecRuntime.NONE,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="template123"
        )
        self.assertEqual(str(template), "template123")

    def test_device_profile_template_str_method_no_id(self):
        """Test DeviceProfileTemplate string representation without ID raises error."""
        template = DeviceProfileTemplate(
            name="Test Template",
            vendor="Test Vendor",
            firmware="1.0.0",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            adr_algorithm_id="default",
            payload_codec_runtime=CodecRuntime.NONE,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False
        )
        with self.assertRaises(RuntimeError):
            str(template)

    def test_device_profile_template_to_dict(self):
        """Test DeviceProfileTemplate to_dict method."""
        template = DeviceProfileTemplate(
            name="Test Template",
            vendor="Test Vendor",
            firmware="1.0.0",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            adr_algorithm_id="default",
            payload_codec_runtime=CodecRuntime.NONE,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="template123",
            description="Test device profile template",
            tags={"env": "test"}
        )
        template_dict = template.to_dict()
        expected = {
            'id': 'template123',
            'name': 'Test Template',
            'vendor': 'Test Vendor',
            'firmware': '1.0.0',
            'region': Region.US915.value,
            'mac_version': MacVersion.LORAWAN_1_0_0.value,
            'reg_params_revision': RegParamsRevision.A.value,
            'adr_algorithm_id': 'default',
            'payload_codec_runtime': CodecRuntime.NONE.value,
            'uplink_interval': 3600,
            'supports_otaa': True,
            'supports_class_b': False,
            'supports_class_c': False,
            'description': 'Test device profile template',
            'tags': {'env': 'test'}
        }
        self.assertEqual(template_dict, expected)

    def test_device_profile_template_tags_validation(self):
        """Test DeviceProfileTemplate tags validation raises ValueError for non-string values."""
        with self.assertRaises(ValueError):
            DeviceProfileTemplate(
                name="Test Template",
                vendor="Test Vendor",
                firmware="1.0.0",
                region=Region.US915,
                mac_version=MacVersion.LORAWAN_1_0_0,
                reg_params_revision=RegParamsRevision.A,
                adr_algorithm_id="default",
                payload_codec_runtime=CodecRuntime.NONE,
                uplink_interval=3600,
                supports_otaa=True,
                supports_class_b=False,
                supports_class_c=False,
                tags={"env": 123}
            )

    def test_from_grpc(self):
        """Test DeviceProfileTemplate from_grpc method."""
        mock_grpc_template = Mock()
        mock_grpc_template.name = "Test Template"
        mock_grpc_template.vendor = "Test Vendor"
        mock_grpc_template.firmware = "1.0.0"
        mock_grpc_template.region = Region.US915
        mock_grpc_template.mac_version = MacVersion.LORAWAN_1_0_0
        mock_grpc_template.reg_params_revision = RegParamsRevision.A
        mock_grpc_template.adr_algorithm_id = "default"
        mock_grpc_template.payload_codec_runtime = CodecRuntime.NONE
        mock_grpc_template.uplink_interval = 3600
        mock_grpc_template.supports_otaa = True
        mock_grpc_template.supports_class_b = False
        mock_grpc_template.supports_class_c = False
        mock_grpc_template.id = "template123"
        mock_grpc_template.description = "Test device profile template"
        mock_grpc_template.tags = {"env": "test"}
        
        template = DeviceProfileTemplate.from_grpc(mock_grpc_template)
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.id, "template123")

class TestRelay(unittest.TestCase):
    """Test cases for Relay class."""
    
    def test_relay_init(self):
        """Test Relay initialization."""
        relay = Relay(
            name="Test Relay",
            tenant_id="tenant123",
            device_id="device123",
            id="relay123",
            description="Test relay",
            tags={"env": "test"}
        )
        self.assertEqual(relay.name, "Test Relay")
        self.assertEqual(relay.id, "relay123")
        self.assertEqual(relay.description, "Test relay")
        self.assertEqual(relay.tags, {"env": "test"})

    def test_relay_str_method_with_id(self):
        """Test Relay string representation with ID."""
        relay = Relay(
            name="Test Relay",
            tenant_id="tenant123",
            device_id="device123",
            id="relay123"
        )
        self.assertEqual(str(relay), "relay123")

    def test_relay_str_method_no_id(self):
        """Test Relay string representation without ID raises error."""
        relay = Relay(
            name="Test Relay",
            tenant_id="tenant123",
            device_id="device123"
        )
        with self.assertRaises(RuntimeError):
            str(relay)

    def test_relay_to_dict(self):
        """Test Relay to_dict method."""
        relay = Relay(
            name="Test Relay",
            tenant_id="tenant123",
            device_id="device123",
            id="relay123",
            description="Test relay",
            tags={"env": "test"}
        )
        relay_dict = relay.to_dict()
        expected = {
            'id': 'relay123',
            'name': 'Test Relay',
            'tenant_id': 'tenant123',
            'device_id': 'device123',
            'description': 'Test relay',
            'tags': {'env': 'test'}
        }
        self.assertEqual(relay_dict, expected)

    def test_relay_tags_validation(self):
        """Test Relay tags validation raises ValueError for non-string values."""
        with self.assertRaises(ValueError):
            Relay(
                name="Test Relay",
                tenant_id="tenant123",
                device_id="device123",
                tags={"env": 123}
            )

    def test_from_grpc(self):
        """Test Relay from_grpc method."""
        mock_grpc_relay = Mock()
        mock_grpc_relay.name = "Test Relay"
        mock_grpc_relay.tenant_id = "tenant123"
        mock_grpc_relay.device_id = "device123"
        mock_grpc_relay.id = "relay123"
        mock_grpc_relay.description = "Test relay"
        mock_grpc_relay.tags = {"env": "test"}
        
        relay = Relay.from_grpc(mock_grpc_relay)
        self.assertEqual(relay.name, "Test Relay")
        self.assertEqual(relay.id, "relay123")

class TestDeviceProfile(unittest.TestCase):
    """Test cases for DeviceProfile class."""
    
    def test_tags_ValueError(self):
        """
        Test DeviceProfile's tags ValueError in init 
        """
        mock_tags = {
            "mock1": 1, # NOT a str
            "mock2": "test2"
        }
        # Init dp and Assert Raise
        with self.assertRaises(ValueError) as context:
            DeviceProfile(
                name="mock",
                tenant_id="mock_id",
                region=Region.US915,
                mac_version=MacVersion.LORAWAN_1_0_0,
                reg_params_revision=RegParamsRevision.A,
                uplink_interval=3600,
                supports_otaa=True,
                supports_class_b=False,
                supports_class_c=False,
                tags=mock_tags)

    def test_abp_rx1_delay_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx1_delay Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            abp_rx1_dr_offset=1,
            abp_rx2_dr=1,
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.abp_rx1_delay

    def test_abp_rx1_delay_setter(self):
        """
        Test DeviceProfile's abp_rx1_delay setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        dp.abp_rx1_delay = 1
        self.assertEqual(dp.abp_rx1_delay, 1)

    def test_abp_rx1_delay_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx1_delay setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx1_delay = None

    def test_abp_rx1_dr_offset_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx1_dr_offset Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            abp_rx1_delay=1,
            abp_rx2_dr=1,
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.abp_rx1_dr_offset

    def test_abp_rx1_dr_offset_setter(self):
        """
        Test DeviceProfile's abp_rx1_dr_offset setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        dp.abp_rx1_dr_offset = 1
        self.assertEqual(dp.abp_rx1_dr_offset, 1)

    def test_abp_rx1_dr_offset_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx1_dr_offset setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx1_dr_offset = None

    def test_abp_rx2_dr_offset_setter(self):
        """
        Test DeviceProfile's abp_rx2_dr setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        dp.abp_rx2_dr = 1
        self.assertEqual(dp.abp_rx2_dr, 1)

    def test_abp_rx2_dr_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx2_dr Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            abp_rx1_delay=1,
            abp_rx1_dr_offset=1,
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.abp_rx2_dr

    def test_abp_rx2_dr_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx2_dr setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx2_dr = None

    def test_abp_rx2_freq_offset_setter(self):
        """
        Test DeviceProfile's abp_rx2_freq setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        dp.abp_rx2_freq = 1
        self.assertEqual(dp.abp_rx2_freq, 1)

    def test_abp_rx2_freq_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx2_freq Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            abp_rx1_delay=1,
            abp_rx1_dr_offset=1,
            abp_rx2_dr=1,
            supports_class_b=False,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.abp_rx2_freq

    def test_abp_rx2_freq_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx2_freq setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=False,
            supports_class_b=False,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx2_freq = None

    def test_class_b_ping_slot_dr_offset_setter(self):
        """
        Test DeviceProfile's class_b_ping_slot_dr setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        dp.class_b_ping_slot_dr = 1
        self.assertEqual(dp.class_b_ping_slot_dr, 1)

    def test_class_b_ping_slot_dr_prop_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_dr Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.class_b_ping_slot_dr

    def test_class_b_ping_slot_dr_setter_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_dr setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_ping_slot_dr = None

    def test_class_b_ping_slot_freq_prop_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_freq Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.class_b_ping_slot_freq

    def test_class_b_ping_slot_freq_setter(self):
        """
        Test DeviceProfile's class_b_ping_slot_freq setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        dp.class_b_ping_slot_freq = 1
        self.assertEqual(dp.class_b_ping_slot_freq, 1)

    def test_class_b_ping_slot_freq_setter_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_freq setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_ping_slot_freq = None

    def test_class_b_ping_slot_periodicity_offset_setter(self):
        """
        Test DeviceProfile's class_b_ping_slot_periodicity setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        dp.class_b_ping_slot_periodicity = 1
        self.assertEqual(dp.class_b_ping_slot_periodicity, 1)

    def test_class_b_ping_slot_periodicity_prop_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_periodicity Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.class_b_ping_slot_periodicity

    def test_class_b_ping_slot_periodicity_setter_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_periodicity setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_ping_slot_periodicity = None

    def test_class_b_timeout_offset_setter(self):
        """
        Test DeviceProfile's class_b_timeout setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        dp.class_b_timeout = 1
        self.assertEqual(dp.class_b_timeout, 1)

    def test_class_b_timeout_prop_valueError(self):
        """
        Test DeviceProfile's class_b_timeout Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.class_b_timeout

    def test_class_b_timeout_setter_valueError(self):
        """
        Test DeviceProfile's class_b_timeout setter Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=False)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_timeout = None

    def test_class_c_timeout_prop_valueError(self):
        """
        Test DeviceProfile's class_c_timeout Value error is raised when it is required
        """
        # Init dp and Assert Raise
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=True)
        
        # Access the property to trigger validation
        with self.assertRaises(ValueError) as context:
            _ = dp.class_c_timeout

    def test_class_c_timeout_setter(self):
        """
        Test DeviceProfile's class_c_timeout setter
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=True)
        
        dp.class_c_timeout = 1
        self.assertEqual(dp.class_c_timeout, 1)

    def test_class_c_timeout_valueError(self):
        """
        Test DeviceProfile's class_c_timeout Value error is raised when it is required
        """
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=True)
        
        # Assert Raise
        with self.assertRaises(ValueError) as context:
            dp.class_c_timeout = None

    def test_str_method(self):
        """
        Test DeviceProfile's conversion to string
        """
        mock_dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="mock_dp_id")

        # Assertations
        self.assertEqual(str(mock_dp), "mock_dp_id")

    def test_str_method_no_id(self):
        """
        Test DeviceProfile's conversion to string when the id is empty
        """
        mock_dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False)

        #Assert Raise
        with self.assertRaises(RuntimeError) as context:
            str(mock_dp)

    def test_tags_ValueError(self):
        """
        Test DeviceProfile's tags ValueError in init 
        """
        mock_tags = {
            "mock1": 1, # NOT a str
            "mock2": "test2"
        }
        # Init dp and Assert Raise
        with self.assertRaises(ValueError) as context:
            DeviceProfile(
                name="mock",
                tenant_id="mock_id",
                region=Region.US915,
                mac_version=MacVersion.LORAWAN_1_0_0,
                reg_params_revision=RegParamsRevision.A,
                uplink_interval=3600,
                supports_otaa=True,
                supports_class_b=False,
                supports_class_c=False,
                tags=mock_tags)

    def test_device_profile_init_with_all_params(self):
        """Test DeviceProfile initialization with all parameters."""
        app_layer_params = AppLayerParams(
            ts003_version=Ts003Version.V1_1,
            ts003_f_port=1,
            ts004_version=Ts004Version.V1_1,
            ts004_f_port=2,
            ts005_version=Ts005Version.V1_1,
            ts005_f_port=3
        )
        
        device_profile = DeviceProfile(
            name="Test Profile",
            tenant_id="tenant123",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            supports_class_c=True,
            abp_rx1_delay=1,
            abp_rx1_dr_offset=0,
            abp_rx2_dr=8,
            abp_rx2_freq=923300000,
            class_b_timeout=30,
            class_b_ping_slot_periodicity=ClassBPingSlot.EVERY_SEC,
            class_b_ping_slot_dr=8,
            class_b_ping_slot_freq=923300000,
            class_c_timeout=30,
            id="dp123",
            description="Test device profile",
            payload_codec_runtime=CodecRuntime.NONE,
            payload_codec_script="",
            flush_queue_on_activate=True,
            device_status_req_interval=1,
            tags={"env": "test"},
            auto_detect_measurements=True,
            allow_roaming=False,
            adr_algorithm_id=AdrAlgorithm.LORA_ONLY,
            rx1_delay=1,
            app_layer_params=app_layer_params,
            region_config_id="config123",
            is_relay=False,
            is_relay_ed=False,
            relay_ed_relay_only=False,
            relay_enabled=False,
            relay_cad_periodicity=CadPeriodicity.NONE,
            relay_default_channel_index=0,
            relay_second_channel_freq=0,
            relay_second_channel_dr=0,
            relay_second_channel_ack_offset=SecondChAckOffset.NONE,
            relay_ed_activation_mode=RelayModeActivation.DISABLED,
            relay_ed_smart_enable_level=0,
            relay_ed_back_off=0,
            relay_ed_uplink_limit_bucket_size=0,
            relay_ed_uplink_limit_reload_rate=0,
            relay_join_req_limit_reload_rate=0,
            relay_notify_limit_reload_rate=0,
            relay_global_uplink_limit_reload_rate=0,
            relay_overall_limit_reload_rate=0,
            relay_join_req_limit_bucket_size=0,
            relay_notify_limit_bucket_size=0,
            relay_global_uplink_limit_bucket_size=0,
            relay_overall_limit_bucket_size=0,
            measurements={"temperature": {"kind": "UNKNOWN"}}
        )
        
        self.assertEqual(device_profile.name, "Test Profile")
        self.assertEqual(device_profile.id, "dp123")
        self.assertEqual(device_profile.description, "Test device profile")
        self.assertEqual(device_profile.tags, {"env": "test"})
        self.assertTrue(device_profile.supports_otaa)
        self.assertTrue(device_profile.supports_class_b)
        self.assertTrue(device_profile.supports_class_c)
        self.assertEqual(device_profile.abp_rx1_delay, 1)
        self.assertEqual(device_profile.class_b_timeout, 30)
        self.assertEqual(device_profile.class_c_timeout, 30)
        self.assertEqual(device_profile.measurements, {"temperature": {"kind": "UNKNOWN"}})

    def test_device_profile_to_dict(self):
        """Test DeviceProfile to_dict method."""
        device_profile = DeviceProfile(
            name="Test Profile",
            tenant_id="tenant123",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="dp123",
            description="Test device profile",
            tags={"env": "test"}
        )
        device_profile_dict = device_profile.to_dict()
        
        # Check key fields
        self.assertEqual(device_profile_dict['id'], "dp123")
        self.assertEqual(device_profile_dict['name'], "Test Profile")
        self.assertEqual(device_profile_dict['tenant_id'], "tenant123")
        self.assertEqual(device_profile_dict['region'], Region.US915.value)
        self.assertEqual(device_profile_dict['mac_version'], MacVersion.LORAWAN_1_0_0.value)
        self.assertEqual(device_profile_dict['reg_params_revision'], RegParamsRevision.A.value)
        self.assertEqual(device_profile_dict['uplink_interval'], 3600)
        self.assertTrue(device_profile_dict['supports_otaa'])
        self.assertFalse(device_profile_dict['supports_class_b'])
        self.assertFalse(device_profile_dict['supports_class_c'])
        self.assertEqual(device_profile_dict['description'], "Test device profile")
        self.assertEqual(device_profile_dict['tags'], {"env": "test"})

    def test_device_profile_from_grpc(self):
        """Test DeviceProfile from_grpc method."""
        mock_grpc_profile = Mock()
        mock_grpc_profile.name = "Test Profile"
        mock_grpc_profile.tenant_id = "tenant123"
        mock_grpc_profile.region = Region.US915
        mock_grpc_profile.mac_version = MacVersion.LORAWAN_1_0_0
        mock_grpc_profile.reg_params_revision = RegParamsRevision.A
        mock_grpc_profile.uplink_interval = 3600
        mock_grpc_profile.supports_otaa = True
        mock_grpc_profile.supports_class_b = False
        mock_grpc_profile.supports_class_c = False
        mock_grpc_profile.abp_rx1_delay = 1
        mock_grpc_profile.abp_rx1_dr_offset = 0
        mock_grpc_profile.abp_rx2_dr = 8
        mock_grpc_profile.abp_rx2_freq = 923300000
        mock_grpc_profile.class_b_timeout = 30
        mock_grpc_profile.class_b_ping_slot_periodicity = ClassBPingSlot.EVERY_SEC
        mock_grpc_profile.class_b_ping_slot_dr = 8
        mock_grpc_profile.class_b_ping_slot_freq = 923300000
        mock_grpc_profile.class_c_timeout = 30
        mock_grpc_profile.id = "dp123"
        mock_grpc_profile.description = "Test device profile"
        mock_grpc_profile.payload_codec_runtime = CodecRuntime.NONE
        mock_grpc_profile.payload_codec_script = ""
        mock_grpc_profile.flush_queue_on_activate = True
        mock_grpc_profile.device_status_req_interval = 1
        mock_grpc_profile.tags = {"env": "test"}
        mock_grpc_profile.auto_detect_measurements = True
        mock_grpc_profile.allow_roaming = False
        mock_grpc_profile.adr_algorithm_id = AdrAlgorithm.LORA_ONLY
        mock_grpc_profile.rx1_delay = 1
        mock_grpc_profile.region_config_id = "config123"
        mock_grpc_profile.is_relay = False
        mock_grpc_profile.is_relay_ed = False
        mock_grpc_profile.relay_ed_relay_only = False
        mock_grpc_profile.relay_enabled = False
        mock_grpc_profile.relay_cad_periodicity = CadPeriodicity.NONE
        mock_grpc_profile.relay_default_channel_index = 0
        mock_grpc_profile.relay_second_channel_freq = 0
        mock_grpc_profile.relay_second_channel_dr = 0
        mock_grpc_profile.relay_second_channel_ack_offset = SecondChAckOffset.NONE
        mock_grpc_profile.relay_ed_activation_mode = RelayModeActivation.DISABLED
        mock_grpc_profile.relay_ed_smart_enable_level = 0
        mock_grpc_profile.relay_ed_back_off = 0
        mock_grpc_profile.relay_ed_uplink_limit_bucket_size = 0
        mock_grpc_profile.relay_ed_uplink_limit_reload_rate = 0
        mock_grpc_profile.relay_join_req_limit_reload_rate = 0
        mock_grpc_profile.relay_notify_limit_reload_rate = 0
        mock_grpc_profile.relay_global_uplink_limit_reload_rate = 0
        mock_grpc_profile.relay_overall_limit_reload_rate = 0
        mock_grpc_profile.relay_join_req_limit_bucket_size = 0
        mock_grpc_profile.relay_notify_limit_bucket_size = 0
        mock_grpc_profile.relay_global_uplink_limit_bucket_size = 0
        mock_grpc_profile.relay_overall_limit_bucket_size = 0
        mock_grpc_profile.measurements = {"temperature": {"kind": "UNKNOWN"}}
        
        # Mock app_layer_params
        mock_app_layer_params = Mock()
        mock_app_layer_params.ts003_version = 1
        mock_app_layer_params.ts003_f_port = 1
        mock_app_layer_params.ts004_version = 1
        mock_app_layer_params.ts004_f_port = 2
        mock_app_layer_params.ts005_version = 1
        mock_app_layer_params.ts005_f_port = 3
        mock_grpc_profile.app_layer_params = mock_app_layer_params
        
        device_profile = DeviceProfile.from_grpc(mock_grpc_profile)
        self.assertEqual(device_profile.name, "Test Profile")
        self.assertEqual(device_profile.id, "dp123")
        self.assertEqual(device_profile.description, "Test device profile")
        self.assertEqual(device_profile.tags, {"env": "test"})
        self.assertTrue(device_profile.supports_otaa)
        self.assertFalse(device_profile.supports_class_b)
        self.assertFalse(device_profile.supports_class_c)
        self.assertEqual(device_profile.measurements, {"temperature": {"kind": "UNKNOWN"}})

    def test_device_profile_repr(self):
        """Test DeviceProfile __repr__ method."""
        device_profile = DeviceProfile(
            name="Test Profile",
            tenant_id="tenant123",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="dp123"
        )
        # The __repr__ method calls to_dict(), so we expect a dictionary representation
        self.assertIn("'id': 'dp123'", repr(device_profile))
        self.assertIn("'name': 'Test Profile'", repr(device_profile))

class TestDevice(unittest.TestCase):
    def test_str_method(self):
        """
        Test Device's conversion to string
        """
        mock_device = Device(
            name="mock",
            dev_eui="mock_dev_eui",
            application_id="mock_app_id",
            device_profile_id="mock_dp_id")

        # Assertations
        self.assertEqual(str(mock_device), "mock_dev_eui")

    def test_tags_ValueError(self):
        """
        Test Device's tags ValueError in init 
        """
        mock_tags = {
            "mock1": 1, # NOT a str
            "mock2": "test2"
        }
        # Init Device and Assert Raise
        with self.assertRaises(ValueError) as context:
            Device(
                name="mock",
                dev_eui="mock_dev_eui",
                application_id="mock_app_id",
                device_profile_id="mock_dp_id",
                tags=mock_tags)

    def test_vars_ValueError(self):
        """
        Test Device's variables ValueError in init 
        """
        mock_vars = {
            "mock1": 1, # NOT a str
            "mock2": "test2"
        }
        # Init Device and Assert Raise
        with self.assertRaises(ValueError) as context:
            Device(
                name="mock",
                dev_eui="mock_dev_eui",
                application_id="mock_app_id",
                device_profile_id="mock_dp_id",
                variables=mock_vars)

    def test_device_init_with_all_params(self):
        """Test Device initialization with all parameters."""
        device = Device(
            name="Test Device",
            dev_eui="dev_eui_123",
            application_id="app123",
            device_profile_id="dp123",
            join_eui="join_eui_123",
            description="Test device",
            skip_fcnt_check=True,
            is_disabled=False,
            tags={"env": "test"},
            variables={"key": "value"}
        )
        self.assertEqual(device.name, "Test Device")
        self.assertEqual(device.dev_eui, "dev_eui_123")
        self.assertEqual(device.application_id, "app123")
        self.assertEqual(device.device_profile_id, "dp123")
        self.assertEqual(device.join_eui, "join_eui_123")
        self.assertEqual(device.description, "Test device")
        self.assertTrue(device.skip_fcnt_check)
        self.assertFalse(device.is_disabled)
        self.assertEqual(device.tags, {"env": "test"})
        self.assertEqual(device.variables, {"key": "value"})

    def test_device_init_with_application_object(self):
        """Test Device initialization with Application object."""
        app = Application("Test App", "tenant123", "app123")
        device_profile = DeviceProfile(
            name="Test Profile",
            tenant_id="tenant123",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="dp123"
        )
        
        device = Device(
            name="Test Device",
            dev_eui="dev_eui_123",
            application_id=app,
            device_profile_id=device_profile
        )
        self.assertEqual(device.application_id, "app123")
        self.assertEqual(device.device_profile_id, "dp123")

    def test_device_to_dict(self):
        """Test Device to_dict method."""
        device = Device(
            name="Test Device",
            dev_eui="dev_eui_123",
            application_id="app123",
            device_profile_id="dp123",
            join_eui="join_eui_123",
            description="Test device",
            skip_fcnt_check=True,
            is_disabled=False,
            tags={"env": "test"},
            variables={"key": "value"}
        )
        device_dict = device.to_dict()
        expected = {
            'name': 'Test Device',
            'dev_eui': 'dev_eui_123',
            'application_id': 'app123',
            'device_profile_id': 'dp123',
            'join_eui': 'join_eui_123',
            'description': 'Test device',
            'skip_fcnt_check': True,
            'is_disabled': False,
            'tags': {'env': 'test'},
            'variables': {'key': 'value'}
        }
        self.assertEqual(device_dict, expected)

    def test_device_from_grpc(self):
        """Test Device from_grpc method."""
        mock_grpc_device = Mock()
        mock_grpc_device.name = "Test Device"
        mock_grpc_device.dev_eui = "dev_eui_123"
        mock_grpc_device.application_id = "app123"
        mock_grpc_device.device_profile_id = "dp123"
        mock_grpc_device.join_eui = "join_eui_123"
        mock_grpc_device.description = "Test device"
        mock_grpc_device.skip_fcnt_check = True
        mock_grpc_device.is_disabled = False
        mock_grpc_device.tags = {"env": "test"}
        mock_grpc_device.variables = {"key": "value"}
        
        device = Device.from_grpc(mock_grpc_device)
        self.assertEqual(device.name, "Test Device")
        self.assertEqual(device.dev_eui, "dev_eui_123")
        self.assertEqual(device.application_id, "app123")
        self.assertEqual(device.device_profile_id, "dp123")
        self.assertEqual(device.join_eui, "join_eui_123")
        self.assertEqual(device.description, "Test device")
        self.assertTrue(device.skip_fcnt_check)
        self.assertFalse(device.is_disabled)
        self.assertEqual(device.tags, {"env": "test"})
        self.assertEqual(device.variables, {"key": "value"})

    def test_device_repr(self):
        """Test Device __repr__ method."""
        device = Device(
            name="Test Device",
            dev_eui="dev_eui_123",
            application_id="app123",
            device_profile_id="dp123"
        )
        expected = "{'name': 'Test Device', 'dev_eui': 'dev_eui_123', 'application_id': 'app123', 'device_profile_id': 'dp123', 'join_eui': '', 'description': '', 'skip_fcnt_check': False, 'is_disabled': False, 'tags': {}, 'variables': {}}"
        self.assertEqual(repr(device), expected)

if __name__ == "__main__":
    unittest.main()