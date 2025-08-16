import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, AlertCircle, CheckCircle, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { ibConnectionApi, IBSettings as IBSettingsType, ConnectionStatus } from '../../api/ib-connection';

export const IBSettings: React.FC = () => {
	const [settings, setSettings] = useState<IBSettingsType>({
		host: '127.0.0.1',
		port: 7497,
		client_id: 1,
		username: '',
		password: '',
		account_id: '',
		auto_connect: false
	});

	const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
		connected: false,
		message: 'Not connected',
		account_info: null
	});

	const [loading, setLoading] = useState(false);
	const [loadingSettings, setLoadingSettings] = useState(true);
	const [saving, setSaving] = useState(false);
	const [connecting, setConnecting] = useState(false);
	const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
	const [showPassword, setShowPassword] = useState(false);
	const [errors, setErrors] = useState<Record<string, string>>({});

	// Load settings and connection status on mount
	useEffect(() => {
		loadSettings();
		checkConnectionStatus();
		
		// Set up periodic status checks
		const interval = setInterval(checkConnectionStatus, 5000);
		return () => clearInterval(interval);
	}, []);

	const loadSettings = async () => {
		try {
			setLoadingSettings(true);
			const data = await ibConnectionApi.getSettings();
			setSettings(data);
		} catch (error) {
			console.error('Failed to load settings:', error);
		} finally {
			setLoadingSettings(false);
		}
	};

	const checkConnectionStatus = async () => {
		try {
			const status = await ibConnectionApi.getConnectionStatus();
			setConnectionStatus(status);
		} catch (error) {
			console.error('Failed to check connection status:', error);
			setConnectionStatus({ 
				connected: false,
				message: 'Not connected',
				account_info: null
			});
		}
	};

	const validateForm = (): boolean => {
		const newErrors: Record<string, string> = {};

		if (!settings.host.trim()) {
			newErrors.host = 'Host is required';
		}

		if (!settings.port || settings.port < 1 || settings.port > 65535) {
			newErrors.port = 'Port must be between 1 and 65535';
		}

		if (settings.client_id <= 0) {
			newErrors.client_id = 'Client ID must be a positive number';
		}

		setErrors(newErrors);
		return Object.keys(newErrors).length === 0;
	};

	const handleSaveSettings = async () => {
		if (!validateForm()) {
			return;
		}

		try {
			setSaving(true);
			setMessage(null);
			const response = await ibConnectionApi.updateSettings(settings);
			setMessage({ type: 'success', text: response.message || 'Settings updated successfully' });
		} catch (error: any) {
			setMessage({ type: 'error', text: error.message || 'Failed to save settings' });
		} finally {
			setSaving(false);
		}
	};

	const handleConnect = async () => {
		try {
			setConnecting(true);
			setMessage(null);
			const response = await ibConnectionApi.connect();
			setMessage({ type: 'success', text: response.message || 'Connected successfully' });
			await checkConnectionStatus();
		} catch (error: any) {
			setMessage({ type: 'error', text: error.message || 'Failed to connect to IB Gateway' });
		} finally {
			setConnecting(false);
		}
	};

	const handleDisconnect = async () => {
		try {
			setConnecting(true);
			setMessage(null);
			const response = await ibConnectionApi.disconnect();
			setMessage({ type: 'success', text: response.message || 'Disconnected successfully' });
			await checkConnectionStatus();
		} catch (error: any) {
			setMessage({ type: 'error', text: error.message || 'Failed to disconnect' });
		} finally {
			setConnecting(false);
		}
	};

	const handleInputChange = (field: keyof IBSettingsType, value: any) => {
		setSettings(prev => ({ ...prev, [field]: value }));
		// Clear error for this field
		if (errors[field]) {
			setErrors(prev => {
				const newErrors = { ...prev };
				delete newErrors[field];
				return newErrors;
			});
		}
	};

	const getPortIndicator = () => {
		if (settings.port === 7496) {
			return (
				<div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 text-sm mt-1">
					<AlertCircle size={14} />
					<span>Warning: Port 7496 is typically used for live trading</span>
				</div>
			);
		}
		if (settings.port === 7497) {
			return (
				<div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 text-sm mt-1">
					<CheckCircle size={14} />
					<span>Paper trading port</span>
				</div>
			);
		}
		return null;
	};

	if (loadingSettings) {
		return (
			<div className="flex items-center justify-center p-8">
				<Loader2 className="animate-spin mr-2" />
				<span>Loading settings...</span>
			</div>
		);
	}

	return (
		<div className="max-w-2xl mx-auto p-6">
			<div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
				<h2 className="text-2xl font-bold mb-6">Interactive Brokers Settings</h2>

				{/* Connection Status */}
				<div className="mb-6 p-4 rounded-lg bg-gray-50 dark:bg-gray-900">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-3">
							{connectionStatus.connected ? (
								<>
									<Wifi className="text-green-500" size={24} />
									<div>
										<span className="font-semibold text-green-600 dark:text-green-400">Connected</span>
										{connectionStatus.account_info && (
											<span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
												Account: {connectionStatus.account_info.account_id} ({connectionStatus.account_info.account_type})
											</span>
										)}
									</div>
								</>
							) : (
								<>
									<WifiOff className="text-gray-400" size={24} />
									<span className="font-semibold text-gray-600 dark:text-gray-400">Disconnected</span>
								</>
							)}
						</div>
						<button
							onClick={connectionStatus.connected ? handleDisconnect : handleConnect}
							disabled={connecting}
							className={`px-4 py-2 rounded-md font-medium transition-colors ${
								connectionStatus.connected
									? 'bg-red-500 hover:bg-red-600 text-white'
									: 'bg-green-500 hover:bg-green-600 text-white'
							} disabled:opacity-50 disabled:cursor-not-allowed`}
						>
							{connecting ? (
								<Loader2 className="animate-spin" size={20} />
							) : connectionStatus.connected ? (
								'Disconnect'
							) : (
								'Connect'
							)}
						</button>
					</div>
				</div>

				{/* Settings Form */}
				<div className="space-y-4">
					{/* Host */}
					<div>
						<label htmlFor="host" className="block text-sm font-medium mb-1">
							Host
						</label>
						<input
							id="host"
							type="text"
							value={settings.host}
							onChange={(e) => handleInputChange('host', e.target.value)}
							disabled={connectionStatus.connected}
							className={`w-full px-3 py-2 border rounded-md ${
								errors.host ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
							} bg-white dark:bg-gray-700 disabled:bg-gray-100 dark:disabled:bg-gray-800`}
						/>
						{errors.host && (
							<p className="text-red-500 text-sm mt-1">{errors.host}</p>
						)}
					</div>

					{/* Port */}
					<div>
						<label htmlFor="port" className="block text-sm font-medium mb-1">
							Port
						</label>
						<input
							id="port"
							type="number"
							value={settings.port}
							onChange={(e) => handleInputChange('port', parseInt(e.target.value) || 0)}
							disabled={connectionStatus.connected}
							className={`w-full px-3 py-2 border rounded-md ${
								errors.port ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
							} bg-white dark:bg-gray-700 disabled:bg-gray-100 dark:disabled:bg-gray-800`}
						/>
						{errors.port && (
							<p className="text-red-500 text-sm mt-1">{errors.port}</p>
						)}
						{getPortIndicator()}
					</div>

					{/* Client ID */}
					<div>
						<label htmlFor="client_id" className="block text-sm font-medium mb-1">
							Client ID
						</label>
						<input
							id="client_id"
							type="number"
							value={settings.client_id}
							onChange={(e) => {
								const value = parseInt(e.target.value);
								handleInputChange('client_id', isNaN(value) ? 0 : value);
							}}
							disabled={connectionStatus.connected}
							className={`w-full px-3 py-2 border rounded-md ${
								errors.client_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
							} bg-white dark:bg-gray-700 disabled:bg-gray-100 dark:disabled:bg-gray-800`}
						/>
						{errors.client_id && (
							<p className="text-red-500 text-sm mt-1">{errors.client_id}</p>
						)}
					</div>

					{/* Username */}
					<div>
						<label htmlFor="username" className="block text-sm font-medium mb-1">
							Username (Optional)
						</label>
						<input
							id="username"
							type="text"
							value={settings.username || ''}
							onChange={(e) => handleInputChange('username', e.target.value)}
							className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
						/>
					</div>

					{/* Password */}
					<div>
						<label htmlFor="password" className="block text-sm font-medium mb-1">
							Password (Optional)
						</label>
						<div className="relative">
							<input
								id="password"
								type={showPassword ? 'text' : 'password'}
								value={settings.password || ''}
								onChange={(e) => handleInputChange('password', e.target.value)}
								className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
							/>
							<button
								type="button"
								onClick={() => setShowPassword(!showPassword)}
								className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
								aria-label={showPassword ? 'Hide password' : 'Show password'}
							>
								{showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
							</button>
						</div>
					</div>

					{/* Account ID */}
					<div>
						<label htmlFor="account" className="block text-sm font-medium mb-1">
							Account ID (Optional)
						</label>
						<input
							id="account"
							type="text"
							value={settings.account_id || ''}
							onChange={(e) => handleInputChange('account_id', e.target.value)}
							placeholder="e.g., DU123456"
							className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
						/>
					</div>

					{/* Auto-connect */}
					<div className="flex items-center">
						<input
							id="auto_connect"
							type="checkbox"
							checked={settings.auto_connect}
							onChange={(e) => handleInputChange('auto_connect', e.target.checked)}
							className="mr-2"
						/>
						<label htmlFor="auto_connect" className="text-sm font-medium">
							Auto-connect on startup
						</label>
					</div>
				</div>

				{/* Messages */}
				{message && (
					<div
						className={`mt-4 p-3 rounded-md ${
							message.type === 'success'
								? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
								: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
						}`}
					>
						<div className="flex items-center gap-2">
							{message.type === 'success' ? (
								<CheckCircle size={20} />
							) : (
								<AlertCircle size={20} />
							)}
							<span>{message.text}</span>
						</div>
					</div>
				)}

				{/* Save Button */}
				<div className="mt-6 flex justify-end">
					<button
						onClick={handleSaveSettings}
						disabled={saving}
						className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{saving ? (
							<span className="flex items-center gap-2">
								<Loader2 className="animate-spin" size={20} />
								Saving...
							</span>
						) : (
							'Save Settings'
						)}
					</button>
				</div>
			</div>
		</div>
	);
};
