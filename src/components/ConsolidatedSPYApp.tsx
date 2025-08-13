import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { BarChart3, BookOpen, Trash2 } from 'lucide-react';
import HeaderSection from './generated/HeaderSection';
import { ConsolidatedStrategyCard, StrategyType } from './ConsolidatedStrategyCard';
import { apiService } from '../services/api';
import { SpreadConfig, AnalysisData, Trade } from './generated/SPYSpreadStrategiesApp';

// Function to round price to nearest $5 for options strikes
const roundToNearestFive = (price: number): number => {
  return Math.round(price / 5) * 5;
};

// Calculate strikes based on current SPY price using common options strategies
const calculateStrikes = (currentPrice: number): SpreadConfig => {
  const rounded = roundToNearestFive(currentPrice);
  
  return {
    // Bull Call Spread: ATM and 1 strike OTM (conservative, high probability)
    bullCallLower: rounded,
    bullCallUpper: rounded + 5,
    
    // Iron Condor: ~5% OTM on each side (targeting 16-delta strikes)
    ironCondorPutShort: roundToNearestFive(currentPrice * 0.95),  // 5% below
    ironCondorPutLong: roundToNearestFive(currentPrice * 0.93),   // 7% below  
    ironCondorCallShort: roundToNearestFive(currentPrice * 1.05), // 5% above
    ironCondorCallLong: roundToNearestFive(currentPrice * 1.07),  // 7% above
    
    // Butterfly: ATM with $10 wings (standard butterfly)
    butterflyLower: rounded - 10,
    butterflyBody: rounded,
    butterflyUpper: rounded + 10
  };
};

const ConsolidatedSPYApp: React.FC = () => {
  const [spyPrice, setSpyPrice] = useState<number | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [contracts, setContracts] = useState<number>(1);
  const [entryTime, setEntryTime] = useState<string>('09:30');
  const [exitTime, setExitTime] = useState<string>('16:00');
  const [spreadConfig, setSpreadConfig] = useState<SpreadConfig | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [chartData, setChartData] = useState<{
    time: string;
    price: number;
    volume: number;
  }[]>([]);

  // Fetch real-time SPY price updates
  useEffect(() => {
    const fetchSpyPrice = async () => {
      try {
        const marketData = await apiService.getMarketData('SPY');
        setSpyPrice(marketData.current_price);
        setLastUpdate(new Date());
        setConnectionError(null);
        // Calculate strikes if not already set
        if (!spreadConfig && marketData.current_price) {
          setSpreadConfig(calculateStrikes(marketData.current_price));
        }
      } catch (error) {
        console.error('Failed to fetch SPY price:', error);
        setConnectionError('Unable to connect to market data. Please check API connection.');
      }
    };

    // Initial fetch
    fetchSpyPrice();
    
    // Update every 30 seconds
    const interval = setInterval(fetchSpyPrice, 30000);
    return () => clearInterval(interval);
  }, [spreadConfig]);

  // Update strikes when SPY price changes significantly
  useEffect(() => {
    if (!spyPrice || !spreadConfig) return;
    
    const currentRounded = roundToNearestFive(spyPrice);
    const configRounded = roundToNearestFive(spreadConfig.butterflyBody);
    
    // Only update if price moved to a different $5 strike level
    if (Math.abs(currentRounded - configRounded) >= 5) {
      console.log(`SPY moved to new strike level: ${configRounded} → ${currentRounded}, updating strikes`);
      setSpreadConfig(calculateStrikes(spyPrice));
    }
  }, [spyPrice, spreadConfig?.butterflyBody]);

  // Fetch real historical chart data
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const historicalData = await apiService.getHistoricalData('SPY', '1d', '1m');
        // Transform the API data to match our chart format
        const transformedData = historicalData.map(point => ({
          time: point.timestamp,
          price: point.close,
          volume: point.volume
        }));
        setChartData(transformedData);
      } catch (error) {
        console.error('Failed to fetch chart data:', error);
        // Fallback to mock data generation
        const data: {
          time: string;
          price: number;
          volume: number;
        }[] = [];
        const basePrice = spyPrice || 425;
        for (let i = 0; i < 100; i++) {
          const variation = Math.sin(i * 0.1) * 5 + (Math.random() - 0.5) * 3;
          data.push({
            time: new Date(Date.now() - (100 - i) * 60000).toISOString(),
            price: basePrice + variation,
            volume: Math.floor(Math.random() * 1000000) + 500000
          });
        }
        setChartData(data);
      }
    };
    
    fetchChartData();
  }, [spyPrice, selectedDate]);

  // Handle strategy analysis
  const handleAnalyzeStrategies = async () => {
    setIsAnalyzing(true);
    
    try {
      // Call the actual /analyze endpoint
      const analysisResult = await apiService.analyzeStrategies(
        selectedDate,
        spreadConfig,
        contracts,
        entryTime,
        exitTime
      );

      setAnalysisData(analysisResult);
    } catch (error) {
      console.error('Failed to analyze strategies:', error);
      
      // Fallback to mock analysis if API fails
      if (spreadConfig) {
        const fallbackAnalysis: AnalysisData = {
          bullCall: {
            maxProfit: (spreadConfig.bullCallUpper - spreadConfig.bullCallLower - 1.5) * 100 * contracts,
            maxLoss: 1.5 * 100 * contracts,
            breakeven: spreadConfig.bullCallLower + 1.5,
            riskReward: 2.33
          },
          ironCondor: {
            maxProfit: 0.75 * 100 * contracts,
            maxLoss: 2.25 * 100 * contracts,
            upperBreakeven: spreadConfig.ironCondorCallShort + 0.75,
            lowerBreakeven: spreadConfig.ironCondorPutShort - 0.75,
            riskReward: 0.33
          },
          butterfly: {
            maxProfit: (spreadConfig.butterflyBody - spreadConfig.butterflyLower - 2.5) * 100 * contracts,
            maxLoss: 2.5 * 100 * contracts,
            breakeven1: spreadConfig.butterflyLower + 2.5,
            breakeven2: spreadConfig.butterflyUpper - 2.5,
            riskReward: 3
          }
        };
        setAnalysisData(fallbackAnalysis);
      }
    }
    
    setIsAnalyzing(false);
  };

  // Handle configuration updates
  const handleUpdateConfig = (updates: Partial<SpreadConfig>) => {
    if (spreadConfig) {
      setSpreadConfig({ ...spreadConfig, ...updates });
    }
  };

  // Handle strategy execution
  const handleExecuteStrategy = (strategy: StrategyType) => {
    console.log(`Executing ${strategy} strategy`);
    // TODO: Implement actual strategy execution
  };

  // Handle trade logging
  const handleLogTrade = (strategy: string, pnl: number) => {
    const newTrade: Trade = {
      id: Date.now().toString(),
      date: selectedDate.toLocaleDateString(),
      strategy,
      strikes: getStrikesString(strategy),
      contracts,
      pnl,
      notes: `${entryTime} - ${exitTime}`,
      timestamp: Date.now()
    };
    setTrades(prev => [newTrade, ...prev]);
  };
  
  // Handle deleting trades
  const handleDeleteTrade = (tradeId: string) => {
    setTrades(prev => prev.filter(trade => trade.id !== tradeId));
  };

  const getStrikesString = (strategy: string): string => {
    if (!spreadConfig) return '';
    
    switch (strategy) {
      case 'Bull Call':
        return `${spreadConfig.bullCallLower}/${spreadConfig.bullCallUpper}`;
      case 'Iron Condor':
        return `${spreadConfig.ironCondorPutLong}/${spreadConfig.ironCondorPutShort}/${spreadConfig.ironCondorCallShort}/${spreadConfig.ironCondorCallLong}`;
      case 'Butterfly':
        return `${spreadConfig.butterflyLower}/${spreadConfig.butterflyBody}/${spreadConfig.butterflyUpper}`;
      default:
        return '';
    }
  };
  
  // Helper functions for trade statistics
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

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.6 }}
        >
          <HeaderSection 
            spyPrice={spyPrice} 
            lastUpdate={lastUpdate} 
            connectionError={connectionError} 
          />
        </motion.div>

        {/* Global Controls */}
        <motion.div 
          className="mt-8 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <h2 className="text-lg font-semibold text-slate-100 mb-4">Trading Parameters</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">Date</label>
              <input
                type="date"
                value={selectedDate.toISOString().split('T')[0]}
                onChange={(e) => setSelectedDate(new Date(e.target.value))}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">Contracts</label>
              <input
                type="number"
                value={contracts}
                onChange={(e) => setContracts(parseInt(e.target.value) || 1)}
                min="1"
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">Entry Time</label>
              <input
                type="time"
                value={entryTime}
                onChange={(e) => setEntryTime(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">Exit Time</label>
              <input
                type="time"
                value={exitTime}
                onChange={(e) => setExitTime(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>
          </div>
        </motion.div>

        {/* Consolidated Strategy Cards */}
        <div className="mt-8 space-y-6">
          {(['bullCall', 'ironCondor', 'butterfly'] as StrategyType[]).map((strategy, index) => (
            <motion.div
              key={strategy}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 + (index * 0.1) }}
            >
              <ConsolidatedStrategyCard
                strategy={strategy}
                spreadConfig={spreadConfig}
                analysisData={analysisData}
                currentPrice={spyPrice}
                contracts={contracts}
                selectedDate={selectedDate}
                onUpdateConfig={handleUpdateConfig}
                onExecuteStrategy={handleExecuteStrategy}
                onAnalyze={handleAnalyzeStrategies}
                isAnalyzing={isAnalyzing}
              />
            </motion.div>
          ))}
        </div>
        
        {/* SPY Price Chart */}
        <motion.div 
          className="mt-8 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
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
                <XAxis 
                  dataKey="time" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickFormatter={value => new Date(value).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })} 
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={12} 
                  domain={['dataMin - 5', 'dataMax + 5']} 
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                    color: '#f1f5f9'
                  }} 
                  labelFormatter={value => new Date(value).toLocaleString()} 
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'SPY Price']} 
                />
                <Line 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#3b82f6" 
                  strokeWidth={2} 
                  dot={false} 
                />
                
                {/* Strike Price Reference Lines */}
                {spreadConfig && (
                  <>
                    <ReferenceLine 
                      y={spreadConfig.bullCallLower} 
                      stroke="#22c55e" 
                      strokeDasharray="5 5" 
                      label={{
                        value: `Bull Call Lower: $${spreadConfig.bullCallLower}`,
                        position: 'insideBottomLeft'
                      }} 
                    />
                    <ReferenceLine 
                      y={spreadConfig.bullCallUpper} 
                      stroke="#22c55e" 
                      strokeDasharray="5 5" 
                      label={{
                        value: `Bull Call Upper: $${spreadConfig.bullCallUpper}`,
                        position: 'insideTopLeft'
                      }} 
                    />
                    <ReferenceLine 
                      y={spreadConfig.ironCondorPutShort} 
                      stroke="#a855f7" 
                      strokeDasharray="3 3" 
                      label={{
                        value: `IC Put Short: $${spreadConfig.ironCondorPutShort}`,
                        position: 'insideBottomRight'
                      }} 
                    />
                    <ReferenceLine 
                      y={spreadConfig.ironCondorCallShort} 
                      stroke="#a855f7" 
                      strokeDasharray="3 3" 
                      label={{
                        value: `IC Call Short: $${spreadConfig.ironCondorCallShort}`,
                        position: 'insideTopRight'
                      }} 
                    />
                    <ReferenceLine 
                      y={spreadConfig.butterflyBody} 
                      stroke="#eab308" 
                      strokeDasharray="2 2" 
                      label={{
                        value: `Butterfly Body: $${spreadConfig.butterflyBody}`,
                        position: 'insideMiddle'
                      }} 
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Trade Log */}
        <motion.div 
          className="mt-8 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
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
            {trades.length > 0 && (
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
            )}
          </div>

          <div className="space-y-3 max-h-80 overflow-y-auto">
            {trades.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No trades logged yet</p>
                <p className="text-xs">Use the + button on strategy cards to log trades</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-2 text-slate-400">Date</th>
                      <th className="text-left py-2 text-slate-400">Strategy</th>
                      <th className="text-left py-2 text-slate-400">Strikes</th>
                      <th className="text-left py-2 text-slate-400">Contracts</th>
                      <th className="text-left py-2 text-slate-400">P&L</th>
                      <th className="text-left py-2 text-slate-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.slice(0, 10).map((trade) => (
                      <tr key={trade.id} className="border-b border-slate-700/50">
                        <td className="py-2 text-slate-300">{trade.date}</td>
                        <td className="py-2 text-slate-300">{trade.strategy}</td>
                        <td className="py-2 text-slate-300 font-mono text-xs">{trade.strikes}</td>
                        <td className="py-2 text-slate-300">{trade.contracts}</td>
                        <td className={`py-2 font-semibold ${
                          trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          ${trade.pnl.toFixed(2)}
                        </td>
                        <td className="py-2">
                          <motion.button 
                            onClick={() => handleDeleteTrade(trade.id)} 
                            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors duration-200"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </motion.button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ConsolidatedSPYApp;
