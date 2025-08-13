#!/bin/bash
sed -i 's/connected: false,\n\t\t\t\tmessage: "Not connected"/connected: false,\n\t\t\t\tmessage: "Not connected",\n\t\t\t\taccount_info: null/g' src/components/IBSettings/IBSettings.test.tsx
