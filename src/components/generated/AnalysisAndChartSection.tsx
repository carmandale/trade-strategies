import React from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp, Target, Zap, BookOpen, Trash2, Plus, DollarSign, Percent, BarChart3 } from 'lucide-react';
import { AnalysisData, SpreadConfig, Trade } from './SPYSpreadStrategiesApp';
interface AnalysisAndChartSectionProps {
  analysisData: AnalysisData | null;
  chartData: {
    time: string;
    price: number;
    volume: number;
  }[];
  spreadConfig: SpreadConfig;
  trades: Trade[];
  onLogTrade: (strategy: string, pnl: number) => void;
  onDeleteTrade: (tradeId: string) => void;
  isAnalyzing: boolean;
}
const AnalysisAndChartSection: React.FC<AnalysisAndChartSectionProps> = ({
  analysisData,
  chartData,
  spreadConfig,
  trades,
  onLogTrade,
  onDeleteTrade,
  isAnalyzing
}) => {
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };
  const formatPercentage = (value: number): string => {
    return `${value.toFixed(2)}%`;
  };
  const getTotalPnL = (): number => {
    return trades.reduce((sum, trade) => sum + trade.pnl, 0);
  };
  const getWinRate = (): number => {
    if (trades.length === 0) return 0;
    const wins = trades.filter(trade => trade.pnl > 0).length;
    return wins / trades.length * 100;
  };
  const StrategyCard: React.FC<{
    title: string;
    icon: React.ReactNode;
    data?: {
      maxProfit: number;
      maxLoss: number;
      breakeven?: number;
      upperBreakeven?: number;
      lowerBreakeven?: number;
      breakeven1?: number;
      breakeven2?: number;
      riskReward: number;
    };
    color: string;
    strategy: string;
  }> = ({
    title,
    icon,
    data,
    color,
    strategy
  }) => <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
    scale: 1.02
  }} transition={{
    duration: 0.2
  }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 ${color} rounded-lg`}>
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">{title}</h3>
            <p className="text-xs text-slate-400">Risk/Reward Analysis</p>
          </div>
        </div>
        {analysisData && data && <motion.button onClick={() => onLogTrade(strategy, data.maxProfit * 0.6)} className="p-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg transition-colors duration-200" whileHover={{
        scale: 1.1
      }} whileTap={{
        scale: 0.9
      }}>
            <Plus className="w-4 h-4 text-blue-400" />
          </motion.button>}
      </div>

      {isAnalyzing ? <div className="space-y-3">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-4 bg-slate-700/50 rounded animate-pulse" />)}
        </div> : analysisData && data ? <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-700/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <DollarSign className="w-3 h-3 text-green-400" />
                <span className="text-xs text-slate-400">Max Profit</span>
              </div>
              <div className="text-sm font-semibold text-green-400">
                {formatCurrency(data.maxProfit)}
              </div>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <DollarSign className="w-3 h-3 text-red-400" />
                <span className="text-xs text-slate-400">Max Loss</span>
              </div>
              <div className="text-sm font-semibold text-red-400">
                {formatCurrency(data.maxLoss)}
              </div>
            </div>
          </div>

          <div className="bg-slate-700/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Percent className="w-3 h-3 text-blue-400" />
              <span className="text-xs text-slate-400">Risk/Reward Ratio</span>
            </div>
            <div className="text-sm font-semibold text-blue-400">
              1:{data.riskReward.toFixed(2)}
            </div>
          </div>

          {data.breakeven !== undefined && <div className="bg-slate-700/30 rounded-lg p-3">
              <div className="text-xs text-slate-400 mb-1">Breakeven</div>
              <div className="text-sm font-semibold text-slate-100">
                ${data.breakeven.toFixed(2)}
              </div>
            </div>}

          {data.upperBreakeven !== undefined && data.lowerBreakeven !== undefined && <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-700/30 rounded-lg p-2">
                <div className="text-xs text-slate-400">Lower BE</div>
                <div className="text-xs font-semibold text-slate-100">
                  ${data.lowerBreakeven.toFixed(2)}
                </div>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-2">
                <div className="text-xs text-slate-400">Upper BE</div>
                <div className="text-xs font-semibold text-slate-100">
                  ${data.upperBreakeven.toFixed(2)}
                </div>
              </div>
            </div>}

          {data.breakeven1 !== undefined && data.breakeven2 !== undefined && <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-700/30 rounded-lg p-2">
                <div className="text-xs text-slate-400">BE 1</div>
                <div className="text-xs font-semibold text-slate-100">
                  ${data.breakeven1.toFixed(2)}
                </div>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-2">
                <div className="text-xs text-slate-400">BE 2</div>
                <div className="text-xs font-semibold text-slate-100">
                  ${data.breakeven2.toFixed(2)}
                </div>
              </div>
            </div>}
        </div> : <div className="text-center py-8 text-slate-400">
          <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Run analysis to see results</p>
        </div>}
    </motion.div>;
  return <div className="space-y-6">
      {/* Strategy Analysis Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <StrategyCard title="Bull Call" icon={<TrendingUp className="w-5 h-5 text-green-400" />} data={analysisData?.bullCall} color="bg-green-500/20" strategy="Bull Call" />
        <StrategyCard title="Iron Condor" icon={<Target className="w-5 h-5 text-purple-400" />} data={analysisData?.ironCondor} color="bg-purple-500/20" strategy="Iron Condor" />
        <StrategyCard title="Butterfly" icon={<Zap className="w-5 h-5 text-yellow-400" />} data={analysisData?.butterfly} color="bg-yellow-500/20" strategy="Butterfly" />
      </div>

      {/* Basic Strategy Display (Issue #6) */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-indigo-500/20 rounded-lg">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Strategy Portfolio</h3>
            <p className="text-xs text-slate-400">Analyzed strategies ready for execution</p>
          </div>
        </div>
        {analysisData ? (
          <div className="space-y-3">
            {/* Bull Call Strategy */}
            <div className="bg-slate-700/30 rounded-lg p-3 hover:bg-slate-700/50 transition-colors">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-green-400">Bull Call Spread</div>
                  <div className="text-xs text-slate-400">
                    {spreadConfig.bullCallLower}/{spreadConfig.bullCallUpper} • Max P: ${analysisData.bullCall.maxProfit.toFixed(0)}
                  </div>
                </div>
                <button
                  onClick={() => onLogTrade('Bull Call', analysisData.bullCall.maxProfit)}
                  className="px-3 py-1 bg-green-500/20 text-green-400 rounded-lg text-xs hover:bg-green-500/30 transition-colors"
                >
                  Execute
                </button>
              </div>
            </div>
            
            {/* Iron Condor Strategy */}
            <div className="bg-slate-700/30 rounded-lg p-3 hover:bg-slate-700/50 transition-colors">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-purple-400">Iron Condor</div>
                  <div className="text-xs text-slate-400">
                    {spreadConfig.ironCondorPutLong}/{spreadConfig.ironCondorPutShort}-{spreadConfig.ironCondorCallShort}/{spreadConfig.ironCondorCallLong} • Max P: ${analysisData.ironCondor.maxProfit.toFixed(0)}
                  </div>
                </div>
                <button
                  onClick={() => onLogTrade('Iron Condor', analysisData.ironCondor.maxProfit)}
                  className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-lg text-xs hover:bg-purple-500/30 transition-colors"
                >
                  Execute
                </button>
              </div>
            </div>
            
            {/* Butterfly Strategy */}
            <div className="bg-slate-700/30 rounded-lg p-3 hover:bg-slate-700/50 transition-colors">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-yellow-400">Butterfly Spread</div>
                  <div className="text-xs text-slate-400">
                    {spreadConfig.butterflyLower}/{spreadConfig.butterflyBody}/{spreadConfig.butterflyUpper} • Max P: ${analysisData.butterfly.maxProfit.toFixed(0)}
                  </div>
                </div>
                <button
                  onClick={() => onLogTrade('Butterfly', analysisData.butterfly.maxProfit)}
                  className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-lg text-xs hover:bg-yellow-500/30 transition-colors"
                >
                  Execute
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8">
            <TrendingUp className="w-8 h-8 text-slate-500 mb-2" />
            <p className="text-sm text-slate-400">No strategies analyzed yet</p>
            <p className="text-xs text-slate-500 mt-1">Click "Analyze Strategies" to populate</p>
          </div>
        )}
      </div>

      {/* Price Chart */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" initial={{
      opacity: 0,
      y: 20
    }} animate={{
      opacity: 1,
      y: 0
    }} transition={{
      duration: 0.6
    }}>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <BarChart3 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">SPY Price Chart</h3>
            <p className="text-xs text-slate-400">Real-time price action with strike levels</p>
          </div>
        </div>

        <div className="h-80" data-testid="equity-curve-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickFormatter={value => new Date(value).toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit'
            })} />
              <YAxis stroke="#64748b" fontSize={12} domain={['dataMin - 5', 'dataMax + 5']} />
              <Tooltip contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
              color: '#f1f5f9'
            }} labelFormatter={value => new Date(value).toLocaleString()} formatter={(value: number) => [`$${value.toFixed(2)}`, 'SPY Price']} />
              <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} />
              
              {/* Strike Price Reference Lines */}
              <ReferenceLine y={spreadConfig.bullCallLower} stroke="#22c55e" strokeDasharray="5 5" label={{
              value: `Bull Call Lower: $${spreadConfig.bullCallLower}`
            }} />
              <ReferenceLine y={spreadConfig.bullCallUpper} stroke="#22c55e" strokeDasharray="5 5" label={{
              value: `Bull Call Upper: $${spreadConfig.bullCallUpper}`
            }} />
              <ReferenceLine y={spreadConfig.ironCondorPutShort} stroke="#a855f7" strokeDasharray="3 3" label={{
              value: `IC Put Short: $${spreadConfig.ironCondorPutShort}`
            }} />
              <ReferenceLine y={spreadConfig.ironCondorCallShort} stroke="#a855f7" strokeDasharray="3 3" label={{
              value: `IC Call Short: $${spreadConfig.ironCondorCallShort}`
            }} />
              <ReferenceLine y={spreadConfig.butterflyBody} stroke="#eab308" strokeDasharray="2 2" label={{
              value: `Butterfly Body: $${spreadConfig.butterflyBody}`
            }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Trade Log */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" initial={{
      opacity: 0,
      y: 20
    }} animate={{
      opacity: 1,
      y: 0
    }} transition={{
      duration: 0.6,
      delay: 0.2
    }}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <BookOpen className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-100">Trade Log</h3>
              <p className="text-xs text-slate-400">Track your trading performance</p>
            </div>
          </div>
          
          {/* Summary Stats */}
          <div className="flex gap-4">
            <div className="text-right">
              <div className="text-xs text-slate-400">Total P&L</div>
              <div className={`text-sm font-semibold ${getTotalPnL() >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatCurrency(getTotalPnL())}
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400">Win Rate</div>
              <div className="text-sm font-semibold text-blue-400">
                {formatPercentage(getWinRate())}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-3 max-h-80 overflow-y-auto">
          {trades.length === 0 ? <div className="text-center py-8 text-slate-400">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No trades logged yet</p>
              <p className="text-xs">Use the + button on strategy cards to log trades</p>
            </div> : trades.map((trade, index) => <motion.div key={trade.id} className="bg-slate-700/30 rounded-xl p-4 flex items-center justify-between" initial={{
          opacity: 0,
          x: -20
        }} animate={{
          opacity: 1,
          x: 0
        }} transition={{
          duration: 0.3,
          delay: index * 0.1
        }}>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-slate-100">{trade.strategy}</span>
                    <span className="text-xs text-slate-400">{trade.date}</span>
                    <span className="text-xs bg-slate-600/50 px-2 py-1 rounded">
                      {trade.contracts}x
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>Strikes: {trade.strikes}</span>
                    <span>{trade.notes}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className={`text-sm font-semibold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {formatCurrency(trade.pnl)}
                  </div>
                  <motion.button onClick={() => onDeleteTrade(trade.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors duration-200" whileHover={{
              scale: 1.1
            }} whileTap={{
              scale: 0.9
            }}>
                    <Trash2 className="w-4 h-4" />
                  </motion.button>
                </div>
              </motion.div>)}
        </div>
      </motion.div>
    </div>;
};
export default AnalysisAndChartSection;