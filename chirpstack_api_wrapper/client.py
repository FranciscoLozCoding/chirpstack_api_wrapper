"""Abstraction layer over chirpstack_api"""
import grpc
import logging
import sys
import os
import time
import requests
from grpc import _channel as channel
from google.protobuf.json_format import ParseDict
from google.protobuf import empty_pb2
from chirpstack_api import api
from chirpstack_api_wrapper.objects import *

#TODO: Refactor based on chatgpt suggestions: https://chatgpt.com/c/689ff792-55c8-832c-9afa-7ac1f6e504b3
#TODO: Expand the client to include all chirpstack api(s) and methods.

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

    def list_all_devices(self, apps: list[api.ApplicationListItem]) -> list[api.DeviceListItem]:
        """
        List all devices.

        Parameters
        ----------
        - app_resp: Response of ChirpstackClient.list_all_apps().
        """
        devices = []
        for app in apps:
            devices.extend(
                self._list_with_pagination(
                    "DeviceService",
                    {"application_id": app.id},
                    "ListDevicesRequest"
                )
            )
        return devices

    def list_all_apps(self, tenants: list[api.TenantListItem]) -> list[api.ApplicationListItem]:
        """
        List all apps.

        Parameters
        ----------
        - tenant_resp: Response of ChirpstackClient.list_tenants().
        """
        apps = []
        for t in tenants:
            apps.extend(
                self._list_with_pagination(
                    "ApplicationService",
                    {"tenant_id": t.id},
                    "ListApplicationsRequest"
                )
            )
        return apps

    def list_tenants(self) -> list[api.TenantListItem]:
        """
        List all tenants.
        """
        return self._list_with_pagination("TenantService", {}, "ListTenantsRequest")

    def get_app(self, app_id: api.Application | str) -> api.GetApplicationResponse | dict:
        """
        Get application.

        Parameters
        ----------
        - app_id: unique identifier of the app.
            Passing in an Application object will also work.
        """
        try:
            return self._call_rpc("ApplicationService", "Get",
                                 "GetApplicationRequest", {"id": str(app_id)})
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_app(): Application {app_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_app(): An error occurred with status code {status_code} - {details}")
            return {}

    def get_device(self, dev_eui: api.Device | str) -> api.GetDeviceResponse | dict:
        """
        Get device.

        Parameters
        ----------
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.
        """
        try:
            return self._call_rpc("DeviceService", "Get",
                             "GetDeviceRequest", {"dev_eui": str(dev_eui)})
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device(): Device {dev_eui} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_app(): An error occurred with status code {status_code} - {details}")
            return {}
        
    def get_device_profile(self, device_profile_id: api.DeviceProfile | str) -> api.GetDeviceProfileResponse | dict:
        """
        Get device profile.

        Parameters
        ----------
        - device_profile_id: unique identifier of the device profile.
            Passing in a Device Profile object will also work.
        """
        try:
            return self._call_rpc("DeviceProfileService", "Get",
                                 "GetDeviceProfileRequest", {"id": str(device_profile_id)})
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device_profile(): Device Profile {device_profile_id} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_device_profile(): An error occurred with status code {status_code} - {details}")
            return {}
        
    def get_device_app_key(self, deveui: api.Device | str, lw_v: MacVersion | int) -> str:
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

    def get_device_activation(self, deveui: api.Device | str) -> api.GetDeviceActivationResponse | dict:
        """
        Get Activation returns the current activation details of the device (OTAA or ABP).

        Parameters
        ----------
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.
        """
        try:
            return self._call_rpc("DeviceService", "GetActivation",
                                 "GetDeviceActivationRequest", {"dev_eui": str(deveui)})
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()
            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_device_activation(): Device Activation {deveui} not found - {details}")
            else:
                logging.error(f"ChirpstackClient.get_device_profile(): An error occurred with status code {status_code} - {details}")
            return {}

    def get_gateway(self, gateway_id: api.Gateway | str) -> api.GetGatewayResponse | dict:
        """
        Get gateway.

        Parameters
        ----------
        - gateway_id (EUI64): Unique identifier for the gateway.
            Passing in a Gateway object will also work.
        """
        try:
            return self._call_rpc("GatewayService", "Get",
                                 "GetGatewayRequest", {"gateway_id": str(gateway_id)})
        except grpc.RpcError as e:
            status_code, details = e.code(), e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error(f"ChirpstackClient.get_gateway(): Gateway {gateway_id} not found - {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self._get_gateway, gateway_id)
            else:
                logging.error(f"ChirpstackClient.get_gateway(): An error occurred with status code {status_code} - {details}")
            return {}
    
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
                                            "name": app.name,
                                            "description": app.description,
                                            "tenant_id": app.tenant_id,
                                            "tags": app.tags
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
                                            "name": device_profile.name,
                                            "tenant_id": device_profile.tenant_id,
                                            "region": device_profile.region,
                                            "mac_version": device_profile.mac_version,
                                            "reg_params_revision": device_profile.reg_params_revision,
                                            "uplink_interval": device_profile.uplink_interval,
                                            "supports_otaa": device_profile.supports_otaa,
                                            "abp_rx1_delay": device_profile.abp_rx1_delay if device_profile.abp_rx1_delay is not None else 0,
                                            "abp_rx1_dr_offset": device_profile.abp_rx1_dr_offset if device_profile.abp_rx1_dr_offset is not None else 0,
                                            "abp_rx2_dr": device_profile.abp_rx2_dr if device_profile.abp_rx2_dr is not None else 0,
                                            "abp_rx2_freq": device_profile.abp_rx2_freq if device_profile.abp_rx2_freq is not None else 0,
                                            "supports_class_b": device_profile.supports_class_b,
                                            "class_b_timeout": device_profile.class_b_timeout if device_profile.class_b_timeout is not None else 0,
                                            "class_b_ping_slot_nb_k": device_profile.class_b_ping_slot_nb_k if device_profile.class_b_ping_slot_nb_k is not None else 0,
                                            "class_b_ping_slot_dr": device_profile.class_b_ping_slot_dr if device_profile.class_b_ping_slot_dr is not None else 0,
                                            "class_b_ping_slot_freq": device_profile.class_b_ping_slot_freq if device_profile.class_b_ping_slot_freq is not None else 0,
                                            "supports_class_c": device_profile.supports_class_c,
                                            "class_c_timeout": device_profile.class_c_timeout if device_profile.class_c_timeout is not None else 0,
                                            "description": device_profile.description,
                                            "payload_codec_runtime": device_profile.payload_codec_runtime,
                                            "payload_codec_script": device_profile.payload_codec_script,
                                            "flush_queue_on_activate": device_profile.flush_queue_on_activate,
                                            "device_status_req_interval": device_profile.device_status_req_interval,
                                            "auto_detect_measurements": device_profile.auto_detect_measurements,
                                            "allow_roaming": device_profile.allow_roaming,
                                            "adr_algorithm_id": device_profile.adr_algorithm_id,
                                            "tags": device_profile.tags
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
                                            "name": device.name,
                                            "dev_eui": device.dev_eui,
                                            "application_id": device.application_id,
                                            "device_profile_id": device.device_profile_id,
                                            "join_eui": device.join_eui,
                                            "description": device.description,
                                            "skip_fcnt_check": device.skip_fcnt_check,
                                            "is_disabled": device.is_disabled,
                                            "tags": device.tags,
                                            "variables": device.variables
                                        }
                                    })
        device.dev_eui = resp.dev_eui #attach chirp generated dev_eui to device object
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
                                    "dev_eui": device_keys.dev_eui,
                                    "nwk_key": device_keys.nwk_key,
                                    "app_key": device_keys.app_key
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
        
        resp = self._call_rpc("GatewayService", "Create",
                                    "CreateGatewayRequest", {
                                        "gateway": {
                                            "gateway_id": gateway.gateway_id,
                                            "name": gateway.name,
                                            "description": gateway.description,
                                            "tenant_id": gateway.tenant_id,
                                            "stats_interval": gateway.stats_interval,
                                            "tags": gateway.tags
                                        }
                                    })
        gateway.id = resp.id #attach chirp generated uuid to gateway object
        return
    
    def delete_app(self, app_id: api.Application | str) -> None:
        """
        Delete an Application.

        Parameters
        ----------
        - app_id: unique identifier of the application.
            Passing in an Application object will also work.
        """
        return self._call_rpc("ApplicationService", "Delete",
                             "DeleteApplicationRequest", {"id": str(app_id)})

    def delete_device(self, dev_eui: api.Device | str) -> None:
        """
        Delete a Device.

        Parameters
        ----------
        - dev_eui: The unique identifier of the device to delete.
            Passing in a Device object will also work.
        """
        return self._call_rpc("DeviceService", "Delete",
                             "DeleteDeviceRequest", {"dev_eui": str(dev_eui)})

    def delete_device_profile(self, device_profile_id: api.DeviceProfile | str) -> None:
        """
        Delete a Device Profile.

        Parameters
        ----------
        - device_profile_id: unique identifier of the device profile.
            Passing in a Device Profile object will also work.
        """
        return self._call_rpc("DeviceProfileService", "Delete",
                             "DeleteDeviceProfileRequest", {"id": str(device_profile_id)})

    def delete_gateway(self, gateway_id: api.Gateway | str) -> None:
        """
        Delete a Gateway.

        Parameters
        ----------
        - gateway_id (EUI64): Unique identifier for the gateway.
            Passing in a Gateway object will also work.
        """
        return self._call_rpc("GatewayService", "Delete",
                             "DeleteGatewayRequest", {"id": str(gateway_id)})

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