from unittest.mock import Mock

class MessageTemplate:
    def __init__(self):
        self.sample = """{
            "deduplicationId": "3ac7e3c4-4401-4b8d-9386-a5c902f9202d",
            "time": "2022-07-18T09:34:15.775023242+00:00",
            "payload": "",
            "deviceInfo": {
                "tenantId": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
                "tenantName": "ChirpStack",
                "applicationId": "17c82e96-be03-4f38-aef3-f83d48582d97",
                "applicationName": "Test application",
                "deviceProfileId": "14855bf7-d10d-4aee-b618-ebfcb64dc7ad",
                "deviceProfileName": "Test device-profile",
                "deviceName": "Test device",
                "devEui": "0101010101010101",
                "tags": {
                    "key": "value"
                }
            },
            "devAddr": "00189440",
            "dr": 1,
            "fPort": 1,
            "data": "qg==",
            "rxInfo": [{
                "gatewayId": "0016c001f153a14c",
                "uplinkId": 4217106255,
                "rssi": -36,
                "snr": 10.5,
                "context": "E3OWOQ==",
                "metadata": {
                    "region_name": "eu868",
                    "region_common_name": "EU868"
                }
            }],
            "txInfo": {
                "frequency": 867100000,
                "modulation": {
                    "lora": {
                        "bandwidth": 125000,
                        "spreadingFactor": 11,
                        "codeRate": "CR_4_5"
                    }
                }
            }
        }"""

class Mock_ChirpstackClient_Methods:

    def __init__(self, deveui: str):
        self.deveui = deveui
        self.get_device_ret_val = self.__Mock_gd_ret_val()
        self.get_device_profile_ret_val = self.__Mock_gdp_ret_val()
        self.get_device_activation_ret_val = self.__Mock_gda_ret_val() 
        self.get_device_app_key_ret_val = self.__Mock_gdak_ret_val()

    def edit_deveui(self, deveui: str):
        """
        Edit the deveui on all methods' return values
        """
        self.deveui = deveui
        self.get_device_ret_val = self.__Mock_gd_ret_val()
        self.get_device_activation_ret_val = self.__Mock_gda_ret_val()
        self.get_device_app_key_ret_val = self.__Mock_gdak_ret_val()
        return

    def __Mock_gd_ret_val(self):
        """
        Mock ChirpstackClient.get_device() return value
        """
        val = Mock()
        val.device = Mock()
        val.device.dev_eui = self.deveui
        val.device.name = "mock device"
        val.device.application_id = "ac81e18b-1925-47f9-839a-27d999a8af11"
        val.device.device_profile_id = "cf2aec2f-03e1-4a60-a32c-0faeef5730c1"
        val.created_at = Mock()
        val.created_at.seconds = 1695922619
        val.created_at.nanos = 943604000
        val.updated_at = Mock()
        val.updated_at.seconds = 1695923278
        val.updated_at.nanos = 943604000
        val.last_seen_at = Mock()
        val.last_seen_at.seconds = 1700675528
        val.last_seen_at.nanos = 993262000
        val.device_status = Mock()
        val.device_status.margin = 11
        val.device_status.external_power_source = True
        val.device_status.battery_level = -1

        return val

    def __Mock_gdp_ret_val(self):
        """
        Mock ChirpstackClient.get_device_profile() return value
        """
        val = Mock()
        val.device_profile = Mock()
        val.device_profile.id = "cf2aec2f-03e1-4a60-a32c-0faeef5730d9"
        val.device_profile.tenant_id = "52f14cd4-c6f1-4fbd-8f87-4025e1d49241"
        val.device_profile.name = "Mock Profile"
        val.device_profile.description = "this is a mock profile"
        val.device_profile.region = 2 #2 = US915
        val.device_profile.mac_version = 2 #2 = LORAWAN_1_0_2
        val.device_profile.reg_params_revision = 1 #1 = B
        val.device_profile.adr_algorithm_id = "default"
        val.device_profile.payload_codec_runtime = 1 #1 = JS
        val.device_profile.payload_codec_script = "var=example\nreturn var;"
        val.device_profile.flush_queue_on_activate = True
        val.device_profile.uplink_interval = 1020
        val.device_profile.device_status_req_interval = 10
        val.device_profile.supports_otaa = True
        val.device_profile.measurements = None
        val.device_profile.auto_detect_measurements = True
        val.created_at = Mock()
        val.created_at.seconds = 1694716861
        val.created_at.nanos = 633915000
        val.updated_at = Mock()
        val.updated_at.seconds = 1704991331
        val.updated_at.nanos = 511071000

        return val

    def __Mock_gda_ret_val(self):
        """
        Mock ChirpstackClient.get_device_activation() return value
        """
        val = Mock()
        val.device_activation = Mock()
        val.device_activation.dev_eui = self.deveui
        val.device_activation.dev_addr = "00d65cd1"
        val.device_activation.app_s_key = "6e0f556d5975b872d744aee2c1239d5"
        val.device_activation.nwk_s_enc_key = "123456785975b872d744aee2a1239d12"
        val.device_activation.s_nwk_s_int_key = "1234567891023s89s53122s5678d9"
        val.device_activation.f_nwk_s_int_key = "23655489416521d5615a61651d652"
        val.device_activation.f_cnt_up = 200
        val.device_activation.n_f_cnt_down = 23
        val.device_activation.a_f_cnt_down = 10

        return val

    def __Mock_gdak_ret_val(self):
        """
        Mock ChirpstackClient.get_device_app_key() return value
        """
        val = Mock()
        val.device_keys = Mock()
        val.device_keys.dev_eui = self.deveui
        val.device_keys.nwk_key = "7e19d51b647b123dd123c484707aadc1"
        val.device_keys.app_key = "00000000000000000000000000000000"
        val.created_at = Mock()
        val.created_at.seconds = 1689015468
        val.created_at.nanos = 197740000
        val.updated_at = Mock()
        val.updated_at.seconds = 1700603333
        val.updated_at.nanos = 648973000

        return val