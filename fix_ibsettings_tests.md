# IBSettings Test Fixes

This commit fixes the IBSettings tests by:

1. Adding `account_info: null` to all connection status mocks
2. Adding proper async handling with `waitFor` to ensure components are fully loaded before testing
3. Fixing test assertions to match the expected component behavior
4. Ensuring all tests wait for loading states to complete

These changes ensure that the tests properly handle the asynchronous nature of the component and the API calls.

