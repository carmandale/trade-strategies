import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IBSettings } from './IBSettings';
import { ibConnectionApi } from '../../api/ib-connection';

// Mock the API module
vi.mock('../../api/ib-connection', () => ({
	ibConnectionApi: {
		getSettings: vi.fn().mockResolvedValue({
			host: '127.0.0.1',
			port: 7497,
			client_id: 1,
			username: 'testuser',
			account_id: 'DU123456',
			auto_connect: false
		}),
		updateSettings: vi.fn(),
		connect: vi.fn(),
		disconnect: vi.fn(),
		getConnectionStatus: vi.fn().mockResolvedValue({
			connected: false,
			message: 'Not connected'
		}),
	}
}));

describe('IBSettings', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Initial Load', () => {
		it('should render the settings form', () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			render(<IBSettings />);
			
			expect(screen.getByText('Interactive Brokers Settings')).toBeInTheDocument();
			expect(screen.getByLabelText(/Host/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/Port/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/Client ID/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
		});

		it('should load existing settings on mount', async () => {
			const mockSettings = {
				host: '127.0.0.1',
				port: 7497,
				client_id: 1,
				username: 'testuser',
				account_id: 'DU123456',
				auto_connect: true
			};

			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});

			vi.mocked(ibConnectionApi.getSettings).mockResolvedValueOnce(mockSettings);

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByDisplayValue('127.0.0.1')).toBeInTheDocument();
				expect(screen.getByDisplayValue('7497')).toBeInTheDocument();
				expect(screen.getByDisplayValue('1')).toBeInTheDocument();
				expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
			});
		});

		it('should show loading state while fetching settings', () => {
			vi.mocked(ibConnectionApi.getSettings).mockImplementationOnce(
				() => new Promise(() => {}) // Never resolves
			);
			
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});

			render(<IBSettings />);
			
			expect(screen.getByText(/Loading settings.../i)).toBeInTheDocument();
		});
	});

	describe('Form Validation', () => {
		it('should require host field', async () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			render(<IBSettings />);
			
			const hostInput = screen.getByLabelText(/Host/i);
			await userEvent.clear(hostInput);
			
			const saveButton = screen.getByRole('button', { name: /Save Settings/i });
			await userEvent.click(saveButton);
			
			expect(screen.getByText(/Host is required/i)).toBeInTheDocument();
		});

		it('should validate port range', async () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			render(<IBSettings />);
			
			const portInput = screen.getByLabelText(/Port/i);
			await userEvent.clear(portInput);
			await userEvent.type(portInput, '99999');
			
			const saveButton = screen.getByRole('button', { name: /Save Settings/i });
			await userEvent.click(saveButton);
			
			expect(screen.getByText(/Port must be between 1 and 65535/i)).toBeInTheDocument();
		});

		it('should validate client ID is a positive number', async () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			render(<IBSettings />);
			
			const clientIdInput = screen.getByLabelText(/Client ID/i);
			await userEvent.clear(clientIdInput);
			await userEvent.type(clientIdInput, '-1');
			
			const saveButton = screen.getByRole('button', { name: /Save Settings/i });
			await userEvent.click(saveButton);
			
			expect(screen.getByText(/Client ID must be a positive number/i)).toBeInTheDocument();
		});
	});

	describe('Settings Management', () => {
		it('should save settings when form is submitted', async () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			const mockSettings = {
				host: '127.0.0.1',
				port: 7497,
				client_id: 1,
				username: 'testuser',
				password: 'testpass',
				account_id: 'DU123456',
				auto_connect: false
			};

			vi.mocked(ibConnectionApi.updateSettings).mockResolvedValueOnce({
				success: true,
				message: 'Settings updated successfully'
			});

			render(<IBSettings />);

			// Fill in the form
			await userEvent.type(screen.getByLabelText(/Host/i), mockSettings.host);
			await userEvent.type(screen.getByLabelText(/Port/i), mockSettings.port.toString());
			await userEvent.type(screen.getByLabelText(/Client ID/i), mockSettings.client_id.toString());
			await userEvent.type(screen.getByLabelText(/Username/i), mockSettings.username);
			await userEvent.type(screen.getByLabelText(/Password/i), mockSettings.password);
			await userEvent.type(screen.getByLabelText(/Account ID/i), mockSettings.account_id);

			// Submit the form
			const saveButton = screen.getByRole('button', { name: /Save Settings/i });
			await userEvent.click(saveButton);

			await waitFor(() => {
				expect(ibConnectionApi.updateSettings).toHaveBeenCalledWith(
					expect.objectContaining({
						host: mockSettings.host,
						port: mockSettings.port,
						client_id: mockSettings.client_id,
						username: mockSettings.username,
						password: mockSettings.password,
						account_id: mockSettings.account_id
					})
				);
			});

			// Check for success message
			expect(screen.getByText(/Settings updated successfully/i)).toBeInTheDocument();
		});

		it('should handle save errors gracefully', async () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			vi.mocked(ibConnectionApi.updateSettings).mockRejectedValueOnce(
				new Error('Failed to save settings')
			);

			render(<IBSettings />);

			const saveButton = screen.getByRole('button', { name: /Save Settings/i });
			await userEvent.click(saveButton);

			await waitFor(() => {
				expect(screen.getByText(/Failed to save settings/i)).toBeInTheDocument();
			});
		});

		it('should mask password input', () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			render(<IBSettings />);
			
			const passwordInput = screen.getByLabelText(/Password/i) as HTMLInputElement;
			expect(passwordInput.type).toBe('password');
		});

		it('should toggle password visibility', async () => {
			// Mock connection status
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValue({
				connected: false,
				message: 'Not connected'
			});
			
			render(<IBSettings />);
			
			const passwordInput = screen.getByLabelText(/Password/i) as HTMLInputElement;
			const toggleButton = screen.getByRole('button', { name: /Show password/i });
			
			expect(passwordInput.type).toBe('password');
			
			await userEvent.click(toggleButton);
			expect(passwordInput.type).toBe('text');
			
			await userEvent.click(toggleButton);
			expect(passwordInput.type).toBe('password');
		});
	});

	describe('Connection Management', () => {
		it('should show connection status', async () => {
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValueOnce({
				connected: true,
				host: '127.0.0.1',
				port: 7497,
				last_heartbeat: new Date().toISOString(),
				account_info: {
					account_id: 'DU123456',
					account_type: 'DEMO'
				}
			});

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByText(/Connected/i)).toBeInTheDocument();
				expect(screen.getByText(/DU123456/i)).toBeInTheDocument();
			});
		});

		it('should handle connect button click', async () => {
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValueOnce({
				connected: false
			});

			vi.mocked(ibConnectionApi.connect).mockResolvedValueOnce({
				success: true,
				message: 'Connected successfully'
			});

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /Connect/i })).toBeInTheDocument();
			});

			const connectButton = screen.getByRole('button', { name: /Connect/i });
			await userEvent.click(connectButton);

			await waitFor(() => {
				expect(ibConnectionApi.connect).toHaveBeenCalled();
				expect(screen.getByText(/Connected successfully/i)).toBeInTheDocument();
			});
		});

		it('should handle disconnect button click', async () => {
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValueOnce({
				connected: true,
				host: '127.0.0.1',
				port: 7497
			});

			vi.mocked(ibConnectionApi.disconnect).mockResolvedValueOnce({
				success: true,
				message: 'Disconnected successfully'
			});

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /Disconnect/i })).toBeInTheDocument();
			});

			const disconnectButton = screen.getByRole('button', { name: /Disconnect/i });
			await userEvent.click(disconnectButton);

			await waitFor(() => {
				expect(ibConnectionApi.disconnect).toHaveBeenCalled();
				expect(screen.getByText(/Disconnected successfully/i)).toBeInTheDocument();
			});
		});

		it('should handle connection errors', async () => {
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValueOnce({
				connected: false
			});

			vi.mocked(ibConnectionApi.connect).mockRejectedValueOnce(
				new Error('Failed to connect to IB Gateway')
			);

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /Connect/i })).toBeInTheDocument();
			});

			const connectButton = screen.getByRole('button', { name: /Connect/i });
			await userEvent.click(connectButton);

			await waitFor(() => {
				expect(screen.getByText(/Failed to connect to IB Gateway/i)).toBeInTheDocument();
			});
		});

		it('should disable form inputs while connected', async () => {
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValueOnce({
				connected: true,
				host: '127.0.0.1',
				port: 7497
			});

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByLabelText(/Host/i)).toBeDisabled();
				expect(screen.getByLabelText(/Port/i)).toBeDisabled();
				expect(screen.getByLabelText(/Client ID/i)).toBeDisabled();
			});
		});

		it('should enable form inputs when disconnected', async () => {
			vi.mocked(ibConnectionApi.getConnectionStatus).mockResolvedValueOnce({
				connected: false
			});

			render(<IBSettings />);

			await waitFor(() => {
				expect(screen.getByLabelText(/Host/i)).not.toBeDisabled();
				expect(screen.getByLabelText(/Port/i)).not.toBeDisabled();
				expect(screen.getByLabelText(/Client ID/i)).not.toBeDisabled();
			});
		});
	});

	describe('Auto-connect Feature', () => {
		it('should toggle auto-connect setting', async () => {
			render(<IBSettings />);

			const autoConnectCheckbox = screen.getByRole('checkbox', { name: /Auto-connect on startup/i });
			
			expect(autoConnectCheckbox).not.toBeChecked();
			
			await userEvent.click(autoConnectCheckbox);
			expect(autoConnectCheckbox).toBeChecked();
			
			await userEvent.click(autoConnectCheckbox);
			expect(autoConnectCheckbox).not.toBeChecked();
		});

		it('should save auto-connect preference', async () => {
			vi.mocked(ibConnectionApi.updateSettings).mockResolvedValueOnce({
				success: true,
				message: 'Settings updated'
			});

			render(<IBSettings />);

			const autoConnectCheckbox = screen.getByRole('checkbox', { name: /Auto-connect on startup/i });
			await userEvent.click(autoConnectCheckbox);

			const saveButton = screen.getByRole('button', { name: /Save Settings/i });
			await userEvent.click(saveButton);

			await waitFor(() => {
				expect(ibConnectionApi.updateSettings).toHaveBeenCalledWith(
					expect.objectContaining({
						auto_connect: true
					})
				);
			});
		});
	});

	describe('Environment Indicators', () => {
		it('should show production warning for port 7496', async () => {
			render(<IBSettings />);

			const portInput = screen.getByLabelText(/Port/i);
			await userEvent.clear(portInput);
			await userEvent.type(portInput, '7496');

			expect(screen.getByText(/Warning: Port 7496 is typically used for live trading/i)).toBeInTheDocument();
		});

		it('should show paper trading indicator for port 7497', async () => {
			render(<IBSettings />);

			const portInput = screen.getByLabelText(/Port/i);
			await userEvent.clear(portInput);
			await userEvent.type(portInput, '7497');

			expect(screen.getByText(/Paper trading port/i)).toBeInTheDocument();
		});
	});
});
