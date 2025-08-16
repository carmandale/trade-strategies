import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { BarChart3, BookOpen, Trash2 } from 'lucide-react';
import HeaderSection from './generated/HeaderSection';
import { ConsolidatedStrategyCard, StrategyType } from './ConsolidatedStrategyCard';
import { apiService } from '../services/api';
import { SpreadConfig, AnalysisData, Trade } from './generated/SPYSpreadStrategiesApp';
import TradeStorageApiService, { StoredTrade as ApiStoredTrade, TradeCreateRequest } from '../services/tradeStorageApi';
import { TradeManagement } from './TradeManagement';

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
  
  // Load trades from database on component mount
  useEffect(() => {
    const loadStoredTrades = async () => {
      try {
        // First, sync any local trades to database
        const syncedCount = await TradeStorageApiService.syncLocalToDatabase();
        if (syncedCount > 0) {
          console.log(`Synced ${syncedCount} local trades to database`);
        }
        
        // Then load all trades from database
        const storedTrades = await TradeStorageApiService.getAllTrades();
        
        // Convert stored trades to the component's Trade format
        const convertedTrades: Trade[] = storedTrades.map(st => ({
          id: st.id,
          date: new Date(st.trade_date).toLocaleDateString(),
          strategy: formatStrategyName(st.strategy_type),
          strikes: st.strikes.join('/'),
          contracts: st.contracts,
          pnl: st.realized_pnl || 0,
          notes: st.notes || '',
          timestamp: new Date(st.created_at).getTime()
        }));
        setTrades(convertedTrades);
      } catch (error) {
        console.error('Error loading trades:', error);
      }
    };
    
    loadStoredTrades();
  }, []);
  
  // Helper function to format strategy name
  const formatStrategyName = (strategyType: string): string => {
    switch(strategyType.toLowerCase()) {
      case 'bull_call':
      case 'bullcall':
        return 'Bull Call';
      case 'iron_condor':
      case 'ironcondor':
        return 'Iron Condor';
      case 'butterfly':
        return 'Butterfly';
      default:
        return strategyType;
    }
  };

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
  const handleExecuteStrategy = async (strategy: StrategyType) => {
    console.log(`Executing ${strategy} strategy`);
    
    if (!spreadConfig || !spyPrice) {
      console.error('Cannot execute strategy: missing configuration or price data');
      return;
    }
    
    try {
      // Format date for options expiration (third Friday of the month)
      const expirationDate = new Date(selectedDate);
      // Set to the next Friday
      expirationDate.setDate(expirationDate.getDate() + (5 - expirationDate.getDay() + 7) % 7);
      // Format as YYYY-MM-DD for API
      const expirationStr = expirationDate.toISOString().split('T')[0];
      
      // Create appropriate legs and pricing based on strategy type
      let legs = [];
      let pricing = { side: 'DEBIT' as const, net: 0, tif: 'GTC' as const };
      let strategyName = '';
      
      switch (strategy) {
        case 'bullCall':
          // Bull Call Spread: Buy lower strike call, sell higher strike call
          legs = [
            {
              action: 'BUY' as const,
              type: 'CALL' as const,
              strike: spreadConfig.bullCallLower,
              expiration: expirationStr,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'CALL' as const,
              strike: spreadConfig.bullCallUpper,
              expiration: expirationStr,
              quantity: 1
            }
          ];
          
          // Calculate approximate debit (35% of width)
          const bcSpreadWidth = spreadConfig.bullCallUpper - spreadConfig.bullCallLower;
          const bcNetDebit = parseFloat((bcSpreadWidth * 0.35).toFixed(2));
          pricing = { side: 'DEBIT' as const, net: bcNetDebit, tif: 'GTC' as const };
          strategyName = 'Bull Call';
          break;
          
        case 'ironCondor':
          // Iron Condor: Sell put spread and call spread
          legs = [
            {
              action: 'BUY' as const,
              type: 'PUT' as const,
              strike: spreadConfig.ironCondorPutLong,
              expiration: expirationStr,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'PUT' as const,
              strike: spreadConfig.ironCondorPutShort,
              expiration: expirationStr,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'CALL' as const,
              strike: spreadConfig.ironCondorCallShort,
              expiration: expirationStr,
              quantity: 1
            },
            {
              action: 'BUY' as const,
              type: 'CALL' as const,
              strike: spreadConfig.ironCondorCallLong,
              expiration: expirationStr,
              quantity: 1
            }
          ];
          
          // Calculate approximate credit (25% of width)
          const icSpreadWidth = Math.min(
            spreadConfig.ironCondorPutShort - spreadConfig.ironCondorPutLong,
            spreadConfig.ironCondorCallLong - spreadConfig.ironCondorCallShort
          );
          const icNetCredit = parseFloat((icSpreadWidth * 0.25).toFixed(2));
          pricing = { side: 'CREDIT' as const, net: icNetCredit, tif: 'GTC' as const };
          strategyName = 'Iron Condor';
          break;
          
        case 'butterfly':
          // Butterfly: Buy lower strike call, sell 2x body strike calls, buy upper strike call
          legs = [
            {
              action: 'BUY' as const,
              type: 'CALL' as const,
              strike: spreadConfig.butterflyLower,
              expiration: expirationStr,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'CALL' as const,
              strike: spreadConfig.butterflyBody,
              expiration: expirationStr,
              quantity: 2
            },
            {
              action: 'BUY' as const,
              type: 'CALL' as const,
              strike: spreadConfig.butterflyUpper,
              expiration: expirationStr,
              quantity: 1
            }
          ];
          
          // Calculate approximate debit (20% of width)
          const bfSpreadWidth = spreadConfig.butterflyBody - spreadConfig.butterflyLower;
          const bfNetDebit = parseFloat((bfSpreadWidth * 0.20).toFixed(2));
          pricing = { side: 'DEBIT' as const, net: bfNetDebit, tif: 'GTC' as const };
          strategyName = 'Butterfly';
          break;
      }
      
      // Create the options ticket
      const response = await apiService.createOptionsTicket({
        symbol: 'SPY',
        strategy_type: strategyName,
        contracts: contracts || 1, // Default to 1 if contracts is undefined
        pricing: pricing,
        legs: legs,
        notes: `Executed from strategy analyzer on ${new Date().toLocaleString()}`
      });
      
      console.log('Trade ticket created:', response);
      
      // Calculate P&L for trade log based on strategy
      let pnl = 0;
      if (analysisData) {
        switch (strategy) {
          case 'bullCall':
            pnl = analysisData.bullCall.maxProfit;
            break;
          case 'ironCondor':
            pnl = analysisData.ironCondor.maxProfit;
            break;
          case 'butterfly':
            pnl = analysisData.butterfly.maxProfit;
            break;
        }
      }
      
      // Log the trade
      handleLogTrade(strategyName, pnl);
      
    } catch (error) {
      console.error('Failed to execute strategy:', error);
      // Could add UI error notification here
    }
  };

  // Handle trade logging
  const handleLogTrade = async (strategy: string, pnl: number) => {
    // Prepare strikes array based on strategy
    let strikesArray: number[] = [];
    if (spreadConfig) {
      if (strategy === 'Bull Call') {
        strikesArray = [spreadConfig.bullCallLower, spreadConfig.bullCallUpper];
      } else if (strategy === 'Iron Condor') {
        strikesArray = [
          spreadConfig.ironCondorPutLong,
          spreadConfig.ironCondorPutShort,
          spreadConfig.ironCondorCallShort,
          spreadConfig.ironCondorCallLong
        ];
      } else if (strategy === 'Butterfly') {
        strikesArray = [
          spreadConfig.butterflyLower,
          spreadConfig.butterflyBody,
          spreadConfig.butterflyUpper
        ];
      }
    }
    
    try {
      // Save to database using API
      const tradeRequest: TradeCreateRequest = {
        trade_date: selectedDate.toISOString().split('T')[0], // YYYY-MM-DD format
        entry_time: entryTime,
        symbol: 'SPY',
        strategy_type: strategy.toLowerCase().replace(' ', '_'), // e.g., "Bull Call" -> "bull_call"
        strikes: strikesArray,
        contracts: contracts,
        entry_price: spyPrice || 0,
        credit_debit: pnl > 0 ? pnl : -pnl, // Positive for credit, negative for debit
        status: 'open',
        notes: `${entryTime} - ${exitTime}`,
        realized_pnl: undefined // Will be set when trade is closed
      };
      
      const storedTrade = await TradeStorageApiService.saveTrade(tradeRequest);
      
      // Add to component state for immediate UI update
      const newTrade: Trade = {
        id: storedTrade.id,
        date: selectedDate.toLocaleDateString(),
        strategy,
        strikes: strikesArray.join('/'),
        contracts,
        pnl: 0, // P&L is 0 until trade is closed
        notes: `${entryTime} - ${exitTime}`,
        timestamp: Date.now()
      };
      setTrades(prev => [newTrade, ...prev]);
    } catch (error) {
      console.error('Failed to save trade:', error);
      // Show error notification to user
    }
  };
  
  // Handle deleting trades
  const handleDeleteTrade = async (tradeId: string) => {
    try {
      // Delete from database
      const success = await TradeStorageApiService.deleteTrade(tradeId);
      if (success) {
        // Update component state
        setTrades(prev => prev.filter(trade => trade.id !== tradeId));
      }
    } catch (error) {
      console.error('Failed to delete trade:', error);
    }
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

        {/* Trade Management */}
        <motion.div 
          className="mt-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          <TradeManagement
            trades={trades.map(t => ({
              id: t.id,
              trade_date: new Date(t.date).toISOString().split('T')[0],
              entry_time: t.notes?.split(' - ')[0],
              symbol: 'SPY',
              strategy_type: t.strategy.toLowerCase().replace(' ', '_'),
              strikes: t.strikes.split('/').map(Number),
              contracts: t.contracts,
              entry_price: spyPrice || 0,
              credit_debit: 0,
              status: 'open' as const,
              notes: t.notes,
              exit_price: undefined,
              exit_time: undefined,
              realized_pnl: t.pnl,
              created_at: new Date(t.timestamp).toISOString(),
              updated_at: new Date(t.timestamp).toISOString()
            }))}
            onDeleteTrade={handleDeleteTrade}
            onCloseTrade={async (id, closePrice) => {
              try {
                // Close trade in database
                await TradeStorageApiService.closeTrade(id, closePrice)
                // Reload trades from database
                const storedTrades = await TradeStorageApiService.getAllTrades()
                const convertedTrades: Trade[] = storedTrades.map(st => ({
                  id: st.id,
                  date: new Date(st.trade_date).toLocaleDateString(),
                  strategy: formatStrategyName(st.strategy_type),
                  strikes: st.strikes.join('/'),
                  contracts: st.contracts,
                  pnl: st.realized_pnl || 0,
                  notes: st.notes || '',
                  timestamp: new Date(st.created_at).getTime()
                }))
                setTrades(convertedTrades)
              } catch (error) {
                console.error('Failed to close trade:', error)
              }
            }}
            onRefresh={async () => {
              try {
                // Reload trades from database
                const storedTrades = await TradeStorageApiService.getAllTrades()
                const convertedTrades: Trade[] = storedTrades.map(st => ({
                  id: st.id,
                  date: new Date(st.trade_date).toLocaleDateString(),
                  strategy: formatStrategyName(st.strategy_type),
                  strikes: st.strikes.join('/'),
                  contracts: st.contracts,
                  pnl: st.realized_pnl || 0,
                  notes: st.notes || '',
                  timestamp: new Date(st.created_at).getTime()
                }))
                setTrades(convertedTrades)
              } catch (error) {
                console.error('Failed to refresh trades:', error)
              }
            }}
          />
        </motion.div>
      </div>
    </div>
  );
};

export default ConsolidatedSPYApp;
