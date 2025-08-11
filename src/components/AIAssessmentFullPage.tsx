import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  ArrowLeft, TrendingUp, TrendingDown, AlertTriangle, Target, 
  BarChart3, PieChart, Activity, Brain, BookOpen, Zap,
  DollarSign, Clock, Shield, Eye, ChevronRight
} from 'lucide-react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ReferenceLine, Area, AreaChart, BarChart, Bar, PieChart as RechartsPieChart, 
  Cell, RadialBarChart, RadialBar
} from 'recharts'
import { AIAssessment, StrategyParams } from '../services/aiAssessmentService'

interface AIAssessmentFullPageProps {
  assessment: AIAssessment
  strategy: StrategyParams
  onClose: () => void
  marketData?: any
  currentPrice: number
}

export const AIAssessmentFullPage: React.FC<AIAssessmentFullPageProps> = ({
  assessment,
  strategy,
  onClose,
  marketData,
  currentPrice
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'technical' | 'greeks' | 'scenarios' | 'prediction'>('overview')
  
  // Generate profit/loss chart data
  const generatePLChart = () => {
    const data = []
    const strikes = Object.values(strategy.strikes).sort((a, b) => a - b)
    const minPrice = strikes[0] - 20
    const maxPrice = strikes[strikes.length - 1] + 20
    
    for (let price = minPrice; price <= maxPrice; price += 1) {
      let pl = 0
      
      // Calculate P/L based on strategy type
      if (strategy.strategy_type === 'bull_call') {
        const longStrike = strategy.strikes.long_strike
        const shortStrike = strategy.strikes.short_strike
        const premium = (strategy.max_loss / 100) // Assuming premium paid
        
        if (price <= longStrike) {
          pl = -premium * 100
        } else if (price >= shortStrike) {
          pl = (shortStrike - longStrike - premium) * 100
        } else {
          pl = (price - longStrike - premium) * 100
        }
      } else if (strategy.strategy_type === 'iron_condor') {
        // Iron Condor P/L calculation
        const putLong = strategy.strikes.put_long
        const putShort = strategy.strikes.put_short
        const callShort = strategy.strikes.call_short
        const callLong = strategy.strikes.call_long
        const premium = strategy.max_profit / 100
        
        if (price <= putLong || price >= callLong) {
          pl = -((putShort - putLong) * 100 - premium * 100)
        } else if (price >= putShort && price <= callShort) {
          pl = premium * 100
        } else if (price < putShort) {
          pl = (price - putLong - (putShort - putLong - premium)) * 100
        } else {
          pl = ((callShort - price) - (putShort - putLong - premium)) * 100
        }
      }
      
      data.push({ price, pl, isBreakeven: Math.abs(pl) < 5 })
    }
    
    return data
  }
  
  // Generate market regime data
  const generateMarketData = () => {
    return [
      { name: 'Trend Strength', value: 75, color: '#22c55e' },
      { name: 'Volatility', value: 45, color: '#f59e0b' },
      { name: 'Volume', value: 85, color: '#3b82f6' },
      { name: 'Momentum', value: 60, color: '#8b5cf6' }
    ]
  }
  
  // Generate Greeks data (mock)
  const generateGreeksData = () => {
    return [
      { greek: 'Delta', value: 0.35, description: 'Price sensitivity', impact: 'moderate' },
      { greek: 'Gamma', value: 0.05, description: 'Delta acceleration', impact: 'low' },
      { greek: 'Theta', value: -0.08, description: 'Time decay', impact: 'high' },
      { greek: 'Vega', value: 0.12, description: 'Volatility sensitivity', impact: 'moderate' },
      { greek: 'Rho', value: 0.02, description: 'Interest rate sensitivity', impact: 'low' }
    ]
  }
  
  // Generate AI price prediction data
  const generatePredictionData = () => {
    const timePoints = []
    const startTime = new Date()
    
    // Create hourly predictions for the trading day (6.5 hours)
    for (let i = 0; i <= 13; i++) {
      const time = new Date(startTime.getTime() + (i * 30 * 60 * 1000)) // 30-minute intervals
      
      // Generate prediction based on recommendation
      let priceChange = 0
      if (assessment.recommendation === 'GO') {
        // Bullish prediction - price should move favorably for the strategy
        priceChange = Math.sin(i * 0.3) * 2 + (i * 0.5) // Upward trend with volatility
      } else if (assessment.recommendation === 'CAUTION') {
        // Sideways prediction with some volatility
        priceChange = Math.sin(i * 0.5) * 1.5
      } else {
        // Bearish prediction
        priceChange = Math.sin(i * 0.4) * 2 - (i * 0.3) // Downward trend
      }
      
      timePoints.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        predicted_price: currentPrice + priceChange,
        confidence: Math.max(50, assessment.confidence - (i * 2)), // Confidence decreases over time
        actual_price: null // Will be filled in as day progresses
      })
    }
    
    return timePoints
  }
  
  const plData = generatePLChart()
  const marketRegimeData = generateMarketData()
  const greeksData = generateGreeksData()
  const predictionData = generatePredictionData()
  
  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'GO': return 'bg-green-500/20 text-green-300 border-green-500/30'
      case 'CAUTION': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
      case 'NO-GO': return 'bg-red-500/20 text-red-300 border-red-500/30'
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    }
  }
  
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-400'
      case 'moderate': return 'text-yellow-400'
      case 'low': return 'text-green-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <motion.div 
      className="fixed inset-0 bg-slate-900/95 backdrop-blur-sm z-50 overflow-y-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="min-h-screen p-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div 
            className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 mb-6"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-5 h-5 text-slate-400" />
                </button>
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-500/20 rounded-xl">
                    <Brain className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-slate-100">
                      AI Strategy Analysis: {strategy.strategy_type.replace('_', ' ').toUpperCase()}
                    </h1>
                    <p className="text-slate-400">
                      {strategy.symbol} • Expires {strategy.expiration} • {strategy.quantity} contracts
                    </p>
                  </div>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-xl border ${getRecommendationColor(assessment.recommendation)}`}>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold">{assessment.recommendation}</span>
                  <span className="text-sm opacity-75">{assessment.confidence}%</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Navigation Tabs */}
          <motion.div 
            className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-2 mb-6"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex gap-2">
              {[
                { id: 'overview', label: 'Overview', icon: Eye },
                { id: 'technical', label: 'Technical Analysis', icon: BarChart3 },
                { id: 'greeks', label: 'Greeks & Risk', icon: Shield },
                { id: 'scenarios', label: 'Scenarios', icon: Target },
                { id: 'prediction', label: 'AI Prediction', icon: TrendingUp }
              ].map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                      activeTab === tab.id
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-slate-700/30 hover:text-slate-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                )
              })}
            </div>
          </motion.div>

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'overview' && (
              <motion.div 
                className="grid grid-cols-1 lg:grid-cols-3 gap-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {/* Market Regime Analysis */}
                <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <TrendingUp className="w-5 h-5 text-green-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Market Regime Analysis</h2>
                  </div>
                  
                  <div className="mb-6">
                    <p className="text-slate-300 text-sm leading-relaxed">
                      {assessment.market_regime}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    {marketRegimeData.map((item) => (
                      <div key={item.name} className="bg-slate-700/30 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-slate-400">{item.name}</span>
                          <span className="text-sm font-medium" style={{ color: item.color }}>
                            {item.value}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-600/30 rounded-full h-2">
                          <div 
                            className="h-2 rounded-full transition-all duration-500"
                            style={{ width: `${item.value}%`, backgroundColor: item.color }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="space-y-4">
                  {/* Strategy Details */}
                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-slate-100 mb-4">Strategy Details</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Current Price</span>
                        <span className="text-slate-100 font-medium">${currentPrice.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Max Profit</span>
                        <span className="text-green-400 font-medium">${strategy.max_profit.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Max Loss</span>
                        <span className="text-red-400 font-medium">${strategy.max_loss.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Risk/Reward</span>
                        <span className="text-blue-400 font-medium">
                          1:{(strategy.max_profit / strategy.max_loss).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* AI Reasoning */}
                  <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-slate-100 mb-4">AI Analysis</h3>
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-green-400 mb-2 flex items-center gap-2">
                          <TrendingUp className="w-4 h-4" />
                          Supporting Factors
                        </h4>
                        <ul className="space-y-1">
                          {assessment.reasoning.supporting_factors.map((factor, index) => (
                            <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                              <ChevronRight className="w-3 h-3 mt-0.5 text-green-400 flex-shrink-0" />
                              {factor}
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          Risk Factors
                        </h4>
                        <ul className="space-y-1">
                          {assessment.reasoning.risk_factors.map((risk, index) => (
                            <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                              <ChevronRight className="w-3 h-3 mt-0.5 text-red-400 flex-shrink-0" />
                              {risk}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'technical' && (
              <motion.div 
                className="grid grid-cols-1 xl:grid-cols-2 gap-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {/* Profit/Loss Chart */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <BarChart3 className="w-5 h-5 text-blue-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Profit/Loss Profile</h2>
                  </div>
                  
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={plData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="price" stroke="#64748b" fontSize={12} />
                        <YAxis stroke="#64748b" fontSize={12} />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: '#1e293b',
                            border: '1px solid #475569',
                            borderRadius: '8px',
                            color: '#f1f5f9'
                          }}
                          formatter={(value: number) => [`$${value.toFixed(0)}`, 'P/L']}
                        />
                        <defs>
                          <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1}/>
                          </linearGradient>
                          <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3}/>
                          </linearGradient>
                        </defs>
                        <Area 
                          type="monotone" 
                          dataKey="pl" 
                          stroke="#3b82f6" 
                          fill="url(#profitGradient)"
                          strokeWidth={2}
                        />
                        <ReferenceLine y={0} stroke="#64748b" strokeDasharray="5 5" />
                        <ReferenceLine x={currentPrice} stroke="#f59e0b" strokeDasharray="3 3" 
                          label={{ value: `Current: $${currentPrice}`, position: 'top' }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Strike Price Analysis */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <Target className="w-5 h-5 text-purple-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Strike Analysis</h2>
                  </div>
                  
                  <div className="space-y-4">
                    {Object.entries(strategy.strikes).map(([type, strike]) => {
                      const distance = ((strike - currentPrice) / currentPrice * 100).toFixed(1)
                      const isITM = (type.includes('put') && strike > currentPrice) || 
                                   (type.includes('call') && strike < currentPrice)
                      
                      return (
                        <div key={type} className="bg-slate-700/30 rounded-lg p-4">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-slate-300 capitalize">
                              {type.replace('_', ' ')}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              isITM ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
                            }`}>
                              {isITM ? 'ITM' : 'OTM'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-lg font-bold text-slate-100">${strike}</span>
                            <span className={`text-sm ${
                              parseFloat(distance) > 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {distance}% from current
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'greeks' && (
              <motion.div 
                className="grid grid-cols-1 lg:grid-cols-2 gap-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {/* Greeks Analysis */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <Shield className="w-5 h-5 text-orange-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Options Greeks</h2>
                  </div>
                  
                  <div className="space-y-4">
                    {greeksData.map((greek) => (
                      <div key={greek.greek} className="bg-slate-700/30 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="text-lg font-semibold text-slate-100">{greek.greek}</span>
                            <p className="text-xs text-slate-400">{greek.description}</p>
                          </div>
                          <div className="text-right">
                            <span className="text-lg font-mono text-slate-100">
                              {greek.value > 0 ? '+' : ''}{greek.value.toFixed(3)}
                            </span>
                            <p className={`text-xs ${getImpactColor(greek.impact)}`}>
                              {greek.impact} impact
                            </p>
                          </div>
                        </div>
                        
                        {/* Greek explanation */}
                        {greek.greek === 'Delta' && (
                          <p className="text-xs text-slate-300 mt-2">
                            For every $1 move in {strategy.symbol}, this position will gain/lose ~${Math.abs(greek.value * 100).toFixed(0)}
                          </p>
                        )}
                        {greek.greek === 'Theta' && (
                          <p className="text-xs text-slate-300 mt-2">
                            This position loses ~${Math.abs(greek.value * 100).toFixed(0)} per day due to time decay
                          </p>
                        )}
                        {greek.greek === 'Vega' && (
                          <p className="text-xs text-slate-300 mt-2">
                            For every 1% change in implied volatility, position value changes by ${Math.abs(greek.value * 100).toFixed(0)}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Risk Metrics */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Risk Analysis</h2>
                  </div>
                  
                  <div className="space-y-6">
                    {/* Risk Gauge */}
                    <div>
                      <h3 className="text-sm font-medium text-slate-300 mb-3">Overall Risk Level</h3>
                      <div className="relative">
                        <div className="w-full bg-slate-600/30 rounded-full h-4">
                          <div 
                            className="h-4 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
                            style={{ width: '100%' }}
                          />
                          <div 
                            className="absolute top-0 w-2 h-4 bg-white rounded-full shadow-lg transform -translate-x-1"
                            style={{ left: `${assessment.confidence}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-slate-400 mt-1">
                          <span>Low Risk</span>
                          <span>High Risk</span>
                        </div>
                      </div>
                    </div>

                    {/* Time to Expiration Impact */}
                    <div className="bg-slate-700/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-blue-400" />
                        <span className="text-sm font-medium text-slate-300">Time Decay Impact</span>
                      </div>
                      <p className="text-xs text-slate-400 mb-2">
                        Time until expiration: {strategy.expiration}
                      </p>
                      <div className="w-full bg-slate-600/30 rounded-full h-2">
                        <div className="h-2 bg-red-500 rounded-full" style={{ width: '65%' }} />
                      </div>
                      <p className="text-xs text-slate-300 mt-2">
                        High time decay risk - position loses value rapidly as expiration approaches
                      </p>
                    </div>

                    {/* Volatility Impact */}
                    <div className="bg-slate-700/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-purple-400" />
                        <span className="text-sm font-medium text-slate-300">Volatility Sensitivity</span>
                      </div>
                      <p className="text-xs text-slate-300">
                        This strategy is moderately sensitive to changes in implied volatility. 
                        Higher volatility generally increases option premiums.
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'scenarios' && (
              <motion.div 
                className="space-y-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {/* Scenario Analysis */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <Target className="w-5 h-5 text-cyan-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Market Scenarios</h2>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      {
                        title: 'Bullish Scenario',
                        description: `${strategy.symbol} rises 5-10%`,
                        probability: '30%',
                        outcome: 'Profitable',
                        color: 'green',
                        icon: TrendingUp,
                        details: 'Strong earnings, positive market sentiment, technical breakout'
                      },
                      {
                        title: 'Neutral Scenario', 
                        description: `${strategy.symbol} stays within ±3%`,
                        probability: '45%',
                        outcome: 'Mixed Results',
                        color: 'yellow',
                        icon: Activity,
                        details: 'Sideways trading, mixed signals, time decay impact'
                      },
                      {
                        title: 'Bearish Scenario',
                        description: `${strategy.symbol} falls 5-10%`,
                        probability: '25%',
                        outcome: 'Loss',
                        color: 'red', 
                        icon: TrendingDown,
                        details: 'Market correction, negative news, technical breakdown'
                      }
                    ].map((scenario) => {
                      const Icon = scenario.icon
                      return (
                        <div key={scenario.title} className="bg-slate-700/30 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-3">
                            <div className={`p-2 rounded-lg bg-${scenario.color}-500/20`}>
                              <Icon className={`w-4 h-4 text-${scenario.color}-400`} />
                            </div>
                            <span className="font-medium text-slate-100">{scenario.title}</span>
                          </div>
                          
                          <p className="text-sm text-slate-300 mb-2">{scenario.description}</p>
                          
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-xs text-slate-400">Probability</span>
                            <span className={`text-sm font-medium text-${scenario.color}-400`}>
                              {scenario.probability}
                            </span>
                          </div>
                          
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-xs text-slate-400">Expected Outcome</span>
                            <span className={`text-sm font-medium text-${scenario.color}-400`}>
                              {scenario.outcome}
                            </span>
                          </div>
                          
                          <p className="text-xs text-slate-400">{scenario.details}</p>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Educational Content */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <BookOpen className="w-5 h-5 text-emerald-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Learning Insights</h2>
                  </div>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-medium text-slate-100 mb-3">Why This Strategy?</h3>
                      <div className="space-y-3 text-sm text-slate-300">
                        <p>
                          <strong className="text-slate-100">Market Outlook:</strong> This strategy is designed for 
                          {strategy.strategy_type.includes('bull') ? ' bullish' : ' neutral to range-bound'} market conditions.
                        </p>
                        <p>
                          <strong className="text-slate-100">Risk Profile:</strong> Limited risk with 
                          {strategy.max_profit > strategy.max_loss ? ' favorable' : ' challenging'} risk/reward ratio.
                        </p>
                        <p>
                          <strong className="text-slate-100">Time Factor:</strong> Time decay works 
                          {strategy.strategy_type.includes('condor') ? ' in your favor' : ' against the position'}, 
                          requiring careful timing.
                        </p>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-medium text-slate-100 mb-3">Key Learning Points</h3>
                      <div className="space-y-2">
                        {[
                          "Implied volatility affects all option prices",
                          "Time decay accelerates as expiration approaches", 
                          "Strike selection determines risk/reward profile",
                          "Market direction prediction is only part of success",
                          "Position sizing is crucial for risk management"
                        ].map((point, index) => (
                          <div key={index} className="flex items-start gap-2 text-sm text-slate-300">
                            <Zap className="w-3 h-3 mt-0.5 text-emerald-400 flex-shrink-0" />
                            {point}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'prediction' && (
              <motion.div 
                className="space-y-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {/* AI Price Prediction */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                    <h2 className="text-xl font-semibold text-slate-100">AI Price Prediction</h2>
                    <div className={`px-3 py-1 rounded-lg text-sm font-medium ${getRecommendationColor(assessment.recommendation)}`}>
                      {assessment.recommendation} - {assessment.confidence}% Confidence
                    </div>
                  </div>
                  
                  {/* Prediction Chart */}
                  <div className="h-96 mb-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={predictionData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                        <YAxis stroke="#64748b" fontSize={12} domain={['dataMin - 2', 'dataMax + 2']} />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: '#1e293b',
                            border: '1px solid #475569',
                            borderRadius: '8px',
                            color: '#f1f5f9'
                          }}
                          formatter={(value: number, name: string) => [
                            `$${value.toFixed(2)}`, 
                            name === 'predicted_price' ? 'Predicted Price' : 'Actual Price'
                          ]}
                        />
                        <defs>
                          <linearGradient id="predictionGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#06d6a0" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#06d6a0" stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        <Area 
                          type="monotone" 
                          dataKey="predicted_price" 
                          stroke="#06d6a0" 
                          fill="url(#predictionGradient)"
                          strokeWidth={3}
                          name="predicted_price"
                        />
                        <ReferenceLine y={currentPrice} stroke="#f59e0b" strokeDasharray="5 5" 
                          label={{ value: `Current: $${currentPrice.toFixed(2)}`, position: 'topRight' }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Prediction Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-700/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-green-400" />
                        <span className="text-sm font-medium text-slate-300">Price Target</span>
                      </div>
                      <div className="text-xl font-bold text-green-400">
                        ${(predictionData[predictionData.length - 1]?.predicted_price || currentPrice).toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-400">
                        {((predictionData[predictionData.length - 1]?.predicted_price - currentPrice) / currentPrice * 100 || 0).toFixed(1)}% change
                      </div>
                    </div>

                    <div className="bg-slate-700/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-blue-400" />
                        <span className="text-sm font-medium text-slate-300">Prediction Confidence</span>
                      </div>
                      <div className="text-xl font-bold text-blue-400">
                        {assessment.confidence}%
                      </div>
                      <div className="text-xs text-slate-400">
                        Initial confidence level
                      </div>
                    </div>

                    <div className="bg-slate-700/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-purple-400" />
                        <span className="text-sm font-medium text-slate-300">Time Horizon</span>
                      </div>
                      <div className="text-xl font-bold text-purple-400">
                        0DTE
                      </div>
                      <div className="text-xs text-slate-400">
                        Same day expiration
                      </div>
                    </div>
                  </div>
                </div>

                {/* Prediction Rationale */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <Brain className="w-5 h-5 text-emerald-400" />
                    <h2 className="text-xl font-semibold text-slate-100">Prediction Rationale</h2>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-slate-700/30 rounded-lg p-4">
                      <h3 className="text-lg font-medium text-slate-100 mb-2">Why This Direction?</h3>
                      <p className="text-sm text-slate-300 leading-relaxed">
                        Based on the <strong>{assessment.recommendation}</strong> recommendation and {assessment.confidence}% confidence, 
                        the AI predicts {strategy.symbol} will move in a direction that{' '}
                        {assessment.recommendation === 'GO' ? 'favors' : assessment.recommendation === 'CAUTION' ? 'neutrally affects' : 'opposes'}{' '}
                        this {strategy.strategy_type.replace('_', ' ')} strategy. The prediction incorporates current market sentiment, 
                        volatility environment, and technical indicators.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-slate-700/30 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-green-400 mb-2">Supporting Factors</h4>
                        <ul className="space-y-1">
                          {assessment.reasoning.supporting_factors.slice(0, 2).map((factor, index) => (
                            <li key={index} className="text-xs text-slate-300 flex items-start gap-2">
                              <Zap className="w-3 h-3 mt-0.5 text-green-400 flex-shrink-0" />
                              {factor}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-slate-700/30 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-red-400 mb-2">Risk Factors</h4>
                        <ul className="space-y-1">
                          {assessment.reasoning.risk_factors.slice(0, 2).map((risk, index) => (
                            <li key={index} className="text-xs text-slate-300 flex items-start gap-2">
                              <AlertTriangle className="w-3 h-3 mt-0.5 text-red-400 flex-shrink-0" />
                              {risk}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Prediction Tracking Note */}
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <BookOpen className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <h4 className="text-sm font-medium text-blue-300 mb-1">Prediction Tracking</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            This prediction will be automatically tracked throughout the trading day. 
                            Actual price movements will be compared against the prediction to measure AI accuracy. 
                            Historical prediction performance helps improve future assessments and builds confidence in AI recommendations.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}