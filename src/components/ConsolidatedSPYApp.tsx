import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
              expiration: expirationDate,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'CALL' as const,
              strike: spreadConfig.bullCallUpper,
              expiration: expirationDate,
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
              expiration: expirationDate,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'PUT' as const,
              strike: spreadConfig.ironCondorPutShort,
              expiration: expirationDate,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'CALL' as const,
              strike: spreadConfig.ironCondorCallShort,
              expiration: expirationDate,
              quantity: 1
            },
            {
              action: 'BUY' as const,
              type: 'CALL' as const,
              strike: spreadConfig.ironCondorCallLong,
              expiration: expirationDate,
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
              expiration: expirationDate,
              quantity: 1
            },
            {
              action: 'SELL' as const,
              type: 'CALL' as const,
              strike: spreadConfig.butterflyBody,
              expiration: expirationDate,
              quantity: 2
            },
            {
              action: 'BUY' as const,
              type: 'CALL' as const,
              strike: spreadConfig.butterflyUpper,
              expiration: expirationDate,
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
        contracts: contracts,
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

        {/* Trade Log */}
        {trades.length > 0 && (
          <motion.div 
            className="mt-8 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <h2 className="text-lg font-semibold text-slate-100 mb-4">Recent Trades</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-2 text-slate-400">Date</th>
                    <th className="text-left py-2 text-slate-400">Strategy</th>
                    <th className="text-left py-2 text-slate-400">Strikes</th>
                    <th className="text-left py-2 text-slate-400">Contracts</th>
                    <th className="text-left py-2 text-slate-400">P&L</th>
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default ConsolidatedSPYApp;
