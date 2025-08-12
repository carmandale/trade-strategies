/**
 * API client for Interactive Brokers connection management
 */

interface IBSettings {
	host: string;
	port: number;
	client_id: number;
	username?: string;
	password?: string;
	account?: string;  // Changed from account_id to match backend
	auto_connect: boolean;
}

interface ConnectionStatus {
	connected: boolean;
	host?: string;
	port?: number;
	last_heartbeat?: string;
	account_info?: {
		account_id: string;
		account_type: string;
	};
	error?: string;
}

interface APIResponse {
	success: boolean;
	message: string;
	data?: any;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class IBConnectionAPI {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE) {
		this.baseUrl = baseUrl;
	}

	/**
	 * Get current IB settings
	 */
	async getSettings(): Promise<IBSettings> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/settings`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch settings: ${response.statusText}`);
		}

		return response.json();
	}

	/**
	 * Update IB settings
	 */
	async updateSettings(settings: Partial<IBSettings>): Promise<APIResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/settings`, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(settings),
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || 'Failed to update settings');
		}

		return response.json();
	}

	/**
	 * Connect to Interactive Brokers
	 */
	async connect(): Promise<APIResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/connection/connect`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || 'Failed to connect');
		}

		return response.json();
	}

	/**
	 * Disconnect from Interactive Brokers
	 */
	async disconnect(): Promise<APIResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/connection/disconnect`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || 'Failed to disconnect');
		}

		return response.json();
	}

	/**
	 * Get connection status
	 */
	async getConnectionStatus(): Promise<ConnectionStatus> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/connection/status`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch connection status: ${response.statusText}`);
		}

		return response.json();
	}

	/**
	 * Test connection with given settings
	 */
	async testConnection(settings: Partial<IBSettings>): Promise<APIResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/connection/test`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(settings),
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || 'Connection test failed');
		}

		return response.json();
	}

	/**
	 * Get connection health metrics
	 */
	async getHealthMetrics(): Promise<any> {
		const response = await fetch(`${this.baseUrl}/api/v1/ib/connection/health`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch health metrics: ${response.statusText}`);
		}

		return response.json();
	}
}

// Export singleton instance
export const ibConnectionApi = new IBConnectionAPI();

// Export types
export type { IBSettings, ConnectionStatus, APIResponse };