# chirpstack-api-wrapper
An abstraction layer over the `chirpstack_api` python library. Implements `ChirpstackClient` that simplifies calling the chirpstack grpc api.

## Using ChirpstackClient
```py
from chirpstack_api_wrapper import ChirpstackClient

def main():
    chirpstack_client = ChirpstackClient("mock_email","mock_password","localhost:8080")

    print(chirpstack_client.list_tenants())

if __name__ == "__main__":
    main() 
```

## Using the Lib
This is not published on pip so use pip together with git.
```
pip install git+https://github.com/waggle-sensor/chirpstack_api_wrapper
```

## Test Suite
To run unit tests download the requirements in `/test/`, then run the following command
```
pytest
```