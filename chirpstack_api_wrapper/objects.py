"""Definitions of Objects that are used in Chirpstack"""

class Gateway:
    """
    Definition of Gateway Object for Chirpstack

    Params:
    - name: Name of the gateway.
    - gateway_id: Unique identifier for the gateway.
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