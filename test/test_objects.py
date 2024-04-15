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

class TestDeviceProfile(unittest.TestCase):
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
        with self.assertRaises(ValueError) as context:
            DeviceProfile(
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

    def test_abp_rx1_delay_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx1_delay Value error is raised when it is required
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx1_delay=None

    def test_abp_rx1_delay_setter(self):
        """
        Test DeviceProfile's abp_rx1_delay setter happy path
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #use setter
        dp.abp_rx1_delay = 3

        #Assertations
        self.assertEqual(dp._abp_rx1_delay, 3)

    def test_abp_rx1_dr_offset_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx1_dr_offset Value error is raised when it is required
        """
        # Init dp and Assert Raise
        with self.assertRaises(ValueError) as context:
            DeviceProfile(
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

    def test_abp_rx1_dr_offset_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx1_dr_offset Value error is raised when it is required
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx1_dr_offset=None

    def test_abp_rx1_dr_offset_setter(self):
        """
        Test DeviceProfile's abp_rx1_dr_offset setter happy path
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #use setter
        dp.abp_rx1_dr_offset = 3

        #Assertations
        self.assertEqual(dp._abp_rx1_dr_offset, 3)

    def test_abp_rx2_dr_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx2_dr Value error is raised when it is required
        """
        # Init dp and Assert Raise
        with self.assertRaises(ValueError) as context:
            DeviceProfile(
                name="mock",
                tenant_id="mock_id",
                region=Region.US915,
                mac_version=MacVersion.LORAWAN_1_0_0,
                reg_params_revision=RegParamsRevision.A,
                uplink_interval=3600,
                supports_otaa=False,
                abp_rx1_dr_offset=1,
                abp_rx2_freq=1,
                abp_rx1_delay=1,
                supports_class_b=False,
                supports_class_c=False)

    def test_abp_rx2_dr_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx2_dr Value error is raised when it is required
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx2_dr=None

    def test_abp_rx2_dr_offset_setter(self):
        """
        Test DeviceProfile's abp_rx2_dr setter happy path
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #use setter
        dp.abp_rx2_dr = 3

        #Assertations
        self.assertEqual(dp._abp_rx2_dr, 3)

    def test_abp_rx2_freq_prop_valueError(self):
        """
        Test DeviceProfile's abp_rx2_freq Value error is raised when it is required
        """
        # Init dp and Assert Raise
        with self.assertRaises(ValueError) as context:
            DeviceProfile(
                name="mock",
                tenant_id="mock_id",
                region=Region.US915,
                mac_version=MacVersion.LORAWAN_1_0_0,
                reg_params_revision=RegParamsRevision.A,
                uplink_interval=3600,
                supports_otaa=False,
                abp_rx1_dr_offset=1,
                abp_rx1_delay=1,
                abp_rx2_dr=1,
                supports_class_b=False,
                supports_class_c=False)

    def test_abp_rx2_freq_setter_valueError(self):
        """
        Test DeviceProfile's abp_rx2_freq Value error is raised when it is required
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.abp_rx2_freq=None

    def test_abp_rx2_freq_offset_setter(self):
        """
        Test DeviceProfile's abp_rx2_freq setter happy path
        """
        #init dp
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
            abp_rx2_freq=1,
            supports_class_b=False,
            supports_class_c=False)
        
        #use setter
        dp.abp_rx2_freq = 3

        #Assertations
        self.assertEqual(dp._abp_rx2_freq, 3)

    def test_class_b_timeout_prop_valueError(self):
        """
        Test DeviceProfile's class_b_timeout Value error is raised when it is required
        """
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
                supports_class_b=True,
                class_b_ping_slot_dr=1,
                class_b_ping_slot_freq=1,
                class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
                supports_class_c=False)

    def test_class_b_timeout_setter_valueError(self):
        """
        Test DeviceProfile's class_b_timeout Value error is raised when it is required
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_timeout=None

    def test_class_b_timeout_offset_setter(self):
        """
        Test DeviceProfile's class_b_timeout setter happy path
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #use setter
        dp.class_b_timeout = 3

        #Assertations
        self.assertEqual(dp._class_b_timeout, 3)

    def test_class_b_ping_slot_nb_k_prop_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_nb_k Value error is raised when it is required
        """
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
                supports_class_b=True,
                class_b_timeout=1,
                class_b_ping_slot_dr=1,
                class_b_ping_slot_freq=1,
                supports_class_c=False)

    def test_class_b_ping_slot_nb_k_setter_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_nb_k Value error is raised when it is required
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_ping_slot_nb_k=None

    def test_class_b_ping_slot_nb_k_offset_setter(self):
        """
        Test DeviceProfile's class_b_ping_slot_nb_k setter happy path
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #use setter
        dp.class_b_ping_slot_nb_k = ClassBPingSlot.EVERY_16SEC

        #Assertations
        self.assertEqual(dp._class_b_ping_slot_nb_k, ClassBPingSlot.EVERY_16SEC)

    def test_class_b_ping_slot_dr_prop_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_dr Value error is raised when it is required
        """
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
                supports_class_b=True,
                class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
                class_b_timeout=1,
                class_b_ping_slot_freq=1,
                supports_class_c=False)

    def test_class_b_ping_slot_dr_setter_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_dr Value error is raised when it is required
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_ping_slot_dr=None

    def test_class_b_ping_slot_dr_offset_setter(self):
        """
        Test DeviceProfile's class_b_ping_slot_dr setter happy path
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #use setter
        dp.class_b_ping_slot_dr = 3

        #Assertations
        self.assertEqual(dp._class_b_ping_slot_dr, 3)

    def test_class_b_ping_slot_freq_prop_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_freq Value error is raised when it is required
        """
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
                supports_class_b=True,
                class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
                class_b_ping_slot_dr=1,
                class_b_timeout=1,
                supports_class_c=False)

    def test_class_b_ping_slot_freq_setter_valueError(self):
        """
        Test DeviceProfile's class_b_ping_slot_freq Value error is raised when it is required
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.class_b_ping_slot_freq=None

    def test_class_b_ping_slot_freq_setter(self):
        """
        Test DeviceProfile's class_b_ping_slot_freq setter happy path
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=True,
            class_b_timeout=1,
            class_b_ping_slot_dr=1,
            class_b_ping_slot_freq=1,
            class_b_ping_slot_nb_k=ClassBPingSlot.EVERY_128SEC,
            supports_class_c=False)
        
        #use setter
        dp.class_b_ping_slot_freq = 3

        #Assertations
        self.assertEqual(dp._class_b_ping_slot_freq, 3)

    def test_class_c_timeout_prop_valueError(self):
        """
        Test DeviceProfile's class_c_timeout Value error is raised when it is required
        """
        # Init dp and Assert Raise
        with self.assertRaises(ValueError) as context:
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

    def test_class_c_timeout_valueError(self):
        """
        Test DeviceProfile's class_c_timeout Value error is raised when it is required
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=True,
            class_c_timeout=1)
        
        #Assert raise
        with self.assertRaises(ValueError) as context:
            dp.class_c_timeout=None

    def test_class_c_timeout_setter(self):
        """
        Test DeviceProfile's class_c_timeout setter happy path
        """
        #init dp
        dp = DeviceProfile(
            name="mock",
            tenant_id="mock_id",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_0,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=True,
            class_c_timeout=1)
        
        #use setter
        dp.class_c_timeout = 3

        #Assertations
        self.assertEqual(dp._class_c_timeout, 3)

    def test_str_method(self):
        """
        Test DeviceProfile's conversion to string
        """
        mock_dp = DeviceProfile(
            name="mock",
            tenant_id="mock",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_2,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False,
            id="mock_id")

        # Assertations
        self.assertEqual(str(mock_dp), "mock_id")

    def test_str_method_no_id(self):
        """
        Test DeviceProfile's conversion to string when the id is empty
        """
        mock_dp = DeviceProfile(
            name="mock",
            tenant_id="mock",
            region=Region.US915,
            mac_version=MacVersion.LORAWAN_1_0_2,
            reg_params_revision=RegParamsRevision.A,
            uplink_interval=3600,
            supports_otaa=True,
            supports_class_b=False,
            supports_class_c=False)

        #Assert Raise
        with self.assertRaises(RuntimeError) as context:
            str(mock_dp)

class TestDevice(unittest.TestCase):
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
            Device("mock_name", "mock_deveui", "mock_app_id", "mock_dp_id", tags=mock_tags)

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
            Device("mock_name", "mock_deveui", "mock_app_id", "mock_dp_id", variables=mock_vars)

    def test_str_method(self):
        """
        Test Device's conversion to string
        """
        mock_device = Device("mock_name", "mock_deveui", "mock_app_id", "mock_dp_id")

        # Assertations
        self.assertEqual(str(mock_device), "mock_deveui")

if __name__ == "__main__":
    unittest.main()