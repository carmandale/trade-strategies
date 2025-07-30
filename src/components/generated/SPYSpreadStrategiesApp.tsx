import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import HeaderSection from './HeaderSection';
import InputControlsSection from './InputControlsSection';
import StrikePriceConfigSection from './StrikePriceConfigSection';
import AnalysisAndChartSection from './AnalysisAndChartSection';
import { apiService, type StrategyData, type BacktestResult } from '../../services/api';
export interface Trade {
  id: string;
  date: string;
  strategy: string;
  strikes: string;
  contracts: number;
  pnl: number;
  notes: string;
  timestamp: number;
}
export interface SpreadConfig {
  bullCallLower: number;
  bullCallUpper: number;
  ironCondorPutShort: number;
  ironCondorPutLong: number;
  ironCondorCallShort: number;
  ironCondorCallLong: number;
  butterflyLower: number;
  butterflyBody: number;
  butterflyUpper: number;
}
export interface AnalysisData {
  bullCall: {
    maxProfit: number;
    maxLoss: number;
    breakeven: number;
    riskReward: number;
  };
  ironCondor: {
    maxProfit: number;
    maxLoss: number;
    upperBreakeven: number;
    lowerBreakeven: number;
    riskReward: number;
  };
  butterfly: {
    maxProfit: number;
    maxLoss: number;
    breakeven1: number;
    breakeven2: number;
    riskReward: number;
  };
}
const SPYSpreadStrategiesApp: React.FC = () => {
  const [spyPrice, setSpyPrice] = useState<number>(425.50);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [contracts, setContracts] = useState<number>(1);
  const [entryTime, setEntryTime] = useState<string>('09:30');
  const [exitTime, setExitTime] = useState<string>('16:00');
  const [spreadConfig, setSpreadConfig] = useState<SpreadConfig>({
    bullCallLower: 420,
    bullCallUpper: 425,
    ironCondorPutShort: 415,
    ironCondorPutLong: 410,
    ironCondorCallShort: 435,
    ironCondorCallLong: 440,
    butterflyLower: 420,
    butterflyBody: 425,
    butterflyUpper: 430
  });
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
      } catch (error) {
        console.error('Failed to fetch SPY price:', error);
        // Fallback to current price with small variation
        const variation = (Math.random() - 0.5) * 2;
        setSpyPrice(prev => Math.max(400, Math.min(500, prev + variation)));
        setLastUpdate(new Date());
      }
    };

    // Initial fetch
    fetchSpyPrice();
    
    // Update every 30 seconds
    const interval = setInterval(fetchSpyPrice, 30000);
    return () => clearInterval(interval);
  }, []);

  // Generate mock chart data
  useEffect(() => {
    const generateChartData = () => {
      const data: {
        time: string;
        price: number;
        volume: number;
      }[] = [];
      const basePrice = spyPrice;
      for (let i = 0; i < 100; i++) {
        const variation = Math.sin(i * 0.1) * 5 + (Math.random() - 0.5) * 3;
        data.push({
          time: new Date(Date.now() - (100 - i) * 60000).toISOString(),
          price: basePrice + variation,
          volume: Math.floor(Math.random() * 1000000) + 500000
        });
      }
      return data;
    };
    setChartData(generateChartData());
  }, [spyPrice, selectedDate]);
  const handleAnalyzeStrategies = async () => {
    setIsAnalyzing(true);

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock analysis calculations
    const mockAnalysis: AnalysisData = {
      bullCall: {
        maxProfit: (spreadConfig.bullCallUpper - spreadConfig.bullCallLower) * 100 * contracts,
        maxLoss: 150 * contracts,
        breakeven: spreadConfig.bullCallLower + 1.5,
        riskReward: 2.33
      },
      ironCondor: {
        maxProfit: 200 * contracts,
        maxLoss: 300 * contracts,
        upperBreakeven: spreadConfig.ironCondorCallShort + 2,
        lowerBreakeven: spreadConfig.ironCondorPutShort - 2,
        riskReward: 0.67
      },
      butterfly: {
        maxProfit: 350 * contracts,
        maxLoss: 150 * contracts,
        breakeven1: spreadConfig.butterflyLower + 1.5,
        breakeven2: spreadConfig.butterflyUpper - 1.5,
        riskReward: 2.33
      }
    };
    setAnalysisData(mockAnalysis);
    setIsAnalyzing(false);
  };
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
  const handleDeleteTrade = (tradeId: string) => {
    setTrades(prev => prev.filter(trade => trade.id !== tradeId));
  };
  return <div className="min-h-screen bg-slate-900 text-slate-100">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <motion.div initial={{
        opacity: 0,
        y: -20
      }} animate={{
        opacity: 1,
        y: 0
      }} transition={{
        duration: 0.6
      }}>
          <HeaderSection spyPrice={spyPrice} lastUpdate={lastUpdate} />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-8">
          <motion.div className="lg:col-span-3" initial={{
          opacity: 0,
          x: -20
        }} animate={{
          opacity: 1,
          x: 0
        }} transition={{
          duration: 0.6,
          delay: 0.1
        }}>
            <InputControlsSection selectedDate={selectedDate} setSelectedDate={setSelectedDate} contracts={contracts} setContracts={setContracts} entryTime={entryTime} setEntryTime={setEntryTime} exitTime={exitTime} setExitTime={setExitTime} onAnalyze={handleAnalyzeStrategies} isAnalyzing={isAnalyzing} />
          </motion.div>

          <motion.div className="lg:col-span-3" initial={{
          opacity: 0,
          x: -20
        }} animate={{
          opacity: 1,
          x: 0
        }} transition={{
          duration: 0.6,
          delay: 0.2
        }}>
            <StrikePriceConfigSection spreadConfig={spreadConfig} setSpreadConfig={setSpreadConfig} currentPrice={spyPrice} />
          </motion.div>

          <motion.div className="lg:col-span-6" initial={{
          opacity: 0,
          x: 20
        }} animate={{
          opacity: 1,
          x: 0
        }} transition={{
          duration: 0.6,
          delay: 0.3
        }}>
            <AnalysisAndChartSection analysisData={analysisData} chartData={chartData} spreadConfig={spreadConfig} trades={trades} onLogTrade={handleLogTrade} onDeleteTrade={handleDeleteTrade} isAnalyzing={isAnalyzing} />
          </motion.div>
        </div>
      </div>
    </div>;
};
export default SPYSpreadStrategiesApp;