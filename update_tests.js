const fs = require('fs');

// Read the file
const filePath = 'src/components/IBSettings/IBSettings.test.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Replace all instances of the connection status mock without account_info
content = content.replace(/vi\.mocked\(ibConnectionApi\.getConnectionStatus\)\.mockResolvedValue\(\{\s+connected: false,\s+message: 'Not connected'\s+\}\);/g, 
  `vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected',
				account_info: null
			});`);

// Add waitFor to all test cases
content = content.replace(/render\(<IBSettings \/>\);\s+\s+const (hostInput|portInput|clientIdInput|passwordInput)/g, 
  `render(<IBSettings />);
			
			// Wait for loading to complete
			await waitFor(() => {
				expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
			});
			
			const $1`);

// Write the updated content back to the file
fs.writeFileSync(filePath, content);
