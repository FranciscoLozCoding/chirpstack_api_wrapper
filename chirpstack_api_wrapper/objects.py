"""Definitions of Objects that are used in Chirpstack"""

class Gateway:
    """
    Definition of Gateway Object for Chirpstack

    Params:
    - name: Name of the gateway.
    - gateway_id (EUI64): Unique identifier for the gateway.
    - tenant_id: Identifier for the tenant associated with the gateway.
    - description (optional): Description of the gateway.
    - tags (dict<string,string>, optional): Additional metadata associated with the gateway.
    - stats_interval (optional): The expected interval in seconds in which the gateway sends its statistics (default is 30 sec).
    """
    def __init__(self,name:str,gateway_id:str,tenant_id:str,description:str='',tags:dict={},stats_interval:int=30):
        """Constructor method to initialize a Gateway object."""            
        if not all(isinstance(value, str) for value in tags.values()):
            raise ValueError("All values in 'tags' dictionary must be strings.")

        self.gateway_id = gateway_id
        self.name = name
        self.description = description
        self.tenant_id = tenant_id
        self.tags = tags
        self.stats_interval = stats_interval
        # self.location = None # configure later if needed
    
    def __str__(self):
        """String representation of the Gateway object"""
        return self.gateway_id

class Device:
    """
    Definition of Device Object for Chirpstack.

    Params:
    - name: Name of the device.
    - dev_eui (EUI64): unique identifier of the device (EUI64).
    - application_id: unique identifier of the application associated to the device.
    - device_profile_id: unique identifier of the device profile associated to the device.
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
            raise ValueError("All values in 'tags' dictionary must be strings.")
        if not all(isinstance(value, str) for value in variables.values()):
            raise ValueError("All values in 'variables' dictionary must be strings.")

        self.name = name
        self.dev_eui = dev_eui
        self.application_id = application_id #TODO: I have to create an application  object
        self.device_profile_id = device_profile_id #TODO: I have to create a device profile object
        self.join_eui = join_eui
        self.description = description
        self.skip_fcnt_check = skip_fcnt_check
        self.is_disabled = is_disabled
        self.tags = tags
        self.variables = variables

    def __str__(self):
        """String representation of the Device object"""
        return self.dev_eui