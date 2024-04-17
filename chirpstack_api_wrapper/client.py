"""Abstraction layer over chirpstack_api"""
import grpc
import logging
import sys
import os
import time
from grpc import _channel as channel
from chirpstack_api import api
from chirpstack_api_wrapper.objects import *

#Pagination
LIMIT = 100 #Max number of records to return in the result-set.
OFFSET = LIMIT #Offset in the result-set (setting offset=limit goes to the next set of records aka next page)

class ChirpstackClient:
    """
    Chirpstack client to call Api(s).

    Params:
    - email: The email of the Account that will be used to call the Api(s).
    - password: The password of the Account that will be used to call the Api(s).
    - api_endpoint: The Chirpstack grpc api endpoint (usually port 8080).
    """
    def __init__(self, email:str, password:str, api_endpoint:str):
        """Constructor method to initialize a ChirpstackClient object."""   
        self.server = api_endpoint
        self.channel = grpc.insecure_channel(self.server)
        self.email = email
        self.password = password
        self.auth_token = self.login()

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
                logging.error("ChirpstackClient.login(): Service is unavailable. This might be a DNS resolution issue.")
                logging.error(f"    Details: {details}")
            else:
                logging.error(f"ChirpstackClient.login(): An error occurred with status code {status_code}")
                logging.error(f"    Details: {details}")

            # Exit with a non-zero status code to indicate failure
            sys.exit(1)
        except Exception as e:
            # Handle other exceptions if needed
            logging.error(f"ChirpstackClient.login(): An error occurred: {e}")

            # Exit with a non-zero status code to indicate failure
            sys.exit(1)
                
        logging.info("ChirpstackClient.login(): Connected to Chirpstack Server")

        return resp.jwt

    def list_all_devices(self,app_resp: dict) -> dict:
        """
        List all devices.

        Params:
        - app_resp: Response of ChirpstackClient.list_all_apps().
        """
        client = api.DeviceServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        devices = []
        for app in app_resp:
            # Construct request.
            req = api.ListDevicesRequest()
            req.limit = LIMIT
            req.offset = 0 #get first page
            req.application_id = app.id #Application ID (UUID) to filter devices on.
            #req.search = "" #If set, the given string will be used to search on name (optional).

            try:
                devices.extend(self.List_agg_pagination(client,req,metadata))
            except grpc.RpcError as e:
                return self.refresh_token(e, self.list_all_devices, app_resp)

        return devices

    def list_all_apps(self,tenant_resp: dict) -> dict:
        """
        List all apps.

        Params:
        - tenant_resp: Response of ChirpstackClient.list_tenants().
        """
        client = api.ApplicationServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        apps = []

        for tenant in tenant_resp:
            # Construct request
            req = api.ListApplicationsRequest()
            req.limit = LIMIT
            req.offset = 0 #get first page
            req.tenant_id = tenant.id #Tenant ID to list the applications for.
            #req.search = "" #If set, the given string will be used to search on name (optional).

            try:
                apps.extend(self.List_agg_pagination(client,req,metadata))
            except grpc.RpcError as e:
                return self.refresh_token(e, self.list_all_apps, tenant_resp)

        return apps

    def list_tenants(self) -> dict:
        """
        List all tenants.
        """
        client = api.TenantServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.ListTenantsRequest()
        req.limit = LIMIT
        req.offset = 0 #get first page
        #req.search = "" #If set, the given string will be used to search on name (optional).
        #req.user_id = "" #If set, filters the result set to the tenants of the user. Only global API keys are able to filter by this field.

        try:
            return self.List_agg_pagination(client,req,metadata)
        except grpc.RpcError as e:
            return self.refresh_token(e, self.list_tenants)

    def get_device(self, dev_eui: str) -> dict:
        """
        Get device.

        Params:
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.
        """
        client = api.DeviceServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.GetDeviceRequest()
        req.dev_eui = str(dev_eui)

        try:
            return client.Get(req, metadata=metadata)
        except grpc.RpcError as e:

            status_code = e.code()
            details = e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error("ChirpstackClient.get_device(): The device does not exist")
                logging.error(f"    Details: {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self.get_device, dev_eui)
            else:
                logging.error(f"ChirpstackClient.get_device(): An error occurred with status code {status_code}")
                logging.error(f"    Details: {details}")
            
            return {}

    def get_device_profile(self,device_profile_id: str) -> dict:
        """
        Get device profile.

        Params:
        - device_profile_id: unique identifier of the device profile.
            Passing in a Device Profile object will also work.
        """
        client = api.DeviceProfileServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.GetDeviceProfileRequest()
        req.id = str(device_profile_id)

        try:
            return client.Get(req, metadata=metadata)
        except grpc.RpcError as e:

            status_code = e.code()
            details = e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error("ChirpstackClient.get_device_profile(): The device profile does not exist")
                logging.error(f"    Details: {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self.get_device_profile, device_profile_id)
            else:
                logging.error(f"ChirpstackClient.get_device_profile(): An error occurred with status code {status_code}")
                logging.error(f"    Details: {details}")
            
            return {}
    
    def get_device_app_key(self,deveui: str,lw_v: int) -> str:
        """
        Get device Application key (Only OTAA).

        Params:
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.
        - lw_v: The lorawan version the device is using. 
            input directly from ChirpstackClient.get_device_profile() output or use MacVersion Object.
        """
        client = api.DeviceServiceStub(self.channel)

        #define the JWT key metadata
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #construct request
        req = api.GetDeviceKeysRequest()
        req.dev_eui = str(deveui)

        try:
            resp = client.GetKeys(req, metadata=metadata)
        except grpc.RpcError as e:

            status_code = e.code()
            details = e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error("ChirpstackClient.get_device_app_key(): The device key does not exist. It is possible that the device is using ABP which does not use an application key")
                logging.error(f"    Details: {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self.get_device_app_key, deveui, lw_v)
            else:
                logging.error(f"ChirpstackClient.get_device_app_key(): An error occurred with status code {status_code}")
                logging.error(f"    Details: {details}")

            return
        except Exception as e:
            # Handle other exceptions
            logging.error(f"ChirpstackClient.get_device_app_key(): An error occurred: {e}")
            return
        
        # what key to return is based on lorawan version (For LoRaWAN 1.1 devices return app_key)
        # < 5 is lorawan 1.0.x
        return resp.device_keys.nwk_key if lw_v < 5 else resp.device_keys.app_key

    def get_device_activation(self,deveui: str) -> dict:
        """
        Get Activation returns the current activation details of the device (OTAA or ABP).

        Params:
        - dev_eui: unique identifier of the device.
            Passing in a Device object will also work.
        """
        client = api.DeviceServiceStub(self.channel)

        #define the JWT key metadata
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #construct request
        req = api.GetDeviceActivationRequest()
        req.dev_eui = str(deveui)

        try:
            return client.GetActivation(req, metadata=metadata)
        except grpc.RpcError as e:

            status_code = e.code()
            details = e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error("ChirpstackClient.get_device_activation(): The device activation does not exist")
                logging.error(f"    Details: {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self.get_device_activation, deveui)
            else:
                logging.error(f"ChirpstackClient.get_device_activation(): An error occurred with status code {status_code}")
                logging.error(f"    Details: {details}")
            
            return {}

    def get_gateway(self,gateway_id:str) -> dict:
        """
        Get gateway.

        Params:
        - gateway_id (EUI64): Unique identifier for the gateway.
            Passing in a Gateway object will also work.
        """
        client = api.GatewayServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.GetGatewayRequest()
        req.gateway_id = str(gateway_id)

        try:
            return client.Get(req, metadata=metadata)
        except grpc.RpcError as e:

            status_code = e.code()
            details = e.details()

            if status_code == grpc.StatusCode.NOT_FOUND:
                logging.error("ChirpstackClient.get_gateway(): The gateway does not exist")
                logging.error(f"    Details: {details}")
            elif status_code == grpc.StatusCode.UNAUTHENTICATED:
                return self.refresh_token(e, self.get_gateway, gateway_id)
            else:
                logging.error(f"ChirpstackClient.get_gateway(): An error occurred with status code {status_code}")
                logging.error(f"    Details: {details}")
            
            return {}

    def create_app(self,app:Application) -> None:
        """
        Create an Application.

        Params:
        - app: The app record to create.
        """
        if not isinstance(app, Application):
            raise TypeError("Expected Application object")

        client = api.ApplicationServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.CreateApplicationRequest()
        req.application.name = app.name
        req.application.description = app.description
        req.application.tenant_id = app.tenant_id
        req.application.tags.update(app.tags)

        try:
            resp = client.Create(req, metadata=metadata)
            app.id = resp.id #attach chirp generated uuid to app object
            return 
        except grpc.RpcError as e:
            return self.refresh_token(e, self.create_app, app)

    def create_device_profile(self,device_profile:DeviceProfile) -> None:
        """
        Create a Device Profile.

        Params:
        - device_profile: The device profile record to create.
        """
        if not isinstance(device_profile, DeviceProfile):
            raise TypeError("Expected DeviceProfile object")

        client = api.DeviceProfileServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.CreateDeviceProfileRequest()
        req.device_profile.name = device_profile.name
        req.device_profile.tenant_id = device_profile.tenant_id
        req.device_profile.region = device_profile.region
        req.device_profile.mac_version = device_profile.mac_version
        req.device_profile.reg_params_revision = device_profile.reg_params_revision
        req.device_profile.uplink_interval = device_profile.uplink_interval
        req.device_profile.supports_otaa = device_profile.supports_otaa
        req.device_profile.abp_rx1_delay = device_profile.abp_rx1_delay if device_profile.abp_rx1_delay is not None else 0
        req.device_profile.abp_rx1_dr_offset = device_profile.abp_rx1_dr_offset if device_profile.abp_rx1_dr_offset is not None else 0
        req.device_profile.abp_rx2_dr = device_profile.abp_rx2_dr if device_profile.abp_rx2_dr is not None else 0
        req.device_profile.abp_rx2_freq = device_profile.abp_rx2_freq if device_profile.abp_rx2_freq is not None else 0
        req.device_profile.supports_class_b = device_profile.supports_class_b
        req.device_profile.class_b_timeout = device_profile.class_b_timeout if device_profile.class_b_timeout is not None else 0
        req.device_profile.class_b_ping_slot_nb_k = device_profile.class_b_ping_slot_nb_k if device_profile.class_b_ping_slot_nb_k is not None else 0
        req.device_profile.class_b_ping_slot_dr = device_profile.class_b_ping_slot_dr if device_profile.class_b_ping_slot_dr is not None else 0
        req.device_profile.class_b_ping_slot_freq = device_profile.class_b_ping_slot_freq if device_profile.class_b_ping_slot_freq is not None else 0
        req.device_profile.supports_class_c = device_profile.supports_class_c
        req.device_profile.class_c_timeout = device_profile.class_c_timeout if device_profile.class_c_timeout is not None else 0
        req.device_profile.description = device_profile.description
        req.device_profile.payload_codec_runtime = device_profile.payload_codec_runtime
        req.device_profile.payload_codec_script = device_profile.payload_codec_script
        req.device_profile.flush_queue_on_activate = device_profile.flush_queue_on_activate
        req.device_profile.device_status_req_interval = device_profile.device_status_req_interval
        req.device_profile.auto_detect_measurements = device_profile.auto_detect_measurements
        req.device_profile.allow_roaming = device_profile.allow_roaming
        req.device_profile.adr_algorithm_id = device_profile.adr_algorithm_id
        req.device_profile.tags.update(device_profile.tags)

        try:
            resp = client.Create(req, metadata=metadata)
            device_profile.id = resp.id #attach chirp generated uuid to device profile object
            return 
        except grpc.RpcError as e:
            return self.refresh_token(e, self.create_device_profile, device_profile)

    def create_device(self,device:Device) -> None:
        """
        Create a Device.

        Params:
        - device: The device record to create.
        """
        if not isinstance(device, Device):
            raise TypeError("Expected Device object")

        client = api.DeviceServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.CreateDeviceRequest()
        req.device.name = device.name
        req.device.dev_eui = device.dev_eui
        req.device.application_id = device.application_id
        req.device.device_profile_id = device.device_profile_id
        req.device.join_eui = device.join_eui
        req.device.description = device.description
        req.device.skip_fcnt_check = device.skip_fcnt_check
        req.device.is_disabled = device.is_disabled
        req.device.tags.update(device.tags)
        req.device.variables.update(device.variables)

        try:
            return client.Create(req, metadata=metadata)
        except grpc.RpcError as e:
            return self.refresh_token(e, self.create_device, device)

    def create_device_keys(self,device_keys:DeviceKeys) -> None:
        """
        Create device keys.

        Params:
        - device_keys: The device keys record to create.
        """
        client = api.DeviceServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.CreateDeviceKeysRequest()
        req.device_keys.dev_eui = device_keys.dev_eui
        req.device_keys.nwk_key = device_keys.nwk_key
        req.device_keys.app_key = device_keys.app_key

        try:
            return client.CreateKeys(req, metadata=metadata)
        except grpc.RpcError as e:
            return self.refresh_token(e, self.create_device_keys, device_keys)

    def create_gateway(self,gateway:Gateway) -> None:
        """
        Create a Gateway.

        Params:
        - gateway: The gateway record to create.
        """
        if not isinstance(gateway, Gateway):
            raise TypeError("Expected Gateway object")

        client = api.GatewayServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.CreateGatewayRequest()
        req.gateway.gateway_id = gateway.gateway_id
        req.gateway.name = gateway.name
        req.gateway.description = gateway.description
        req.gateway.tenant_id = gateway.tenant_id
        req.gateway.stats_interval = gateway.stats_interval
        req.gateway.tags.update(gateway.tags)

        try:
            return client.Create(req, metadata=metadata)
        except grpc.RpcError as e:
            return self.refresh_token(e, self.create_gateway, gateway)

    def delete_device(self, dev_eui:str) -> None:
        """
        Delete a Device.

        Params:
        - dev_eui: The unique identifier of the device to delete.
            Passing in a Device object will also work.
        """
        client = api.DeviceServiceStub(self.channel)

        # Define the JWT key metadata.
        metadata = [("authorization", "Bearer %s" % self.auth_token)]

        #Construct request
        req = api.DeleteDeviceRequest()
        req.dev_eui = str(dev_eui)

        try:
            return client.Delete(req, metadata=metadata)
        except grpc.RpcError as e:
            return self.refresh_token(e, self.delete_device, dev_eui)

    @staticmethod
    def List_agg_pagination(client,req,metadata) -> dict:
        """
        This method aggregates all the result-sets in pagination from rpc List into one list.
        """
        records=[]
        while True:
            resp = client.List(req, metadata=metadata)
            records.extend(resp.result)

            req.offset += OFFSET

            if (len(records) == resp.total_count):
                break

        return records

    def refresh_token(self, e: grpc.RpcError, method, *args, **kwargs):
        """
        Handle exception of ExpiredSignature, by logging into the server to refresh the jwt auth token
        and calling the method again that raised the exception.

        Params:
        - e: The RpcError thrown.
        - method: The ChirpstackClient method to call after the token is refreshed.
        - *args: Arguments that will be inputted to method.
        - **kwargs: Key Word Arguments that will be inputted to method.
        """
        # Handle the exception here
        status_code = e.code()
        details = e.details()

        if status_code == grpc.StatusCode.UNAUTHENTICATED and "ExpiredSignature" in details:
            # Retry login and then re-run the specified method
            logging.warning(f"ChirpstackClient.{method.__name__}():JWT token expired. Retrying login...")
            self.auth_token = self.login()  # Update auth_token with the new token
            time.sleep(2)  # Introduce a short delay before retrying
            return method(*args, **kwargs)  # Re-run the specified method with the same parameters

        logging.error(f"ChirpstackClient.{method.__name__}(): Unknown error occurred with status code {status_code}")
        logging.error(f"    Details: {details}")
        raise Exception(f"The JWT token failed to be refreshed")