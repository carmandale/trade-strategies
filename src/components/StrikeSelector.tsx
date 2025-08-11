import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { debounce } from 'lodash'
import * as Slider from '@radix-ui/react-slider'
import type { StrikeConfig } from '../types/strategy'

interface StrikeSelectorProps {
	strikes: StrikeConfig
	currentPrice: number
	onStrikesChange: (strikes: StrikeConfig) => void
	loading?: boolean
}

// Round to nearest $5 increment
const roundToFive = (value: number): number => {
	return Math.round(value / 5) * 5
}

export const StrikeSelector: React.FC<StrikeSelectorProps> = ({
	strikes,
	currentPrice,
	onStrikesChange,
	loading = false
}) => {
	// Local state for immediate UI updates
	const [localStrikes, setLocalStrikes] = useState<StrikeConfig>(strikes)
	const [errors, setErrors] = useState<Record<string, string>>({})

	// Update local state when props change
	useEffect(() => {
		setLocalStrikes(strikes)
	}, [strikes])

	// Debounced callback to parent
	const debouncedOnChange = useMemo(
		() => debounce((newStrikes: StrikeConfig) => {
			onStrikesChange(newStrikes)
		}, 300),
		[onStrikesChange]
	)

	// Calculate actual strike prices from percentages
	const calculateStrikePrice = (percentage: number): number => {
		const price = currentPrice * (percentage / 100)
		return roundToFive(price)
	}

	// Validate strike values
	const validateStrikes = (field: keyof StrikeConfig, value: number, newStrikes?: StrikeConfig): string | null => {
		const strikes = newStrikes || localStrikes
		
		// Put strikes must be between 0-100%
		if (field === 'put_short_pct' || field === 'put_long_pct') {
			if (value < 0 || value > 100) {
				return 'Put strikes must be between 0-100%'
			}
			// Check ordering after value is updated
			const putShort = field === 'put_short_pct' ? value : strikes.put_short_pct
			const putLong = field === 'put_long_pct' ? value : strikes.put_long_pct
			
			if (putLong >= putShort) {
				return 'Put long strike must be lower than put short'
			}
		}

		// Call strikes must be between 100-200%
		if (field === 'call_short_pct' || field === 'call_long_pct') {
			if (value < 100 || value > 200) {
				return 'Call strikes must be between 100-200%'
			}
			// Check ordering after value is updated
			const callShort = field === 'call_short_pct' ? value : strikes.call_short_pct
			const callLong = field === 'call_long_pct' ? value : strikes.call_long_pct
			
			if (callShort >= callLong) {
				return 'Call short strike must be lower than call long'
			}
		}

		return null
	}

	// Handle input changes
	const handleInputChange = (field: keyof StrikeConfig, value: number) => {
		// Create new strikes with updated value
		const newStrikes = { ...localStrikes, [field]: value }
		const error = validateStrikes(field, value, newStrikes)
		
		// Update errors state
		setErrors(prev => {
			if (error) {
				return { ...prev, [field]: error }
			} else {
				const newErrors = { ...prev }
				delete newErrors[field]
				return newErrors
			}
		})

		// Update local state immediately for responsiveness
		setLocalStrikes(newStrikes)

		// Only call parent if valid
		if (!error) {
			debouncedOnChange(newStrikes)
		}
	}

	// Handle keyboard navigation
	const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, field: keyof StrikeConfig) => {
		const currentValue = localStrikes[field]
		
		if (e.key === 'ArrowUp') {
			e.preventDefault()
			handleInputChange(field, currentValue + 1)
		} else if (e.key === 'ArrowDown') {
			e.preventDefault()
			handleInputChange(field, currentValue - 1)
		}
	}

	// Render strike input with slider
	const renderStrikeControl = (
		label: string,
		field: keyof StrikeConfig,
		min: number,
		max: number,
		testIdPrefix: string
	) => {
		const value = localStrikes[field]
		const price = calculateStrikePrice(value)
		const error = errors[field]

		return (
			<div className="space-y-2">
				<div className="flex items-center justify-between">
					<label htmlFor={field} className="text-sm font-medium text-gray-700">
						{label}
					</label>
					<span 
						data-testid={`${testIdPrefix}-price`}
						className="text-sm font-semibold text-gray-900"
					>
						${price}
					</span>
				</div>
				
				<div className="flex items-center space-x-3">
					{/* Slider */}
					<input
						type="range"
						data-testid={`${testIdPrefix}-slider`}
						min={min}
						max={max}
						step={0.5}
						value={value}
						onChange={(e) => handleInputChange(field, parseFloat(e.target.value))}
						disabled={loading}
						className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
					/>
					
					{/* Input field */}
					<input
						type="number"
						id={field}
						aria-label={label}
						min={min}
						max={max}
						step={0.5}
						value={value}
						onChange={(e) => handleInputChange(field, parseFloat(e.target.value) || 0)}
						onKeyDown={(e) => handleKeyDown(e, field)}
						disabled={loading}
						className={`w-20 px-2 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${
							error ? 'border-red-500' : 'border-gray-300'
						}`}
					/>
				</div>
				
				{/* Error message */}
				{error && (
					<p className="text-xs text-red-500">{error}</p>
				)}
			</div>
		)
	}

	return (
		<div className="bg-white rounded-lg shadow p-6 space-y-6">
			<div className="flex items-center justify-between">
				<h3 className="text-lg font-semibold text-gray-900">Strike Selection</h3>
				{loading && (
					<span className="text-sm text-gray-500">Calculating...</span>
				)}
			</div>

			<div className="space-y-6">
				{/* Put Strikes */}
				<div className="space-y-4">
					<h4 className="text-sm font-medium text-gray-700 uppercase tracking-wider">
						Put Strikes
					</h4>
					{renderStrikeControl(
						'Put Short Strike (%)',
						'put_short_pct',
						0,
						100,
						'put-short'
					)}
					{renderStrikeControl(
						'Put Long Strike (%)',
						'put_long_pct',
						0,
						100,
						'put-long'
					)}
				</div>

				{/* Call Strikes */}
				<div className="space-y-4">
					<h4 className="text-sm font-medium text-gray-700 uppercase tracking-wider">
						Call Strikes
					</h4>
					{renderStrikeControl(
						'Call Short Strike (%)',
						'call_short_pct',
						100,
						200,
						'call-short'
					)}
					{renderStrikeControl(
						'Call Long Strike (%)',
						'call_long_pct',
						100,
						200,
						'call-long'
					)}
				</div>
			</div>

			{/* Summary */}
			<div className="pt-4 border-t border-gray-200">
				<div className="grid grid-cols-2 gap-4 text-sm">
					<div>
						<span className="text-gray-500">Put Spread:</span>
						<span className="ml-2 font-medium">
							${calculateStrikePrice(localStrikes.put_long_pct)} / ${calculateStrikePrice(localStrikes.put_short_pct)}
						</span>
					</div>
					<div>
						<span className="text-gray-500">Call Spread:</span>
						<span className="ml-2 font-medium">
							${calculateStrikePrice(localStrikes.call_short_pct)} / ${calculateStrikePrice(localStrikes.call_long_pct)}
						</span>
					</div>
				</div>
			</div>
		</div>
	)
}