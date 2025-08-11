import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StrikeSelector } from '../StrikeSelector'
import type { StrikeConfig } from '../../types/strategy'

describe('StrikeSelector Component', () => {
	const mockOnStrikesChange = vi.fn()
	const defaultCurrentPrice = 500.00
	
	const defaultStrikes: StrikeConfig = {
		put_short_pct: 97.5,
		put_long_pct: 97.0,
		call_short_pct: 102.5,
		call_long_pct: 103.0
	}

	beforeEach(() => {
		vi.clearAllMocks()
	})

	it('renders with default strike percentages', () => {
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		// Check that number inputs show correct default values
		expect(screen.getByRole('spinbutton', { name: /Put Short Strike/i })).toHaveValue(97.5)
		expect(screen.getByRole('spinbutton', { name: /Put Long Strike/i })).toHaveValue(97.0)
		expect(screen.getByRole('spinbutton', { name: /Call Short Strike/i })).toHaveValue(102.5)
		expect(screen.getByRole('spinbutton', { name: /Call Long Strike/i })).toHaveValue(103.0)
	})

	it('displays calculated strike prices correctly', () => {
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		// Check calculated prices are displayed
		// Put Short: 500 * 0.975 = 487.50, rounded to 490
		expect(screen.getByTestId('put-short-price')).toHaveTextContent('$490')
		// Put Long: 500 * 0.97 = 485, stays at 485
		expect(screen.getByTestId('put-long-price')).toHaveTextContent('$485')
		// Call Short: 500 * 1.025 = 512.50, rounded to 515
		expect(screen.getByTestId('call-short-price')).toHaveTextContent('$515')
		// Call Long: 500 * 1.03 = 515, stays at 515
		expect(screen.getByTestId('call-long-price')).toHaveTextContent('$515')
	})

	it('updates local state when input value changes', async () => {
		const user = userEvent.setup()
		
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const putShortInput = screen.getByRole('spinbutton', { name: /Put Short Strike/i })
		
		// Clear and type new value
		await user.clear(putShortInput)
		await user.type(putShortInput, '96.5')

		// Check input shows new value
		expect(putShortInput).toHaveValue(96.5)
		
		// Check price updates
		// 500 * 0.965 = 482.50, rounded to 485
		await waitFor(() => {
			expect(screen.getByTestId('put-short-price')).toHaveTextContent('$485')
		})
	})

	it('validates input ranges for put strikes (0-100)', async () => {
		const user = userEvent.setup()
		
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const putShortInput = screen.getByRole('spinbutton', { name: /Put Short Strike/i })
		
		// Try to enter invalid value > 100
		await user.clear(putShortInput)
		await user.type(putShortInput, '105')

		// Should show error or clamp to 100
		expect(screen.getByText(/Put strikes must be between 0-100%/i)).toBeInTheDocument()
	})

	it('validates input ranges for call strikes (100-200)', async () => {
		const user = userEvent.setup()
		
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const callShortInput = screen.getByRole('spinbutton', { name: /Call Short Strike/i })
		
		// Try to enter invalid value < 100
		await user.clear(callShortInput)
		await user.type(callShortInput, '95')

		// Should show error
		expect(screen.getByText(/Call strikes must be between 100-200%/i)).toBeInTheDocument()
	})

	it('calls onStrikesChange callback with debounce', async () => {
		vi.useFakeTimers()
		
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const putShortInput = screen.getByRole('spinbutton', { name: /Put Short Strike/i })
		
		// Simulate input change directly (use valid value that doesn't violate ordering)
		fireEvent.change(putShortInput, { target: { value: '98' } })

		// Callback should not be called immediately
		expect(mockOnStrikesChange).not.toHaveBeenCalled()

		// Fast forward debounce timer (300ms)
		vi.advanceTimersByTime(300)

		// Now callback should be called with new values
		expect(mockOnStrikesChange).toHaveBeenCalledWith({
			put_short_pct: 98,
			put_long_pct: 97.0,
			call_short_pct: 102.5,
			call_long_pct: 103.0
		})

		vi.useRealTimers()
	})

	it('handles slider movements correctly', () => {
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const putShortSlider = screen.getByTestId('put-short-slider')
		
		// Simulate slider change
		fireEvent.change(putShortSlider, { target: { value: '95' } })

		// Check that the input reflects the change
		expect(screen.getByLabelText(/Put Short Strike/i)).toHaveValue(95)
		
		// Check price updates (500 * 0.95 = 475)
		expect(screen.getByTestId('put-short-price')).toHaveTextContent('$475')
	})

	it('maintains strike order constraints (long < short)', () => {
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const putLongInput = screen.getByRole('spinbutton', { name: /Put Long Strike/i })
		
		// Try to set put long higher than put short (97.5)
		fireEvent.change(putLongInput, { target: { value: '98' } })

		// Should show error
		expect(screen.getByText(/Put long strike must be lower than put short/i)).toBeInTheDocument()
	})

	it('supports keyboard navigation for accessibility', () => {
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		const putShortInput = screen.getByRole('spinbutton', { name: /Put Short Strike/i })
		
		// Focus the input
		putShortInput.focus()
		expect(putShortInput).toHaveFocus()

		// Use arrow keys to adjust value
		fireEvent.keyDown(putShortInput, { key: 'ArrowUp' })
		expect(putShortInput).toHaveValue(98.5) // Increments by 1

		fireEvent.keyDown(putShortInput, { key: 'ArrowDown' })
		fireEvent.keyDown(putShortInput, { key: 'ArrowDown' })
		expect(putShortInput).toHaveValue(96.5) // Decrements by 1
	})

	it('rounds strike prices to nearest $5 increment', () => {
		render(
			<StrikeSelector
				strikes={{
					put_short_pct: 97.3, // 486.50 -> 485
					put_long_pct: 96.8,  // 484 -> 485
					call_short_pct: 102.7, // 513.50 -> 515
					call_long_pct: 103.2  // 516 -> 515
				}}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
			/>
		)

		expect(screen.getByTestId('put-short-price')).toHaveTextContent('$485')
		expect(screen.getByTestId('put-long-price')).toHaveTextContent('$485')
		expect(screen.getByTestId('call-short-price')).toHaveTextContent('$515')
		expect(screen.getByTestId('call-long-price')).toHaveTextContent('$515')
	})

	it('displays loading state during calculation', async () => {
		render(
			<StrikeSelector
				strikes={defaultStrikes}
				currentPrice={defaultCurrentPrice}
				onStrikesChange={mockOnStrikesChange}
				loading={true}
			/>
		)

		// Inputs should be disabled during loading
		expect(screen.getByLabelText(/Put Short Strike/i)).toBeDisabled()
		expect(screen.getByLabelText(/Put Long Strike/i)).toBeDisabled()
		expect(screen.getByLabelText(/Call Short Strike/i)).toBeDisabled()
		expect(screen.getByLabelText(/Call Long Strike/i)).toBeDisabled()
		
		// Loading indicator should be visible
		expect(screen.getByText(/Calculating.../i)).toBeInTheDocument()
	})
})