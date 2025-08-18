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
from unittest.mock import patch
from chirpstack_api_wrapper import ChirpstackClient
from chirpstack_api_wrapper.objects import (
    Application, Tenant, DeviceProfile, Device, Gateway, Region, 
    MacVersion, RegParamsRevision, CodecRuntime, AdrAlgorithm
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
            
            # 5. Create test gateway (skip if not supported by server)
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
    def test_16_device_keys(self):
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
    def test_18_verify_test_records_exist(self):
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


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)
