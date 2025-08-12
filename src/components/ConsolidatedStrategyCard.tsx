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
  ComposedChart, 
  Line, 
  Area,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine
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

// Helper to interpolate between two points for smooth lines
const interpolatePoints = (x1: number, y1: number, x2: number, y2: number, steps: number = 100) => {
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    points.push({
      price: x1 + (x2 - x1) * t,  // Don't round - keep smooth
      pnl: y1 + (y2 - y1) * t      // Don't round - keep smooth
    });
  }
  return points;
};

// Generate P&L data for visualization - interpolated for smooth tooltips
const generatePnLData = (strategy: StrategyType, config: SpreadConfig, currentPrice: number) => {
  const data = [];
  
  switch (strategy) {
    case 'bullCall':
      // Bull Call Spread
      const bullCallDebit = (config.bullCallUpper - config.bullCallLower) * 0.4 * 100;
      const bullCallMaxProfit = (config.bullCallUpper - config.bullCallLower) * 100 - bullCallDebit;
      
      // Interpolate between key points for smooth tooltip
      data.push(...interpolatePoints(config.bullCallLower - 15, -bullCallDebit, config.bullCallLower, -bullCallDebit, 100));
      data.push(...interpolatePoints(config.bullCallLower, -bullCallDebit, config.bullCallUpper, bullCallMaxProfit, 200));
      data.push(...interpolatePoints(config.bullCallUpper, bullCallMaxProfit, config.bullCallUpper + 15, bullCallMaxProfit, 100));
      break;
      
    case 'ironCondor':
      // Iron Condor 
      const ironCondorCredit = Math.min(
        config.ironCondorPutShort - config.ironCondorPutLong,
        config.ironCondorCallLong - config.ironCondorCallShort
      ) * 0.3 * 100;
      const ironCondorMaxLoss = -((config.ironCondorPutShort - config.ironCondorPutLong) * 100 - ironCondorCredit);
      
      data.push(...interpolatePoints(config.ironCondorPutLong - 10, ironCondorMaxLoss, config.ironCondorPutLong, ironCondorMaxLoss, 50));
      data.push(...interpolatePoints(config.ironCondorPutLong, ironCondorMaxLoss, config.ironCondorPutShort, ironCondorCredit, 100));
      data.push(...interpolatePoints(config.ironCondorPutShort, ironCondorCredit, config.ironCondorCallShort, ironCondorCredit, 100));
      data.push(...interpolatePoints(config.ironCondorCallShort, ironCondorCredit, config.ironCondorCallLong, ironCondorMaxLoss, 100));
      data.push(...interpolatePoints(config.ironCondorCallLong, ironCondorMaxLoss, config.ironCondorCallLong + 10, ironCondorMaxLoss, 50));
      break;
      
    case 'butterfly':
      // Butterfly
      const butterflyDebit = (config.butterflyBody - config.butterflyLower) * 0.25 * 100;
      const butterflyMaxProfit = (config.butterflyBody - config.butterflyLower) * 100 - butterflyDebit;
      
      data.push(...interpolatePoints(config.butterflyLower - 5, -butterflyDebit, config.butterflyLower, -butterflyDebit, 50));
      data.push(...interpolatePoints(config.butterflyLower, -butterflyDebit, config.butterflyBody, butterflyMaxProfit, 100));
      data.push(...interpolatePoints(config.butterflyBody, butterflyMaxProfit, config.butterflyUpper, -butterflyDebit, 100));
      data.push(...interpolatePoints(config.butterflyUpper, -butterflyDebit, config.butterflyUpper + 5, -butterflyDebit, 50));
      break;
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

// Get chart title with strike configuration
const getChartTitle = (strategy: StrategyType, config: SpreadConfig, currentPrice: number): string => {
  switch (strategy) {
    case 'bullCall':
      return `Bull Call Spread (${config.bullCallLower}/${config.bullCallUpper})`;
    case 'ironCondor':
      return `Iron Condor (${config.ironCondorPutLong}/${config.ironCondorPutShort}/${config.ironCondorCallShort}/${config.ironCondorCallLong})`;
    case 'butterfly':
      return `Butterfly Spread (${config.butterflyLower}/${config.butterflyBody}/${config.butterflyUpper})`;
    default:
      return 'Profit & Loss Chart';
  }
};

// Get chart information panels
const getChartInfo = (strategy: StrategyType, config: SpreadConfig, currentPrice: number) => {
  const info = [];
  
  switch (strategy) {
    case 'bullCall':
      const bullCallSpreadWidth = config.bullCallUpper - config.bullCallLower;
      const bullCallNetDebit = Math.round(bullCallSpreadWidth * 0.4 * 100);
      info.push(
        { label: 'Long Call', value: `$${config.bullCallLower}` },
        { label: 'Short Call', value: `$${config.bullCallUpper}` },
        { label: 'Width', value: `$${bullCallSpreadWidth}` },
        { label: 'Est. Debit', value: `$${bullCallNetDebit}` }
      );
      break;
      
    case 'ironCondor':
      const netCredit = Math.round(Math.min(
        config.ironCondorPutShort - config.ironCondorPutLong,
        config.ironCondorCallLong - config.ironCondorCallShort
      ) * 0.3 * 100);
      info.push(
        { label: 'Put Spread', value: `$${config.ironCondorPutLong}/$${config.ironCondorPutShort}` },
        { label: 'Call Spread', value: `$${config.ironCondorCallShort}/$${config.ironCondorCallLong}` },
        { label: 'Profit Zone', value: `$${config.ironCondorPutShort}-$${config.ironCondorCallShort}` },
        { label: 'Est. Credit', value: `$${netCredit}` }
      );
      break;
      
    case 'butterfly':
      const wingWidth = config.butterflyBody - config.butterflyLower;
      const butterflyDebit = Math.round(wingWidth * 0.25 * 100);
      info.push(
        { label: 'Lower Wing', value: `$${config.butterflyLower}` },
        { label: 'Body (2x)', value: `$${config.butterflyBody}` },
        { label: 'Upper Wing', value: `$${config.butterflyUpper}` },
        { label: 'Est. Debit', value: `$${butterflyDebit}` }
      );
      break;
  }
  
  return info;
};

// Get strike lines for chart with optimized labels
const getStrikeLines = (strategy: StrategyType, config: SpreadConfig) => {
  const strikes = [];
  
  switch (strategy) {
    case 'bullCall':
      // Shorter labels for close strikes
      strikes.push(
        { value: config.bullCallLower, label: 'Long', color: '#10b981' },
        { value: config.bullCallUpper, label: 'Short', color: '#ef4444' }
      );
      break;
      
    case 'ironCondor':
      strikes.push(
        { value: config.ironCondorPutLong, label: 'LP', color: '#8b5cf6' },
        { value: config.ironCondorPutShort, label: 'SP', color: '#ef4444' },
        { value: config.ironCondorCallShort, label: 'SC', color: '#ef4444' },
        { value: config.ironCondorCallLong, label: 'LC', color: '#8b5cf6' }
      );
      break;
      
    case 'butterfly':
      // Shorter labels for close strikes
      strikes.push(
        { value: config.butterflyLower, label: 'Lower', color: '#10b981' },
        { value: config.butterflyBody, label: 'Body', color: '#ef4444' },
        { value: config.butterflyUpper, label: 'Upper', color: '#10b981' }
      );
      break;
  }
  
  return strikes;
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
    
    // Always use meaningful time to expiration for delta calculations (minimum 2 weeks)
    const deltaTimeToExpiration = Math.max(0.04, timeToExpiration); // 2 weeks minimum
    
    const putStrike = findStrikeForDelta(currentPrice, preset.putDelta, deltaTimeToExpiration, 0.05, 0.20, false);
    const callStrike = findStrikeForDelta(currentPrice, preset.callDelta, deltaTimeToExpiration, 0.05, 0.20, true);
    const atmStrike = Math.round(currentPrice / 5) * 5;
    
    const updates: Partial<SpreadConfig> = {};
    
    switch (strategy) {
      case 'bullCall':
        // For bull call, use ATM as long and the call strike as short
        updates.bullCallLower = atmStrike;
        updates.bullCallUpper = callStrike;
        break;
      case 'ironCondor':
        // Use different spread widths based on aggressiveness - more differentiation
        const isAggressive = Math.abs(preset.callDelta) >= 0.35;
        const isConservative = Math.abs(preset.callDelta) <= 0.16;
        let spreadWidth: number;
        
        if (isConservative) {
          spreadWidth = 10; // Narrow spreads for conservative (16-delta)
        } else if (isAggressive) {
          spreadWidth = 20; // Wide spreads for aggressive (35-delta)
        } else {
          spreadWidth = 15; // Medium spreads for moderate (25-delta)
        }
        
        updates.ironCondorPutShort = putStrike;
        updates.ironCondorPutLong = putStrike - spreadWidth;
        updates.ironCondorCallShort = callStrike;
        updates.ironCondorCallLong = callStrike + spreadWidth;
        break;
      case 'butterfly':
        // For butterfly, use put/call strikes as wings and ATM as body
        const wingWidth = Math.abs(callStrike - atmStrike); // Distance from ATM to call strike
        updates.butterflyLower = atmStrike - wingWidth;
        updates.butterflyBody = atmStrike;
        updates.butterflyUpper = atmStrike + wingWidth;
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
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                      <BarChart3 className="w-4 h-4" />
                      {getChartTitle(strategy, spreadConfig, currentPrice)}
                    </h4>
                  </div>
                  {/* Chart Info */}
                  <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    {getChartInfo(strategy, spreadConfig, currentPrice).map((info, index) => (
                      <div key={index} className="bg-slate-700/30 rounded-lg p-2 text-center">
                        <div className="text-slate-400 uppercase tracking-wider">{info.label}</div>
                        <div className="text-slate-100 font-medium">{info.value}</div>
                      </div>
                    ))}
                  </div>
                  <div className="bg-slate-900/50 rounded-lg h-96">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartData} margin={{ top: 15, right: 5, left: 5, bottom: 20 }}>
                        <defs>
                          <linearGradient id={`profitGradient-${strategy}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity={0.6}/>
                            <stop offset="100%" stopColor="#10b981" stopOpacity={0.3}/>
                          </linearGradient>
                          <linearGradient id={`lossGradient-${strategy}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3}/>
                            <stop offset="100%" stopColor="#ef4444" stopOpacity={0.6}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                        <XAxis 
                          dataKey="price" 
                          stroke="#9ca3af" 
                          fontSize={9}
                          tick={{ fontSize: 9 }}
                          tickFormatter={(value) => `${value}`}
                          domain={['dataMin', 'dataMax']}
                          type="number"
                        />
                        <YAxis 
                          stroke="#9ca3af" 
                          fontSize={9}
                          tick={{ fontSize: 9 }}
                          tickFormatter={(value) => value >= 0 ? `+${value}` : `${value}`}
                          width={40}
                        />
                        <Tooltip content={<PnLTooltip />} />
                        
                        {/* Zero P&L line */}
                        <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" strokeWidth={1} />
                        
                        {/* Current price line */}
                        <ReferenceLine 
                          x={Math.round(currentPrice)} 
                          stroke="#60a5fa" 
                          strokeWidth={1}
                          strokeDasharray="5 2"
                          label={{ 
                            value: `Now $${Math.round(currentPrice)}`, 
                            position: "top",
                            offset: 5,
                            fill: "#60a5fa",
                            fontSize: 12
                          }}
                        />
                        
                        {/* Strike level indicators */}
                        {getStrikeLines(strategy, spreadConfig).map((strike, index) => {
                          const currentStrike = Math.round(strike.value / 5) * 5;
                          
                          return (
                            <ReferenceLine
                              key={`strike-${index}`}
                              x={currentStrike}
                              stroke={strike.color}
                              strokeDasharray="3 3"
                              strokeWidth={1}
                              opacity={0.5}
                            />
                          );
                        })}
                        
                        {/* Profit area (above zero) */}
                        <Area
                          type="linear"
                          dataKey={(entry: any) => Math.max(0, entry.pnl)}
                          stroke="none"
                          fill={`url(#profitGradient-${strategy})`}
                        />
                        
                        {/* Loss area (below zero) */}
                        <Area
                          type="linear"
                          dataKey={(entry: any) => Math.min(0, entry.pnl)}
                          stroke="none"
                          fill={`url(#lossGradient-${strategy})`}
                        />
                        
                        {/* P&L Line - straight lines, no curves */}
                        <Line
                          type="linear"
                          dataKey="pnl"
                          stroke="#60a5fa"
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4 }}
                        />
                      </ComposedChart>
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