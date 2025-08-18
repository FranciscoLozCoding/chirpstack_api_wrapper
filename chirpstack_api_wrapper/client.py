"""Abstraction layer over chirpstack_api"""
import grpc
import logging
import sys
import time
import requests
from google.protobuf.json_format import ParseDict
from google.protobuf import empty_pb2
from chirpstack_api import api
from chirpstack_api_wrapper.objects import *

#Pagination
LIMIT = 100 #Max number of records to return in the result-set.
OFFSET = LIMIT #Offset in the result-set (setting offset=limit goes to the next set of records aka next page)

class ChirpstackClient:
    """
    Chirpstack client to call Api(s).

    Parameters
    ----------
    - email: The email of the Account that will be used to call the Api(s).
    - password: The password of the Account that will be used to call the Api(s).
    - api_endpoint: The Chirpstack grpc api endpoint (usually port 8080).
    - login_on_init (optional): The instance will try to login when initialized.
    """
    def __init__(self, email:str, password:str, api_endpoint:str, login_on_init: bool = True):
        """Constructor method to initialize a ChirpstackClient object."""   
        self.server = api_endpoint
        self.channel = grpc.insecure_channel(self.server)
        self.email = email
        self.password = password
        self.login_on_init = login_on_init
        if self.login_on_init:
            self.auth_token = self.login()
        else:
            self.auth_token = None

        
    def _get_stub(self, service_name: str):
        """
        Return the gRPC stub class instance for *service_name*.

        Parameters
        ----------
        service_name : str
            Name of the gRPC service, e.g. ``"DeviceService"``.

        Example
        -------
        stub = self._get_stub("DeviceService")  # returns api.DeviceServiceStub
        """
        try:
            stub_cls = getattr(api, f"{service_name}Stub")
            return stub_cls(self.channel)
        except AttributeError as err:
            raise ValueError(f"Unknown service '{service_name}'") from err

    def _call_rpc(
        self,
        service_name: str,
        rpc_name: str,
        request_type: str | None = None,
        params: dict | None = None,
    ):
        """
        Generic RPC invoker used by all convenience wrappers.

        * Automatically attaches JWT bearer token.
        * Accepts params as dict → converted to protobuf with ParseDict.
        * If `request_type == "google.protobuf.Empty"` or params is ``None``,
          the request sent is ``google.protobuf.Empty()``.

        Parameters
        ----------
        service_name : str
            Name of the gRPC service, e.g. ``"DeviceService"``.
        rpc_name : str
            Name of the RPC method, e.g. ``"Get"``.
        request_type : str, optional
            Name of the request message type, e.g. ``"GetDeviceRequest"``.
            If ``None``, it is assumed to be ``"{rpc_name}Request"``.
        params : dict, optional
            Fields to set in the request message.
        """
        if self.auth_token is None:
            self.login()

        client = self._get_stub(service_name)
        rpc_fn = getattr(client, rpc_name)

        # Determine request message class
        if request_type is None:
            request_type = f"{rpc_name}Request"

        if request_type == "google.protobuf.Empty":
            req_msg = empty_pb2.Empty()
        else:
            try:
                req_cls = getattr(api, request_type)
            except AttributeError as err:
                raise ValueError(f"No message type '{request_type}'") from err
            req_msg = ParseDict(params or {}, req_cls())

        metadata = [("authorization", f"Bearer {self.auth_token}")]
        try:
            return rpc_fn(req_msg, metadata=metadata)
        except grpc.RpcError as e:
            # transparently refresh if token expired
            return self.refresh_token(e, self._call_rpc,
                                      service_name, rpc_name,
                                      request_type, params)

    def _list_with_pagination(
        self,
        service_name: str,
        request_dict: dict,
        request_type: str | None = None,
        result_field: str = "result",
        limit: int = LIMIT,
    ) -> list:
        """
        Aggregate all pages for any <Service>.List RPC.

        Parameters
        ----------
        service_name : str
            Name of the gRPC service, e.g. ``"DeviceService"``.
        request_dict : dict
            Fields for the ``List*Request`` message (offset/limit filled in here).
        result_field : str
            Usually ``"result"`` – the repeated field in the List response.
        limit : int
            Page size. Uses global ``LIMIT`` constant by default.
        """
        records: list = []
        offset = 0
        while True:
            request_dict.update(limit=limit, offset=offset)
            resp = self._call_rpc(service_name, "List", request_type=request_type, params=request_dict)
            records.extend(getattr(resp, result_field))
            if len(records) >= resp.total_count:
                break
            offset += limit
        return records

    def login(self) -> str:
        """
        Login to the server to get jwt auth token.
        """
        client = api.InternalServiceStub(self.channel)

        # Construct the Login request.
        req = api.LoginRequest()
        req.email = self.email
        req.password = self.password

        # Send the Login request.
        logging.info(f"ChirpstackClient.login(): connecting {self.server}...")
        try:
            resp = client.Login(req)
        except grpc.RpcError as e:
            # Handle the exception here
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.UNAVAILABLE:
                logging.error(f"ChirpstackClient.login(): Service is unavailable. This might be a DNS resolution issue. - {details}")
            else:
                logging.error(f"ChirpstackClient.login(): An error occurred with status code {status_code} - {details}")

            # Exit with a non-zero status code to indicate failure
            sys.exit(1)
        except Exception as e:
            # Handle other exceptions if needed
            logging.error(f"ChirpstackClient.login(): An error occurred: {e}")

            # Exit with a non-zero status code to indicate failure
            sys.exit(1)
                
        logging.info("ChirpstackClient.login(): Connected to Chirpstack Server")

        return resp.jwt

    def ping(self) -> bool:
        """
        Checks if the server is reachable by sending a request. Returns True if reachable, False otherwise.
        """
        try:
            response = requests.get(f"http://{self.server}")
            if response.status_code >= 200 and response.status_code < 300:
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"ChirpstackClient.ping(): {e}")
            return False

    def list_all_devices(self, apps: list[Application]) -> list[Device]:
        """
        List all devices.

        Parameters
        ----------
        - apps: List of Application objects from ChirpstackClient.list_all_apps().

        Returns
        -------
        - List of Device objects.
        """
        devices = []
        for app in apps:
            # First list the Device summary items for this application
            list_response = self._list_with_pagination(
                "DeviceService",
                {"application_id": app.id},
                "ListDevicesRequest"
            )
            
            # For each summary item, fetch the full Device using Get
            for device_item in list_response:
                try:
                    get_resp = self._call_rpc(
                        "DeviceService",
                        "Get",
                        request_type="GetDeviceRequest",
                        params={"dev_eui": getattr(device_item, "dev_eui", "")}
                    )
                    if get_resp and hasattr(get_resp, "device"):
                        devices.append(Device.from_grpc(get_resp.device))
                except grpc.RpcError as e:
                    logging.error(
                        f"ChirpstackClient.list_all_devices(): Failed to fetch full device for dev_eui={getattr(device_item, 'dev_eui', '')} - {e.code()} {e.details()}"
                    )
                    continue
        return devices

    def list_all_apps(self, tenants: list[Tenant]) -> list[Application]:
        """
        List all apps.

        Parameters
        ----------
        - tenants: List of Tenant objects from ChirpstackClient.list_tenants().

        Returns
        -------
        - List of Application objects.
        """
        apps = []
        for t in tenants:
            # First list the Application summary items for this tenant
            list_response = self._list_with_pagination(
                "ApplicationService",
                {"tenant_id": t.id},
                "ListApplicationsRequest"
            )
            
            # For each summary item, fetch the full Application using Get
            for app_item in list_response:
                try:
                    get_resp = self._call_rpc(
                        "ApplicationService",
                        "Get",
                        request_type="GetApplicationRequest",
                        params={"id": getattr(app_item, "id", "")}
                    )
                    if get_resp and hasattr(get_resp, "application"):
                        apps.append(Application.from_grpc(get_resp.application))
                except grpc.RpcError as e:
                    logging.error(
                        f"ChirpstackClient.list_all_apps(): Failed to fetch full application for id={getattr(app_item, 'id', '')} - {e.code()} {e.details()}"
                    )
                    continue
        return apps

    def list_tenants(self) -> list[Tenant]:
        """
        List all tenants.
        
        Returns
        -------
        - List of Tenant objects.
        """
        # First list the Tenant summary items
        list_response = self._list_with_pagination("TenantService", {}, "ListTenantsRequest")
        tenants = []
        
        # For each summary item, fetch the full Tenant using Get
        for tenant_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "TenantService",
                    "Get",
                    request_type="GetTenantRequest",
                    params={"id": getattr(tenant_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "tenant"):
                    tenants.append(Tenant.from_grpc(get_resp.tenant))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_tenants(): Failed to fetch full tenant for id={getattr(tenant_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return tenants

    def get_app(self, app_id: Application | str) -> Application | None:
        """
        Get application.

        Parameters
        ----------
        - app_id: unique identifier of the app.
            Passing in an Application object will also work.

        Returns
        -------
        - Application object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "Get",
                                     "GetApplicationRequest", {"id": str(app_id)})
            
            if not response or not hasattr(response, 'application'):
                return None
            
            return Application.from_grpc(response.application)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_app(): Application {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_app(): An error occurred with status code {status_code} - {details}")
            return None

    def get_device(self, dev_eui: Device | str) -> Device | None:
        """
        Get device.

        Parameters
        ----------
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.

        Returns
        -------
        - Device object or None if not found.
        """
        try:
            response = self._call_rpc("DeviceService", "Get",
                                     "GetDeviceRequest", {"dev_eui": str(dev_eui)})
            
            if not response or not hasattr(response, 'device'):
                return None
            
            return Device.from_grpc(response.device)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device(): Device {dev_eui} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_device(): An error occurred with status code {status_code} - {details}")
            return None
        
    def get_device_profile(self, device_profile_id: DeviceProfile | str) -> DeviceProfile | None:
        """
        Get device profile.

        Parameters
        ----------
        - device_profile_id: unique identifier of the device profile.
            Passing in a Device Profile object will also work.

        Returns
        -------
        - DeviceProfile object or None if not found.
        """
        try:
            response = self._call_rpc("DeviceProfileService", "Get",
                                     "GetDeviceProfileRequest", {"id": str(device_profile_id)})
            
            if not response or not hasattr(response, 'device_profile'):
                return None
            
            return DeviceProfile.from_grpc(response.device_profile)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device_profile(): Device Profile {device_profile_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_device_profile(): An error occurred with status code {status_code} - {details}")
            return None

    def get_device_app_key(self, deveui: Device | str, lw_v: MacVersion | int) -> str:
        """
        Get device Application key (Only OTAA).

        Parameters
        ----------
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.
        - lw_v: The lorawan version the device is using. 
            input directly from ChirpstackClient.get_device_profile() output or use MacVersion Object.
        """
        try:
            resp = self._call_rpc("DeviceService", "GetKeys",
                                 "GetDeviceKeysRequest", {"dev_eui": str(deveui)})
            # what key to return is based on lorawan version (For LoRaWAN 1.1 devices return app_key)
            # < 5 is lorawan 1.0.x
            return resp.device_keys.nwk_key if lw_v < 5 else resp.device_keys.app_key
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device_app_key(): The device key does not exist. It is possible that the device is using ABP which does not use an application key - {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self._get_device_app_key, deveui, lw_v)
            else:
                logging.error(f"ChirpstackClient.get_device_app_key(): An error occurred with status code {status_code} - {details}")
            return ""

    def get_device_activation(self, deveui: Device | str) -> DeviceActivation | None:
        """
        Get Activation returns the current activation details of the device (OTAA or ABP).

        Parameters
        ----------
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.

        Returns
        -------
        - DeviceActivation object or None if not found.
        """
        try:
            response = self._call_rpc("DeviceService", "GetActivation",
                                     "GetDeviceActivationRequest", {"dev_eui": str(deveui)})
            
            return DeviceActivation.from_grpc(response.device_activation)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device_activation(): Device Activation {deveui} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_device_activation(): An error occurred with status code {status_code} - {details}")
            return None

    def get_gateway(self, gateway_id: Gateway | str) -> Gateway | None:
        """
        Get gateway.

        Parameters
        ----------
        - gateway_id (EUI64): Unique identifier for the gateway.
            Passing in a Gateway object will also work.

        Returns
        -------
        - Gateway object or None if not found.
        """
        try:
            response = self._call_rpc("GatewayService", "Get",
                                     "GetGatewayRequest", {"gateway_id": str(gateway_id)})
            
            if not response or not hasattr(response, 'gateway'):
                return None
            
            return Gateway.from_grpc(response.gateway)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_gateway(): Gateway {gateway_id} not found - {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self._get_gateway, gateway_id)
            else:
                logging.error(f"ChirpstackClient.get_gateway(): An error occurred with status code {status_code} - {details}")
            return None
    
    def create_app(self,app:Application) -> None:
        """
        Create an Application.

        Parameters
        ----------
        - app: The app record to create.
        """
        if not isinstance(app, Application):
            raise TypeError("Expected Application object")
        
        resp = self._call_rpc("ApplicationService", "Create",
                                    "CreateApplicationRequest", {
                                        "application": {
                                            "name": getattr(app, 'name', ''),
                                            "description": getattr(app, 'description', ''),
                                            "tenant_id": getattr(app, 'tenant_id', ''),
                                            "tags": getattr(app, 'tags', {})
                                        }
                                    })
        app.id = resp.id #attach chirp generated uuid to app object
        return
    
    def create_device_profile(self,device_profile:DeviceProfile) -> None:
        """
        Create a Device Profile.

        Parameters
        ----------
        - device_profile: The device profile record to create.
        """
        if not isinstance(device_profile, DeviceProfile):
            raise TypeError("Expected DeviceProfile object")
        
        resp = self._call_rpc("DeviceProfileService", "Create",
                                    "CreateDeviceProfileRequest", {
                                        "device_profile": {
                                            "name": getattr(device_profile, 'name', ''),
                                            "tenant_id": getattr(device_profile, 'tenant_id', ''),
                                            "region": getattr(device_profile, 'region', ''),
                                            "mac_version": getattr(device_profile, 'mac_version', ''),
                                            "reg_params_revision": getattr(device_profile, 'reg_params_revision', ''),
                                            "uplink_interval": getattr(device_profile, 'uplink_interval', 0),
                                            "supports_otaa": getattr(device_profile, 'supports_otaa', False),
                                            "abp_rx1_delay": getattr(device_profile, 'abp_rx1_delay', 0),
                                            "abp_rx1_dr_offset": getattr(device_profile, 'abp_rx1_dr_offset', 0),
                                            "abp_rx2_dr": getattr(device_profile, 'abp_rx2_dr', 0),
                                            "abp_rx2_freq": getattr(device_profile, 'abp_rx2_freq', 0),
                                            "supports_class_b": getattr(device_profile, 'supports_class_b', False),
                                            "class_b_timeout": getattr(device_profile, 'class_b_timeout', 0),
                                            "class_b_ping_slot_periodicity": getattr(device_profile, 'class_b_ping_slot_periodicity', 0),
                                            "class_b_ping_slot_dr": getattr(device_profile, 'class_b_ping_slot_dr', 0),
                                            "class_b_ping_slot_freq": getattr(device_profile, 'class_b_ping_slot_freq', 0),
                                            "supports_class_c": getattr(device_profile, 'supports_class_c', False),
                                            "class_c_timeout": getattr(device_profile, 'class_c_timeout', 0),
                                            "description": getattr(device_profile, 'description', ''),
                                            "payload_codec_runtime": getattr(device_profile, 'payload_codec_runtime', ''),
                                            "payload_codec_script": getattr(device_profile, 'payload_codec_script', ''),
                                            "flush_queue_on_activate": getattr(device_profile, 'flush_queue_on_activate', False),
                                            "device_status_req_interval": getattr(device_profile, 'device_status_req_interval', 0),
                                            "auto_detect_measurements": getattr(device_profile, 'auto_detect_measurements', False),
                                            "allow_roaming": getattr(device_profile, 'allow_roaming', False),
                                            "adr_algorithm_id": getattr(device_profile, 'adr_algorithm_id', ''),
                                            "rx1_delay": getattr(device_profile, 'rx1_delay', 0),
                                            "app_layer_params": getattr(device_profile, 'app_layer_params', {}).to_dict(),
                                            "region_config_id": getattr(device_profile, 'region_config_id', ''),
                                            "is_relay": getattr(device_profile, 'is_relay', False),
                                            "is_relay_ed": getattr(device_profile, 'is_relay_ed', False),
                                            "relay_ed_relay_only": getattr(device_profile, 'relay_ed_relay_only', False),
                                            "relay_enabled": getattr(device_profile, 'relay_enabled', False),
                                            "relay_cad_periodicity": getattr(device_profile, 'relay_cad_periodicity', ''),
                                            "relay_default_channel_index": getattr(device_profile, 'relay_default_channel_index', 0),
                                            "relay_second_channel_freq": getattr(device_profile, 'relay_second_channel_freq', 0),
                                            "relay_second_channel_dr": getattr(device_profile, 'relay_second_channel_dr', 0),
                                            "relay_second_channel_ack_offset": getattr(device_profile, 'relay_second_channel_ack_offset', ''),
                                            "relay_ed_activation_mode": getattr(device_profile, 'relay_ed_activation_mode', ''),
                                            "relay_ed_smart_enable_level": getattr(device_profile, 'relay_ed_smart_enable_level', 0),
                                            "relay_ed_back_off": getattr(device_profile, 'relay_ed_back_off', 0),
                                            "relay_ed_uplink_limit_bucket_size": getattr(device_profile, 'relay_ed_uplink_limit_bucket_size', 0),
                                            "relay_ed_uplink_limit_reload_rate": getattr(device_profile, 'relay_ed_uplink_limit_reload_rate', 0),
                                            "relay_join_req_limit_reload_rate": getattr(device_profile, 'relay_join_req_limit_reload_rate', 0),
                                            "relay_notify_limit_reload_rate": getattr(device_profile, 'relay_notify_limit_reload_rate', 0),
                                            "relay_global_uplink_limit_reload_rate": getattr(device_profile, 'relay_global_uplink_limit_reload_rate', 0),
                                            "relay_overall_limit_reload_rate": getattr(device_profile, 'relay_overall_limit_reload_rate', 0),
                                            "relay_join_req_limit_bucket_size": getattr(device_profile, 'relay_join_req_limit_bucket_size', 0),
                                            "relay_notify_limit_bucket_size": getattr(device_profile, 'relay_notify_limit_bucket_size', 0),
                                            "relay_global_uplink_limit_bucket_size": getattr(device_profile, 'relay_global_uplink_limit_bucket_size', 0),
                                            "relay_overall_limit_bucket_size": getattr(device_profile, 'relay_overall_limit_bucket_size', 0),
                                            "measurements": getattr(device_profile, 'measurements', {}),
                                            "tags": getattr(device_profile, 'tags', {})
                                        }
                                    })
        device_profile.id = resp.id #attach chirp generated uuid to device profile object
        return

    def create_device(self,device:Device) -> None:
        """
        Create a Device.

        Parameters
        ----------
        - device: The device record to create.
        """
        if not isinstance(device, Device):
            raise TypeError("Expected Device object")
        resp = self._call_rpc("DeviceService", "Create",
                                    "CreateDeviceRequest", {
                                        "device": {
                                            "name": getattr(device, 'name', ''),
                                            "dev_eui": getattr(device, 'dev_eui', ''),
                                            "application_id": getattr(device, 'application_id', ''),
                                            "device_profile_id": getattr(device, 'device_profile_id', ''),
                                            "join_eui": getattr(device, 'join_eui', ''),
                                            "description": getattr(device, 'description', ''),
                                            "skip_fcnt_check": getattr(device, 'skip_fcnt_check', False),
                                            "is_disabled": getattr(device, 'is_disabled', False),
                                            "tags": getattr(device, 'tags', {}),
                                            "variables": getattr(device, 'variables', {})
                                        }
                                    })
        return

    def create_device_keys(self,device_keys:DeviceKeys) -> None:
        """
        Create device keys.

        Parameters
        ----------
        - device_keys: The device keys record to create.
        """
        if not isinstance(device_keys, DeviceKeys):
            raise TypeError("Expected DeviceKeys object")
        
        return self._call_rpc("DeviceService", "CreateKeys",
                                "CreateDeviceKeysRequest", {
                                "device_keys": {
                                    "dev_eui": getattr(device_keys, 'dev_eui', ''),
                                    "nwk_key": getattr(device_keys, 'nwk_key', ''),
                                    "app_key": getattr(device_keys, 'app_key', '')
                                }
                                })
    
    def create_gateway(self,gateway:Gateway) -> None:
        """
        Create a Gateway.

        Parameters
        ----------
        - gateway: The gateway record to create.
        """
        if not isinstance(gateway, Gateway):
            raise TypeError("Expected Gateway object")
        
        self._call_rpc("GatewayService", "Create",
                                    "CreateGatewayRequest", {
                                        "gateway": {
                                            "gateway_id": getattr(gateway, 'gateway_id', ''),
                                            "name": getattr(gateway, 'name', ''),
                                            "description": getattr(gateway, 'description', ''),
                                            "tenant_id": getattr(gateway, 'tenant_id', ''),
                                            "stats_interval": gateway.stats_interval,
                                            "tags": getattr(gateway, 'tags', {}),
                                            "location": getattr(gateway, 'location', None),
                                            "metadata": getattr(gateway, 'metadata', {})
                                        }
                                    })
        return

    def delete_app(self, app_id: Application | str) -> None:
        """
        Delete an Application.

        Parameters
        ----------
        - app_id: unique identifier of the application.
            Passing in an Application object will also work.
        """
        return self._call_rpc("ApplicationService", "Delete",
                             "DeleteApplicationRequest", {"id": str(app_id)})

    def delete_device(self, dev_eui: Device | str) -> None:
        """
        Delete a Device.

        Parameters
        ----------
        - dev_eui: The unique identifier of the device to delete.
            Passing in a Device object will also work.
        """
        return self._call_rpc("DeviceService", "Delete",
                             "DeleteDeviceRequest", {"dev_eui": str(dev_eui)})

    def delete_device_profile(self, device_profile_id: DeviceProfile | str) -> None:
        """
        Delete a Device Profile.

        Parameters
        ----------
        - device_profile_id: unique identifier of the device profile.
            Passing in a Device Profile object will also work.
        """
        return self._call_rpc("DeviceProfileService", "Delete",
                             "DeleteDeviceProfileRequest", {"id": str(device_profile_id)})

    def delete_gateway(self, gateway_id: Gateway | str) -> None:
        """
        Delete a Gateway.

        Parameters
        ----------
        - gateway_id (EUI64): Unique identifier for the gateway.
            Passing in a Gateway object will also work.
        """
        return self._call_rpc("GatewayService", "Delete",
                             "DeleteGatewayRequest", {"gateway_id": str(gateway_id)})

    def update_app(self, app: Application) -> None:
        """
        Update an Application.

        Parameters
        ----------
        - app: The app record to update.
        """
        if not isinstance(app, Application):
            raise TypeError("Expected Application object")
        
        return self._call_rpc("ApplicationService", "Update",
                             "UpdateApplicationRequest", {
                                 "application": {
                                     "id": getattr(app, 'id', ''),
                                     "name": getattr(app, 'name', ''),
                                     "description": getattr(app, 'description', ''),
                                     "tenant_id": getattr(app, 'tenant_id', ''),
                                     "tags": getattr(app, 'tags', {})
                                 }
                             })

    def list_device_profiles_for_app(self, app_id: Application | str) -> list[DeviceProfile]:
        """
        List device profiles for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - List of DeviceProfile objects.
        """
        # First list the DeviceProfile summary items for this application
        list_response = self._list_with_pagination("ApplicationService", 
                                                {"application_id": str(app_id)}, 
                                                "ListDeviceProfilesRequest", 
                                                "result")
        device_profiles = []
        
        # For each summary item, fetch the full DeviceProfile using Get
        for profile_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "DeviceProfileService",
                    "Get",
                    request_type="GetDeviceProfileRequest",
                    params={"id": getattr(profile_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "device_profile"):
                    device_profiles.append(DeviceProfile.from_grpc(get_resp.device_profile))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_device_profiles_for_app(): Failed to fetch full device profile for id={getattr(profile_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return device_profiles

    def list_device_tags_for_app(self, app_id: Application | str) -> list[dict]:
        """
        List device tags for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - List of device tag dictionaries.
        """
        api_response = self._list_with_pagination("ApplicationService", 
                                                {"application_id": str(app_id)}, 
                                                "ListDeviceTagsRequest", 
                                                "result")
        device_tags = []
        for tag_item in api_response:
            device_tag = {
                'dev_eui': getattr(tag_item, 'dev_eui', ''),
                'tags': dict(getattr(tag_item, 'tags', {}))
            }
            device_tags.append(device_tag)
        return device_tags

    def list_integrations_for_app(self, app_id: Application | str) -> list[dict]:
        """
        List integrations for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - List of integration dictionaries.
        """
        api_response = self._list_with_pagination("ApplicationService", 
                                                {"application_id": str(app_id)}, 
                                                "ListIntegrationsRequest", 
                                                "result")
        integrations = []
        for integration_item in api_response:
            integration = {
                'id': getattr(integration_item, 'id', ''),
                'kind': getattr(integration_item, 'kind', ''),
                'created_at': getattr(integration_item, 'created_at', ''),
                'updated_at': getattr(integration_item, 'updated_at', '')
            }
            integrations.append(integration)
        return integrations

    def create_http_integration(self, integration: HttpIntegration) -> None:
        """
        Create an HTTP integration for an application.

        Parameters
        ----------
        - integration: The HTTP integration record to create.
        """
        if not isinstance(integration, HttpIntegration):
            raise TypeError("Expected HttpIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateHttpIntegration",
                             "CreateHttpIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "headers": getattr(integration, 'headers', {}),
                                     "url": getattr(integration, 'url', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_http_integration(self, app_id: str) -> HttpIntegration | None:
        """
        Get HTTP integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - HttpIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetHttpIntegration",
                                     "GetHttpIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            return HttpIntegration.from_grpc(response.integration)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_http_integration(): HTTP integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_http_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_http_integration(self, integration: HttpIntegration) -> None:
        """
        Update an HTTP integration for an application.

        Parameters
        ----------
        - integration: The HTTP integration record to update.
        """
        if not isinstance(integration, HttpIntegration):
            raise TypeError("Expected HttpIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateHttpIntegration",
                             "UpdateHttpIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "headers": getattr(integration, 'headers', {}),
                                     "url": getattr(integration, 'url', '')
                                 }
                             })

    def delete_http_integration(self, app_id: str) -> None:
        """
        Delete HTTP integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteHttpIntegration",
                             "DeleteHttpIntegrationRequest", {"application_id": app_id})

    def create_influxdb_integration(self, integration: InfluxDbIntegration) -> None:
        """
        Create an InfluxDB integration for an application.

        Parameters
        ----------
        - integration: The InfluxDB integration record to create.
        """
        if not isinstance(integration, InfluxDbIntegration):
            raise TypeError("Expected InfluxDbIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateInfluxDbIntegration",
                             "CreateInfluxDbIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "endpoint": getattr(integration, 'endpoint', ''),
                                     "token": getattr(integration, 'token', ''),
                                     "organization": getattr(integration, 'organization', ''),
                                     "bucket": getattr(integration, 'bucket', ''),
                                     "version": getattr(integration, 'version', ''),
                                     "precision": getattr(integration, 'precision', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_influxdb_integration(self, app_id: str) -> InfluxDbIntegration | None:
        """
        Get InfluxDB integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - InfluxDbIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetInfluxDbIntegration",
                                     "GetInfluxDbIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            # Import the enums here to avoid circular imports
            from chirpstack_api_wrapper.objects import InfluxDbVersion, InfluxDbPrecision
            
            # Find the enum values by comparing the response values
            version_enum = next((v for v in InfluxDbVersion if v.value == response.integration.version), InfluxDbVersion.INFLUXDB_1)
            precision_enum = next((p for p in InfluxDbPrecision if p.value == response.integration.precision), InfluxDbPrecision.S)
            
            integration = InfluxDbIntegration(
                application_id=response.integration.application_id,
                endpoint=response.integration.endpoint,
                token=response.integration.token,
                organization=response.integration.organization,
                bucket=response.integration.bucket,
                version=version_enum,
                precision=precision_enum,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_influxdb_integration(): InfluxDB integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_influxdb_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_influxdb_integration(self, integration: InfluxDbIntegration) -> None:
        """
        Update an InfluxDB integration for an application.

        Parameters
        ----------
        - integration: The InfluxDB integration record to update.
        """
        if not isinstance(integration, InfluxDbIntegration):
            raise TypeError("Expected InfluxDbIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateInfluxDbIntegration",
                             "UpdateInfluxDbIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "endpoint": getattr(integration, 'endpoint', ''),
                                     "token": getattr(integration, 'token', ''),
                                     "organization": getattr(integration, 'organization', ''),
                                     "bucket": getattr(integration, 'bucket', ''),
                                     "version": getattr(integration, 'version', ''),
                                     "precision": getattr(integration, 'precision', '')
                                 }
                             })

    def delete_influxdb_integration(self, app_id: str) -> None:
        """
        Delete InfluxDB integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteInfluxDbIntegration",
                             "DeleteInfluxDbIntegrationRequest", {"application_id": app_id})

    def create_thingsboard_integration(self, integration: ThingsBoardIntegration) -> None:
        """
        Create a ThingsBoard integration for an application.

        Parameters
        ----------
        - integration: The ThingsBoard integration record to create.
        """
        if not isinstance(integration, ThingsBoardIntegration):
            raise TypeError("Expected ThingsBoardIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateThingsBoardIntegration",
                             "CreateThingsBoardIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "server": getattr(integration, 'server', ''),
                                     "token": getattr(integration, 'token', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_thingsboard_integration(self, app_id: str) -> ThingsBoardIntegration | None:
        """
        Get ThingsBoard integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - ThingsBoardIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetThingsBoardIntegration",
                                     "GetThingsBoardIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            integration = ThingsBoardIntegration(
                application_id=response.integration.application_id,
                server=response.integration.server,
                token=response.integration.token,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_thingsboard_integration(): ThingsBoard integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_thingsboard_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_thingsboard_integration(self, integration: ThingsBoardIntegration) -> None:
        """
        Update a ThingsBoard integration for an application.

        Parameters
        ----------
        - integration: The ThingsBoard integration record to update.
        """
        if not isinstance(integration, ThingsBoardIntegration):
            raise TypeError("Expected ThingsBoardIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateThingsBoardIntegration",
                             "UpdateThingsBoardIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "server": getattr(integration, 'server', ''),
                                     "token": getattr(integration, 'token', '')
                                 }
                             })

    def delete_thingsboard_integration(self, app_id: str) -> None:
        """
        Delete ThingsBoard integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteThingsBoardIntegration",
                             "DeleteThingsBoardIntegrationRequest", {"application_id": app_id})

    def create_aws_sns_integration(self, integration: AwsSnsIntegration) -> None:
        """
        Create an AWS SNS integration for an application.

        Parameters
        ----------
        - integration: The AWS SNS integration record to create.
        """
        if not isinstance(integration, AwsSnsIntegration):
            raise TypeError("Expected AwsSnsIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateAwsSnsIntegration",
                             "CreateAwsSnsIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "aws_region": getattr(integration, 'aws_region', ''),
                                     "aws_access_key_id": getattr(integration, 'aws_access_key_id', ''),
                                     "aws_secret_access_key": getattr(integration, 'aws_secret_access_key', ''),
                                     "topic_arn": getattr(integration, 'topic_arn', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_aws_sns_integration(self, app_id: str) -> AwsSnsIntegration | None:
        """
        Get AWS SNS integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - AwsSnsIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetAwsSnsIntegration",
                                     "GetAwsSnsIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            integration = AwsSnsIntegration(
                application_id=response.integration.application_id,
                aws_region=response.integration.aws_region,
                aws_access_key_id=response.integration.aws_access_key_id,
                aws_secret_access_key=response.integration.aws_secret_access_key,
                topic_arn=response.integration.topic_arn,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_aws_sns_integration(): AWS SNS integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_aws_sns_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_aws_sns_integration(self, integration: AwsSnsIntegration) -> None:
        """
        Update an AWS SNS integration for an application.

        Parameters
        ----------
        - integration: The AWS SNS integration record to update.
        """
        if not isinstance(integration, AwsSnsIntegration):
            raise TypeError("Expected AwsSnsIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateAwsSnsIntegration",
                             "UpdateAwsSnsIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "aws_region": getattr(integration, 'aws_region', ''),
                                     "aws_access_key_id": getattr(integration, 'aws_access_key_id', ''),
                                     "aws_secret_access_key": getattr(integration, 'aws_secret_access_key', ''),
                                     "topic_arn": getattr(integration, 'topic_arn', '')
                                 }
                             })

    def delete_aws_sns_integration(self, app_id: str) -> None:
        """
        Delete AWS SNS integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteAwsSnsIntegration",
                             "DeleteAwsSnsIntegrationRequest", {"application_id": app_id})

    def create_azure_service_bus_integration(self, integration: AzureServiceBusIntegration) -> None:
        """
        Create an Azure Service Bus integration for an application.

        Parameters
        ----------
        - integration: The Azure Service Bus integration record to create.
        """
        if not isinstance(integration, AzureServiceBusIntegration):
            raise TypeError("Expected AzureServiceBusIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateAzureServiceBusIntegration",
                             "CreateAzureServiceBusIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "connection_string": getattr(integration, 'connection_string', ''),
                                     "topic_name": getattr(integration, 'topic_name', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_azure_service_bus_integration(self, app_id: str) -> AzureServiceBusIntegration | None:
        """
        Get Azure Service Bus integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - AzureServiceBusIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetAzureServiceBusIntegration",
                                     "GetAzureServiceBusIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            integration = AzureServiceBusIntegration(
                application_id=response.integration.application_id,
                connection_string=response.integration.connection_string,
                topic_name=response.integration.topic_name,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_azure_service_bus_integration(): Azure Service Bus integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_azure_service_bus_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_azure_service_bus_integration(self, integration: AzureServiceBusIntegration) -> None:
        """
        Update an Azure Service Bus integration for an application.

        Parameters
        ----------
        - integration: The Azure Service Bus integration record to update.
        """
        if not isinstance(integration, AzureServiceBusIntegration):
            raise TypeError("Expected AzureServiceBusIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateAzureServiceBusIntegration",
                             "UpdateAzureServiceBusIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "connection_string": getattr(integration, 'connection_string', ''),
                                     "topic_name": getattr(integration, 'topic_name', '')
                                 }
                             })

    def delete_azure_service_bus_integration(self, app_id: str) -> None:
        """
        Delete Azure Service Bus integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteAzureServiceBusIntegration",
                             "DeleteAzureServiceBusIntegrationRequest", {"application_id": app_id})

    def create_gcp_pubsub_integration(self, integration: GcpPubSubIntegration) -> None:
        """
        Create a GCP Pub/Sub integration for an application.

        Parameters
        ----------
        - integration: The GCP Pub/Sub integration record to create.
        """
        if not isinstance(integration, GcpPubSubIntegration):
            raise TypeError("Expected GcpPubSubIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateGcpPubSubIntegration",
                             "CreateGcpPubSubIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "encoding": getattr(integration, 'encoding', ''),
                                     "project_id": getattr(integration, 'project_id', ''),
                                     "topic_name": getattr(integration, 'topic_name', ''),
                                     "service_account_key": getattr(integration, 'service_account_key', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_gcp_pubsub_integration(self, app_id: str) -> GcpPubSubIntegration | None:
        """
        Get GCP Pub/Sub integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - GcpPubSubIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetGcpPubSubIntegration",
                                     "GetGcpPubSubIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            # Import the enum here to avoid circular imports
            from chirpstack_api_wrapper.objects import Encoding
            
            # Find the enum value by comparing the response value
            encoding_enum = next((e for e in Encoding if e.value == response.integration.encoding), Encoding.JSON)
            
            integration = GcpPubSubIntegration(
                application_id=response.integration.application_id,
                encoding=encoding_enum,
                project_id=response.integration.project_id,
                topic_name=response.integration.topic_name,
                service_account_key=response.integration.service_account_key,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_gcp_pubsub_integration(): GCP Pub/Sub integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_gcp_pubsub_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_gcp_pubsub_integration(self, integration: GcpPubSubIntegration) -> None:
        """
        Update a GCP Pub/Sub integration for an application.

        Parameters
        ----------
        - integration: The GCP Pub/Sub integration record to update.
        """
        if not isinstance(integration, GcpPubSubIntegration):
            raise TypeError("Expected GcpPubSubIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateGcpPubSubIntegration",
                             "UpdateGcpPubSubIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "encoding": getattr(integration, 'encoding', ''),
                                     "project_id": getattr(integration, 'project_id', ''),
                                     "topic_name": getattr(integration, 'topic_name', ''),
                                     "service_account_key": getattr(integration, 'service_account_key', '')
                                 }
                             })

    def delete_gcp_pubsub_integration(self, app_id: str) -> None:
        """
        Delete GCP Pub/Sub integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteGcpPubSubIntegration",
                             "DeleteGcpPubSubIntegrationRequest", {"application_id": app_id})

    def create_ifttt_integration(self, integration: IftttIntegration) -> None:
        """
        Create an IFTTT integration for an application.

        Parameters
        ----------
        - integration: The IFTTT integration record to create.
        """
        if not isinstance(integration, IftttIntegration):
            raise TypeError("Expected IftttIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateIftttIntegration",
                             "CreateIftttIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "key": getattr(integration, 'key', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_ifttt_integration(self, app_id: str) -> IftttIntegration | None:
        """
        Get IFTTT integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - IftttIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetIftttIntegration",
                                     "GetIftttIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            integration = IftttIntegration(
                application_id=response.integration.application_id,
                key=response.integration.key,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_ifttt_integration(): IFTTT integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_ifttt_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_ifttt_integration(self, integration: IftttIntegration) -> None:
        """
        Update an IFTTT integration for an application.

        Parameters
        ----------
        - integration: The IFTTT integration record to update.
        """
        if not isinstance(integration, IftttIntegration):
            raise TypeError("Expected IftttIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateIftttIntegration",
                             "UpdateIftttIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "key": getattr(integration, 'key', '')
                                 }
                             })

    def delete_ifttt_integration(self, app_id: str) -> None:
        """
        Delete IFTTT integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteIftttIntegration",
                             "DeleteIftttIntegrationRequest", {"application_id": app_id})

    def create_mydevices_integration(self, integration: MyDevicesIntegration) -> None:
        """
        Create a MyDevices integration for an application.

        Parameters
        ----------
        - integration: The MyDevices integration record to create.
        """
        if not isinstance(integration, MyDevicesIntegration):
            raise TypeError("Expected MyDevicesIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreateMyDevicesIntegration",
                             "CreateMyDevicesIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "endpoint": getattr(integration, 'endpoint', ''),
                                     "token": getattr(integration, 'token', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_mydevices_integration(self, app_id: str) -> MyDevicesIntegration | None:
        """
        Get MyDevices integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - MyDevicesIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetMyDevicesIntegration",
                                     "GetMyDevicesIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            integration = MyDevicesIntegration(
                application_id=response.integration.application_id,
                endpoint=response.integration.endpoint,
                token=response.integration.token,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_mydevices_integration(): MyDevices integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_mydevices_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_mydevices_integration(self, integration: MyDevicesIntegration) -> None:
        """
        Update a MyDevices integration for an application.

        Parameters
        ----------
        - integration: The MyDevices integration record to update.
        """
        if not isinstance(integration, MyDevicesIntegration):
            raise TypeError("Expected MyDevicesIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdateMyDevicesIntegration",
                             "UpdateMyDevicesIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "endpoint": getattr(integration, 'endpoint', ''),
                                     "token": getattr(integration, 'token', '')
                                 }
                             })

    def delete_mydevices_integration(self, app_id: str) -> None:
        """
        Delete MyDevices integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeleteMyDevicesIntegration",
                             "DeleteMyDevicesIntegrationRequest", {"application_id": app_id})

    def create_pilot_things_integration(self, integration: PilotThingsIntegration) -> None:
        """
        Create a Pilot Things integration for an application.

        Parameters
        ----------
        - integration: The Pilot Things integration record to create.
        """
        if not isinstance(integration, PilotThingsIntegration):
            raise TypeError("Expected PilotThingsIntegration object")
        
        resp = self._call_rpc("ApplicationService", "CreatePilotThingsIntegration",
                             "CreatePilotThingsIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "server": getattr(integration, 'server', ''),
                                     "token": getattr(integration, 'token', '')
                                 }
                             })
        integration.id = resp.id
        return

    def get_pilot_things_integration(self, app_id: str) -> PilotThingsIntegration | None:
        """
        Get Pilot Things integration for an application.

        Parameters
        ----------
        - app_id: Application ID.

        Returns
        -------
        - PilotThingsIntegration object or None if not found.
        """
        try:
            response = self._call_rpc("ApplicationService", "GetPilotThingsIntegration",
                                     "GetPilotThingsIntegrationRequest", {"application_id": app_id})
            
            if not response or not hasattr(response, 'integration'):
                return None
            
            integration = PilotThingsIntegration(
                application_id=response.integration.application_id,
                server=response.integration.server,
                token=response.integration.token,
                id=response.integration.id
            )
            return integration
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_pilot_things_integration(): Pilot Things integration for app {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_pilot_things_integration(): An error occurred with status code {status_code} - {details}")
            return None

    def update_pilot_things_integration(self, integration: PilotThingsIntegration) -> None:
        """
        Update a Pilot Things integration for an application.

        Parameters
        ----------
        - integration: The Pilot Things integration record to update.
        """
        if not isinstance(integration, PilotThingsIntegration):
            raise TypeError("Expected PilotThingsIntegration object")
        
        return self._call_rpc("ApplicationService", "UpdatePilotThingsIntegration",
                             "UpdatePilotThingsIntegrationRequest", {
                                 "integration": {
                                     "application_id": getattr(integration, 'application_id', ''),
                                     "server": getattr(integration, 'server', ''),
                                     "token": getattr(integration, 'token', '')
                                 }
                             })

    def delete_pilot_things_integration(self, app_id: str) -> None:
        """
        Delete Pilot Things integration for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "DeletePilotThingsIntegration",
                             "DeletePilotThingsIntegrationRequest", {"application_id": app_id})

    def generate_mqtt_integration_client_certificate(self, app_id: str) -> dict:
        """
        Generate MQTT integration client certificate for an application.

        Parameters
        ----------
        - app_id: Application ID.
        """
        return self._call_rpc("ApplicationService", "GenerateMqttIntegrationClientCertificate",
                             "GenerateMqttIntegrationClientCertificateRequest", {"application_id": app_id})

    def update_device(self, device: Device) -> None:
        """
        Update a Device.

        Parameters
        ----------
        - device: The device record to update.
        """
        if not isinstance(device, Device):
            raise TypeError("Expected Device object")
        
        return self._call_rpc("DeviceService", "Update",
                             "UpdateDeviceRequest", {
                                 "device": {
                                     "dev_eui": getattr(device, 'dev_eui', ''),
                                     "name": getattr(device, 'name', ''),
                                     "application_id": getattr(device, 'application_id', ''),
                                     "device_profile_id": getattr(device, 'device_profile_id', ''),
                                     "join_eui": getattr(device, 'join_eui', ''),
                                     "description": getattr(device, 'description', ''),
                                     "skip_fcnt_check": getattr(device, 'skip_fcnt_check', False),
                                     "is_disabled": getattr(device, 'is_disabled', False),
                                     "tags": getattr(device, 'tags', {}),
                                     "variables": getattr(device, 'variables', {})
                                 }
                             })

    def update_device_keys(self, device_keys: DeviceKeys) -> None:
        """
        Update device keys.

        Parameters
        ----------
        - device_keys: The device keys record to update.
        """
        if not isinstance(device_keys, DeviceKeys):
            raise TypeError("Expected DeviceKeys object")
        
        return self._call_rpc("DeviceService", "UpdateKeys",
                             "UpdateDeviceKeysRequest", {
                                 "device_keys": {
                                     "dev_eui": getattr(device_keys, 'dev_eui', ''),
                                     "nwk_key": getattr(device_keys, 'nwk_key', ''),
                                     "app_key": getattr(device_keys, 'app_key', '')
                                 }
                             })

    def delete_device_keys(self, dev_eui: Device | str) -> None:
        """
        Delete device keys.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        return self._call_rpc("DeviceService", "DeleteKeys",
                             "DeleteDeviceKeysRequest", {"dev_eui": str(dev_eui)})

    def activate_device(self, dev_eui: Device | str, dev_addr: str, 
                       nwk_s_key: str, app_s_key: str, f_cnt_up: int = 0, 
                       f_cnt_down: int = 0, skip_f_cnt_check: bool = False) -> None:
        """
        Activate a device (ABP).

        Parameters
        ----------
        - dev_eui: Device EUI.
        - dev_addr: Device address.
        - nwk_s_key: Network session key.
        - app_s_key: Application session key.
        - f_cnt_up: Frame counter up.
        - f_cnt_down: Frame counter down.
        - skip_f_cnt_check: Skip frame counter check.
        """
        return self._call_rpc("DeviceService", "Activate",
                             "ActivateDeviceRequest", {
                                 "device_activation": {
                                     "dev_eui": str(dev_eui),
                                     "dev_addr": dev_addr,
                                     "nwk_s_key": nwk_s_key,
                                     "app_s_key": app_s_key,
                                     "f_cnt_up": f_cnt_up,
                                     "f_cnt_down": f_cnt_down,
                                     "skip_f_cnt_check": skip_f_cnt_check
                                 }
                             })

    def deactivate_device(self, dev_eui: Device | str) -> None:
        """
        Deactivate a device.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        return self._call_rpc("DeviceService", "Deactivate",
                             "DeactivateDeviceRequest", {"dev_eui": str(dev_eui)})

    def enqueue_device_downlink(self, dev_eui: Device | str, data: bytes, 
                               f_port: int, confirmed: bool = False) -> None:
        """
        Enqueue a downlink message for a device.

        Parameters
        ----------
        - dev_eui: Device EUI.
        - data: Downlink data.
        - f_port: Frame port.
        - confirmed: Whether the message requires confirmation.
        """
        return self._call_rpc("DeviceService", "Enqueue",
                             "EnqueueDeviceQueueItemRequest", {
                                 "queue_item": {
                                     "dev_eui": str(dev_eui),
                                     "frm_payload": data,
                                     "f_port": f_port,
                                     "confirmed": confirmed
                                 }
                             })

    def get_device_queue(self, dev_eui: Device | str) -> list:
        """
        Get the downlink queue for a device.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        resp = self._call_rpc("DeviceService", "GetQueue",
                             "GetDeviceQueueItemsRequest", {"dev_eui": str(dev_eui)})
        return list(resp.items)

    def flush_device_queue(self, dev_eui: Device | str) -> None:
        """
        Flush the downlink queue for a device.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        return self._call_rpc("DeviceService", "FlushQueue",
                             "FlushDeviceQueueRequest", {"dev_eui": str(dev_eui)})

    def get_device_metrics(self, dev_eui: Device | str, start: str, end: str) -> dict:
        """
        Get device metrics.

        Parameters
        ----------
        - dev_eui: Device EUI.
        - start: Start timestamp (ISO format).
        - end: End timestamp (ISO format).
        """
        return self._call_rpc("DeviceService", "GetMetrics",
                             "GetDeviceMetricsRequest", {
                                 "dev_eui": str(dev_eui),
                                 "start": start,
                                 "end": end
                             })

    def get_device_link_metrics(self, dev_eui: Device | str) -> dict:
        """
        Get device link metrics.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        return self._call_rpc("DeviceService", "GetLinkMetrics",
                             "GetDeviceLinkMetricsRequest", {"dev_eui": str(dev_eui)})

    def get_next_f_cnt_down(self, dev_eui: Device | str) -> int:
        """
        Get the next frame counter down for a device.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        resp = self._call_rpc("DeviceService", "GetNextFCntDown",
                             "GetDeviceNextFCntDownRequest", {"dev_eui": str(dev_eui)})
        return resp.f_cnt_down

    def get_random_dev_addr(self, dev_eui: Device | str) -> str:
        """
        Get a random device address for a device.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        resp = self._call_rpc("DeviceService", "GetRandomDevAddr",
                             "GetRandomDevAddrRequest", {"dev_eui": str(dev_eui)})
        return resp.dev_addr

    def flush_dev_nonces(self, dev_eui: Device | str) -> None:
        """
        Flush device nonces.

        Parameters
        ----------
        - dev_eui: Device EUI.
        """
        return self._call_rpc("DeviceService", "FlushDevNonces",
                             "FlushDevNoncesRequest", {"dev_eui": str(dev_eui)})

    def update_gateway(self, gateway: Gateway) -> None:
        """
        Update a Gateway.

        Parameters
        ----------
        - gateway: The gateway record to update.
        """
        if not isinstance(gateway, Gateway):
            raise TypeError("Expected Gateway object")
        
        return self._call_rpc("GatewayService", "Update",
                             "UpdateGatewayRequest", {
                                 "gateway": {
                                     "id": getattr(gateway, 'id', ''),
                                     "gateway_id": getattr(gateway, 'gateway_id', ''),
                                     "name": getattr(gateway, 'name', ''),
                                     "description": getattr(gateway, 'description', ''),
                                     "tenant_id": getattr(gateway, 'tenant_id', ''),
                                     "stats_interval": getattr(gateway, 'stats_interval', ''),
                                     "tags": getattr(gateway, 'tags', {}),
                                     "location": getattr(gateway, 'location', {}),
                                     "metadata": getattr(gateway, 'metadata', {})
                                 }
                             })

    def update_gateway_location(self, gateway_id: str, location: Location) -> None:
        """
        Update gateway location.

        Parameters
        ----------
        - gateway_id: Gateway ID.
        - location: Location object with new coordinates.
        """
        if not isinstance(location, Location):
            raise TypeError("Expected Location object")
        
        location_dict = {
            "latitude": getattr(location, 'latitude', ''),
            "longitude": getattr(location, 'longitude', ''),
            "altitude": getattr(location, 'altitude', ''),
            "source": getattr(location, 'source', ''),
            "accuracy": getattr(location, 'accuracy', '')
        }
        
        return self._call_rpc("GatewayService", "Update",
                             "UpdateGatewayRequest", {
                                 "gateway": {
                                     "gateway_id": gateway_id,
                                     "location": location_dict
                                 }
                             })

    def get_gateway_metrics(self, gateway_id: Gateway | str, start: str, end: str) -> dict:
        """
        Get gateway metrics.

        Parameters
        ----------
        - gateway_id: Gateway ID.
        - start: Start timestamp (ISO format).
        - end: End timestamp (ISO format).
        """
        return self._call_rpc("GatewayService", "GetMetrics",
                             "GetGatewayMetricsRequest", {
                                 "gateway_id": str(gateway_id),
                                 "start": start,
                                 "end": end
                             })

    def get_gateway_duty_cycle_metrics(self, gateway_id: Gateway | str, start: str, end: str) -> dict:
        """
        Get gateway duty cycle metrics.

        Parameters
        ----------
        - gateway_id: Gateway ID.
        - start: Start timestamp (ISO format).
        - end: End timestamp (ISO format).
        """
        return self._call_rpc("GatewayService", "GetDutyCycleMetrics",
                             "GetGatewayDutyCycleMetricsRequest", {
                                 "gateway_id": str(gateway_id),
                                 "start": start,
                                 "end": end
                             })

    def generate_gateway_client_certificate(self, gateway_id: Gateway | str) -> dict:
        """
        Generate a client certificate for a gateway.

        Parameters
        ----------
        - gateway_id: Gateway ID.
        """
        return self._call_rpc("GatewayService", "GenerateClientCertificate",
                             "GenerateGatewayClientCertificateRequest", {"gateway_id": str(gateway_id)})

    def get_relay_gateway(self, gateway_id: Gateway | str) -> dict:
        """
        Get relay gateway.

        Parameters
        ----------
        - gateway_id: Gateway ID.

        Returns
        -------
        - Dictionary with relay gateway data or empty dict if not found.
        """
        try:
            response = self._call_rpc("GatewayService", "GetRelayGateway",
                                     "GetRelayGatewayRequest", {"gateway_id": str(gateway_id)})
            
            if not response or not hasattr(response, 'relay_gateway'):
                return {}
            
            # Return relay gateway data as dictionary since there's no specific object for it
            relay_data = {
                "gateway_id": response.relay_gateway.gateway_id,
                "relay": response.relay_gateway.relay
            }
            return relay_data
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_relay_gateway(): Relay gateway {gateway_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_relay_gateway(): An error occurred with status code {status_code} - {details}")
            return {}

    def update_relay_gateway(self, gateway_id: Gateway | str, relay_config: dict) -> None:
        """
        Update relay gateway configuration.

        Parameters
        ----------
        - gateway_id: Gateway ID.
        - relay_config: Relay configuration dictionary.
        """
        return self._call_rpc("GatewayService", "UpdateRelayGateway",
                             "UpdateRelayGatewayRequest", {
                                 "gateway_id": str(gateway_id),
                                 "relay": relay_config
                             })

    def delete_relay_gateway(self, gateway_id: Gateway | str) -> None:
        """
        Delete relay gateway configuration.

        Parameters
        ----------
        - gateway_id: Gateway ID.
        """
        return self._call_rpc("GatewayService", "DeleteRelayGateway",
                             "DeleteRelayGatewayRequest", {"gateway_id": str(gateway_id)})

    def list_relay_gateways(self) -> list[dict]:
        """
        List all relay gateways.
        
        Returns
        -------
        - List of relay gateway dictionaries.
        """
        api_response = self._list_with_pagination("GatewayService", {}, "ListRelayGatewaysRequest", "result")
        relay_gateways = []
        for gateway_item in api_response:
            relay_gateway = {
                'gateway_id': gateway_item.gateway_id,
                'relay': gateway_item.relay
            }
            relay_gateways.append(relay_gateway)
        return relay_gateways

    def update_device_profile(self, device_profile: DeviceProfile) -> None:
        """
        Update a Device Profile.

        Parameters
        ----------
        - device_profile: The device profile record to update.
        """
        if not isinstance(device_profile, DeviceProfile):
            raise TypeError("Expected DeviceProfile object")
        
        return self._call_rpc("DeviceProfileService", "Update",
                             "UpdateDeviceProfileRequest", {
                                 "device_profile": {
                                    "id": getattr(device_profile, 'id', ''),
                                    "name": getattr(device_profile, 'name', ''),
                                    "tenant_id": getattr(device_profile, 'tenant_id', ''),
                                    "region": getattr(device_profile, 'region', ''),
                                    "mac_version": getattr(device_profile, 'mac_version', ''),
                                    "reg_params_revision": getattr(device_profile, 'reg_params_revision', ''),
                                    "uplink_interval": getattr(device_profile, 'uplink_interval', ''),
                                    "supports_otaa": getattr(device_profile, 'supports_otaa', ''),
                                    "abp_rx1_delay": getattr(device_profile, 'abp_rx1_delay', ''),
                                    "abp_rx1_dr_offset": getattr(device_profile, 'abp_rx1_dr_offset', ''),
                                    "abp_rx2_dr": getattr(device_profile, 'abp_rx2_dr', ''),
                                    "abp_rx2_freq": getattr(device_profile, 'abp_rx2_freq', ''),
                                    "supports_class_b": getattr(device_profile, 'supports_class_b', ''),
                                    "class_b_timeout": getattr(device_profile, 'class_b_timeout', ''),
                                    "class_b_ping_slot_periodicity": getattr(device_profile, 'class_b_ping_slot_periodicity', ''),
                                    "class_b_ping_slot_dr": getattr(device_profile, 'class_b_ping_slot_dr', ''),
                                    "class_b_ping_slot_freq": getattr(device_profile, 'class_b_ping_slot_freq', ''),
                                    "supports_class_c": getattr(device_profile, 'supports_class_c', ''),
                                    "class_c_timeout": getattr(device_profile, 'class_c_timeout', ''),
                                    "description": getattr(device_profile, 'description', ''),
                                    "payload_codec_runtime": getattr(device_profile, 'payload_codec_runtime', ''),
                                    "payload_codec_script": getattr(device_profile, 'payload_codec_script', ''),
                                    "flush_queue_on_activate": getattr(device_profile, 'flush_queue_on_activate', ''),
                                    "device_status_req_interval": getattr(device_profile, 'device_status_req_interval', ''),
                                    "auto_detect_measurements": getattr(device_profile, 'auto_detect_measurements', ''),
                                    "allow_roaming": getattr(device_profile, 'allow_roaming', ''),
                                    "adr_algorithm_id": getattr(device_profile, 'adr_algorithm_id', ''),
                                    "rx1_delay": getattr(device_profile, 'rx1_delay', ''),
                                    "app_layer_params": getattr(device_profile, 'app_layer_params', {}).to_dict(),
                                    "region_config_id": getattr(device_profile, 'region_config_id', ''),
                                    "is_relay": getattr(device_profile, 'is_relay', ''),
                                    "is_relay_ed": getattr(device_profile, 'is_relay_ed', ''),
                                    "relay_ed_relay_only": getattr(device_profile, 'relay_ed_relay_only', ''),
                                    "relay_enabled": getattr(device_profile, 'relay_enabled', ''),
                                    "relay_cad_periodicity": getattr(device_profile, 'relay_cad_periodicity', ''),
                                    "relay_default_channel_index": getattr(device_profile, 'relay_default_channel_index', ''),
                                    "relay_second_channel_freq": getattr(device_profile, 'relay_second_channel_freq', ''),
                                    "relay_second_channel_dr": getattr(device_profile, 'relay_second_channel_dr', ''),
                                    "relay_second_channel_ack_offset": getattr(device_profile, 'relay_second_channel_ack_offset', ''),
                                    "relay_ed_activation_mode": getattr(device_profile, 'relay_ed_activation_mode', ''),
                                    "relay_ed_smart_enable_level": getattr(device_profile, 'relay_ed_smart_enable_level', ''),
                                    "relay_ed_back_off": getattr(device_profile, 'relay_ed_back_off', ''),
                                    "relay_ed_uplink_limit_bucket_size": getattr(device_profile, 'relay_ed_uplink_limit_bucket_size', ''),
                                    "relay_ed_uplink_limit_reload_rate": getattr(device_profile, 'relay_ed_uplink_limit_reload_rate', ''),
                                    "relay_join_req_limit_reload_rate": getattr(device_profile, 'relay_join_req_limit_reload_rate', ''),
                                    "relay_notify_limit_reload_rate": getattr(device_profile, 'relay_notify_limit_reload_rate', ''),
                                    "relay_global_uplink_limit_reload_rate": getattr(device_profile, 'relay_global_uplink_limit_reload_rate', ''),
                                    "relay_overall_limit_reload_rate": getattr(device_profile, 'relay_overall_limit_reload_rate', ''),
                                    "relay_join_req_limit_bucket_size": getattr(device_profile, 'relay_join_req_limit_bucket_size', ''),
                                    "relay_notify_limit_bucket_size": getattr(device_profile, 'relay_notify_limit_bucket_size', ''),
                                    "relay_global_uplink_limit_bucket_size": getattr(device_profile, 'relay_global_uplink_limit_bucket_size', ''),
                                    "relay_overall_limit_bucket_size": getattr(device_profile, 'relay_overall_limit_bucket_size', ''),
                                    "measurements": getattr(device_profile, 'measurements', {}),
                                    "tags": getattr(device_profile, 'tags', {})
                                 }
                             })

    def list_adr_algorithms(self) -> list[dict]:
        """
        List available ADR algorithms.
        
        Returns
        -------
        - List of ADR algorithm dictionaries.
        """
        resp = self._call_rpc("DeviceProfileService", "ListAdrAlgorithms",
                             "ListAdrAlgorithmsRequest")
        algorithms = []
        for algorithm_item in resp.result:
            algorithm = {
                'id': algorithm_item.id,
                'name': algorithm_item.name
            }
            algorithms.append(algorithm)
        return algorithms

    def create_tenant(self, tenant: Tenant) -> None:
        """
        Create a Tenant.

        Parameters
        ----------
        - tenant: The tenant record to create.
        """
        if not isinstance(tenant, Tenant):
            raise TypeError("Expected Tenant object")
        
        resp = self._call_rpc("TenantService", "Create",
                             "CreateTenantRequest", {
                                 "tenant": {
                                     "name": getattr(tenant, 'name', ''),
                                     "description": getattr(tenant, 'description', ''),
                                     "can_have_gateways": getattr(tenant, 'can_have_gateways', False),
                                     "max_gateway_count": getattr(tenant, 'max_gateway_count', 0),
                                     "max_device_count": getattr(tenant, 'max_device_count', 0),
                                     "private_gateways_up": getattr(tenant, 'private_gateways_up', False),
                                     "private_gateways_down": getattr(tenant, 'private_gateways_down', False),
                                     "tags": getattr(tenant, 'tags', {})
                                 }
                             })
        tenant.id = resp.id
        return

    def update_tenant(self, tenant: Tenant) -> None:
        """
        Update a Tenant.

        Parameters
        ----------
        - tenant: The tenant record to update.
        """
        if not isinstance(tenant, Tenant):
            raise TypeError("Expected Tenant object")
        
        return self._call_rpc("TenantService", "Update",
                             "UpdateTenantRequest", {
                                 "tenant": {
                                     "id": tenant.id,
                                     "name": getattr(tenant, 'name', ''),
                                     "description": getattr(tenant, 'description', ''),
                                     "can_have_gateways": getattr(tenant, 'can_have_gateways', False),
                                     "max_gateway_count": getattr(tenant, 'max_gateway_count', 0),
                                     "max_device_count": getattr(tenant, 'max_device_count', 0),
                                     "private_gateways_up": getattr(tenant, 'private_gateways_up', False),
                                     "private_gateways_down": getattr(tenant, 'private_gateways_down', False),
                                     "tags": getattr(tenant, 'tags', {})
                                 }
                             })

    def get_tenant(self, tenant_id: Tenant | str) -> Tenant | None:
        """
        Get tenant.

        Parameters
        ----------
        - tenant_id: Tenant ID.

        Returns
        -------
        - Tenant object or None if not found.
        """
        try:
            response = self._call_rpc("TenantService", "Get",
                                     "GetTenantRequest", {"id": str(tenant_id)})
            
            if not response or not hasattr(response, 'tenant'):
                return None
            
            return Tenant.from_grpc(response.tenant)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_tenant(): Tenant {tenant_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_tenant(): An error occurred with status code {status_code} - {details}")
            return None

    def delete_tenant(self, tenant_id: Tenant | str) -> None:
        """
        Delete a Tenant.

        Parameters
        ----------
        - tenant_id: Tenant ID.
        """
        return self._call_rpc("TenantService", "Delete",
                             "DeleteTenantRequest", {"id": str(tenant_id)})

    def create_user(self, user: User, tenant_id: str) -> None:
        """
        Create a User.

        Parameters
        ----------
        - user: The user record to create.
        - tenant_id: Tenant ID.
        """
        if not isinstance(user, User):
            raise TypeError("Expected User object")
        
        resp = self._call_rpc("TenantService", "CreateUser",
                             "CreateTenantUserRequest", {
                                 "user": {
                                     "email": getattr(user, 'email', ''),
                                     "password": getattr(user, 'password', ''),
                                     "is_active": getattr(user, 'is_active', ''),
                                     "is_admin": getattr(user, 'is_admin', ''),
                                     "note": getattr(user, 'note', '')
                                 },
                                 "tenant_id": tenant_id
                             })
        user.id = resp.id
        return

    def update_user(self, user: User, tenant_id: str) -> None:
        """
        Update a User.

        Parameters
        ----------
        - user: The user record to update.
        - tenant_id: Tenant ID.
        """
        if not isinstance(user, User):
            raise TypeError("Expected User object")
        
        return self._call_rpc("TenantService", "UpdateUser",
                             "UpdateTenantUserRequest", {
                                 "user": {
                                     "id": getattr(user, 'id', ''),
                                     "email": getattr(user, 'email', ''),
                                     "is_active": getattr(user, 'is_active', ''),
                                     "is_admin": getattr(user, 'is_admin', ''),
                                     "note": getattr(user, 'note', '')
                                 },
                                 "tenant_id": tenant_id
                             })

    def get_user(self, user_id: str, tenant_id: str) -> User | None:
        """
        Get user.

        Parameters
        ----------
        - user_id: User ID.
        - tenant_id: Tenant ID.

        Returns
        -------
        - User object or None if not found.
        """
        try:
            response = self._call_rpc("TenantService", "GetUser",
                                     "GetTenantUserRequest", {
                                         "user_id": user_id,
                                         "tenant_id": tenant_id
                                     })
            
            if not response or not hasattr(response, 'user'):
                return None
            
            return User.from_grpc(response.user)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_user(): User {user_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_user(): An error occurred with status code {status_code} - {details}")
            return None

    def delete_user(self, user_id: str, tenant_id: str) -> None:
        """
        Delete a User.

        Parameters
        ----------
        - user_id: User ID.
        - tenant_id: Tenant ID.
        """
        return self._call_rpc("TenantService", "DeleteUser",
                             "DeleteTenantUserRequest", {
                                 "user_id": user_id,
                                 "tenant_id": tenant_id
                             })

    def list_users_for_tenant(self, tenant_id: str) -> list[User]:
        """
        List users for a tenant.

        Parameters
        ----------
        - tenant_id: Tenant ID.

        Returns
        -------
        - List of User objects.
        """
        # First list the User summary items for this tenant
        list_response = self._list_with_pagination("TenantService", 
                                                {"tenant_id": tenant_id}, 
                                                "ListTenantUsersRequest", 
                                                "result")
        users = []
        
        # For each summary item, fetch the full User using Get
        for user_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "TenantService",
                    "GetUser",
                    request_type="GetTenantUserRequest",
                    params={"user_id": getattr(user_item, "id", ""), "tenant_id": tenant_id}
                )
                if get_resp and hasattr(get_resp, "user"):
                    users.append(User.from_grpc(get_resp.user))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_users_for_tenant(): Failed to fetch full user for id={getattr(user_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return users

    def create_user_standalone(self, user: User) -> None:
        """
        Create a User (standalone, not tied to a tenant).

        Parameters
        ----------
        - user: The user record to create.
        """
        if not isinstance(user, User):
            raise TypeError("Expected User object")
        
        resp = self._call_rpc("UserService", "Create",
                             "CreateUserRequest", {
                                 "user": {
                                     "email": getattr(user, 'email', ''),
                                     "password": getattr(user, 'password', ''),
                                     "is_active": getattr(user, 'is_active', ''),
                                     "is_admin": getattr(user, 'is_admin', ''),
                                     "note": getattr(user, 'note', '')
                                 }
                             })
        user.id = resp.id
        return

    def update_user_standalone(self, user: User) -> None:
        """
        Update a User (standalone, not tied to a tenant).

        Parameters
        ----------
        - user: The user record to update.
        """
        if not isinstance(user, User):
            raise TypeError("Expected User object")
        
        return self._call_rpc("UserService", "Update",
                             "UpdateUserRequest", {
                                 "user": {
                                     "id": getattr(user, 'id', ''),
                                     "email": getattr(user, 'email', ''),
                                     "is_active": getattr(user, 'is_active', ''),
                                     "is_admin": getattr(user, 'is_admin', ''),
                                     "note": getattr(user, 'note', '')
                                 }
                             })

    def get_user_standalone(self, user_id: str) -> User | None:
        """
        Get user (standalone, not tied to a tenant).

        Parameters
        ----------
        - user_id: User ID.

        Returns
        -------
        - User object or None if not found.
        """
        try:
            response = self._call_rpc("UserService", "Get",
                                     "GetUserRequest", {"id": user_id})
            
            if not response or not hasattr(response, 'user'):
                return None
            
            return User.from_grpc(response.user)
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_user_standalone(): User {user_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_user_standalone(): An error occurred with status code {status_code} - {details}")
            return None

    def delete_user_standalone(self, user_id: str) -> None:
        """
        Delete a User (standalone, not tied to a tenant).

        Parameters
        ----------
        - user_id: User ID.
        """
        return self._call_rpc("UserService", "Delete",
                             "DeleteUserRequest", {"id": user_id})

    def list_users_standalone(self) -> list[User]:
        """
        List all users (standalone, not tied to tenants).
        
        Returns
        -------
        - List of User objects.
        """
        # First list the User summary items
        list_response = self._list_with_pagination("UserService", {}, "ListUsersRequest", "result")
        users = []
        
        # For each summary item, fetch the full User using Get
        for user_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "UserService",
                    "Get",
                    request_type="GetUserRequest",
                    params={"id": getattr(user_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "user"):
                    users.append(User.from_grpc(get_resp.user))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_users_standalone(): Failed to fetch full user for id={getattr(user_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return users

    def update_user_password(self, user_id: str, password: str) -> None:
        """
        Update user password.

        Parameters
        ----------
        - user_id: User ID.
        - password: New password.
        """
        return self._call_rpc("UserService", "UpdatePassword",
                             "UpdateUserPasswordRequest", {
                                 "user_id": user_id,
                                 "password": password
                             })

    def create_multicast_group(self, multicast_group: MulticastGroup) -> None:
        """
        Create a Multicast Group.

        Parameters
        ----------
        - multicast_group: The multicast group record to create.
        """
        if not isinstance(multicast_group, MulticastGroup):
            raise TypeError("Expected MulticastGroup object")
        
        resp = self._call_rpc("MulticastGroupService", "Create",
                             "CreateMulticastGroupRequest", {
                                 "multicast_group": {
                                     "name": getattr(multicast_group, 'name', ''),
                                     "mc_addr": getattr(multicast_group, 'mc_addr', ''),
                                     "mc_nwk_s_key": getattr(multicast_group, 'mc_nwk_s_key', ''),
                                     "mc_app_s_key": getattr(multicast_group, 'mc_app_s_key', ''),
                                     "f_cnt": getattr(multicast_group, 'f_cnt', ''),
                                     "group_type": getattr(multicast_group, 'group_type', ''),
                                     "mc_timeout": getattr(multicast_group, 'mc_timeout', ''),
                                     "application_id": getattr(multicast_group, 'application_id', ''),
                                     "description": getattr(multicast_group, 'description', ''),
                                     "tags": getattr(multicast_group, 'tags', {})
                                 }
                             })
        multicast_group.id = resp.id
        return

    def get_multicast_group(self, multicast_group_id: str) -> MulticastGroup | None:
        """
        Get multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.

        Returns
        -------
        - MulticastGroup object or None if not found.
        """
        try:
            response = self._call_rpc("MulticastGroupService", "Get",
                                     "GetMulticastGroupRequest", {"id": multicast_group_id})
            
            if not response or not hasattr(response, 'multicast_group'):
                return None
            
            # Import the enum here to avoid circular imports
            from chirpstack_api_wrapper.objects import MulticastGroupType
            
            # Find the enum value by comparing the response value
            group_type_enum = next((g for g in MulticastGroupType if g.value == response.multicast_group.group_type), MulticastGroupType.CLASS_C)
            
            multicast_group = MulticastGroup(
                name=getattr(response.multicast_group, 'name', ''),
                mc_addr=getattr(response.multicast_group, 'mc_addr', ''),
                mc_nwk_s_key=getattr(response.multicast_group, 'mc_nwk_s_key', ''),
                mc_app_s_key=getattr(response.multicast_group, 'mc_app_s_key', ''),
                f_cnt=getattr(response.multicast_group, 'f_cnt', ''),
                group_type=group_type_enum,
                mc_timeout=getattr(response.multicast_group, 'mc_timeout', ''),
                application_id=getattr(response.multicast_group, 'application_id', ''),
                id=getattr(response.multicast_group, 'id', ''),
                description=getattr(response.multicast_group, 'description', ''),
                tags=dict(getattr(response.multicast_group, 'tags', {}))
            )
            return multicast_group
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_multicast_group(): Multicast group {multicast_group_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_multicast_group(): An error occurred with status code {status_code} - {details}")
            return None

    def update_multicast_group(self, multicast_group: MulticastGroup) -> None:
        """
        Update a Multicast Group.

        Parameters
        ----------
        - multicast_group: The multicast group record to update.
        """
        if not isinstance(multicast_group, MulticastGroup):
            raise TypeError("Expected MulticastGroup object")
        
        return self._call_rpc("MulticastGroupService", "Update",
                             "UpdateMulticastGroupRequest", {
                                 "multicast_group": {
                                     "id": getattr(multicast_group, 'id', ''),
                                     "name": getattr(multicast_group, 'name', ''),
                                     "mc_addr": getattr(multicast_group, 'mc_addr', ''),
                                     "mc_nwk_s_key": getattr(multicast_group, 'mc_nwk_s_key', ''),
                                     "mc_app_s_key": getattr(multicast_group, 'mc_app_s_key', ''),
                                     "f_cnt": getattr(multicast_group, 'f_cnt', ''),
                                     "group_type": getattr(multicast_group, 'group_type', ''),
                                     "mc_timeout": getattr(multicast_group, 'mc_timeout', ''),
                                     "application_id": getattr(multicast_group, 'application_id', ''),
                                     "description": getattr(multicast_group, 'description', ''),
                                     "tags": getattr(multicast_group, 'tags', {})
                                 }
                             })

    def delete_multicast_group(self, multicast_group_id: str) -> None:
        """
        Delete a Multicast Group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        """
        return self._call_rpc("MulticastGroupService", "Delete",
                             "DeleteMulticastGroupRequest", {"id": multicast_group_id})

    def list_multicast_groups(self, application_id: str) -> list[MulticastGroup]:
        """
        List multicast groups for an application.

        Parameters
        ----------
        - application_id: Application ID.

        Returns
        -------
        - List of MulticastGroup objects.
        """
        # First list the MulticastGroup summary items for this application
        list_response = self._list_with_pagination("MulticastGroupService", 
                                                {"application_id": application_id}, 
                                                "ListMulticastGroupsRequest", 
                                                "result")
        multicast_groups = []
        
        # For each summary item, fetch the full MulticastGroup using Get
        for group_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "MulticastGroupService",
                    "Get",
                    request_type="GetMulticastGroupRequest",
                    params={"id": getattr(group_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "multicast_group"):
                    multicast_groups.append(MulticastGroup.from_grpc(get_resp.multicast_group))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_multicast_groups(): Failed to fetch full multicast group for id={getattr(group_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return multicast_groups

    def add_device_to_multicast_group(self, multicast_group_id: str, dev_eui: str) -> None:
        """
        Add a device to a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        - dev_eui: Device EUI.
        """
        return self._call_rpc("MulticastGroupService", "AddDevice",
                             "AddDeviceToMulticastGroupRequest", {
                                 "multicast_group_id": multicast_group_id,
                                 "dev_eui": dev_eui
                             })

    def remove_device_from_multicast_group(self, multicast_group_id: str, dev_eui: str) -> None:
        """
        Remove a device from a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        - dev_eui: Device EUI.
        """
        return self._call_rpc("MulticastGroupService", "RemoveDevice",
                             "RemoveDeviceFromMulticastGroupRequest", {
                                 "multicast_group_id": multicast_group_id,
                                 "dev_eui": dev_eui
                             })

    def add_gateway_to_multicast_group(self, multicast_group_id: str, gateway_id: str) -> None:
        """
        Add a gateway to a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        - gateway_id: Gateway ID.
        """
        return self._call_rpc("MulticastGroupService", "AddGateway",
                             "AddGatewayToMulticastGroupRequest", {
                                 "multicast_group_id": multicast_group_id,
                                 "gateway_id": gateway_id
                             })

    def remove_gateway_from_multicast_group(self, multicast_group_id: str, gateway_id: str) -> None:
        """
        Remove a gateway from a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        - gateway_id: Gateway ID.
        """
        return self._call_rpc("MulticastGroupService", "RemoveGateway",
                             "RemoveGatewayFromMulticastGroupRequest", {
                                 "multicast_group_id": multicast_group_id,
                                 "gateway_id": gateway_id
                             })

    def enqueue_multicast_downlink(self, multicast_group_id: str, data: bytes, 
                                  f_port: int, confirmed: bool = False) -> None:
        """
        Enqueue a downlink message for a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        - data: Downlink data.
        - f_port: Frame port.
        - confirmed: Whether the message requires confirmation.
        """
        return self._call_rpc("MulticastGroupService", "Enqueue",
                             "EnqueueMulticastQueueItemRequest", {
                                 "queue_item": {
                                     "multicast_group_id": multicast_group_id,
                                     "frm_payload": data,
                                     "f_port": f_port,
                                     "confirmed": confirmed
                                 }
                             })

    def get_multicast_group_queue(self, multicast_group_id: str) -> list:
        """
        Get the downlink queue for a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        """
        resp = self._call_rpc("MulticastGroupService", "ListQueue",
                             "ListMulticastGroupQueueItemsRequest", {"multicast_group_id": multicast_group_id})
        return list(resp.items)

    def flush_multicast_group_queue(self, multicast_group_id: str) -> None:
        """
        Flush the downlink queue for a multicast group.

        Parameters
        ----------
        - multicast_group_id: Multicast group ID.
        """
        return self._call_rpc("MulticastGroupService", "FlushQueue",
                             "FlushMulticastGroupQueueRequest", {"multicast_group_id": multicast_group_id})

    def create_fuota_deployment(self, fuota_deployment: FuotaDeployment) -> None:
        """
        Create a FUOTA deployment.

        Parameters
        ----------
        - fuota_deployment: The FUOTA deployment record to create.
        """
        if not isinstance(fuota_deployment, FuotaDeployment):
            raise TypeError("Expected FuotaDeployment object")
        
        resp = self._call_rpc("FuotaService", "CreateDeployment",
                             "CreateFuotaDeploymentRequest", {
                                 "deployment": {
                                     "name": getattr(fuota_deployment, 'name', ''),
                                     "application_id": getattr(fuota_deployment, 'application_id', ''),
                                     "device_profile_id": getattr(fuota_deployment, 'device_profile_id', ''),
                                     "multicast_group_id": getattr(fuota_deployment, 'multicast_group_id', ''),
                                     "multicast_group_type": getattr(fuota_deployment, 'multicast_group_type', ''),
                                     "mc_addr": getattr(fuota_deployment, 'mc_addr', ''),
                                     "mc_nwk_s_key": getattr(fuota_deployment, 'mc_nwk_s_key', ''),
                                     "mc_app_s_key": getattr(fuota_deployment, 'mc_app_s_key', ''),
                                     "f_cnt": getattr(fuota_deployment, 'f_cnt', ''),
                                     "group_type": getattr(fuota_deployment, 'group_type', ''),
                                     "dr": getattr(fuota_deployment, 'dr', ''),
                                     "frequency": getattr(fuota_deployment, 'frequency', ''),
                                     "class_c_timeout": getattr(fuota_deployment, 'class_c_timeout', ''),
                                     "description": getattr(fuota_deployment, 'description', ''),
                                     "tags": getattr(fuota_deployment, 'tags', {})
                                 }
                             })
        fuota_deployment.id = resp.id
        return

    def get_fuota_deployment(self, deployment_id: str) -> FuotaDeployment | None:
        """
        Get FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.

        Returns
        -------
        - FuotaDeployment object or None if not found.
        """
        try:
            response = self._call_rpc("FuotaService", "GetDeployment",
                                     "GetFuotaDeploymentRequest", {"id": deployment_id})
            
            if not response or not hasattr(response, 'deployment'):
                return None
            
            # Import the enum here to avoid circular imports
            from chirpstack_api_wrapper.objects import MulticastGroupType
            
            # Find the enum values by comparing the response values
            multicast_group_type_enum = next((m for m in MulticastGroupType if m.value == response.deployment.multicast_group_type), MulticastGroupType.CLASS_C)
            group_type_enum = next((g for g in MulticastGroupType if g.value == response.deployment.group_type), MulticastGroupType.CLASS_C)
            
            fuota_deployment = FuotaDeployment(
                name=getattr(response.deployment, 'name', ''),
                application_id=getattr(response.deployment, 'application_id', ''),
                device_profile_id=getattr(response.deployment, 'device_profile_id', ''),
                multicast_group_id=getattr(response.deployment, 'multicast_group_id', ''),
                multicast_group_type=multicast_group_type_enum,
                mc_addr=getattr(response.deployment, 'mc_addr', ''),
                mc_nwk_s_key=getattr(response.deployment, 'mc_nwk_s_key', ''),
                mc_app_s_key=getattr(response.deployment, 'mc_app_s_key', ''),
                f_cnt=getattr(response.deployment, 'f_cnt', ''),
                group_type=group_type_enum,
                dr=getattr(response.deployment, 'dr', ''),
                frequency=getattr(response.deployment, 'frequency', ''),
                class_c_timeout=getattr(response.deployment, 'class_c_timeout', ''),
                id=getattr(response.deployment, 'id', ''),
                description=getattr(response.deployment, 'description', ''),
                tags=dict(getattr(response.deployment, 'tags', {}))
            )
            return fuota_deployment
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_fuota_deployment(): Deployment {deployment_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_fuota_deployment(): An error occurred with status code {status_code} - {details}")
            return None

    def update_fuota_deployment(self, fuota_deployment: FuotaDeployment) -> None:
        """
        Update a FUOTA deployment.

        Parameters
        ----------
        - fuota_deployment: The FUOTA deployment record to update.
        """
        if not isinstance(fuota_deployment, FuotaDeployment):
            raise TypeError("Expected FuotaDeployment object")
        
        return self._call_rpc("FuotaService", "UpdateDeployment",
                             "UpdateFuotaDeploymentRequest", {
                                 "deployment": {
                                     "id": getattr(fuota_deployment, 'id', ''),
                                     "name": getattr(fuota_deployment, 'name', ''),
                                     "application_id": getattr(fuota_deployment, 'application_id', ''),
                                     "device_profile_id": getattr(fuota_deployment, 'device_profile_id', ''),
                                     "multicast_group_id": getattr(fuota_deployment, 'multicast_group_id', ''),
                                     "multicast_group_type": getattr(fuota_deployment, 'multicast_group_type', ''),
                                     "mc_addr": getattr(fuota_deployment, 'mc_addr', ''),
                                     "mc_nwk_s_key": getattr(fuota_deployment, 'mc_nwk_s_key', ''),
                                     "mc_app_s_key": getattr(fuota_deployment, 'mc_app_s_key', ''),
                                     "f_cnt": getattr(fuota_deployment, 'f_cnt', ''),
                                     "group_type": getattr(fuota_deployment, 'group_type', ''),
                                     "dr": getattr(fuota_deployment, 'dr', ''),
                                     "frequency": getattr(fuota_deployment, 'frequency', ''),
                                     "class_c_timeout": getattr(fuota_deployment, 'class_c_timeout', ''),
                                     "description": getattr(fuota_deployment, 'description', ''),
                                     "tags": getattr(fuota_deployment, 'tags', {})
                                 }
                             })

    def delete_fuota_deployment(self, deployment_id: str) -> None:
        """
        Delete a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.
        """
        return self._call_rpc("FuotaService", "DeleteDeployment",
                             "DeleteFuotaDeploymentRequest", {"id": deployment_id})

    def list_fuota_deployments(self, application_id: str) -> list[FuotaDeployment]:
        """
        List FUOTA deployments for an application.

        Parameters
        ----------
        - application_id: Application ID.

        Returns
        -------
        - List of FuotaDeployment objects.
        """
        # First list the FuotaDeployment summary items for this application
        list_response = self._list_with_pagination("FuotaService", 
                                                {"application_id": application_id}, 
                                                "ListFuotaDeploymentsRequest", 
                                                "result")
        fuota_deployments = []
        
        # For each summary item, fetch the full FuotaDeployment using Get
        for deployment_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "FuotaService",
                    "GetDeployment",
                    request_type="GetFuotaDeploymentRequest",
                    params={"id": getattr(deployment_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "deployment"):
                    fuota_deployments.append(FuotaDeployment.from_grpc(get_resp.deployment))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_fuota_deployments(): Failed to fetch full deployment for id={getattr(deployment_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return fuota_deployments

    def start_fuota_deployment(self, deployment_id: str) -> None:
        """
        Start a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.
        """
        return self._call_rpc("FuotaService", "StartDeployment",
                             "StartFuotaDeploymentRequest", {"id": deployment_id})

    def list_fuota_devices(self, deployment_id: str) -> list[dict]:
        """
        List devices in a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.

        Returns
        -------
        - List of FUOTA device dictionaries.
        """
        api_response = self._list_with_pagination("FuotaService", 
                                                {"deployment_id": deployment_id}, 
                                                "ListFuotaDevicesRequest", 
                                                "result")
        fuota_devices = []
        for device_item in api_response:
            fuota_device = {
                'dev_eui': getattr(device_item, 'dev_eui', ''),
                'created_at': getattr(device_item, 'created_at', ''),
                'updated_at': getattr(device_item, 'updated_at', '')
            }
            fuota_devices.append(fuota_device)
        return fuota_devices

    def list_fuota_gateways(self, deployment_id: str) -> list[dict]:
        """
        List gateways in a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.

        Returns
        -------
        - List of FUOTA gateway dictionaries.
        """
        api_response = self._list_with_pagination("FuotaService", 
                                                {"deployment_id": deployment_id}, 
                                                "ListFuotaGatewaysRequest", 
                                                "result")
        fuota_gateways = []
        for gateway_item in api_response:
            fuota_gateway = {
                'gateway_id': getattr(gateway_item, 'gateway_id', ''),
                'created_at': getattr(gateway_item, 'created_at', ''),
                'updated_at': getattr(gateway_item, 'updated_at', '')
            }
            fuota_gateways.append(fuota_gateway)
        return fuota_gateways

    def list_fuota_jobs(self, deployment_id: str) -> list[dict]:
        """
        List jobs in a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.

        Returns
        -------
        - List of FUOTA job dictionaries.
        """
        api_response = self._list_with_pagination("FuotaService", 
                                                {"deployment_id": deployment_id}, 
                                                "ListFuotaJobsRequest", 
                                                "result")
        fuota_jobs = []
        for job_item in api_response:
            fuota_job = {
                'id': getattr(job_item, 'id', ''),
                'created_at': getattr(job_item, 'created_at', ''),
                'updated_at': getattr(job_item, 'updated_at', '')
            }
            fuota_jobs.append(fuota_job)
        return fuota_jobs

    def add_devices_to_fuota(self, deployment_id: str, dev_euis: list) -> None:
        """
        Add devices to a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.
        - dev_euis: List of device EUIs.
        """
        return self._call_rpc("FuotaService", "AddDevices",
                             "AddFuotaDevicesRequest", {
                                 "deployment_id": deployment_id,
                                 "dev_euis": dev_euis
                             })

    def remove_devices_from_fuota(self, deployment_id: str, dev_euis: list) -> None:
        """
        Remove devices from a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.
        - dev_euis: List of device EUIs.
        """
        return self._call_rpc("FuotaService", "RemoveDevices",
                             "RemoveFuotaDevicesRequest", {
                                 "deployment_id": deployment_id,
                                 "dev_euis": dev_euis
                             })

    def add_gateways_to_fuota(self, deployment_id: str, gateway_ids: list) -> None:
        """
        Add gateways to a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.
        - gateway_ids: List of gateway IDs.
        """
        return self._call_rpc("FuotaService", "AddGateways",
                             "AddFuotaGatewaysRequest", {
                                 "deployment_id": deployment_id,
                                 "gateway_ids": gateway_ids
                             })

    def remove_gateways_from_fuota(self, deployment_id: str, gateway_ids: list) -> None:
        """
        Remove gateways from a FUOTA deployment.

        Parameters
        ----------
        - deployment_id: Deployment ID.
        - gateway_ids: List of gateway IDs.
        """
        return self._call_rpc("FuotaService", "RemoveGateways",
                             "RemoveFuotaGatewaysRequest", {
                                 "deployment_id": deployment_id,
                                 "gateway_ids": gateway_ids
                             })

    def create_device_profile_template(self, template: DeviceProfileTemplate) -> None:
        """
        Create a Device Profile Template.

        Parameters
        ----------
        - template: The device profile template record to create.
        """
        if not isinstance(template, DeviceProfileTemplate):
            raise TypeError("Expected DeviceProfileTemplate object")
        
        resp = self._call_rpc("DeviceProfileTemplateService", "Create",
                             "CreateDeviceProfileTemplateRequest", {
                                 "device_profile_template": {
                                     "name": getattr(template, 'name', ''),
                                     "vendor": getattr(template, 'vendor', ''),
                                     "firmware": getattr(template, 'firmware', ''),
                                     "region": getattr(template, 'region', Region.US915),
                                     "mac_version": getattr(template, 'mac_version', MacVersion.LORAWAN_1_0_0),
                                     "reg_params_revision": getattr(template, 'reg_params_revision', RegParamsRevision.B),
                                     "adr_algorithm_id": getattr(template, 'adr_algorithm_id', ''),
                                     "payload_codec_runtime": getattr(template, 'payload_codec_runtime', CodecRuntime.NONE),
                                     "uplink_interval": getattr(template, 'uplink_interval', 0),
                                     "supports_otaa": getattr(template, 'supports_otaa', False),
                                     "supports_class_b": getattr(template, 'supports_class_b', False),
                                     "supports_class_c": getattr(template, 'supports_class_c', False),
                                     "description": getattr(template, 'description', ''),
                                     "tags": getattr(template, 'tags', {})
                                 }
                             })
        template.id = resp.id
        return

    def get_device_profile_template(self, template_id: str) -> DeviceProfileTemplate | None:
        """
        Get device profile template.

        Parameters
        ----------
        - template_id: Template ID.

        Returns
        -------
        - DeviceProfileTemplate object or None if not found.
        """
        try:
            response = self._call_rpc("DeviceProfileTemplateService", "Get",
                                     "GetDeviceProfileTemplateRequest", {"id": template_id})
            
            if not response or not hasattr(response, 'device_profile_template'):
                return None
            
            # Import the enums here to avoid circular imports
            from chirpstack_api_wrapper.objects import Region, MacVersion, RegParamsRevision, CodecRuntime
            
            # Find the enum values by comparing the response values
            region_enum = next((r for r in Region if r.value == response.device_profile_template.region), Region.EU868)
            mac_version_enum = next((m for m in MacVersion if m.value == response.device_profile_template.mac_version), MacVersion.LORAWAN_1_0_0)
            reg_params_revision_enum = next((r for r in RegParamsRevision if r.value == response.device_profile_template.reg_params_revision), RegParamsRevision.A)
            payload_codec_runtime_enum = next((c for c in CodecRuntime if c.value == response.device_profile_template.payload_codec_runtime), CodecRuntime.NONE)
            
            template = DeviceProfileTemplate(
                name=getattr(response.device_profile_template, 'name', ''),
                vendor=getattr(response.device_profile_template, 'vendor', ''),
                firmware=getattr(response.device_profile_template, 'firmware', ''),
                region=region_enum,
                mac_version=mac_version_enum,
                reg_params_revision=reg_params_revision_enum,
                adr_algorithm_id=getattr(response.device_profile_template, 'adr_algorithm_id', ''),
                payload_codec_runtime=payload_codec_runtime_enum,
                uplink_interval=getattr(response.device_profile_template, 'uplink_interval', 0),
                supports_otaa=getattr(response.device_profile_template, 'supports_otaa', False),
                supports_class_b=getattr(response.device_profile_template, 'supports_class_b', False),
                supports_class_c=getattr(response.device_profile_template, 'supports_class_c', False),
                id=getattr(response.device_profile_template, 'id', ''),
                description=getattr(response.device_profile_template, 'description', ''),
                tags=dict(getattr(response.device_profile_template, 'tags', {}))
            )
            return template
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device_profile_template(): Template {template_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_device_profile_template(): An error occurred with status code {status_code} - {details}")
            return None

    def update_device_profile_template(self, template: DeviceProfileTemplate) -> None:
        """
        Update a Device Profile Template.

        Parameters
        ----------
        - template: The device profile template record to update.
        """
        if not isinstance(template, DeviceProfileTemplate):
            raise TypeError("Expected DeviceProfileTemplate object")
        
        return self._call_rpc("DeviceProfileTemplateService", "Update",
                             "UpdateDeviceProfileTemplateRequest", {
                                 "device_profile_template": {
                                     "id": getattr(template, 'id', ''),
                                     "name": getattr(template, 'name', ''),
                                     "vendor": getattr(template, 'vendor', ''),
                                     "firmware": getattr(template, 'firmware', ''),
                                     "region": getattr(template, 'region', Region.US915),
                                     "mac_version": getattr(template, 'mac_version', MacVersion.LORAWAN_1_0_0),
                                     "reg_params_revision": getattr(template, 'reg_params_revision', RegParamsRevision.B),
                                     "adr_algorithm_id": getattr(template, 'adr_algorithm_id', ''),
                                     "payload_codec_runtime": getattr(template, 'payload_codec_runtime', CodecRuntime.NONE),
                                     "uplink_interval": getattr(template, 'uplink_interval', 0),
                                     "supports_otaa": getattr(template, 'supports_otaa', False),
                                     "supports_class_b": getattr(template, 'supports_class_b', False),
                                     "supports_class_c": getattr(template, 'supports_class_c', False),
                                     "description": getattr(template, 'description', ''),
                                     "tags": getattr(template, 'tags', {})
                                 }
                             })

    def delete_device_profile_template(self, template_id: str) -> None:
        """
        Delete a Device Profile Template.

        Parameters
        ----------
        - template_id: Template ID.
        """
        return self._call_rpc("DeviceProfileTemplateService", "Delete",
                             "DeleteDeviceProfileTemplateRequest", {"id": template_id})

    def list_device_profile_templates(self) -> list[DeviceProfileTemplate]:
        """
        List all device profile templates.
        
        Returns
        -------
        - List of DeviceProfileTemplate objects.
        """
        # First list the DeviceProfileTemplate summary items
        list_response = self._list_with_pagination("DeviceProfileTemplateService", {}, "ListDeviceProfileTemplatesRequest", "result")
        templates = []
        
        # For each summary item, fetch the full DeviceProfileTemplate using Get
        for template_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "DeviceProfileTemplateService",
                    "Get",
                    request_type="GetDeviceProfileTemplateRequest",
                    params={"id": getattr(template_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "device_profile_template"):
                    templates.append(DeviceProfileTemplate.from_grpc(get_resp.device_profile_template))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_device_profile_templates(): Failed to fetch full template for id={getattr(template_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return templates

    def create_relay(self, relay: Relay) -> None:
        """
        Create a Relay.

        Parameters
        ----------
        - relay: The relay record to create.
        """
        if not isinstance(relay, Relay):
            raise TypeError("Expected Relay object")
        
        resp = self._call_rpc("RelayService", "Create",
                             "CreateRelayRequest", {
                                 "relay": {
                                     "name": getattr(relay, 'name', ''),
                                     "tenant_id": getattr(relay, 'tenant_id', ''),
                                     "device_id": getattr(relay, 'device_id', ''),
                                     "description": getattr(relay, 'description', ''),
                                     "tags": getattr(relay, 'tags', {})
                                 }
                             })
        relay.id = resp.id
        return

    def get_relay(self, relay_id: str) -> Relay | None:
        """
        Get relay.

        Parameters
        ----------
        - relay_id: Relay ID.

        Returns
        -------
        - Relay object or None if not found.
        """
        try:
            response = self._call_rpc("RelayService", "Get",
                                     "GetRelayRequest", {"id": relay_id})
            
            if not response or not hasattr(response, 'relay'):
                return None
            
            relay = Relay(
                name=getattr(response.relay, 'name', ''),
                tenant_id=getattr(response.relay, 'tenant_id', ''),
                device_id=getattr(response.relay, 'device_id', ''),
                id=getattr(response.relay, 'id', ''),
                description=getattr(response.relay, 'description', ''),
                tags=dict(getattr(response.relay, 'tags', {}))
            )
            return relay
            
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_relay(): Relay {relay_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_relay(): An error occurred with status code {status_code} - {details}")
            return None

    def update_relay(self, relay: Relay) -> None:
        """
        Update a Relay.

        Parameters
        ----------
        - relay: The relay record to update.
        """
        if not isinstance(relay, Relay):
            raise TypeError("Expected Relay object")
        
        return self._call_rpc("RelayService", "Update",
                             "UpdateRelayRequest", {
                                 "relay": {
                                     "id": getattr(relay, 'id', ''),
                                     "name": getattr(relay, 'name', ''),
                                     "tenant_id": getattr(relay, 'tenant_id', ''),
                                     "device_id": getattr(relay, 'device_id', ''),
                                     "description": getattr(relay, 'description', ''),
                                     "tags": getattr(relay, 'tags', {})
                                 }
                             })

    def delete_relay(self, relay_id: str) -> None:
        """
        Delete a Relay.

        Parameters
        ----------
        - relay_id: Relay ID.
        """
        return self._call_rpc("RelayService", "Delete",
                             "DeleteRelayRequest", {"id": relay_id})

    def list_relays(self, tenant_id: str) -> list[Relay]:
        """
        List relays for a tenant.

        Parameters
        ----------
        - tenant_id: Tenant ID.

        Returns
        -------
        - List of Relay objects.
        """
        # First list the Relay summary items for this tenant
        list_response = self._list_with_pagination("RelayService", 
                                                {"tenant_id": tenant_id}, 
                                                "ListRelaysRequest", 
                                                "result")
        relays = []
        
        # For each summary item, fetch the full Relay using Get
        for relay_item in list_response:
            try:
                get_resp = self._call_rpc(
                    "RelayService",
                    "Get",
                    request_type="GetRelayRequest",
                    params={"id": getattr(relay_item, "id", "")}
                )
                if get_resp and hasattr(get_resp, "relay"):
                    relays.append(Relay.from_grpc(get_resp.relay))
            except grpc.RpcError as e:
                logging.error(
                    f"ChirpstackClient.list_relays(): Failed to fetch full relay for id={getattr(relay_item, 'id', '')} - {e.code()} {e.details()}"
                )
                continue
        return relays

    def list_relay_devices(self, relay_id: str) -> list[dict]:
        """
        List devices for a relay.

        Parameters
        ----------
        - relay_id: Relay ID.

        Returns
        -------
        - List of relay device dictionaries.
        """
        api_response = self._list_with_pagination("RelayService", 
                                                {"relay_id": relay_id}, 
                                                "ListRelayDevicesRequest", 
                                                "result")
        relay_devices = []
        for device_item in api_response:
            relay_device = {
                'dev_eui': getattr(device_item, 'dev_eui', ''),
                'created_at': getattr(device_item, 'created_at', ''),
                'updated_at': getattr(device_item, 'updated_at', '')
            }
            relay_devices.append(relay_device)
        return relay_devices

    def add_device_to_relay(self, relay_id: str, dev_eui: str) -> None:
        """
        Add a device to a relay.

        Parameters
        ----------
        - relay_id: Relay ID.
        - dev_eui: Device EUI.
        """
        return self._call_rpc("RelayService", "AddDevice",
                             "AddRelayDeviceRequest", {
                                 "relay_id": relay_id,
                                 "dev_eui": dev_eui
                             })

    def remove_device_from_relay(self, relay_id: str, dev_eui: str) -> None:
        """
        Remove a device from a relay.

        Parameters
        ----------
        - relay_id: Relay ID.
        - dev_eui: Device EUI.
        """
        return self._call_rpc("RelayService", "RemoveDevice",
                             "RemoveRelayDeviceRequest", {
                                 "relay_id": relay_id,
                                 "dev_eui": dev_eui
                             })

    def refresh_token(self, e: grpc.RpcError, method, *args, **kwargs):
        """
        Handle exception of ExpiredSignature, by logging into the server to refresh the jwt auth token
        and calling the method again that raised the exception.

        Parameters
        ----------
        - e: The RpcError thrown.
        - method: The ChirpstackClient method to call after the token is refreshed.
        - *args: Arguments that will be inputted to method.
        - **kwargs: Key Word Arguments that will be inputted to method.
        """
        # Handle the exception here
        status_code, details = e.code(), e.details()

        # Don't attempt token refresh for NOT_FOUND errors - these are legitimate API responses
        if status_code == grpc.StatusCode.NOT_FOUND:
            logging.error(f"ChirpstackClient.{method.__name__}(): Object not found - {details}")
            raise e  # Re-raise the original exception
        
        if status_code == grpc.StatusCode.UNAUTHENTICATED and "ExpiredSignature" in details:
            # Retry login and then re-run the specified method
            logging.warning(f"ChirpstackClient.{method.__name__}():JWT token expired. Retrying login...")
            self.auth_token = self.login()  # Update auth_token with the new token
            time.sleep(2)  # Introduce a short delay before retrying
            return method(*args, **kwargs)  # Re-run the specified method with the same parameters
        elif not self.login_on_init:
            self.auth_token = self.login() #login, since client didn't on init
            time.sleep(2)  # Introduce a short delay before retrying
            return method(*args, **kwargs)  # Re-run the specified method with the same parameters

        logging.error(f"ChirpstackClient.{method.__name__}(): Unknown error occurred with status code {status_code} - {details}")
        raise Exception(f"The JWT token failed to be refreshed")

    def list_all_device_profiles(self, tenants: list[Tenant]) -> list[DeviceProfile]:
        """
        List all device profiles.

        Parameters
        ----------
        - tenants: List of Tenant objects from ChirpstackClient.list_all_tenants().

        Returns
        -------
        - List of DeviceProfile objects.
        """
        device_profiles = []
        for tenant in tenants:
            # First list the DeviceProfile summary items for this tenant
            list_response = self._list_with_pagination(
                "DeviceProfileService",
                {"tenant_id": tenant.id},
                "ListDeviceProfilesRequest"
            )

            # For each summary item, fetch the full DeviceProfile using Get
            for profile_item in list_response:
                try:
                    get_resp = self._call_rpc(
                        "DeviceProfileService",
                        "Get",
                        request_type="GetDeviceProfileRequest",
                        params={"id": getattr(profile_item, "id", "")}
                    )
                    if get_resp and hasattr(get_resp, "device_profile"):
                        device_profiles.append(DeviceProfile.from_grpc(get_resp.device_profile))
                except grpc.RpcError as e:
                    logging.error(
                        f"ChirpstackClient.list_all_device_profiles(): Failed to fetch full profile for id={getattr(profile_item, 'id', '')} - {e.code()} {e.details()}"
                    )
                    continue
        return device_profiles
    
    def list_all_gateways(self, tenants: list[Tenant]) -> list[Gateway]:
        """
        List all gateways.

        Parameters
        ----------
        - tenants: List of Tenant objects from ChirpstackClient.list_all_tenants().

        Returns
        -------
        - List of Gateway objects.
        """
        gateways = []
        for tenant in tenants:
            # First list the Gateway summary items for this tenant
            list_response = self._list_with_pagination(
                "GatewayService",
                {"tenant_id": tenant.id},
                "ListGatewaysRequest"
            )
            
            # For each summary item, fetch the full Gateway using Get
            for gateway_item in list_response:
                try:
                    get_resp = self._call_rpc(
                        "GatewayService",
                        "Get",
                        request_type="GetGatewayRequest",
                        params={"gateway_id": getattr(gateway_item, "gateway_id", "")}
                    )
                    if get_resp and hasattr(get_resp, "gateway"):
                        gateways.append(Gateway.from_grpc(get_resp.gateway))
                except grpc.RpcError as e:
                    logging.error(
                        f"ChirpstackClient.list_all_gateways(): Failed to fetch full gateway for gateway_id={getattr(gateway_item, 'gateway_id', '')} - {e.code()} {e.details()}"
                    )
                    continue
        return gateways