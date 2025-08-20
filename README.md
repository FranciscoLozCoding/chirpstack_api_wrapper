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

## Versioning
The version of the wrapper is aligned with the version of the chirpstack-api library, but the patch version can differ.

For example, if the chirpstack-api library is at version 4.14, the wrapper is at version 4.14. But if a patch version is needed, the wrapper can be at version 4.14.1 even if the chirpstack-api library is at version 4.14.0.

## Test Suite
To run the test suite download the requirements in `/test/`, then run the following command:
```
pytest
```
This will run both the unit and integration tests.

## Unit Tests

This section describes the unit tests for the Chirpstack API Wrapper.

### Running Unit Tests

To run the unit tests for this project from the project root directory, run the following command:

```bash
pytest -m "not integration"
```

This will automatically discover and run all unit tests. Optionally, you can also run a specific test by name:
```bash
pytest test/test_objects.py::TestObjects::test_device_profile_to_dict -v
```

### Notes

- Unit tests use mocks and do **not** require a running Chirpstack server.
- Coverage reports will be generated in the default locations (see below for integration test coverage).
- If you add new tests, follow the naming conventions in `pytest.ini` and place them in the `test/` directory.

## Integration Tests

This section describes the integration tests for the Chirpstack API Wrapper.

### Overview

Integration tests verify that the wrapper correctly communicates with a real Chirpstack server. These tests create, read, update, and delete actual records on the server to ensure the API wrapper functions correctly in a real environment.

### Prerequisites

1. **Running Chirpstack Server**: The tests require a Chirpstack server running on `localhost:8081`
2. **Admin Access**: Username `admin` with password `admin`
3. **Python Environment**: The same environment used for unit tests
4. **Dependencies**: All dependencies from `requirements.txt` must be installed

### Test Data

All test records are marked with a `"test": "true"` tag to identify them as test data. This makes it easy to:
- Identify test records in the Chirpstack UI
- Clean up test data if needed
- Distinguish from production data

### Test Coverage

The integration tests cover:

#### Core Operations
- ✅ **Authentication**: Login and token management
- ✅ **Tenants**: Create, read, list, and delete
- ✅ **Applications**: Create, read, list, update, and delete
- ✅ **Device Profiles**: Create, read, list, and delete
- ✅ **Devices**: Create, read, list, update, and delete
- ✅ **Gateways**: Create, read, list, and delete

#### Advanced Features
- ✅ **Pagination**: Testing list operations with limits and offsets
- ✅ **Error Handling**: Testing behavior with non-existent resources
- ✅ **Data Validation**: Ensuring created records match expected values
- ✅ **Cleanup**: Automatic cleanup of test data

### Running Integration Tests

#### Option 1: Using the Script (Recommended)

```bash
# Make sure you're in the project root directory
cd /path/to/chirpstack_api_wrapper

# Run the integration test script
python run_integration_tests.py
```

The script will:
- Check prerequisites
- Confirm you want to create test data
- Run all integration tests
- Generate coverage reports
- Clean up test data automatically

#### Option 2: Using pytest directly

```bash
# Run all integration tests
pytest test/test_integration.py -v

# Run with coverage
pytest test/test_integration.py -v --cov=chirpstack_api_wrapper --cov-report=html
```

### Test Execution Order

Tests are numbered to ensure proper execution order:

1. **Setup**: Login and server connectivity
2. **Tenant Creation**: Create test tenant
3. **Application Creation**: Create test application
4. **Device Profile Creation**: Create test device profile
5. **Device Creation**: Create test device
6. **Gateway Creation**: Create test gateway
7. **Operations**: Test CRUD operations
8. **Advanced Features**: Test pagination and error handling
9. **Cleanup**: Verify all records before cleanup

### Test Data Lifecycle

1. **Setup**: Tests create minimal required data
2. **Execution**: Each test verifies its operations
3. **Cleanup**: All test data is automatically removed
4. **Verification**: Final test ensures cleanup was successful

### Safety Features

- **Automatic Cleanup**: All test data is removed after tests complete
- **Unique Names**: Test records use timestamps to avoid conflicts
- **Error Handling**: Tests handle failures gracefully
- **User Confirmation**: Script asks for confirmation before running

### Troubleshooting

#### Common Issues

1. **Connection Refused**
   - Ensure Chirpstack server is running on localhost:8081
   - Check firewall settings

2. **Authentication Failed**
   - Verify username/password are correct
   - Check server configuration

3. **Test Data Not Cleaned Up**
   - Check test logs for cleanup errors
   - Manually remove test records if needed (look for "test" tags)

4. **Permission Denied**
   - Ensure admin user has full permissions
   - Check server access control settings

#### Debug Mode

Run tests with verbose output for debugging:

```bash
pytest test/test_integration.py -v -s --tb=long
```

#### Manual Cleanup

If tests fail and leave test data, you can manually clean up:

1. Open Chirpstack web interface
2. Look for records with `"test": "true"` tags
3. Delete them manually

### Coverage Reports

Integration tests generate coverage reports in:
- `htmlcov-integration/` - HTML coverage report
- `coverage-integration.xml` - XML coverage report
- `coverage-integration.lcov` - LCOV coverage report

### Contributing

When adding new integration tests:

1. **Follow Naming Convention**: Use `test_XX_description` format
2. **Add Integration Marker**: Use `@pytest.mark.integration` decorator
3. **Include Cleanup**: Ensure test data is cleaned up
4. **Add Documentation**: Update this file with new test descriptions
5. **Test Safety**: Ensure tests don't interfere with production data

## Integration vs Unit Tests

| Aspect | Unit Tests | Integration Tests |
|--------|------------|-------------------|
| **Scope** | Individual functions/methods | Full API workflow |
| **Dependencies** | Mocked | Real server |
| **Speed** | Fast | Slower |
| **Reliability** | High | Depends on server |
| **Coverage** | Code logic | API behavior |
| **Use Case** | Development | Validation |

Run unit tests for development and integration tests for validation.