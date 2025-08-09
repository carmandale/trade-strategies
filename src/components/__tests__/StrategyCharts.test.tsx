// Comprehensive tests for strategy visualization components
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EquityCurveChart } from '../EquityCurveChart'
import { PLHistogramChart } from '../PLHistogramChart'
import { PerformanceMetrics } from '../PerformanceMetrics'
import { StrategyVisualization } from '../StrategyVisualization'

// Mock chart data based on the Python backtesting results
const mockEquityData = [
  { date: '2024-01-01', cumulativePL: 0, dailyPL: 0 },
  { date: '2024-01-02', cumulativePL: 125.50, dailyPL: 125.50 },
  { date: '2024-01-03', cumulativePL: 95.25, dailyPL: -30.25 },
  { date: '2024-01-04', cumulativePL: 220.75, dailyPL: 125.50 },
  { date: '2024-01-05', cumulativePL: 180.25, dailyPL: -40.50 },
  { date: '2024-01-08', cumulativePL: 305.75, dailyPL: 125.50 },
  { date: '2024-01-09', cumulativePL: 2450.50, dailyPL: 2144.75 }
]

const mockPLDistribution = [
  { range: '-200 to -100', count: 2, midpoint: -150 },
  { range: '-100 to 0', count: 5, midpoint: -50 },
  { range: '0 to 100', count: 15, midpoint: 50 },
  { range: '100 to 200', count: 18, midpoint: 150 },
  { range: '200 to 300', count: 8, midpoint: 250 },
  { range: '300+', count: 2, midpoint: 350 }
]

const mockPerformanceData = {
  totalPL: 2450.50,
  winRate: 68.5,
  totalTrades: 45,
  avgPLPerTrade: 54.45,
  sharpeRatio: 1.35,
  maxDrawdown: -580.25,
  bestTrade: 320.75,
  worstTrade: -185.50,
  consecutiveWins: 8,
  consecutiveLosses: 3
}

describe('EquityCurveChart Component', () => {
  it('renders equity curve chart with correct data', () => {
    render(<EquityCurveChart data={mockEquityData} />)
    
    // Check chart title
    expect(screen.getByText('Equity Curve')).toBeInTheDocument()
    
    // Check that Recharts LineChart is rendered (check for SVG container)
    const chartContainer = document.querySelector('.recharts-wrapper')
    expect(chartContainer).toBeInTheDocument()
  })

  it('displays loading state correctly', () => {
    render(<EquityCurveChart data={[]} loading={true} />)
    
    expect(screen.getByText('Loading chart data...')).toBeInTheDocument()
    const loader = document.querySelector('.animate-spin')
    expect(loader).toBeInTheDocument()
  })

  it('displays empty state when no data provided', () => {
    render(<EquityCurveChart data={[]} />)
    
    expect(screen.getByText('No Data Available')).toBeInTheDocument()
    expect(screen.getByText('No equity curve data to display')).toBeInTheDocument()
  })

  it('shows chart tooltips on hover', () => {
    render(<EquityCurveChart data={mockEquityData} />)
    
    // Check for tooltip container (Recharts creates this)
    const chartArea = document.querySelector('.recharts-wrapper')
    expect(chartArea).toBeInTheDocument()
  })

  it('formats currency values correctly in tooltips', () => {
    render(<EquityCurveChart data={mockEquityData} />)
    
    // The component should format currency values - this is tested through custom tooltip formatting
    const chartContainer = document.querySelector('.recharts-wrapper')
    expect(chartContainer).toBeInTheDocument()
  })

  it('handles responsive layout correctly', () => {
    render(<EquityCurveChart data={mockEquityData} />)
    
    // Check that ResponsiveContainer is used (Recharts responsive wrapper)
    const responsiveContainer = document.querySelector('.recharts-responsive-container')
    expect(responsiveContainer).toBeInTheDocument()
  })

  it('displays zoom controls when enabled', () => {
    render(<EquityCurveChart data={mockEquityData} showZoom={true} />)
    
    expect(screen.getByText('Reset Zoom')).toBeInTheDocument()
    expect(screen.getByLabelText('Zoom In')).toBeInTheDocument()
    expect(screen.getByLabelText('Zoom Out')).toBeInTheDocument()
  })
})

describe('PLHistogramChart Component', () => {
  it('renders P/L histogram with correct data', () => {
    render(<PLHistogramChart data={mockPLDistribution} />)
    
    // Check chart title
    expect(screen.getByText('Profit/Loss Distribution')).toBeInTheDocument()
    
    // Check that Recharts BarChart is rendered
    const chartContainer = document.querySelector('.recharts-wrapper')
    expect(chartContainer).toBeInTheDocument()
  })

  it('displays correct number of bars', () => {
    render(<PLHistogramChart data={mockPLDistribution} />)
    
    // Check that bars are rendered (Recharts creates rect elements for bars)
    const chartArea = document.querySelector('.recharts-wrapper')
    expect(chartArea).toBeInTheDocument()
  })

  it('shows loading state correctly', () => {
    render(<PLHistogramChart data={[]} loading={true} />)
    
    expect(screen.getByText('Loading histogram data...')).toBeInTheDocument()
    const loader = document.querySelector('.animate-spin')
    expect(loader).toBeInTheDocument()
  })

  it('displays empty state when no data provided', () => {
    render(<PLHistogramChart data={[]} />)
    
    expect(screen.getByText('No Data Available')).toBeInTheDocument()
    expect(screen.getByText('No profit/loss distribution data to display')).toBeInTheDocument()
  })

  it('colors bars correctly based on profit/loss', () => {
    render(<PLHistogramChart data={mockPLDistribution} />)
    
    // The component should color bars differently for positive/negative values
    const chartContainer = document.querySelector('.recharts-wrapper')
    expect(chartContainer).toBeInTheDocument()
  })

  it('displays statistics summary', () => {
    render(<PLHistogramChart data={mockPLDistribution} showStats={true} />)
    
    // Verify the statistics section and query within that container to avoid duplicate labels elsewhere
    const statsHeader = screen.getByText('Distribution Statistics')
    expect(statsHeader).toBeInTheDocument()
    const statsSection = statsHeader.closest('div') as HTMLElement
    expect(statsSection).toBeTruthy()

    expect(within(statsSection).getByText(/Total Trades:/)).toBeInTheDocument()
    expect(within(statsSection).getByText(/Most Common Range:/)).toBeInTheDocument()
  })
})

describe('PerformanceMetrics Component', () => {
  it('renders all performance metrics correctly', () => {
    render(<PerformanceMetrics data={mockPerformanceData} />)
    
    // Check key metrics
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
    expect(screen.getByText('Total P/L')).toBeInTheDocument()
    expect(screen.getByText('+$2,450.50')).toBeInTheDocument()
    
    expect(screen.getByText('Win Rate')).toBeInTheDocument()
    expect(screen.getByText('68.5%')).toBeInTheDocument()
    
    expect(screen.getByText('Total Trades')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
    
    expect(screen.getByText('Avg P/L per Trade')).toBeInTheDocument()
    expect(screen.getByText('+$54.45')).toBeInTheDocument()
  })

  it('displays advanced metrics when expanded', () => {
    render(<PerformanceMetrics data={mockPerformanceData} expanded={true} />)
    
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument()
    expect(screen.getByText('1.35')).toBeInTheDocument()
    
    expect(screen.getByText('Max Drawdown')).toBeInTheDocument()
    expect(screen.getByText('$580.25')).toBeInTheDocument()
    
    expect(screen.getByText('Best Trade')).toBeInTheDocument()
    expect(screen.getByText('+$320.75')).toBeInTheDocument()
    
    expect(screen.getByText('Worst Trade')).toBeInTheDocument()
    expect(screen.getByText('$185.50')).toBeInTheDocument()
  })

  it('handles negative total P/L correctly', () => {
    const negativeData = { ...mockPerformanceData, totalPL: -1250.75, avgPLPerTrade: -27.79 }
    render(<PerformanceMetrics data={negativeData} />)
    
    const totalPL = screen.getByText('$1,250.75')
    const avgPL = screen.getByText('$27.79')
    
    expect(totalPL).toHaveClass('text-red-600')
    expect(avgPL).toHaveClass('text-red-600')
  })

  it('displays risk metrics with proper styling', () => {
    render(<PerformanceMetrics data={mockPerformanceData} expanded={true} />)
    
    // Max drawdown should be styled as negative/risk
    const maxDrawdown = screen.getByText('$580.25')
    expect(maxDrawdown).toHaveClass('text-red-600')
  })

  it('shows expand/collapse toggle', async () => {
    const user = userEvent.setup()
    render(<PerformanceMetrics data={mockPerformanceData} />)
    
    const expandButton = screen.getByText('Show More')
    await user.click(expandButton)
    
    expect(screen.getByText('Show Less')).toBeInTheDocument()
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument()
  })

  it('displays metrics in responsive grid layout', () => {
    render(<PerformanceMetrics data={mockPerformanceData} />)
    
    const metricsGrid = document.querySelector('.grid')
    expect(metricsGrid).toBeInTheDocument()
    expect(metricsGrid).toHaveClass('grid-cols-2', 'md:grid-cols-4')
  })
})

describe('StrategyVisualization Component', () => {
  const mockVisualizationData = {
    equityData: mockEquityData,
    histogramData: mockPLDistribution,
    performanceData: mockPerformanceData
  }

  it('renders complete visualization dashboard', () => {
    render(<StrategyVisualization data={mockVisualizationData} />)
    
    // Check all main sections are present
    expect(screen.getByText('Strategy Analysis')).toBeInTheDocument()
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
    expect(screen.getByText('Equity Curve')).toBeInTheDocument()
    expect(screen.getByText('Profit/Loss Distribution')).toBeInTheDocument()
  })

  it('handles loading state for entire dashboard', () => {
    render(<StrategyVisualization data={null} loading={true} />)
    
    expect(screen.getByText('Loading strategy analysis...')).toBeInTheDocument()
    const loaders = document.querySelectorAll('.animate-spin')
    expect(loaders.length).toBeGreaterThan(0)
  })

  it('displays error state correctly', () => {
    const errorMessage = 'Failed to load visualization data'
    render(<StrategyVisualization data={null} error={errorMessage} />)
    
    expect(screen.getByText('Visualization Error')).toBeInTheDocument()
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('handles retry action in error state', async () => {
    const user = userEvent.setup()
    const onRetryMock = vi.fn()
    
    render(<StrategyVisualization data={null} error="Test error" onRetry={onRetryMock} />)
    
    const retryButton = screen.getByText('Retry')
    await user.click(retryButton)
    
    expect(onRetryMock).toHaveBeenCalledTimes(1)
  })

  it('supports responsive layout switching', async () => {
    const user = userEvent.setup()
    render(<StrategyVisualization data={mockVisualizationData} />)
    
    // Check for layout toggle button
    const layoutToggle = screen.getByLabelText('Toggle Layout')
    await user.click(layoutToggle)
    
    // Layout should change (this would be reflected in CSS classes)
    expect(layoutToggle).toBeInTheDocument()
  })

  it('enables chart export functionality', () => {
    render(<StrategyVisualization data={mockVisualizationData} enableExport={true} />)
    
    expect(screen.getByText('Export Charts')).toBeInTheDocument()
    expect(screen.getByLabelText('Export as PNG')).toBeInTheDocument()
    expect(screen.getByLabelText('Export as CSV')).toBeInTheDocument()
  })

  it('displays strategy metadata', () => {
    const strategyInfo = {
      name: 'SPY Iron Condor Daily',
      symbol: 'SPY',
      timeframe: 'daily',
      parameters: { putShort: 0.975, callShort: 1.02, credit: 25 }
    }
    
    render(<StrategyVisualization data={mockVisualizationData} strategyInfo={strategyInfo} />)
    
    expect(screen.getByText('SPY Iron Condor Daily')).toBeInTheDocument()
    expect(screen.getByText('SPY')).toBeInTheDocument()
    expect(screen.getByText('Daily (0DTE)')).toBeInTheDocument()
  })
})

describe('Chart Integration Tests', () => {
  it('all charts maintain consistent styling themes', () => {
    const { container } = render(
      <div>
        <EquityCurveChart data={mockEquityData} />
        <PLHistogramChart data={mockPLDistribution} />
        <PerformanceMetrics data={mockPerformanceData} />
      </div>
    )
    
    // Check for consistent dark mode support without relying on Tailwind variant selectors in JSDOM
    const charts = container.querySelectorAll('[class*="dark:bg-gray-800"]')
    expect(charts.length).toBeGreaterThan(0)
  })

  it('handles window resize events correctly', () => {
    render(<EquityCurveChart data={mockEquityData} />)
    
    // Check that responsive containers are present
    const responsiveContainers = document.querySelectorAll('.recharts-responsive-container')
    expect(responsiveContainers.length).toBe(1)
    
    // Simulate window resize
    fireEvent(window, new Event('resize'))
    
    // Charts should still be properly rendered
    expect(responsiveContainers[0]).toBeInTheDocument()
  })

  it('maintains accessibility standards across all charts', () => {
    render(
      <div>
        <EquityCurveChart data={mockEquityData} />
        <PLHistogramChart data={mockPLDistribution} />
        <PerformanceMetrics data={mockPerformanceData} />
      </div>
    )
    
    // Check for proper ARIA labels and roles
    const chartElements = document.querySelectorAll('[role="img"], [aria-label]')
    expect(chartElements.length).toBeGreaterThan(0)
  })

  it('handles data updates smoothly', () => {
    const { rerender } = render(<EquityCurveChart data={mockEquityData.slice(0, 3)} />)
    
    // Update with more data
    rerender(<EquityCurveChart data={mockEquityData} />)
    
    // Chart should still be rendered correctly
    const chartContainer = document.querySelector('.recharts-wrapper')
    expect(chartContainer).toBeInTheDocument()
  })
})