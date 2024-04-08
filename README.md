# chirpstack-api-wrapper
An abstraction layer over the `chirpstack_api` python library. Implements `ChirpstackClient` that simplifies calling the chirpstack grpc api.

## Using ChirpstackClient
```py
from chirpstack_api_wrapper import ChirpstackClient
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chirpstack-account-email",
        default=os.getenv("CHIRPSTACK_ACCOUNT_EMAIL"),
        help="The Chirpstack Account's email to use to access APIs",
    )
    parser.add_argument(
        "--chirpstack-account-password",
        default=os.getenv("CHIRPSTACK_ACCOUNT_PASSWORD"),
        help="The Chirpstack Account's password to use to access APIs",
    )
    parser.add_argument(
        "--chirpstack-api-interface",
        default=os.getenv("CHIRPSTACK_API_INTERFACE"),
        help="Chirpstack's server API interface. The port is usually 8080",
    )
    args = parser.parse_args()

    chirpstack_client = ChirpstackClient(args)

    chirpstack_client.list_tenants()

if __name__ == "__main__":
    main() 
```

## Using the Lib
This is not published on pip so use pip together with git.
```
pip install git+https://github.com/waggle-sensor/chirpstack-api-wrapper
```

## Test Suite
To run unit tests download the requirements in `/test/`, then run the following command
```
pytest
```