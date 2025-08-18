"""
Definitions of Objects that are used in Chirpstack.
Retrieved from: https://github.com/chirpstack/chirpstack/tree/master/api/proto/api
"""
from enum import Enum

class Region(Enum):
    """Definition of Region Object for Chirpstack."""
    EU868 = 0
    US915 = 2
    CN779 = 3
    EU433 = 4
    AU915 = 5
    CN470 = 6
    AS923 = 7
    AS923_2 = 12
    AS923_3 = 13
    AS923_4 = 14
    KR920 = 8
    IN865 = 9
    RU864 = 10
    ISM2400 = 11

class MacVersion(Enum):
    """Definition of MacVersion Object for Chirpstack."""
    LORAWAN_1_0_0 = 0
    LORAWAN_1_0_1 = 1
    LORAWAN_1_0_2 = 2
    LORAWAN_1_0_3 = 3
    LORAWAN_1_0_4 = 4
    LORAWAN_1_1_0 = 5

class RegParamsRevision(Enum):
    """Definition of RegParamsRevision Object for Chirpstack."""
    A = 0
    B = 1
    RP002_1_0_0 = 2
    RP002_1_0_1 = 3
    RP002_1_0_2 = 4
    RP002_1_0_3 = 5

class CodecRuntime(Enum):
    """Definition of CodecRuntime Object for Chirpstack."""
    NONE = 0
    CAYENNE_LPP = 1
    JS = 2

class AdrAlgorithm(Enum):
    """Definition of ADR Algorithm Object."""
    LORA_ONLY = "default"
    LR_FHSS_ONLY = "lr_fhss"
    BOTH = "lora_lr_fhss"

class ClassBPingSlot(Enum):
    """Definition of Class-B ping-slot periodicity Object."""
    NONE = None
    EVERY_SEC = 0
    EVERY_2SEC = 1
    EVERY_4SEC = 2
    EVERY_8SEC = 3
    EVERY_16SEC = 4
    EVERY_32SEC = 5
    EVERY_64SEC = 6
    EVERY_128SEC = 7

class CadPeriodicity(Enum):
    """Definition of CAD Periodicity Object."""
    NONE = 0
    EVERY_100MS = 1
    EVERY_200MS = 2
    EVERY_300MS = 3
    EVERY_400MS = 4
    EVERY_500MS = 5
    EVERY_600MS = 6
    EVERY_700MS = 7
    EVERY_800MS = 8
    EVERY_900MS = 9
    EVERY_1S = 10
    EVERY_2S = 11
    EVERY_4S = 12
    EVERY_8S = 13
    EVERY_16S = 14
    EVERY_32S = 15
    EVERY_64S = 16
    EVERY_128S = 17

class Encoding(Enum):
    """Definition of Encoding Object."""
    JSON = 0
    PROTOBUF = 1

class GatewayState(Enum):
    """Definition of Gateway State Object."""
    ONLINE = 0
    OFFLINE = 1

class InfluxDbPrecision(Enum):
    """Definition of InfluxDB Precision Object."""
    NS = 0
    U = 1
    MS = 2
    S = 3
    M = 4
    H = 5

class InfluxDbVersion(Enum):
    """Definition of InfluxDB Version Object."""
    INFLUXDB_1 = 0
    INFLUXDB_2 = 1

class IntegrationKind(Enum):
    """Definition of Integration Kind Object."""
    HTTP = 0
    INFLUXDB = 1
    THINGSBOARD = 2
    MYDEVICES = 3
    LORACLOUD = 4
    GCP_PUBSUB = 5
    AWS_SNS = 6
    AZURE_SERVICE_BUS = 7
    PILOT_THINGS = 8
    IFTTT = 9

class MeasurementKind(Enum):
    """Definition of Measurement Kind Object."""
    UNKNOWN = 0
    RX_INFO = 1
    TX_INFO = 2
    UPLINK = 3
    DOWNLINK = 4
    GATEWAY = 5
    DEVICE = 6

class MulticastGroupSchedulingType(Enum):
    """Definition of Multicast Group Scheduling Type Object."""
    DELAY = 0
    GPS_TIME = 1
    IMMEDIATE = 2

class MulticastGroupType(Enum):
    """Definition of Multicast Group Type Object."""
    CLASS_C = 0
    CLASS_B = 1

class RelayModeActivation(Enum):
    """Definition of Relay Mode Activation Object."""
    DISABLED = 0
    STATIC = 1
    DYNAMIC = 2

class RequestFragmentationSessionStatus(Enum):
    """Definition of Request Fragmentation Session Status Object."""
    PENDING = 0
    ACTIVE = 1
    COMPLETED = 2
    ABORTED = 3

class SecondChAckOffset(Enum):
    """Definition of Second Channel ACK Offset Object."""
    NONE = 0
    OFFSET_1 = 1
    OFFSET_2 = 2
    OFFSET_3 = 3
    OFFSET_4 = 4
    OFFSET_5 = 5
    OFFSET_6 = 6
    OFFSET_7 = 7

class Ts003Version(Enum):
    """Definition of TS003 Version Object."""
    V1_0 = 0
    V1_1 = 1

class Ts004Version(Enum):
    """Definition of TS004 Version Object."""
    V1_0 = 0
    V1_1 = 1

class Ts005Version(Enum):
    """Definition of TS005 Version Object."""
    V1_0 = 0
    V1_1 = 1

class User:
    """
    Definition of User Object for Chirpstack.

    Params:
    - email: Email address of the user.
    - password: Password for the user.
    - is_active: Whether the user is active.
    - is_admin: Whether the user is an admin.
    - note: Additional notes about the user.
    - id (optional): Unique identifier for the user.
    """
    def __init__(self, email: str, password: str, is_active: bool = True, is_admin: bool = False, note: str = '', id: str = ''):
        self.id = id
        self.email = email
        self.password = password
        self.is_active = is_active
        self.is_admin = is_admin
        self.note = note

    @classmethod
    def from_grpc(cls, grpc_user):
        """Convert gRPC user object to User object."""
        return cls(
            email=getattr(grpc_user, 'email', ''),
            password="",  # Password is not returned by the API
            is_active=getattr(grpc_user, 'is_active', True),
            is_admin=getattr(grpc_user, 'is_admin', False),
            note=getattr(grpc_user, 'note', ''),
            id=getattr(grpc_user, 'id', '')
        )

    def __str__(self):
        return self.email
    
    def to_dict(self) -> dict:
        """Convert User object to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'note': self.note
        }

class Tenant:
    """
    Definition of Tenant Object for Chirpstack.

    Params:
    - name: Name of the tenant.
    - description: Description of the tenant.
    - id (optional): Unique identifier for the tenant.
    - tags (dict<string,string>, optional): Additional metadata associated with the tenant.
    """
    def __init__(self, name: str, description: str = '', id: str = '', tags: dict = {}):
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("Tenant: All values in 'tags' dictionary must be strings.")
        
        self.id = id
        self.name = name
        self.description = description
        self.tags = tags

    @classmethod
    def from_grpc(cls, grpc_tenant):
        """Convert gRPC tenant object to Tenant object."""
        return cls(
            name=getattr(grpc_tenant, 'name', ''),
            description=getattr(grpc_tenant, 'description', ''),
            id=getattr(grpc_tenant, 'id', ''),
            tags=dict(getattr(grpc_tenant, 'tags', {}))
        )

    def __str__(self):
        if self.id == "":
            raise RuntimeError("Tenant: The id is empty, try creating the tenant first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert Tenant object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tags': self.tags
        }

class MulticastGroup:
    """
    Definition of Multicast Group Object for Chirpstack.

    Params:
    - name: Name of the multicast group.
    - mc_addr: Multicast address.
    - mc_nwk_s_key: Multicast network session key.
    - mc_app_s_key: Multicast application session key.
    - f_cnt: Frame counter.
    - group_type: Type of multicast group.
    - mc_timeout: Multicast timeout.
    - application_id: Application ID.
    - id (optional): Unique identifier for the multicast group.
    - description (optional): Description of the multicast group.
    - tags (dict<string,string>, optional): Additional metadata associated with the multicast group.
    """
    def __init__(self, name: str, mc_addr: str, mc_nwk_s_key: str, mc_app_s_key: str, 
                 f_cnt: int, group_type: MulticastGroupType, mc_timeout: int, application_id: str,
                 id: str = '', description: str = '', tags: dict = {}):
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("MulticastGroup: All values in 'tags' dictionary must be strings.")
        
        self.id = id
        self.name = name
        self.mc_addr = mc_addr
        self.mc_nwk_s_key = mc_nwk_s_key
        self.mc_app_s_key = mc_app_s_key
        self.f_cnt = f_cnt
        self.group_type = group_type.value
        self.mc_timeout = mc_timeout
        self.application_id = application_id
        self.description = description
        self.tags = tags

    def __str__(self):
        if self.id == "":
            raise RuntimeError("MulticastGroup: The id is empty, try creating the group first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert MulticastGroup object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'mc_addr': self.mc_addr,
            'mc_nwk_s_key': self.mc_nwk_s_key,
            'mc_app_s_key': self.mc_app_s_key,
            'f_cnt': self.f_cnt,
            'group_type': self.group_type,
            'mc_timeout': self.mc_timeout,
            'application_id': self.application_id,
            'description': self.description,
            'tags': self.tags
        }

class FuotaDeployment:
    """
    Definition of FUOTA Deployment Object for Chirpstack.

    Params:
    - name: Name of the FUOTA deployment.
    - application_id: Application ID.
    - device_profile_id: Device profile ID.
    - multicast_group_id: Multicast group ID.
    - multicast_group_type: Type of multicast group.
    - mc_addr: Multicast address.
    - mc_nwk_s_key: Multicast network session key.
    - mc_app_s_key: Multicast application session key.
    - f_cnt: Frame counter.
    - group_type: Type of multicast group.
    - dr: Data rate.
    - frequency: Frequency in Hz.
    - class_c_timeout: Class C timeout.
    - id (optional): Unique identifier for the FUOTA deployment.
    - description (optional): Description of the FUOTA deployment.
    - tags (dict<string,string>, optional): Additional metadata associated with the FUOTA deployment.
    """
    def __init__(self, name: str, application_id: str, device_profile_id: str, multicast_group_id: str,
                 multicast_group_type: MulticastGroupType, mc_addr: str, mc_nwk_s_key: str, mc_app_s_key: str,
                 f_cnt: int, group_type: MulticastGroupType, dr: int, frequency: int, class_c_timeout: int,
                 id: str = '', description: str = '', tags: dict = {}):
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("FuotaDeployment: All values in 'tags' dictionary must be strings.")
        
        self.id = id
        self.name = name
        self.application_id = application_id
        self.device_profile_id = device_profile_id
        self.multicast_group_id = multicast_group_id
        self.multicast_group_type = multicast_group_type.value
        self.mc_addr = mc_addr
        self.mc_nwk_s_key = mc_nwk_s_key
        self.mc_app_s_key = mc_app_s_key
        self.f_cnt = f_cnt
        self.group_type = group_type.value
        self.dr = dr
        self.frequency = frequency
        self.class_c_timeout = class_c_timeout
        self.description = description
        self.tags = tags

    def __str__(self):
        if self.id == "":
            raise RuntimeError("FuotaDeployment: The id is empty, try creating the deployment first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert FuotaDeployment object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'application_id': self.application_id,
            'device_profile_id': self.device_profile_id,
            'multicast_group_id': self.multicast_group_id,
            'multicast_group_type': self.multicast_group_type,
            'mc_addr': self.mc_addr,
            'mc_nwk_s_key': self.mc_nwk_s_key,
            'mc_app_s_key': self.mc_app_s_key,
            'f_cnt': self.f_cnt,
            'group_type': self.group_type,
            'dr': self.dr,
            'frequency': self.frequency,
            'class_c_timeout': self.class_c_timeout,
            'description': self.description,
            'tags': self.tags
        }

class DeviceProfileTemplate:
    """
    Definition of Device Profile Template Object for Chirpstack.

    Params:
    - name: Name of the device profile template.
    - vendor: Vendor name.
    - firmware: Firmware version.
    - region: Region.
    - mac_version: LoRaWAN MAC version.
    - reg_params_revision: Regional parameters revision.
    - adr_algorithm_id: ADR algorithm ID.
    - payload_codec_runtime: Payload codec runtime.
    - uplink_interval: Uplink interval.
    - supports_otaa: Supports OTAA.
    - supports_class_b: Supports Class B.
    - supports_class_c: Supports Class C.
    - id (optional): Unique identifier for the device profile template.
    - description (optional): Description of the device profile template.
    - tags (dict<string,string>, optional): Additional metadata associated with the device profile template.
    """
    def __init__(self, name: str, vendor: str, firmware: str, region: Region, mac_version: MacVersion,
                 reg_params_revision: RegParamsRevision, adr_algorithm_id: str, payload_codec_runtime: CodecRuntime,
                 uplink_interval: int, supports_otaa: bool, supports_class_b: bool, supports_class_c: bool,
                 id: str = '', description: str = '', tags: dict = {}):
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("DeviceProfileTemplate: All values in 'tags' dictionary must be strings.")
        
        self.id = id
        self.name = name
        self.vendor = vendor
        self.firmware = firmware
        self.region = region.value
        self.mac_version = mac_version.value
        self.reg_params_revision = reg_params_revision.value
        self.adr_algorithm_id = adr_algorithm_id
        self.payload_codec_runtime = payload_codec_runtime.value
        self.uplink_interval = uplink_interval
        self.supports_otaa = supports_otaa
        self.supports_class_b = supports_class_b
        self.supports_class_c = supports_class_c
        self.description = description
        self.tags = tags

    def __str__(self):
        if self.id == "":
            raise RuntimeError("DeviceProfileTemplate: The id is empty, try creating the template first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert DeviceProfileTemplate object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'vendor': self.vendor,
            'firmware': self.firmware,
            'region': self.region,
            'mac_version': self.mac_version,
            'reg_params_revision': self.reg_params_revision,
            'adr_algorithm_id': self.adr_algorithm_id,
            'payload_codec_runtime': self.payload_codec_runtime,
            'uplink_interval': self.uplink_interval,
            'supports_otaa': self.supports_otaa,
            'supports_class_b': self.supports_class_b,
            'supports_class_c': self.supports_class_c,
            'description': self.description,
            'tags': self.tags
        }

class Relay:
    """
    Definition of Relay Object for Chirpstack.

    Params:
    - name: Name of the relay.
    - tenant_id: Tenant ID.
    - device_id: Device ID.
    - id (optional): Unique identifier for the relay.
    - description (optional): Description of the relay.
    - tags (dict<string,string>, optional): Additional metadata associated with the relay.
    """
    def __init__(self, name: str, tenant_id: str, device_id: str, id: str = '', description: str = '', tags: dict = {}):
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("Relay: All values in 'tags' dictionary must be strings.")
        
        self.id = id
        self.name = name
        self.tenant_id = tenant_id
        self.device_id = device_id
        self.description = description
        self.tags = tags

    def __str__(self):
        if self.id == "":
            raise RuntimeError("Relay: The id is empty, try creating the relay first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert Relay object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'tenant_id': self.tenant_id,
            'device_id': self.device_id,
            'description': self.description,
            'tags': self.tags
        }

# Integration objects
class HttpIntegration:
    """
    Definition of HTTP Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - headers: HTTP headers.
    - url: HTTP endpoint URL.
    - id (optional): Unique identifier for the HTTP integration.
    """
    def __init__(self, application_id: str, headers: dict, url: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.headers = headers
        self.url = url

    @classmethod
    def from_grpc(cls, grpc_integration):
        """Convert gRPC HTTP integration object to HttpIntegration object."""
        return cls(
            application_id=grpc_integration.application_id,
            headers=dict(grpc_integration.headers),
            url=grpc_integration.url,
            id=grpc_integration.id
        )

    def __str__(self):
        if self.id == "":
            raise RuntimeError("HttpIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert HttpIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'headers': self.headers,
            'url': self.url
        }

class InfluxDbIntegration:
    """
    Definition of InfluxDB Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - endpoint: InfluxDB endpoint.
    - token: InfluxDB token.
    - organization: InfluxDB organization.
    - bucket: InfluxDB bucket.
    - version: InfluxDB version.
    - precision: InfluxDB precision.
    - id (optional): Unique identifier for the InfluxDB integration.
    """
    def __init__(self, application_id: str, endpoint: str, token: str, organization: str, bucket: str,
                 version: InfluxDbVersion, precision: InfluxDbPrecision, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.endpoint = endpoint
        self.token = token
        self.organization = organization
        self.bucket = bucket
        self.version = version.value
        self.precision = precision.value

    def __str__(self):
        if self.id == "":
            raise RuntimeError("InfluxDbIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert InfluxDbIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'endpoint': self.endpoint,
            'token': self.token,
            'organization': self.organization,
            'bucket': self.bucket,
            'version': self.version,
            'precision': self.precision
        }

class ThingsBoardIntegration:
    """
    Definition of ThingsBoard Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - server: ThingsBoard server URL.
    - token: ThingsBoard token.
    - id (optional): Unique identifier for the ThingsBoard integration.
    """
    def __init__(self, application_id: str, server: str, token: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.server = server
        self.token = token

    def __str__(self):
        if self.id == "":
            raise RuntimeError("ThingsBoardIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert ThingsBoardIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'server': self.server,
            'token': self.token
        }

class AwsSnsIntegration:
    """
    Definition of AWS SNS Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - aws_region: AWS region.
    - aws_access_key_id: AWS access key ID.
    - aws_secret_access_key: AWS secret access key.
    - topic_arn: SNS topic ARN.
    - id (optional): Unique identifier for the AWS SNS integration.
    """
    def __init__(self, application_id: str, aws_region: str, aws_access_key_id: str, aws_secret_access_key: str,
                 topic_arn: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.aws_region = aws_region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.topic_arn = topic_arn

    def __str__(self):
        if self.id == "":
            raise RuntimeError("AwsSnsIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert AwsSnsIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'aws_region': self.aws_region,
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key,
            'topic_arn': self.topic_arn
        }

class AzureServiceBusIntegration:
    """
    Definition of Azure Service Bus Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - connection_string: Azure Service Bus connection string.
    - topic_name: Azure Service Bus topic name.
    - id (optional): Unique identifier for the Azure Service Bus integration.
    """
    def __init__(self, application_id: str, connection_string: str, topic_name: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.connection_string = connection_string
        self.topic_name = topic_name

    def __str__(self):
        if self.id == "":
            raise RuntimeError("AzureServiceBusIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert AzureServiceBusIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'connection_string': self.connection_string,
            'topic_name': self.topic_name
        }

class GcpPubSubIntegration:
    """
    Definition of GCP Pub/Sub Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - encoding: Message encoding.
    - project_id: GCP project ID.
    - topic_name: GCP Pub/Sub topic name.
    - service_account_key: GCP service account key.
    - id (optional): Unique identifier for the GCP Pub/Sub integration.
    """
    def __init__(self, application_id: str, encoding: Encoding, project_id: str, topic_name: str,
                 service_account_key: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.encoding = encoding.value
        self.project_id = project_id
        self.topic_name = topic_name
        self.service_account_key = service_account_key

    def __str__(self):
        if self.id == "":
            raise RuntimeError("GcpPubSubIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert GcpPubSubIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'encoding': self.encoding,
            'project_id': self.project_id,
            'topic_name': self.topic_name,
            'service_account_key': self.service_account_key
        }

class IftttIntegration:
    """
    Definition of IFTTT Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - key: IFTTT key.
    - id (optional): Unique identifier for the IFTTT integration.
    """
    def __init__(self, application_id: str, key: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.key = key

    def __str__(self):
        if self.id == "":
            raise RuntimeError("IftttIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert IftttIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'key': self.key
        }

class MyDevicesIntegration:
    """
    Definition of MyDevices Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - endpoint: MyDevices endpoint.
    - token: MyDevices token.
    - id (optional): Unique identifier for the MyDevices integration.
    """
    def __init__(self, application_id: str, endpoint: str, token: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.endpoint = endpoint
        self.token = token

    def __str__(self):
        if self.id == "":
            raise RuntimeError("MyDevicesIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert MyDevicesIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'endpoint': self.endpoint,
            'token': self.token
        }

class PilotThingsIntegration:
    """
    Definition of Pilot Things Integration Object for Chirpstack.

    Params:
    - application_id: Application ID.
    - server: Pilot Things server URL.
    - token: Pilot Things token.
    - id (optional): Unique identifier for the Pilot Things integration.
    """
    def __init__(self, application_id: str, server: str, token: str, id: str = ''):
        self.id = id
        self.application_id = application_id
        self.server = server
        self.token = token

    def __str__(self):
        if self.id == "":
            raise RuntimeError("PilotThingsIntegration: The id is empty, try creating the integration first in Chirpstack")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert PilotThingsIntegration object to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'server': self.server,
            'token': self.token
        }

class Location:
    """
    Definition of Location Object for Chirpstack.

    Params:
    - latitude: Latitude coordinate.
    - longitude: Longitude coordinate.
    - altitude: Altitude in meters.
    - source: Source of the location data.
    - accuracy: Accuracy of the location data in meters.
    """
    def __init__(self, latitude: float, longitude: float, altitude: float = 0.0, source: str = 'UNKNOWN', accuracy: float = 0.0):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.source = source
        self.accuracy = accuracy

    def __str__(self):
        return f"({self.latitude}, {self.longitude}, {self.altitude}m)"
    
    def to_dict(self) -> dict:
        """Convert Location object to dictionary."""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'source': self.source,
            'accuracy': self.accuracy
        }

class Gateway:
    """
    Definition of Gateway Object for Chirpstack.

    Params:
    - name: Name of the gateway.
    - gateway_id (EUI64): Unique identifier for the gateway.
    - tenant_id: Identifier for the tenant associated with the gateway.
    - description (optional): Description of the gateway.
    - tags (dict<string,string>, optional): Additional metadata associated with the gateway.
    - stats_interval (optional): The expected interval in seconds in which the gateway sends its statistics (default is 30 sec).
    - id (optional): Unique identifier for the gateway.
    - location (optional): Gateway location information (Location object or dict).
    - metadata (optional): Additional metadata for the gateway.
    """
    def __init__(self,name:str,gateway_id:str,tenant_id:str,description:str='',tags:dict={},stats_interval:int=30,id:str='',location:Location|dict=None,metadata:dict=None):
        """Constructor method to initialize a Gateway object."""            
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("Gateway: All values in 'tags' dictionary must be strings.")

        self.id = id
        self.gateway_id = gateway_id
        self.name = name
        self.description = description
        self.tenant_id = tenant_id
        self.tags = tags
        self.stats_interval = stats_interval
        if isinstance(location, Location):
            self.location = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "altitude": location.altitude,
                "source": location.source,
                "accuracy": location.accuracy
            }
        else:
            self.location = location or {}
        self.metadata = metadata or {}

    @classmethod
    def from_grpc(cls, grpc_gateway):
        """Convert gRPC gateway object to Gateway object."""
        # Create Location object if location data exists
        location = None
        if hasattr(grpc_gateway, 'location') and grpc_gateway.location:
            location = Location(
                latitude=getattr(grpc_gateway.location, 'latitude', 0.0),
                longitude=getattr(grpc_gateway.location, 'longitude', 0.0),
                altitude=getattr(grpc_gateway.location, 'altitude', 0.0),
                source=getattr(grpc_gateway.location, 'source', 'UNKNOWN'),
                accuracy=getattr(grpc_gateway.location, 'accuracy', 0.0)
            )
        
        return cls(
            name=getattr(grpc_gateway, 'name', ''),
            gateway_id=getattr(grpc_gateway, 'gateway_id', ''),
            tenant_id=getattr(grpc_gateway, 'tenant_id', ''),
            description=getattr(grpc_gateway, 'description', ''),
            tags=dict(getattr(grpc_gateway, 'tags', {})),
            stats_interval=getattr(grpc_gateway, 'stats_interval', 30),
            id=getattr(grpc_gateway, 'id', ''),
            location=location,
            metadata=dict(getattr(grpc_gateway, 'metadata', {}))
        )
    
    def __str__(self):
        """String representation of the Gateway object"""
        return self.gateway_id
    
    def to_dict(self) -> dict:
        """Convert Gateway object to dictionary."""
        return {
            'id': self.id,
            'gateway_id': self.gateway_id,
            'name': self.name,
            'description': self.description,
            'tenant_id': self.tenant_id,
            'tags': self.tags,
            'stats_interval': self.stats_interval,
            'location': self.location.to_dict() if isinstance(self.location, Location) else self.location,
            'metadata': self.metadata
        }

class Application:
    """
    Definition of Application Object for Chirpstack.

    Params:
    - name: Name of the Application.
    - tenant_id: Identifier for the tenant associated with the application.
    - id (optional): Unique identifier for the application.
        The id gets generated by Chirpstack when it is created. You can either set the id or pass the object through
        `ChirpstackClient.create_app()`.
    - description (optional): Description of the application.
    - tags (dict<string,string>, optional): Additional metadata associated with the application.
    """
    def __init__(self,name:str,tenant_id:str,id:str='',description:str='',tags:dict={}):
        """Constructor method to initialize an Application object."""
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("Application: All values in 'tags' dictionary must be strings.")
        
        self.id = id
        self.name = name
        self.tenant_id = tenant_id
        self.description = description
        self.tags = tags

    @classmethod
    def from_grpc(cls, grpc_application):
        """Convert gRPC application object to Application object."""
        return cls(
            name=getattr(grpc_application, 'name', ''),
            tenant_id=getattr(grpc_application, 'tenant_id', ''),
            id=getattr(grpc_application, 'id', ''),
            description=getattr(grpc_application, 'description', ''),
            tags=dict(getattr(grpc_application, 'tags', {}))
        )

    def __str__(self):
        """String representation of the application object"""
        if self.id == "":
            raise RuntimeError("Application: The id is empty, try creating the app first in Chirpstack using ChirpstackClient.create_app()")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert Application object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'tenant_id': self.tenant_id,
            'description': self.description,
            'tags': self.tags
        }

class DeviceProfile:
    """
    Definition of Device Profile Object for Chirpstack. 

    Params:
    - name: Name of the device profile.
    - tenant_id: Identifier for the tenant associated with the device profile.
    - region: The frequency plan the devices will be using.
    - mac_version: The LoRaWAN MAC version supported by the devices.
    - reg_params_revision: Revision of the Regional Parameters specification supported by the devices.
    - uplink_interval: The expected interval in seconds in which the devices send uplink messages. 
        This is used to determine if the devices are active or inactive.
    - supports_otaa: The devices support OTAA.
    - supports_class_b: The devices support Class-B configurations.
    - supports_class_c: The devices support Class-C configurations.
    - abp_rx1_delay (required if not supports_otaa): The devices' RX1 delay (for ABP).
    - abp_rx1_dr_offset (required if not supports_otaa): The devices' RX1 DR offset (for ABP).
    - abp_rx2_dr (required if not supports_otaa): The devices' RX2 DR (for ABP).
    - abp_rx2_freq (required if not supports_otaa): The devices' RX2 frequency (for ABP, Hz).
    - class_b_timeout (required if supports_class_b): The devices' Class-B timeout in seconds for confirmed downlink transmissions.
    - class_b_ping_slot_nb_k (required if supports_class_b): The devices' Class-B ping-slots per beacon period.
    - class_b_ping_slot_dr (required if supports_class_b): The devices' Class-B ping-slot data rate.
    - class_b_ping_slot_freq (required if supports_class_b): The devices' Class-B ping-slot freq (Hz).
    - class_c_timeout (required if supports_class_c): The devices' Class-C timeout in seconds for confirmed downlink transmissions.
    - id (optional): Unique identifier for the device profile.
        The id gets generated by Chirpstack when it is created. You can either set the id or pass the object through
        `ChirpstackClient.create_device_profile()`.
    - description (optional): Description of the device profile.
    - payload_codec_runtime (optional): The devices' payload codec runtime.
    - payload_codec_script (optional): The devices' encoder and decoder script.
    - flush_queue_on_activate (optional): Flush queue on device activation.
    - device_status_req_interval (optional): Frequency to initiate an End-Device status request (request/day). Set to 0 to disable.
    - tags (dict<string,string>, optional): Additional metadata associated with the device profile.
    - auto_detect_measurements (optional): Auto detect measurements from these devices in Chirpstack.
    - allow_roaming (optional): This allows the devices to use roaming. Roaming must also be configured in the server.
    - adr_algorithm_id (optional): The ADR algorithm that will be used for controlling the devices data-rate.
    - rx1_delay (optional): RX1 delay for OTAA devices.
    - app_layer_params (optional): Application layer parameters.
    - region_config_id (optional): Region configuration ID.
    - is_relay (optional): Whether this is a relay device profile.
    - is_relay_ed (optional): Whether this is a relay end-device profile.
    - relay_ed_relay_only (optional): Whether relay end-device is relay only.
    - relay_enabled (optional): Whether relay is enabled.
    - relay_cad_periodicity (optional): Relay CAD periodicity.
    - relay_default_channel_index (optional): Relay default channel index.
    - relay_second_channel_freq (optional): Relay second channel frequency.
    - relay_second_channel_dr (optional): Relay second channel data rate.
    - relay_second_channel_ack_offset (optional): Relay second channel ACK offset.
    - relay_ed_activation_mode (optional): Relay end-device activation mode.
    - relay_ed_smart_enable_level (optional): Relay end-device smart enable level.
    - relay_ed_back_off (optional): Relay end-device back-off.
    - relay_ed_uplink_limit_bucket_size (optional): Relay end-device uplink limit bucket size.
    - relay_ed_uplink_limit_reload_rate (optional): Relay end-device uplink limit reload rate.
    - relay_join_req_limit_reload_rate (optional): Relay join request limit reload rate.
    - relay_notify_limit_reload_rate (optional): Relay notify limit reload rate.
    - relay_global_uplink_limit_reload_rate (optional): Relay global uplink limit reload rate.
    - relay_overall_limit_reload_rate (optional): Relay overall limit reload rate.
    - relay_join_req_limit_bucket_size (optional): Relay join request limit bucket size.
    - relay_notify_limit_bucket_size (optional): Relay notify limit bucket size.
    - relay_global_uplink_limit_bucket_size (optional): Relay global uplink limit bucket size.
    - relay_overall_limit_bucket_size (optional): Relay overall limit bucket size.
    - measurements (optional): Device measurements configuration.
    """
    def __init__(self,name:str,tenant_id:str,region:Region,mac_version:MacVersion,reg_params_revision:RegParamsRevision,
        uplink_interval:int,supports_otaa:bool,supports_class_b:bool,supports_class_c:bool,abp_rx1_delay:int=None,
        abp_rx1_dr_offset:int=None,abp_rx2_dr:int=None,abp_rx2_freq:int=None,class_b_timeout:int=None,
        class_b_ping_slot_nb_k:ClassBPingSlot=ClassBPingSlot.NONE,class_b_ping_slot_dr:int=None,class_b_ping_slot_freq:int=None,
        class_c_timeout:int=None,id:str="",description:str='',payload_codec_runtime:CodecRuntime=CodecRuntime.NONE,
        payload_codec_script:str="",flush_queue_on_activate:bool=True,device_status_req_interval:int=1,tags:dict={},
        auto_detect_measurements:bool=True,allow_roaming:bool=False,adr_algorithm_id:AdrAlgorithm=AdrAlgorithm.LORA_ONLY,
        rx1_delay:int=None,app_layer_params:dict=None,region_config_id:str="",is_relay:bool=False,is_relay_ed:bool=False,
        relay_ed_relay_only:bool=False,relay_enabled:bool=False,relay_cad_periodicity:CadPeriodicity=CadPeriodicity.NONE,
        relay_default_channel_index:int=None,relay_second_channel_freq:int=None,relay_second_channel_dr:int=None,
        relay_second_channel_ack_offset:SecondChAckOffset=SecondChAckOffset.NONE,relay_ed_activation_mode:RelayModeActivation=RelayModeActivation.DISABLED,
        relay_ed_smart_enable_level:int=None,relay_ed_back_off:int=None,relay_ed_uplink_limit_bucket_size:int=None,
        relay_ed_uplink_limit_reload_rate:int=None,relay_join_req_limit_reload_rate:int=None,relay_notify_limit_reload_rate:int=None,
        relay_global_uplink_limit_reload_rate:int=None,relay_overall_limit_reload_rate:int=None,relay_join_req_limit_bucket_size:int=None,
        relay_notify_limit_bucket_size:int=None,relay_global_uplink_limit_bucket_size:int=None,relay_overall_limit_bucket_size:int=None,
        measurements:dict=None):
        """Constructor method to initialize a DeviceProfile object."""

        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("DeviceProfile: All values in 'tags' dictionary must be strings.")           

        self.id = id
        self.name = name
        self.tenant_id = tenant_id
        self.region = region.value
        self.mac_version = mac_version.value
        self.reg_params_revision = reg_params_revision.value
        self.uplink_interval = uplink_interval
        self.supports_otaa = supports_otaa
        self._abp_rx1_delay = abp_rx1_delay
        self._abp_rx1_dr_offset = abp_rx1_dr_offset
        self._abp_rx2_dr = abp_rx2_dr
        self._abp_rx2_freq = abp_rx2_freq
        self.supports_class_b = supports_class_b
        self._class_b_timeout = class_b_timeout
        self._class_b_ping_slot_nb_k = class_b_ping_slot_nb_k.value
        self._class_b_ping_slot_dr = class_b_ping_slot_dr
        self._class_b_ping_slot_freq = class_b_ping_slot_freq
        self.supports_class_c = supports_class_c
        self._class_c_timeout = class_c_timeout
        self.description = description
        self.payload_codec_runtime = payload_codec_runtime.value
        self.payload_codec_script = payload_codec_script
        self.flush_queue_on_activate = flush_queue_on_activate
        self.device_status_req_interval = device_status_req_interval
        self.tags = tags
        self.auto_detect_measurements = auto_detect_measurements
        self.allow_roaming = allow_roaming
        self.adr_algorithm_id = adr_algorithm_id.value
        self.rx1_delay = rx1_delay
        self.app_layer_params = app_layer_params or {}
        self.region_config_id = region_config_id
        self.is_relay = is_relay
        self.is_relay_ed = is_relay_ed
        self.relay_ed_relay_only = relay_ed_relay_only
        self.relay_enabled = relay_enabled
        self.relay_cad_periodicity = relay_cad_periodicity.value
        self.relay_default_channel_index = relay_default_channel_index
        self.relay_second_channel_freq = relay_second_channel_freq
        self.relay_second_channel_dr = relay_second_channel_dr
        self.relay_second_channel_ack_offset = relay_second_channel_ack_offset.value
        self.relay_ed_activation_mode = relay_ed_activation_mode.value
        self.relay_ed_smart_enable_level = relay_ed_smart_enable_level
        self.relay_ed_back_off = relay_ed_back_off
        self.relay_ed_uplink_limit_bucket_size = relay_ed_uplink_limit_bucket_size
        self.relay_ed_uplink_limit_reload_rate = relay_ed_uplink_limit_reload_rate
        self.relay_join_req_limit_reload_rate = relay_join_req_limit_reload_rate
        self.relay_notify_limit_reload_rate = relay_notify_limit_reload_rate
        self.relay_global_uplink_limit_reload_rate = relay_global_uplink_limit_reload_rate
        self.relay_overall_limit_reload_rate = relay_overall_limit_reload_rate
        self.relay_join_req_limit_bucket_size = relay_join_req_limit_bucket_size
        self.relay_notify_limit_bucket_size = relay_notify_limit_bucket_size
        self.relay_global_uplink_limit_bucket_size = relay_global_uplink_limit_bucket_size
        self.relay_overall_limit_bucket_size = relay_overall_limit_bucket_size
        self.measurements = measurements or {}

    @property 
    def abp_rx1_delay(self):
        if not self.supports_otaa and self._abp_rx1_delay is None:
            raise ValueError("DeviceProfile: abp_rx1_delay is required when supports_otaa is False")
        return self._abp_rx1_delay

    @abp_rx1_delay.setter
    def abp_rx1_delay(self, value):
        if not self.supports_otaa and value is None:
            raise ValueError("DeviceProfile: abp_rx1_delay is required when supports_otaa is False")
        self._abp_rx1_delay = value

    @property 
    def abp_rx1_dr_offset(self):
        if not self.supports_otaa and self._abp_rx1_dr_offset is None:
            raise ValueError("DeviceProfile: abp_rx1_dr_offset is required when supports_otaa is False")
        return self._abp_rx1_dr_offset

    @abp_rx1_dr_offset.setter
    def abp_rx1_dr_offset(self, value):
        if not self.supports_otaa and value is None:
            raise ValueError("DeviceProfile: abp_rx1_dr_offset is required when supports_otaa is False")
        self._abp_rx1_dr_offset = value

    @property
    def abp_rx2_dr(self):
        if not self.supports_otaa and self._abp_rx2_dr is None:
            raise ValueError("DeviceProfile: abp_rx2_dr is required when supports_otaa is False")
        return self._abp_rx2_dr

    @abp_rx2_dr.setter
    def abp_rx2_dr(self, value):
        if not self.supports_otaa and value is None:
            raise ValueError("DeviceProfile: abp_rx2_dr is required when supports_otaa is False")
        self._abp_rx2_dr = value

    @property
    def abp_rx2_freq(self):
        if not self.supports_otaa and self._abp_rx2_freq is None:
            raise ValueError("DeviceProfile: abp_rx2_freq is required when supports_otaa is False")
        return self._abp_rx2_freq

    @abp_rx2_freq.setter
    def abp_rx2_freq(self, value):
        if not self.supports_otaa and value is None:
            raise ValueError("DeviceProfile: abp_rx2_freq is required when supports_otaa is False")
        self._abp_rx2_freq = value

    @property
    def class_b_timeout(self):
        if self.supports_class_b and self._class_b_timeout is None:
            raise ValueError("DeviceProfile: class_b_timeout is required when supports_class_b is True")
        return self._class_b_timeout

    @class_b_timeout.setter
    def class_b_timeout(self, value):
        if self.supports_class_b and value is None:
            raise ValueError("DeviceProfile: class_b_timeout is required when supports_class_b is True")
        self._class_b_timeout = value

    @property  
    def class_b_ping_slot_nb_k(self):
        if self.supports_class_b and self._class_b_ping_slot_nb_k is None:
            raise ValueError("DeviceProfile: class_b_ping_slot_nb_k is required when supports_class_b is True")
        return self._class_b_ping_slot_nb_k

    @class_b_ping_slot_nb_k.setter
    def class_b_ping_slot_nb_k(self, value):
        if self.supports_class_b and value is None:
            raise ValueError("DeviceProfile: class_b_ping_slot_nb_k is required when supports_class_b is True")
        self._class_b_ping_slot_nb_k = value

    @property 
    def class_b_ping_slot_dr(self):
        if self.supports_class_b and self._class_b_ping_slot_dr is None:
            raise ValueError("DeviceProfile: class_b_ping_slot_dr is required when supports_class_b is True")
        return self._class_b_ping_slot_dr

    @class_b_ping_slot_dr.setter
    def class_b_ping_slot_dr(self, value):
        if self.supports_class_b and value is None:
            raise ValueError("DeviceProfile: class_b_ping_slot_dr is required when supports_class_b is True")
        self._class_b_ping_slot_dr = value

    @property 
    def class_b_ping_slot_freq(self):
        if self.supports_class_b and self._class_b_ping_slot_freq is None:
            raise ValueError("DeviceProfile: class_b_ping_slot_freq is required when supports_class_b is True")
        return self._class_b_ping_slot_freq

    @class_b_ping_slot_freq.setter
    def class_b_ping_slot_freq(self, value):
        if self.supports_class_b and value is None:
            raise ValueError("DeviceProfile: class_b_ping_slot_freq is required when supports_class_b is True")
        self._class_b_ping_slot_freq = value

    @property 
    def class_c_timeout(self):
        if self.supports_class_c and self._class_c_timeout is None:
            raise ValueError("DeviceProfile: class_c_timeout is required when supports_class_c is True")
        return self._class_c_timeout

    @class_c_timeout.setter
    def class_c_timeout(self, value):
        if self.supports_class_c and value is None:
            raise ValueError("DeviceProfile: class_c_timeout is required when supports_class_c is True")
        self._class_c_timeout = value

    @classmethod
    def from_grpc(cls, grpc_device_profile):
        """Convert gRPC device profile object to DeviceProfile object."""
        # Import the enums here to avoid circular imports
        from chirpstack_api_wrapper.objects import Region, MacVersion, RegParamsRevision, CodecRuntime, AdrAlgorithm, ClassBPingSlot, CadPeriodicity, SecondChAckOffset, RelayModeActivation
        
        # Find the enum values by comparing the response values
        region_enum = next((r for r in Region if r.value == grpc_device_profile.region), Region.US915)
        mac_version_enum = next((m for m in MacVersion if m.value == grpc_device_profile.mac_version), MacVersion.LORAWAN_1_0_0)
        reg_params_revision_enum = next((r for r in RegParamsRevision if r.value == grpc_device_profile.reg_params_revision), RegParamsRevision.A)
        payload_codec_runtime_enum = next((c for c in CodecRuntime if c.value == grpc_device_profile.payload_codec_runtime), CodecRuntime.NONE)
        adr_algorithm_enum = next((a for a in AdrAlgorithm if a.value == grpc_device_profile.adr_algorithm_id), AdrAlgorithm.LORA_ONLY)
        class_b_ping_slot_nb_k_enum = next((c for c in ClassBPingSlot if c.value == grpc_device_profile.class_b_ping_slot_periodicity), ClassBPingSlot.NONE)
        relay_cad_periodicity_enum = next((c for c in CadPeriodicity if c.value == grpc_device_profile.relay_cad_periodicity), CadPeriodicity.NONE)
        relay_second_channel_ack_offset_enum = next((s for s in SecondChAckOffset if s.value == grpc_device_profile.relay_second_channel_ack_offset), SecondChAckOffset.NONE)
        relay_ed_activation_mode_enum = next((r for r in RelayModeActivation if r.value == grpc_device_profile.relay_ed_activation_mode), RelayModeActivation.DISABLED)
        
        return cls(
            name=getattr(grpc_device_profile, 'name', ''),
            tenant_id=getattr(grpc_device_profile, 'tenant_id', ''),
            region=region_enum,
            mac_version=mac_version_enum,
            reg_params_revision=reg_params_revision_enum,
            uplink_interval=getattr(grpc_device_profile, 'uplink_interval', 0),
            supports_otaa=getattr(grpc_device_profile, 'supports_otaa', False),
            supports_class_b=getattr(grpc_device_profile, 'supports_class_b', False),
            supports_class_c=getattr(grpc_device_profile, 'supports_class_c', False),
            abp_rx1_delay=getattr(grpc_device_profile, 'abp_rx1_delay', 0),
            abp_rx1_dr_offset=getattr(grpc_device_profile, 'abp_rx1_dr_offset', 0),
            abp_rx2_dr=getattr(grpc_device_profile, 'abp_rx2_dr', 0),
            abp_rx2_freq=getattr(grpc_device_profile, 'abp_rx2_freq', 0),
            class_b_timeout=getattr(grpc_device_profile, 'class_b_timeout', 0),
            class_b_ping_slot_nb_k=class_b_ping_slot_nb_k_enum,
            class_b_ping_slot_dr=getattr(grpc_device_profile, 'class_b_ping_slot_dr', 0),
            class_b_ping_slot_freq=getattr(grpc_device_profile, 'class_b_ping_slot_freq', 0),
            class_c_timeout=getattr(grpc_device_profile, 'class_c_timeout', 0),
            id=getattr(grpc_device_profile, 'id', ''),
            description=getattr(grpc_device_profile, 'description', ''),
            payload_codec_runtime=payload_codec_runtime_enum,
            payload_codec_script=getattr(grpc_device_profile, 'payload_codec_script', ''),
            flush_queue_on_activate=getattr(grpc_device_profile, 'flush_queue_on_activate', False),
            device_status_req_interval=getattr(grpc_device_profile, 'device_status_req_interval', 0),
            tags=dict(getattr(grpc_device_profile, 'tags', {})),
            auto_detect_measurements=getattr(grpc_device_profile, 'auto_detect_measurements', False),
            allow_roaming=getattr(grpc_device_profile, 'allow_roaming', False),
            adr_algorithm_id=adr_algorithm_enum,
            rx1_delay=getattr(grpc_device_profile, 'rx1_delay', 0),
            app_layer_params=dict(getattr(grpc_device_profile, 'app_layer_params', {})),
            region_config_id=getattr(grpc_device_profile, 'region_config_id', ''),
            is_relay=getattr(grpc_device_profile, 'is_relay', False),
            is_relay_ed=getattr(grpc_device_profile, 'is_relay_ed', False),
            relay_ed_relay_only=getattr(grpc_device_profile, 'relay_ed_relay_only', False),
            relay_enabled=getattr(grpc_device_profile, 'relay_enabled', False),
            relay_cad_periodicity=relay_cad_periodicity_enum,
            relay_default_channel_index=getattr(grpc_device_profile, 'relay_default_channel_index', 0),
            relay_second_channel_freq=getattr(grpc_device_profile, 'relay_second_channel_freq', 0),
            relay_second_channel_dr=getattr(grpc_device_profile, 'relay_second_channel_dr', 0),
            relay_second_channel_ack_offset=relay_second_channel_ack_offset_enum,
            relay_ed_activation_mode=relay_ed_activation_mode_enum,
            relay_ed_smart_enable_level=getattr(grpc_device_profile, 'relay_ed_smart_enable_level', 0),
            relay_ed_back_off=getattr(grpc_device_profile, 'relay_ed_back_off', 0),
            relay_ed_uplink_limit_bucket_size=getattr(grpc_device_profile, 'relay_ed_uplink_limit_bucket_size', 0),
            relay_ed_uplink_limit_reload_rate=getattr(grpc_device_profile, 'relay_ed_uplink_limit_reload_rate', 0),
            relay_join_req_limit_reload_rate=getattr(grpc_device_profile, 'relay_join_req_limit_reload_rate', 0),
            relay_notify_limit_reload_rate=getattr(grpc_device_profile, 'relay_notify_limit_reload_rate', 0),
            relay_global_uplink_limit_reload_rate=getattr(grpc_device_profile, 'relay_global_uplink_limit_reload_rate', 0),
            relay_overall_limit_reload_rate=getattr(grpc_device_profile, 'relay_overall_limit_reload_rate', 0),
            relay_join_req_limit_bucket_size=getattr(grpc_device_profile, 'relay_join_req_limit_bucket_size', 0),
            relay_notify_limit_bucket_size=getattr(grpc_device_profile, 'relay_notify_limit_bucket_size', 0),
            relay_global_uplink_limit_bucket_size=getattr(grpc_device_profile, 'relay_global_uplink_limit_bucket_size', 0),
            relay_overall_limit_bucket_size=getattr(grpc_device_profile, 'relay_overall_limit_bucket_size', 0),
            measurements=dict(getattr(grpc_device_profile, 'measurements', {}))
        )

    def __str__(self):
        """String representation of the Device Profile object"""
        if self.id == "":
            raise RuntimeError("DeviceProfile: The id is empty, try creating the profile first in Chirpstack using ChirpstackClient.create_device_profile()")
        return self.id
    
    def to_dict(self) -> dict:
        """Convert DeviceProfile object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'tenant_id': self.tenant_id,
            'region': self.region,
            'mac_version': self.mac_version,
            'reg_params_revision': self.reg_params_revision,
            'uplink_interval': self.uplink_interval,
            'supports_otaa': self.supports_otaa,
            'abp_rx1_delay': self.abp_rx1_delay,
            'abp_rx1_dr_offset': self.abp_rx1_dr_offset,
            'abp_rx2_dr': self.abp_rx2_dr,
            'abp_rx2_freq': self.abp_rx2_freq,
            'supports_class_b': self.supports_class_b,
            'class_b_timeout': self.class_b_timeout,
            'class_b_ping_slot_nb_k': self.class_b_ping_slot_nb_k,
            'class_b_ping_slot_dr': self.class_b_ping_slot_dr,
            'class_b_ping_slot_freq': self.class_b_ping_slot_freq,
            'supports_class_c': self.supports_class_c,
            'class_c_timeout': self.class_c_timeout,
            'description': self.description,
            'payload_codec_runtime': self.payload_codec_runtime,
            'payload_codec_script': self.payload_codec_script,
            'flush_queue_on_activate': self.flush_queue_on_activate,
            'device_status_req_interval': self.device_status_req_interval,
            'tags': self.tags,
            'auto_detect_measurements': self.auto_detect_measurements,
            'allow_roaming': self.allow_roaming,
            'adr_algorithm_id': self.adr_algorithm_id,
            'rx1_delay': self.rx1_delay,
            'app_layer_params': self.app_layer_params,
            'region_config_id': self.region_config_id,
            'is_relay': self.is_relay,
            'is_relay_ed': self.is_relay_ed,
            'relay_ed_relay_only': self.relay_ed_relay_only,
            'relay_enabled': self.relay_enabled,
            'relay_cad_periodicity': self.relay_cad_periodicity,
            'relay_default_channel_index': self.relay_default_channel_index,
            'relay_second_channel_freq': self.relay_second_channel_freq,
            'relay_second_channel_dr': self.relay_second_channel_dr,
            'relay_second_channel_ack_offset': self.relay_second_channel_ack_offset,
            'relay_ed_activation_mode': self.relay_ed_activation_mode,
            'relay_ed_smart_enable_level': self.relay_ed_smart_enable_level,
            'relay_ed_back_off': self.relay_ed_back_off,
            'relay_ed_uplink_limit_bucket_size': self.relay_ed_uplink_limit_bucket_size,
            'relay_ed_uplink_limit_reload_rate': self.relay_ed_uplink_limit_reload_rate,
            'relay_join_req_limit_reload_rate': self.relay_join_req_limit_reload_rate,
            'relay_notify_limit_reload_rate': self.relay_notify_limit_reload_rate,
            'relay_global_uplink_limit_reload_rate': self.relay_global_uplink_limit_reload_rate,
            'relay_overall_limit_reload_rate': self.relay_overall_limit_reload_rate,
            'relay_join_req_limit_bucket_size': self.relay_join_req_limit_bucket_size,
            'relay_notify_limit_bucket_size': self.relay_notify_limit_bucket_size,
            'relay_global_uplink_limit_bucket_size': self.relay_global_uplink_limit_bucket_size,
            'relay_overall_limit_bucket_size': self.relay_overall_limit_bucket_size,
            'measurements': self.measurements
        }

class Device:
    """
    Definition of Device Object for Chirpstack.

    Params:
    - name: Name of the device.
    - dev_eui (EUI64): unique identifier of the device.
    - application_id: unique identifier of the application associated to the device.
        Passing in an Application object will also work.
    - device_profile_id: unique identifier of the device profile associated to the device.
        Passing in a DeviceProfile object will also work.
    - join_eui (EUI64, optional): unique identifier of the join server.
        This field will be automatically set on OTAA.
    - description (optional): Description of the device.
    - skip_fcnt_check (optional): Disable frame-counter validation. 
        Note, disabling compromises security as it allows replay-attacks.
    - is_disabled (optional): Disable the device.
    - tags (dict<string,string>, optional): Additional metadata associated with the device.
        These tags are exposed in all the integration events.
    - variables (dict<string,string>, optional): Additional variables associated with the device.
        These variables are not exposed in the event payloads. 
        They can be used together with integrations to store secrets that must be configured per device.
    """
    def __init__(self,name:str,dev_eui:str,application_id:str,device_profile_id:str,
        join_eui:str="",description:str='',skip_fcnt_check:bool=False,is_disabled:bool=False,tags:dict={},variables:dict={}):
        """Constructor method to initialize a Device object."""
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("Device: All values in 'tags' dictionary must be strings.")
        if not all(isinstance(value, str) for value in variables.values()):
            raise ValueError("Device: All values in 'variables' dictionary must be strings.")

        self.name = name
        self.dev_eui = dev_eui
        self.application_id = str(application_id)
        self.device_profile_id = str(device_profile_id)
        self.join_eui = join_eui
        self.description = description
        self.skip_fcnt_check = skip_fcnt_check
        self.is_disabled = is_disabled
        self.tags = tags
        self.variables = variables

    @classmethod
    def from_grpc(cls, grpc_device):
        """Convert gRPC device object to Device object."""
        return cls(
            name=getattr(grpc_device, 'name', ''),
            dev_eui=getattr(grpc_device, 'dev_eui', ''),
            application_id=getattr(grpc_device, 'application_id', ''),
            device_profile_id=getattr(grpc_device, 'device_profile_id', ''),
            join_eui=getattr(grpc_device, 'join_eui', ''),
            description=getattr(grpc_device, 'description', ''),
            skip_fcnt_check=getattr(grpc_device, 'skip_fcnt_check', False),
            is_disabled=getattr(grpc_device, 'is_disabled', False),
            tags=dict(getattr(grpc_device, 'tags', {})),
            variables=dict(getattr(grpc_device, 'variables', {}))
        )

    def __str__(self):
        """String representation of the Device object"""
        return self.dev_eui
    
    def to_dict(self) -> dict:
        """Convert Device object to dictionary."""
        return {
            'name': self.name,
            'dev_eui': self.dev_eui,
            'application_id': self.application_id,
            'device_profile_id': self.device_profile_id,
            'join_eui': self.join_eui,
            'description': self.description,
            'skip_fcnt_check': self.skip_fcnt_check,
            'is_disabled': self.is_disabled,
            'tags': self.tags,
            'variables': self.variables
        }

class DeviceKeys:
    """
    Definition of Device Keys Object for Chirpstack.

    Params:
    - dev_eui (EUI64): The unique identifier of the device associated with the keys.
        Passing in a Device object will also work.
    - nwk_key: Network root key (128 bit). For LoRaWAN 1.0.x, use this field for the LoRaWAN 1.0.x 'AppKey`.
    - app_key (optional): Application root key (128 bit). This field only needs to be set for LoRaWAN 1.1.x devices.
    """
    def __init__(self,dev_eui:str,nwk_key:str,app_key:str=""):
        """Constructor method to initialize a Device Key object."""

        self.dev_eui = str(dev_eui)
        self.nwk_key = nwk_key
        self.app_key = app_key
    
    def to_dict(self) -> dict:
        """Convert DeviceKeys object to dictionary."""
        return {
            'dev_eui': self.dev_eui,
            'nwk_key': self.nwk_key,
            'app_key': self.app_key
        }