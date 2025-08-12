import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronDown, 
  ChevronUp, 
  Target, 
  TrendingUp, 
  Zap, 
  AlertTriangle,
  Activity,
  Play,
  BarChart3
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine,
  Area,
  AreaChart
} from 'recharts';
import { SpreadConfig, AnalysisData } from './generated/SPYSpreadStrategiesApp';
import { calculateDelta, findStrikeForDelta, DELTA_STRATEGIES } from '../utils/optionsCalculations';

export type StrategyType = 'bullCall' | 'ironCondor' | 'butterfly';

interface ConsolidatedStrategyCardProps {
  strategy: StrategyType;
  spreadConfig: SpreadConfig | null;
  analysisData: AnalysisData | null;
  currentPrice: number | null;
  contracts: number;
  selectedDate: Date;
  onUpdateConfig: (updates: Partial<SpreadConfig>) => void;
  onExecuteStrategy: (strategy: StrategyType) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  className?: string;
}

// Strategy metadata for display
const STRATEGY_META = {
  bullCall: {
    name: 'Bull Call Spread',
    description: 'Bullish directional play with limited risk/reward',
    icon: TrendingUp,
    color: 'blue',
    fields: ['bullCallLower', 'bullCallUpper'] as (keyof SpreadConfig)[]
  },
  ironCondor: {
    name: 'Iron Condor',
    description: 'Neutral strategy profiting from low volatility',
    icon: Target,
    color: 'purple',
    fields: ['ironCondorPutLong', 'ironCondorPutShort', 'ironCondorCallShort', 'ironCondorCallLong'] as (keyof SpreadConfig)[]
  },
  butterfly: {
    name: 'Butterfly Spread',
    description: 'Neutral strategy with high profit potential at body strike',
    icon: Activity,
    color: 'green',
    fields: ['butterflyLower', 'butterflyBody', 'butterflyUpper'] as (keyof SpreadConfig)[]
  }
};

// Format currency helper
const formatCurrency = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}$${Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })}`;
};

// Format price helper
const formatPrice = (value: number): string => {
  return `$${value.toFixed(0)}`;
};

// Generate P&L data for visualization
const generatePnLData = (strategy: StrategyType, config: SpreadConfig, currentPrice: number) => {
  const data = [];
  const priceRange = currentPrice * 0.15; // ±15% price range for better focus
  const step = priceRange / 100;
  
  for (let i = 0; i <= 200; i++) {
    const price = currentPrice - priceRange + (i * step);
    let pnl = 0;
    
    switch (strategy) {
      case 'bullCall':
        // Bull Call Spread P&L calculation
        const longCallPayoff = Math.max(0, price - config.bullCallLower) * 100;
        const shortCallPayoff = Math.max(0, price - config.bullCallUpper) * 100;
        const netDebit = (config.bullCallUpper - config.bullCallLower) * 0.4 * 100; // Assume 40% of spread width as debit
        pnl = longCallPayoff - shortCallPayoff - netDebit;
        break;
        
      case 'ironCondor':
        // Iron Condor P&L calculation
        const shortPutPayoff = Math.max(0, config.ironCondorPutShort - price) * 100;
        const longPutPayoff = Math.max(0, config.ironCondorPutLong - price) * 100;
        const shortCallPayoff2 = Math.max(0, price - config.ironCondorCallShort) * 100;
        const longCallPayoff2 = Math.max(0, price - config.ironCondorCallLong) * 100;
        const netCredit = Math.min(
          config.ironCondorPutShort - config.ironCondorPutLong,
          config.ironCondorCallLong - config.ironCondorCallShort
        ) * 0.3 * 100; // Assume 30% of spread width as credit
        pnl = netCredit - shortPutPayoff + longPutPayoff - shortCallPayoff2 + longCallPayoff2;
        break;
        
      case 'butterfly':
        // Butterfly Spread P&L calculation
        const longLowerPayoff = Math.max(0, price - config.butterflyLower) * 100;
        const shortBodyPayoff = Math.max(0, price - config.butterflyBody) * 100 * 2; // Short 2 contracts
        const longUpperPayoff = Math.max(0, price - config.butterflyUpper) * 100;
        const butterflyDebit = (config.butterflyBody - config.butterflyLower) * 0.25 * 100; // Assume 25% of wing width as debit
        pnl = longLowerPayoff - shortBodyPayoff + longUpperPayoff - butterflyDebit;
        break;
    }
    
    data.push({
      price: Math.round(price),
      pnl: Math.round(pnl),
      isProfitable: pnl > 0
    });
  }
  
  return data;
};

// Custom tooltip for P&L chart
const PnLTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-lg">
        <p className="text-slate-100 text-sm font-medium mb-1">
          Price: {formatPrice(data.price)}
        </p>
        <p className="text-sm">
          <span className="text-slate-400">P&L: </span>
          <span className={`font-medium ${
            data.pnl >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {formatCurrency(data.pnl)}
          </span>
        </p>
      </div>
    );
  }
  return null;
};

export const ConsolidatedStrategyCard: React.FC<ConsolidatedStrategyCardProps> = ({
  strategy,
  spreadConfig,
  analysisData,
  currentPrice,
  contracts,
  selectedDate,
  onUpdateConfig,
  onExecuteStrategy,
  onAnalyze,
  isAnalyzing,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const meta = STRATEGY_META[strategy];
  const IconComponent = meta.icon;
  
  // Get analysis data for this strategy
  const strategyAnalysis = analysisData?.[strategy];
  
  // Generate P&L chart data
  const chartData = useMemo(() => {
    if (!spreadConfig || !currentPrice) return [];
    return generatePnLData(strategy, spreadConfig, currentPrice);
  }, [strategy, spreadConfig, currentPrice]);
  
  // Calculate time to expiration for delta calculations
  const timeToExpiration = 0.001; // Assume 0DTE for now
  
  // Apply delta preset with proper differentiation
  const applyDeltaPreset = (preset: typeof DELTA_STRATEGIES[0]) => {
    if (!currentPrice || !preset.putDelta || !preset.callDelta) return;
    
    // Use longer expiration for better delta calculations when not 0DTE
    const deltaTimeToExpiration = timeToExpiration < 0.01 ? 0.04 : timeToExpiration; // Use 2 weeks minimum for delta calc
    
    const putStrike = findStrikeForDelta(currentPrice, preset.putDelta, deltaTimeToExpiration, 0.05, 0.20, false);
    const callStrike = findStrikeForDelta(currentPrice, preset.callDelta, deltaTimeToExpiration, 0.05, 0.20, true);
    const atmStrike = Math.round(currentPrice / 5) * 5;
    
    const updates: Partial<SpreadConfig> = {};
    
    switch (strategy) {
      case 'bullCall':
        updates.bullCallLower = atmStrike;
        updates.bullCallUpper = callStrike;
        break;
      case 'ironCondor':
        // Use proper spread widths based on delta
        const spreadWidth = Math.abs(preset.callDelta) > 0.3 ? 15 : 10; // Wider spreads for aggressive
        updates.ironCondorPutShort = putStrike;
        updates.ironCondorPutLong = putStrike - spreadWidth;
        updates.ironCondorCallShort = callStrike;
        updates.ironCondorCallLong = callStrike + spreadWidth;
        break;
      case 'butterfly':
        updates.butterflyLower = putStrike;
        updates.butterflyBody = atmStrike;
        updates.butterflyUpper = callStrike;
        break;
    }
    
    onUpdateConfig(updates);
  };
  
  // Update individual strike
  const updateStrike = (field: keyof SpreadConfig, value: number) => {
    onUpdateConfig({ [field]: value });
  };
  
  return (
    <motion.div 
      className={`bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Card Header - Always Visible */}
      <div 
        className="p-6 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${
              meta.color === 'blue' ? 'bg-blue-500/20' :
              meta.color === 'purple' ? 'bg-purple-500/20' :
              'bg-green-500/20'
            }`}>
              <IconComponent className={`w-6 h-6 ${
                meta.color === 'blue' ? 'text-blue-400' :
                meta.color === 'purple' ? 'text-purple-400' :
                'text-green-400'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-100">{meta.name}</h3>
              <p className="text-sm text-slate-400">{meta.description}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Quick Stats */}
            {strategyAnalysis && (
              <div className="flex items-center gap-6 text-sm">
                <div className="text-center">
                  <div className="text-green-400 font-semibold">
                    {formatCurrency(strategyAnalysis.maxProfit)}
                  </div>
                  <div className="text-slate-500 text-xs">Max Profit</div>
                </div>
                <div className="text-center">
                  <div className="text-red-400 font-semibold">
                    {formatCurrency(strategyAnalysis.maxLoss)}
                  </div>
                  <div className="text-slate-500 text-xs">Max Loss</div>
                </div>
              </div>
            )}
            
            {/* Expand/Collapse Button */}
            <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-slate-700/50"
          >
            <div className="p-6 space-y-6">
              
              {/* Delta Presets */}
              <div>
                <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Delta Presets
                </h4>
                <div className="flex flex-wrap gap-2">
                  {DELTA_STRATEGIES.map((preset) => (
                    <button
                      key={preset.name}
                      onClick={() => applyDeltaPreset(preset)}
                      className="px-3 py-2 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 text-xs rounded-lg transition-colors border border-slate-600/50"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Strike Configuration */}
              {spreadConfig && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Strike Configuration
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    {meta.fields.map((field) => (
                      <div key={field}>
                        <label className="block text-xs text-slate-400 mb-1 capitalize">
                          {field.replace(/([A-Z])/g, ' $1').toLowerCase()}
                        </label>
                        <input
                          type="number"
                          value={spreadConfig[field]}
                          onChange={(e) => updateStrike(field, parseFloat(e.target.value) || 0)}
                          step="5"
                          className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* P&L Chart */}
              {chartData.length > 0 && currentPrice && spreadConfig && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4" />
                    {getChartTitle(strategy, spreadConfig, currentPrice)}
                  </h4>
                  {/* Chart Info */}
                  <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    {getChartInfo(strategy, spreadConfig, currentPrice).map((info, index) => (
                      <div key={index} className="bg-slate-700/30 rounded-lg p-2 text-center">
                        <div className="text-slate-400 uppercase tracking-wider">{info.label}</div>
                        <div className="text-slate-100 font-medium">{info.value}</div>
                      </div>
                    ))}
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <defs>
                          <linearGradient id={`profitGradient-${strategy}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                          </linearGradient>
                          <linearGradient id={`lossGradient-${strategy}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3}/>
                          </linearGradient>
                        </defs>
                        
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                        <XAxis 
                          dataKey="price" 
                          stroke="#9ca3af" 
                          fontSize={12}
                          tickFormatter={formatPrice}
                        />
                        <YAxis 
                          stroke="#9ca3af" 
                          fontSize={12}
                          tickFormatter={formatCurrency}
                        />
                        <Tooltip content={<PnLTooltip />} />
                        
                        {/* Zero P&L line */}
                        <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
                        
                        {/* Current price line with enhanced label */}
                        <ReferenceLine 
                          x={Math.round(currentPrice)} 
                          stroke="#3b82f6" 
                          strokeWidth={2}
                          label={{ 
                            value: `Today ~$${currentPrice.toFixed(2)}`, 
                            position: "top",
                            fill: "#3b82f6",
                            fontSize: 12,
                            fontWeight: "medium"
                          }}
                        />
                        
                        {/* Strike level indicators */}
                        {getStrikeLines(strategy, spreadConfig).map((strike, index) => (
                          <ReferenceLine
                            key={`strike-${index}`}
                            x={strike.value}
                            stroke={strike.color}
                            strokeDasharray="3 3"
                            strokeWidth={1}
                            label={{
                              value: strike.label,
                              position: "bottom",
                              fill: strike.color,
                              fontSize: 10
                            }}
                          />
                        ))}
                        
                        {/* Profit area (above zero) */}
                        <Area
                          type="monotone"
                          dataKey={(entry: any) => Math.max(0, entry.pnl)}
                          stroke="#10b981"
                          strokeWidth={2}
                          fill={`url(#profitGradient-${strategy})`}
                        />
                        
                        {/* Loss area (below zero) */}
                        <Area
                          type="monotone"
                          dataKey={(entry: any) => Math.min(0, entry.pnl)}
                          stroke="#ef4444"
                          strokeWidth={2}
                          fill={`url(#lossGradient-${strategy})`}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
              
              {/* Analysis Results */}
              {strategyAnalysis && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Analysis Results
                  </h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-slate-900/50 rounded-lg">
                      <div className="text-green-400 font-bold text-lg">
                        {formatCurrency(strategyAnalysis.maxProfit)}
                      </div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Max Profit</div>
                    </div>
                    <div className="text-center p-3 bg-slate-900/50 rounded-lg">
                      <div className="text-red-400 font-bold text-lg">
                        {formatCurrency(strategyAnalysis.maxLoss)}
                      </div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Max Loss</div>
                    </div>
                    <div className="text-center p-3 bg-slate-900/50 rounded-lg">
                      <div className="text-slate-100 font-bold text-lg">
                        {'breakeven' in strategyAnalysis 
                          ? formatPrice((strategyAnalysis as any).breakeven)
                          : 'breakeven1' in strategyAnalysis 
                            ? `${formatPrice((strategyAnalysis as any).breakeven1)} / ${formatPrice((strategyAnalysis as any).breakeven2)}`
                            : `${formatPrice((strategyAnalysis as any).lowerBreakeven)} / ${formatPrice((strategyAnalysis as any).upperBreakeven)}`
                        }
                      </div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Breakeven</div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-slate-700/50">
                <button
                  onClick={onAnalyze}
                  disabled={isAnalyzing}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800/50 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  {isAnalyzing ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <BarChart3 className="w-4 h-4" />
                  )}
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Strategy'}
                </button>
                
                <button
                  onClick={() => onExecuteStrategy(strategy)}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Execute
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};