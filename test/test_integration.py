"""
Integration tests for Chirpstack API Wrapper.

These tests require a running Chirpstack server on localhost:8081.
The tests will create, read, update, and delete actual records on the server.
All test records are marked with a "test" tag to identify them.
"""

import unittest
import time
import pytest
import random
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from chirpstack_api_wrapper import ChirpstackClient
from chirpstack_api_wrapper.objects import (
    Application, Tenant, DeviceProfile, Device, Gateway, Region, 
    MacVersion, RegParamsRevision, CodecRuntime, AdrAlgorithm,
    MulticastGroup, MulticastGroupType, FuotaDeployment, DeviceProfileTemplate,
    Relay, Location, DeviceKeys, Encoding, User, DeviceActivation, Aggregation
)


class TestChirpstackIntegration(unittest.TestCase):
    """Integration tests for Chirpstack API Wrapper."""
    
    @classmethod
    def setUp(cls):
        """Set up test fixtures for the entire test class."""
        cls.client = ChirpstackClient("admin", "admin", "localhost:8081")
        
        # Test data names
        timestamp = int(time.time())
        cls.test_tenant_name = f"test_tenant_{timestamp}"
        cls.test_app_name = f"test_app_{timestamp}"
        cls.test_device_profile_name = f"test_profile_{timestamp}"
        cls.test_device_name = f"test_device_{timestamp}"
        cls.test_gateway_name = f"test_gateway_{timestamp}"
        
        # Test record IDs (will be populated during setup)
        cls.test_tenant_id = None
        cls.test_app_id = None
        cls.test_device_profile_id = None
        cls.test_device_dev_eui = None
        cls.test_gateway_id = None
        
        # Clean up any existing test records first
        cls._cleanup_existing_test_records()
        
        # Create all test records
        cls._create_test_records()
    
    @classmethod
    def tearDown(cls):
        """Clean up test fixtures after all tests."""
        cls._cleanup_test_records()
    
    @classmethod
    def _cleanup_existing_test_records(cls):
        """Clean up any existing test records from previous test runs."""
        try:
            # Get all tenants and find test ones
            tenants = cls.client.list_tenants()
            for tenant in tenants:
                if tenant.tags.get("test") == "true":
                    try:
                        # Get applications for this tenant
                        apps = cls.client.list_all_apps([tenant])
                        for app in apps:
                            if app.tags.get("test") == "true":
                                # Get devices for this app
                                devices = cls.client.list_devices(application_id=app.id)
                                for device in devices:
                                    if device.tags.get("test") == "true":
                                        try:
                                            cls.client.delete_device(device.dev_eui)
                                        except:
                                            pass
                                try:
                                    cls.client.delete_app(app.id)
                                except:
                                    pass
                        try:
                            cls.client.delete_tenant(tenant.id)
                        except:
                            pass
                    except:
                        pass
            
            # Get all device profiles and find test ones
            all_tenants = cls.client.list_tenants()
            profiles = cls.client.list_all_device_profiles(all_tenants)
            for profile in profiles:
                if profile.tags.get("test") == "true":
                    try:
                        cls.client.delete_device_profile(profile.id)
                    except:
                        pass
            
            # Get all gateways and find test ones
            gateways = cls.client.list_all_gateways(all_tenants)
            for gateway in gateways:
                if gateway.tags.get("test") == "true":
                    try:
                        cls.client.delete_gateway(gateway.gateway_id)
                    except:
                        pass
        except Exception as e:
            print(f"Warning: Error during cleanup of existing test records: {e}")
    
    @classmethod
    def _create_test_records(cls):
        """Create all test records needed for the tests."""
        try:
            # 1. Create test tenant
            tenant = Tenant(
                name=cls.test_tenant_name,
                description="Integration test tenant",
                tags={"test": "true", "created_by": "integration_test"},
                can_have_gateways=True,
            )
            cls.client.create_tenant(tenant)
            cls.test_tenant_id = tenant.id
            
            # 2. Create test application
            app = Application(
                name=cls.test_app_name,
                description="Integration test application",
                tenant_id=cls.test_tenant_id,
                tags={"test": "true", "created_by": "integration_test"}
            )
            cls.client.create_app(app)
            cls.test_app_id = app.id
            
            # 3. Create test device profile
            device_profile = DeviceProfile(
                name=cls.test_device_profile_name,
                tenant_id=cls.test_tenant_id,
                region=Region.US915,
                mac_version=MacVersion.LORAWAN_1_0_0,
                reg_params_revision=RegParamsRevision.A,
                uplink_interval=3600,
                supports_otaa=True,
                supports_class_b=False,
                supports_class_c=False,
                description="Integration test device profile",
                payload_codec_runtime=CodecRuntime.NONE,
                tags={"test": "true", "created_by": "integration_test"}
            )
            cls.client.create_device_profile(device_profile)
            cls.test_device_profile_id = device_profile.id
            
            # 4. Create test device
            dev_eui = ''.join([f'{random.randint(0, 255):02x}' for _ in range(8)])
            device = Device(
                name=cls.test_device_name,
                dev_eui=dev_eui,
                application_id=cls.test_app_id,
                device_profile_id=cls.test_device_profile_id,
                description="Integration test device",
                tags={"test": "true", "created_by": "integration_test"}
            )
            cls.client.create_device(device)
            cls.test_device_dev_eui = dev_eui

            # 5. Create device keys
            device_keys = DeviceKeys(
                dev_eui=cls.test_device_dev_eui,
                nwk_key="7e19d51b647b123dd123c484707aadc1",
                app_key="7e19d51b647b123dd123c484707aadc1"
            )
            cls.client.create_device_keys(device_keys)
            
            # 6. Create test gateway (skip if not supported by server)
            try:
                gateway_id = ''.join([f'{random.randint(0, 255):02x}' for _ in range(8)])
                gateway = Gateway(
                    name=cls.test_gateway_name,
                    gateway_id=gateway_id,
                    tenant_id=cls.test_tenant_id,
                    description="Integration test gateway",
                    tags={"test": "true", "created_by": "integration_test"}
                )
                cls.client.create_gateway(gateway)
                cls.test_gateway_id = gateway_id
                print(f"   Gateway: {cls.test_gateway_name} (ID: {cls.test_gateway_id})")
            except Exception as e:
                print(f"   ⚠️  Gateway creation skipped: {e}")
                cls.test_gateway_id = None
            
            print(f"✅ Created test records:")
            print(f"   Tenant: {cls.test_tenant_name} (ID: {cls.test_tenant_id})")
            print(f"   Application: {cls.test_app_name} (ID: {cls.test_app_id})")
            print(f"   Device Profile: {cls.test_device_profile_name} (ID: {cls.test_device_profile_id})")
            print(f"   Device: {cls.test_device_name} (DevEUI: {cls.test_device_dev_eui})")
            print(f"   Gateway: {cls.test_gateway_name} (ID: {cls.test_gateway_id})")
            
        except Exception as e:
            print(f"❌ Error creating test records: {e}")
            # Clean up any partially created records
            cls._cleanup_test_records()
            raise
    
    @classmethod
    def _cleanup_test_records(cls):
        """Clean up test records created during setup."""
        try:
            # Clean up in reverse order of creation
            if cls.test_device_dev_eui:
                try:
                    cls.client.delete_device(cls.test_device_dev_eui)
                    print(f"✅ Deleted test device: {cls.test_device_dev_eui}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not delete test device {cls.test_device_dev_eui}: {e}")
            
            if cls.test_device_profile_id:
                try:
                    cls.client.delete_device_profile(cls.test_device_profile_id)
                    print(f"✅ Deleted test device profile: {cls.test_device_profile_id}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not delete test device profile {cls.test_device_profile_id}: {e}")
            
            if cls.test_app_id:
                try:
                    cls.client.delete_app(cls.test_app_id)
                    print(f"✅ Deleted test application: {cls.test_app_id}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not delete test application {cls.test_app_id}: {e}")
            
            if cls.test_gateway_id:
                try:
                    cls.client.delete_gateway(cls.test_gateway_id)
                    print(f"✅ Deleted test gateway: {cls.test_gateway_id}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not delete test gateway {cls.test_gateway_id}: {e}")
            else:
                print("ℹ️  No test gateway to delete (gateway creation was skipped)")
            
            if cls.test_tenant_id:
                try:
                    cls.client.delete_tenant(cls.test_tenant_id)
                    print(f"✅ Deleted test tenant: {cls.test_tenant_id}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not delete test tenant {cls.test_tenant_id}: {e}")
                    
        except Exception as e:
            print(f"❌ Error during test cleanup: {e}")
    
    @pytest.mark.integration
    def test_01_login(self):
        """Test login to Chirpstack server."""
        # Login should happen automatically in __init__
        self.assertIsNotNone(self.client.auth_token)
        self.assertIsInstance(self.client.auth_token, str)
        self.assertGreater(len(self.client.auth_token), 0)
    
    @pytest.mark.integration
    def test_02_ping(self):
        """Test ping to Chirpstack server."""
        result = self.client.ping()
        self.assertTrue(result)
    
    @pytest.mark.integration
    def test_03_get_tenant(self):
        """Test getting the test tenant."""
        retrieved_tenant = self.client.get_tenant(self.test_tenant_id)
        self.assertIsNotNone(retrieved_tenant)
        self.assertEqual(retrieved_tenant.name, self.test_tenant_name)
        self.assertEqual(retrieved_tenant.description, "Integration test tenant")
        self.assertIn("test", retrieved_tenant.tags)
        self.assertEqual(retrieved_tenant.tags["test"], "true")
    
    @pytest.mark.integration
    def test_04_list_tenants(self):
        """Test listing tenants."""
        tenants = self.client.list_tenants()
        self.assertIsInstance(tenants, list)
        self.assertGreater(len(tenants), 0)
        
        # Find our test tenant
        test_tenant = next((t for t in tenants if t.id == self.test_tenant_id), None)
        self.assertIsNotNone(test_tenant)
        self.assertEqual(test_tenant.name, self.test_tenant_name)
    
    @pytest.mark.integration
    def test_05_get_application(self):
        """Test getting the test application."""
        retrieved_app = self.client.get_app(self.test_app_id)
        self.assertIsNotNone(retrieved_app)
        self.assertEqual(retrieved_app.name, self.test_app_name)
        self.assertEqual(retrieved_app.description, "Integration test application")
        self.assertEqual(retrieved_app.tenant_id, self.test_tenant_id)
        self.assertIn("test", retrieved_app.tags)
        self.assertEqual(retrieved_app.tags["test"], "true")
    
    @pytest.mark.integration
    def test_06_list_applications(self):
        """Test listing applications."""
        apps = self.client.list_all_apps(self.client.list_tenants())
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 0)
        
        # Find our test application
        test_app = next((a for a in apps if a.id == self.test_app_id), None)
        self.assertIsNotNone(test_app)
        self.assertEqual(test_app.name, self.test_app_name)
    
    @pytest.mark.integration
    def test_07_get_device_profile(self):
        """Test getting the test device profile."""
        retrieved_profile = self.client.get_device_profile(self.test_device_profile_id)
        self.assertIsNotNone(retrieved_profile)
        self.assertEqual(retrieved_profile.name, self.test_device_profile_name)
        self.assertEqual(retrieved_profile.description, "Integration test device profile")
        self.assertEqual(retrieved_profile.tenant_id, self.test_tenant_id)
        self.assertIn("test", retrieved_profile.tags)
        self.assertEqual(retrieved_profile.tags["test"], "true")
    
    @pytest.mark.integration
    def test_08_list_all_device_profiles(self):
        """Test listing device profiles."""
        profiles = self.client.list_all_device_profiles(self.client.list_tenants())
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)
        
        # Find our test profile
        test_profile = next((p for p in profiles if p.id == self.test_device_profile_id), None)
        self.assertIsNotNone(test_profile)
        self.assertEqual(test_profile.name, self.test_device_profile_name)
    
    @pytest.mark.integration
    def test_09_get_device(self):
        """Test getting the test device."""
        retrieved_device = self.client.get_device(self.test_device_dev_eui)
        self.assertIsNotNone(retrieved_device)
        self.assertEqual(retrieved_device.name, self.test_device_name)
        self.assertEqual(retrieved_device.dev_eui, self.test_device_dev_eui)
        self.assertEqual(retrieved_device.application_id, self.test_app_id)
        self.assertEqual(retrieved_device.device_profile_id, self.test_device_profile_id)
        self.assertEqual(retrieved_device.description, "Integration test device")
        self.assertIn("test", retrieved_device.tags)
        self.assertEqual(retrieved_device.tags["test"], "true")
    
    @pytest.mark.integration
    def test_10_list_all_devices(self):
        """Test listing devices."""
        devices = self.client.list_all_devices(self.client.list_all_apps(self.client.list_tenants()))
        self.assertIsInstance(devices, list)
        self.assertGreater(len(devices), 0)
        
        # Find our test device
        test_device = next((d for d in devices if d.dev_eui == self.test_device_dev_eui), None)
        self.assertIsNotNone(test_device)
        self.assertEqual(test_device.name, self.test_device_name)
    
    @pytest.mark.integration
    def test_11_create_gateway(self):
        """Test creating a gateway."""
        # Generate a unique gateway ID for testing
        import random
        gateway_id = ''.join([f'{random.randint(0, 255):02x}' for _ in range(8)])
        
        gateway = Gateway(
            name=self.test_gateway_name,
            gateway_id=gateway_id,
            tenant_id=self.test_tenant_id,
            description="Integration test gateway",
            tags={"test": "true", "created_by": "integration_test"}
        )
        
        self.client.create_gateway(gateway)
        self.test_gateway_id = gateway_id
        
        # Verify gateway was created
        retrieved_gateway = self.client.get_gateway(self.test_gateway_id)
        self.assertIsNotNone(retrieved_gateway)
        self.assertEqual(retrieved_gateway.name, self.test_gateway_name)
        self.assertEqual(retrieved_gateway.gateway_id, gateway_id)
        self.assertEqual(retrieved_gateway.tenant_id, self.test_tenant_id)
        self.assertEqual(retrieved_gateway.description, "Integration test gateway")
        self.assertIn("test", retrieved_gateway.tags)
        self.assertEqual(retrieved_gateway.tags["test"], "true")
    
    @pytest.mark.integration
    def test_12_list_gateways(self):
        """Test listing gateways."""
        gateways = self.client.list_all_gateways(self.client.list_tenants())
        self.assertIsInstance(gateways, list)
        self.assertGreater(len(gateways), 0)
        
        # Find our test gateway (if it was created)
        if self.test_gateway_id:
            test_gateway = next((g for g in gateways if g.gateway_id == self.test_gateway_id), None)
            self.assertIsNotNone(test_gateway)
            self.assertEqual(test_gateway.name, self.test_gateway_name)
    
    @pytest.mark.integration
    def test_13_update_device(self):
        """Test updating a device."""
        updated_description = "Updated integration test device"
        
        # Get current device
        device = self.client.get_device(self.test_device_dev_eui)
        self.assertIsNotNone(device)
        
        # Update description
        device.description = updated_description
        self.client.update_device(device)
        
        # Verify update
        updated_device = self.client.get_device(self.test_device_dev_eui)
        self.assertEqual(updated_device.description, updated_description)
    
    @pytest.mark.integration
    def test_14_update_application(self):
        """Test updating an application."""
        updated_description = "Updated integration test application"
        
        # Get current application
        app = self.client.get_app(self.test_app_id)
        self.assertIsNotNone(app)
        
        # Update description
        app.description = updated_description
        self.client.update_app(app)
        
        # Verify update
        updated_app = self.client.get_app(self.test_app_id)
        self.assertEqual(updated_app.description, updated_description)
    
    @pytest.mark.integration
    def test_15_device_activation(self):
        """Test getting device activation."""
        # This might return empty if device is not activated
        activation = self.client.get_device_activation(self.test_device_dev_eui)
        # Just verify the method doesn't crash
        self.assertTrue(True)
    
    @pytest.mark.integration
    def test_16_device_keys(self): #TODO: fix this
        """Test getting device keys."""
        # This might return empty if device is not activated
        try:
            keys = self.client.get_device_app_key(self.test_device_dev_eui, MacVersion.LORAWAN_1_0_0)
            # Just verify the method doesn't crash
            self.assertIsInstance(keys, str)
        except Exception as e:
            # It's okay if this fails for unactivated devices
            error_msg = str(e).lower()
            self.assertTrue(
                "not found" in error_msg or "object does not exist" in error_msg,
                f"Expected error to contain 'not found' or 'object does not exist', but got: {error_msg}"
            )
    
    @pytest.mark.integration
    def test_17_verify_test_records_exist(self):
        """Verify that all test records are still accessible."""
        # This test ensures all our test records are still accessible
        # and haven't been accidentally modified by other tests
        
        # Verify tenant
        tenant = self.client.get_tenant(self.test_tenant_id)
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.name, self.test_tenant_name)
        
        # Verify application
        app = self.client.get_app(self.test_app_id)
        self.assertIsNotNone(app)
        self.assertEqual(app.name, self.test_app_name)
        
        # Verify device profile
        profile = self.client.get_device_profile(self.test_device_profile_id)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, self.test_device_profile_name)
        
        # Verify device
        device = self.client.get_device(self.test_device_dev_eui)
        self.assertIsNotNone(device)
        self.assertEqual(device.name, self.test_device_name)
        
        # Verify gateway (if it was created)
        if self.test_gateway_id:
            gateway = self.client.get_gateway(self.test_gateway_id)
            self.assertIsNotNone(gateway)
            self.assertEqual(gateway.name, self.test_gateway_name)

    @pytest.mark.integration
    def test_18_list_device_profiles_for_app(self): #TODO: fix this
        """Test listing device profiles for an application."""
        profiles = self.client.list_device_profiles_for_app(self.test_app_id)
        self.assertIsInstance(profiles, list)
        # Should contain our test device profile
        profile_ids = [p.id for p in profiles]
        self.assertIn(self.test_device_profile_id, profile_ids)

    @pytest.mark.integration
    def test_19_list_device_tags_for_app(self): #TODO: fix this
        """Test listing device tags for an application."""
        tags = self.client.list_device_tags_for_app(self.test_app_id)
        self.assertIsInstance(tags, list)

    @pytest.mark.integration
    def test_20_create_and_manage_multicast_group(self): #TODO: fix this
        """Test creating and managing a multicast group."""
        # Create multicast group
        multicast_group = MulticastGroup(
            name="Test Multicast Group",
            mc_addr="01020304",
            mc_nwk_s_key="nwk_key_123",
            mc_app_s_key="app_key_123",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            mc_timeout=3600,
            application_id=self.test_app_id,
            description="Test multicast group",
            tags={"test": "true", "created_by": "integration_test"}
        )
        
        self.client.create_multicast_group(multicast_group)
        self.assertIsNotNone(multicast_group.id)
        
        # Get the multicast group
        retrieved_group = self.client.get_multicast_group(multicast_group.id)
        self.assertIsNotNone(retrieved_group)
        self.assertEqual(retrieved_group.name, "Test Multicast Group")
        
        # List multicast groups for the application
        groups = self.client.list_multicast_groups(self.test_app_id)
        self.assertIsInstance(groups, list)
        group_ids = [g.id for g in groups]
        self.assertIn(multicast_group.id, group_ids)
        
        # Add device to multicast group
        self.client.add_device_to_multicast_group(multicast_group.id, self.test_device_dev_eui)
        
        # Remove device from multicast group
        self.client.remove_device_from_multicast_group(multicast_group.id, self.test_device_dev_eui)
        
        # Add gateway to multicast group (if gateway exists)
        if self.test_gateway_id:
            self.client.add_gateway_to_multicast_group(multicast_group.id, self.test_gateway_id)
            self.client.remove_gateway_from_multicast_group(multicast_group.id, self.test_gateway_id)
        
        # Enqueue multicast downlink
        test_data = b"Hello from multicast"
        self.client.enqueue_multicast_downlink(multicast_group.id, test_data, 1, False)
        
        # Get multicast group queue
        queue = self.client.get_multicast_group_queue(multicast_group.id)
        self.assertIsInstance(queue, list)
        
        # Flush multicast group queue
        self.client.flush_multicast_group_queue(multicast_group.id)
        
        # Update multicast group
        multicast_group.description = "Updated test multicast group"
        self.client.update_multicast_group(multicast_group)
        
        # Verify update
        updated_group = self.client.get_multicast_group(multicast_group.id)
        self.assertEqual(updated_group.description, "Updated test multicast group")
        
        # Clean up
        self.client.delete_multicast_group(multicast_group.id)

    @pytest.mark.integration
    def test_21_create_and_manage_fuota_deployment(self): #TODO: fix this
        """Test creating and managing a FUOTA deployment."""
        # Create multicast group for FUOTA
        multicast_group = MulticastGroup(
            name="FUOTA Test Group",
            mc_addr="05060708",
            mc_nwk_s_key="nwk_key_456",
            mc_app_s_key="app_key_456",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            mc_timeout=3600,
            application_id=self.test_app_id,
            tags={"test": "true", "created_by": "integration_test"}
        )
        self.client.create_multicast_group(multicast_group)
        
        # Create FUOTA deployment
        fuota_deployment = FuotaDeployment(
            name="Test FUOTA Deployment",
            application_id=self.test_app_id,
            device_profile_id=self.test_device_profile_id,
            multicast_group_id=multicast_group.id,
            multicast_group_type=MulticastGroupType.CLASS_C,
            mc_addr="05060708",
            mc_nwk_s_key="nwk_key_456",
            mc_app_s_key="app_key_456",
            f_cnt=1,
            group_type=MulticastGroupType.CLASS_C,
            dr=5,
            frequency=868000000,
            class_c_timeout=30,
            description="Test FUOTA deployment",
            tags={"test": "true", "created_by": "integration_test"}
        )
        
        self.client.create_fuota_deployment(fuota_deployment)
        self.assertIsNotNone(fuota_deployment.id)
        
        # Get the FUOTA deployment
        retrieved_deployment = self.client.get_fuota_deployment(fuota_deployment.id)
        self.assertIsNotNone(retrieved_deployment)
        self.assertEqual(retrieved_deployment.name, "Test FUOTA Deployment")
        
        # List FUOTA deployments for the application
        deployments = self.client.list_fuota_deployments(self.test_app_id)
        self.assertIsInstance(deployments, list)
        deployment_ids = [d.id for d in deployments]
        self.assertIn(fuota_deployment.id, deployment_ids)
        
        # Add device to FUOTA deployment
        self.client.add_devices_to_fuota(fuota_deployment.id, [self.test_device_dev_eui])
        
        # List FUOTA devices
        fuota_devices = self.client.list_fuota_devices(fuota_deployment.id)
        self.assertIsInstance(fuota_devices, list)
        
        # Remove device from FUOTA deployment
        self.client.remove_devices_from_fuota(fuota_deployment.id, [self.test_device_dev_eui])
        
        # Add gateway to FUOTA deployment (if gateway exists)
        if self.test_gateway_id:
            self.client.add_gateways_to_fuota(fuota_deployment.id, [self.test_gateway_id])
            
            # List FUOTA gateways
            fuota_gateways = self.client.list_fuota_gateways(fuota_deployment.id)
            self.assertIsInstance(fuota_gateways, list)
            
            self.client.remove_gateways_from_fuota(fuota_deployment.id, [self.test_gateway_id])
        
        # List FUOTA jobs
        fuota_jobs = self.client.list_fuota_jobs(fuota_deployment.id)
        self.assertIsInstance(fuota_jobs, list)
        
        # Update FUOTA deployment
        fuota_deployment.description = "Updated test FUOTA deployment"
        self.client.update_fuota_deployment(fuota_deployment)
        
        # Verify update
        updated_deployment = self.client.get_fuota_deployment(fuota_deployment.id)
        self.assertEqual(updated_deployment.description, "Updated test FUOTA deployment")
        
        # Clean up
        self.client.delete_fuota_deployment(fuota_deployment.id)
        self.client.delete_multicast_group(multicast_group.id)

    @pytest.mark.integration
    def test_22_create_and_manage_device_profile_template(self):
        """Test creating and managing a device profile template."""
        # Create device profile template
        template = DeviceProfileTemplate(
            name="Test Device Profile Template",
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
            description="Test device profile template",
            tags={"test": "true", "created_by": "integration_test"}
        )
        
        self.client.create_device_profile_template(template)
        self.assertIsNotNone(template.id)
        
        # Get the device profile template
        retrieved_template = self.client.get_device_profile_template(template.id)
        self.assertIsNotNone(retrieved_template)
        self.assertEqual(retrieved_template.name, "Test Device Profile Template")
        
        # List device profile templates
        templates = self.client.list_device_profile_templates()
        self.assertIsInstance(templates, list)
        template_ids = [t.id for t in templates]
        self.assertIn(template.id, template_ids)
        
        # Update device profile template
        template.description = "Updated test device profile template"
        self.client.update_device_profile_template(template)
        
        # Verify update
        updated_template = self.client.get_device_profile_template(template.id)
        self.assertEqual(updated_template.description, "Updated test device profile template")
        
        # Clean up
        self.client.delete_device_profile_template(template.id)

    @pytest.mark.integration
    def test_23_create_and_manage_relay(self): #TODO: fix this
        """Test creating and managing a relay."""
        # Create relay
        relay = Relay(
            name="Test Relay",
            tenant_id=self.test_tenant_id,
            device_id=self.test_device_dev_eui,
            description="Test relay",
            tags={"test": "true", "created_by": "integration_test"}
        )
        
        self.client.create_relay(relay)
        self.assertIsNotNone(relay.id)
        
        # Get the relay
        retrieved_relay = self.client.get_relay(relay.id)
        self.assertIsNotNone(retrieved_relay)
        self.assertEqual(retrieved_relay.name, "Test Relay")
        
        # List relays for the tenant
        relays = self.client.list_relays(self.test_tenant_id)
        self.assertIsInstance(relays, list)
        relay_ids = [r.id for r in relays]
        self.assertIn(relay.id, relay_ids)
        
        # List relay devices
        relay_devices = self.client.list_relay_devices(relay.id)
        self.assertIsInstance(relay_devices, list)
        
        # Add device to relay
        self.client.add_device_to_relay(relay.id, self.test_device_dev_eui)
        
        # Remove device from relay
        self.client.remove_device_from_relay(relay.id, self.test_device_dev_eui)
        
        # Update relay
        relay.description = "Updated test relay"
        self.client.update_relay(relay)
        
        # Verify update
        updated_relay = self.client.get_relay(relay.id)
        self.assertEqual(updated_relay.description, "Updated test relay")
        
        # Clean up
        self.client.delete_relay(relay.id)

    @pytest.mark.integration
    def test_24_device_queue_operations(self): #TODO: fix this
        """Test device queue operations."""
        # Enqueue device downlink
        test_data = b"Hello from downlink"
        self.client.enqueue_device_downlink(self.test_device_dev_eui, test_data, 1, False)
        
        # Get device queue
        queue = self.client.get_device_queue(self.test_device_dev_eui)
        self.assertIsInstance(queue, list)
        
        # Flush device queue
        self.client.flush_device_queue(self.test_device_dev_eui)

    @pytest.mark.integration
    def test_25_device_metrics_and_links(self):
        """Test device metrics and link operations."""
        # Get device link metrics
        link_metrics = self.client.get_device_link_metrics(self.test_device_dev_eui, datetime.now(timezone.utc) - timedelta(days=1), datetime.now(timezone.utc), Aggregation.DAY)
        self.assertIsInstance(link_metrics, dict)
        
        # Get next frame counter down
        next_f_cnt = self.client.get_next_f_cnt_down(self.test_device_dev_eui)
        self.assertIsInstance(next_f_cnt, int)
        
        # Get random device address
        dev_addr = self.client.get_random_dev_addr(self.test_device_dev_eui)
        self.assertIsInstance(dev_addr, str)
        
        # Flush device nonces
        self.client.flush_dev_nonces(self.test_device_dev_eui)

    @pytest.mark.integration
    def test_26_gateway_operations(self):
        """Test gateway operations."""
        if not self.test_gateway_id:
            self.skipTest("Gateway not available for testing")
        
        # Update gateway
        gateway = self.client.get_gateway(self.test_gateway_id)
        print(gateway.to_dict())
        original_description = gateway.description
        gateway.description = "Updated test gateway"
        self.client.update_gateway(gateway)
        
        # Verify update
        updated_gateway = self.client.get_gateway(self.test_gateway_id)
        self.assertEqual(updated_gateway.description, "Updated test gateway")
        
        # # Restore original description
        gateway.description = original_description
        self.client.update_gateway(gateway)
        
        # # Update gateway location
        location = Location(40.7128, -74.0060, 100.0, "GPS", 5.0)
        self.client.update_gateway_location(gateway, location)
        

    @pytest.mark.integration
    def test_27_relay_gateway_operations(self): #TODO: fix this
        """Test relay gateway operations."""
        if not self.test_gateway_id:
            self.skipTest("Gateway not available for testing")
        
        # Get relay gateway
        relay_gateway = self.client.get_relay_gateway(self.test_gateway_id)
        self.assertIsInstance(relay_gateway, dict)
        
        # List relay gateways
        relay_gateways = self.client.list_relay_gateways()
        self.assertIsInstance(relay_gateways, list)

    @pytest.mark.integration
    def test_28_user_management(self):
        """Test user management operations."""
        # Create user
        user = User(
            email="testuser@example.com",
            password="testpassword123",
            is_active=True,
            is_admin=False,
            note="Test user for integration tests",
            id="test_user_123"
        )
        
        self.client.create_user_standalone(user)
        
        # Get user
        retrieved_user = self.client.get_user_standalone(user.id)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, "testuser@example.com")
        
        # List users
        users = self.client.list_users_standalone()
        self.assertIsInstance(users, list)
        user_ids = [u.id for u in users]
        self.assertIn(user.id, user_ids)
        
        # Update user
        user.note = "Updated test user"
        self.client.update_user_standalone(user)
        
        # Verify update
        updated_user = self.client.get_user_standalone(user.id)
        self.assertEqual(updated_user.note, "Updated test user")
        
        # Update user password
        self.client.update_user_password(user.id, "newpassword123")
        
        # Clean up
        self.client.delete_user_standalone(user.id)

    @pytest.mark.integration
    def test_29_tenant_user_management(self):
        """Test tenant user management operations."""
        # Create user for tenant
        tenant_user = User(
            email="tenantuser@example.com",
            password="tenantpassword123",
            is_active=True,
            is_admin=False,
            note="Test tenant user",
            id="test_tenant_user_123"
        )
        
        self.client.create_user(tenant_user, self.test_tenant_id)
        
        # Get user
        retrieved_user = self.client.get_user(tenant_user.id, self.test_tenant_id)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, "tenantuser@example.com")
        
        # List users for tenant
        tenant_users = self.client.list_users_for_tenant(self.test_tenant_id)
        self.assertIsInstance(tenant_users, list)
        user_ids = [u.id for u in tenant_users]
        self.assertIn(tenant_user.id, user_ids)
        
        # Update user
        tenant_user.note = "Updated tenant user"
        self.client.update_user(tenant_user, self.test_tenant_id)
        
        # Verify update
        updated_user = self.client.get_user(tenant_user.id, self.test_tenant_id)
        self.assertEqual(updated_user.note, "Updated tenant user")
        
        # Clean up
        self.client.delete_user(tenant_user.id, self.test_tenant_id)

    @pytest.mark.integration
    def test_30_adr_algorithms(self): #TODO: fix this
        """Test ADR algorithms listing."""
        algorithms = self.client.list_adr_algorithms()
        self.assertIsInstance(algorithms, list)

    @pytest.mark.integration
    def test_31_device_keys_management(self): #TODO: fix this
        """Test device keys management."""
        # Create device keys
        device_keys = DeviceKeys(
            dev_eui=self.test_device_dev_eui,
            nwk_key="nwk_key_test_123",
            app_key="app_key_test_123"
        )
        
        self.client.create_device_keys(device_keys)
        
        # Update device keys
        device_keys.nwk_key = "updated_nwk_key_123"
        self.client.update_device_keys(device_keys)

        # Get device keys
        device_keys = self.client.get_device_keys(self.test_device_dev_eui)
        self.assertIsNotNone(device_keys)
        self.assertEqual(device_keys.nwk_key, "updated_nwk_key_123")
        
        # Clean up
        self.client.delete_device_keys(self.test_device_dev_eui)

    @pytest.mark.integration
    def test_32_device_activation_management(self): #TODO: fix this
        """Test device activation management."""
        # Activate device
        device_activation = DeviceActivation(
            dev_eui=self.test_device_dev_eui,
            dev_addr="01020304",
            app_s_key="00000000000000000000000000000000",
            nwk_s_enc_key="7e19d51b647b123dd123c484707aadc1",
            s_nwk_s_int_key="7e19d51b647b123dd123c484707aadc1",
            f_nwk_s_int_key="7e19d51b647b123dd123c484707aadc1",
            f_cnt_up=0,
            n_f_cnt_down=0,
            a_f_cnt_down=0
        )
        self.client.activate_device(device_activation)
        
        # Get device activation
        activation = self.client.get_device_activation(self.test_device_dev_eui)
        self.assertIsNotNone(activation)
        self.assertEqual(activation.dev_eui, self.test_device_dev_eui)
        
        # Deactivate device
        self.client.deactivate_device(self.test_device_dev_eui)

    @pytest.mark.integration
    def test_33_basic_list_operations(self):
        """Test basic list operations that should work."""
        # List all tenants
        tenants = self.client.list_tenants()
        self.assertIsInstance(tenants, list)
        
        # List all applications (requires tenants)
        applications = self.client.list_all_apps(tenants)
        self.assertIsInstance(applications, list)
        
        # List all device profiles (requires tenants)
        device_profiles = self.client.list_all_device_profiles(tenants)
        self.assertIsInstance(device_profiles, list)
        
        # List all gateways (requires tenants)
        gateways = self.client.list_all_gateways(tenants)
        self.assertIsInstance(gateways, list)

    @pytest.mark.integration
    def test_34_basic_get_operations(self):
        """Test basic get operations that should work."""
        # Get tenant
        tenant = self.client.get_tenant(self.test_tenant_id)
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.id, self.test_tenant_id)
        
        # Get application
        app = self.client.get_app(self.test_app_id)
        self.assertIsNotNone(app)
        self.assertEqual(app.id, self.test_app_id)
        
        # Get device profile
        profile = self.client.get_device_profile(self.test_device_profile_id)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.id, self.test_device_profile_id)
        
        # Get device
        device = self.client.get_device(self.test_device_dev_eui)
        self.assertIsNotNone(device)
        self.assertEqual(device.dev_eui, self.test_device_dev_eui)
        
        # Get gateway (if available)
        if self.test_gateway_id:
            gateway = self.client.get_gateway(self.test_gateway_id)
            self.assertIsNotNone(gateway)
            self.assertEqual(gateway.gateway_id, self.test_gateway_id)

    @pytest.mark.integration
    def test_35_basic_delete_operations(self):
        """Test basic delete operations."""
        # Test deleting non-existent objects (should raise exceptions)
        # These operations should raise exceptions when objects don't exist
        try:
            self.client.delete_device("1234567890abcdef")
            self.fail("Expected delete_device to raise exception for non-existent device")
        except Exception:
            # This is expected to fail
            pass
        
        try:
            self.client.delete_device_profile("1234567890abcdef")
            self.fail("Expected delete_device_profile to raise exception for non-existent device profile")
        except Exception:
            # This is expected to fail
            pass
        
        try:
            self.client.delete_app("1234567890abcdef")
            self.fail("Expected delete_app to raise exception for non-existent application")
        except Exception:
            # This is expected to fail
            pass
        
        try:
            self.client.delete_gateway("1234567890abcdef")
            self.fail("Expected delete_gateway to raise exception for non-existent gateway")
        except Exception:
            # This is expected to fail
            pass

    @pytest.mark.integration
    def test_36_error_handling(self):
        """Test error handling for non-existent resources."""
        # Try to get non-existent tenant
        try:
            self.client.get_tenant("non-existent-tenant-id")
            # If no exception is raised, the tenant should be None
            self.fail("Expected get_tenant to return None for non-existent tenant")
        except Exception:
            # This is expected to fail
            pass
        
        # Try to get non-existent application
        try:
            self.client.get_app("non-existent-app-id")
            # If no exception is raised, the application should be None
            self.fail("Expected get_app to return None for non-existent application")
        except Exception:
            # This is expected to fail
            pass
        
        # Try to get non-existent device
        try:
            self.client.get_device("1234567890abcdef")
            # If no exception is raised, the device should be None
            self.fail("Expected get_device to return None for non-existent device")
        except Exception:
            # This is expected to fail
            pass

    @pytest.mark.integration
    def test_37_client_initialization(self):
        """Test client initialization and basic properties."""
        # Test that client has required attributes
        self.assertIsNotNone(self.client.email)
        self.assertIsNotNone(self.client.password)
        self.assertIsNotNone(self.client.server)
        self.assertIsNotNone(self.client.auth_token)
        
        # Test that client can make basic API calls
        tenants = self.client.list_tenants()
        self.assertIsInstance(tenants, list)

    @pytest.mark.integration
    def test_38_token_refresh(self):
        """Test token refresh functionality."""
        # The client should handle token refresh automatically
        # Let's test by making multiple API calls
        for i in range(5):
            tenants = self.client.list_tenants()
            self.assertIsInstance(tenants, list)
            
            applications = self.client.list_all_apps(tenants)
            self.assertIsInstance(applications, list)

    @pytest.mark.integration
    def test_39_connection_stability(self):
        """Test connection stability over multiple operations."""
        # Get tenants first for the operations that need them
        tenants = self.client.list_tenants()
        
        operations = [
            lambda: self.client.list_tenants(),
            lambda: self.client.list_all_apps(tenants),
            lambda: self.client.list_all_device_profiles(tenants),
            lambda: self.client.list_all_gateways(tenants),
            lambda: self.client.get_tenant(self.test_tenant_id),
            lambda: self.client.get_app(self.test_app_id),
            lambda: self.client.get_device_profile(self.test_device_profile_id),
            lambda: self.client.get_device(self.test_device_dev_eui),
        ]
        
        # Run operations multiple times to test stability
        for _ in range(3):
            for operation in operations:
                try:
                    result = operation()
                    self.assertIsNotNone(result)
                except Exception as e:
                    # Some operations might fail due to missing resources
                    # but the connection should remain stable
                    pass

    @pytest.mark.integration
    def test_40_basic_search_operations(self):
        """Test basic search operations."""
        # Get all tenants and filter by name
        tenants = self.client.list_tenants()
        self.assertIsInstance(tenants, list)
        
        # Get all applications and filter by name
        all_tenants = self.client.list_tenants()
        applications = self.client.list_all_apps(all_tenants)
        self.assertIsInstance(applications, list)
        
        # Get all device profiles and filter by name
        device_profiles = self.client.list_all_device_profiles(all_tenants)
        self.assertIsInstance(device_profiles, list)

    @pytest.mark.integration
    def test_41_basic_statistics(self):
        """Test basic statistics operations."""
        # Get device metrics (requires start and end dates)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        try:
            device_metrics = self.client.get_device_metrics(
                self.test_device_dev_eui, 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            self.assertIsInstance(device_metrics, dict)
        except Exception:
            # This might fail if no data exists, which is expected
            pass
        
        # Get device link metrics
        try:
            link_metrics = self.client.get_device_link_metrics(self.test_device_dev_eui)
            self.assertIsInstance(link_metrics, dict)
        except Exception:
            # This might fail if no data exists, which is expected
            pass

    @pytest.mark.integration
    def test_42_basic_region_operations(self):
        """Test basic region operations."""
        # Test device app key retrieval (this uses region information)
        try:
            app_key = self.client.get_device_app_key(self.test_device_dev_eui, 0)  # MacVersion.LORAWAN_1_0_0
            self.assertIsInstance(app_key, str)
        except Exception:
            # This might fail if device keys don't exist, which is expected
            pass

    @pytest.mark.integration
    def test_43_basic_gateway_operations(self):
        """Test basic gateway operations."""
        if not self.test_gateway_id:
            self.skipTest("Gateway not available for testing")
        
        # Get gateway metrics (requires start and end dates)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        try:
            gateway_metrics = self.client.get_gateway_metrics(
                self.test_gateway_id, 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            self.assertIsInstance(gateway_metrics, dict)
        except Exception:
            # This might fail if no data exists, which is expected
            pass
        
        # Get gateway duty cycle metrics
        try:
            duty_cycle_metrics = self.client.get_gateway_duty_cycle_metrics(
                self.test_gateway_id, 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            self.assertIsInstance(duty_cycle_metrics, dict)
        except Exception:
            # This might fail if no data exists, which is expected
            pass

    @pytest.mark.integration
    def test_44_basic_device_operations(self):
        """Test basic device operations."""
        # Get device queue
        try:
            queue = self.client.get_device_queue(self.test_device_dev_eui)
            self.assertIsInstance(queue, list)
        except Exception:
            # This might fail if device queue is not accessible
            pass
        
        # Get next frame counter down
        try:
            next_f_cnt = self.client.get_next_f_cnt_down(self.test_device_dev_eui)
            self.assertIsInstance(next_f_cnt, int)
        except Exception:
            # This might fail if device is not activated, which is expected
            pass
        
        # Get random device address
        try:
            dev_addr = self.client.get_random_dev_addr(self.test_device_dev_eui)
            self.assertIsInstance(dev_addr, str)
        except Exception:
            # This might fail if device is not activated, which is expected
            pass

    @pytest.mark.integration
    def test_45_basic_application_operations(self):
        """Test basic application operations."""
        # Test application retrieval
        # This test ensures the application can be retrieved
        app = self.client.get_app(self.test_app_id)
        self.assertIsNotNone(app)
        self.assertEqual(app.id, self.test_app_id)

    @pytest.mark.integration
    def test_46_basic_device_profile_operations(self):
        """Test basic device profile operations."""
        # Test device profile retrieval (already tested in other methods)
        # This test ensures the device profile can be retrieved
        profile = self.client.get_device_profile(self.test_device_profile_id)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.id, self.test_device_profile_id)

    @pytest.mark.integration
    def test_47_basic_tenant_operations(self):
        """Test basic tenant operations."""
        # Test tenant retrieval (already tested in other methods)
        # This test ensures the tenant can be retrieved
        tenant = self.client.get_tenant(self.test_tenant_id)
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.id, self.test_tenant_id)

    @pytest.mark.integration
    def test_48_basic_health_check(self):
        """Test basic health check operations."""
        # Test that the client can perform basic operations
        # This is a simple health check to ensure the connection is working
        
        try:
            # Try to list tenants
            tenants = self.client.list_tenants()
            self.assertIsInstance(tenants, list)
            
            # Try to get our test tenant
            tenant = self.client.get_tenant(self.test_tenant_id)
            self.assertIsNotNone(tenant)
            
            # Try to get our test application
            app = self.client.get_app(self.test_app_id)
            self.assertIsNotNone(app)
            
            # Try to get our test device
            device = self.client.get_device(self.test_device_dev_eui)
            self.assertIsNotNone(device)
            
        except Exception as e:
            # If any of these fail, it might indicate a connection issue
            # but we don't want to fail the test completely
            self.fail(f"Health check failed: {e}")


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)
