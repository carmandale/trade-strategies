import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Clock, DollarSign } from 'lucide-react';
interface HeaderSectionProps {
  spyPrice: number | null;
  lastUpdate: Date | null;
  connectionError?: string | null;
}
const HeaderSection: React.FC<HeaderSectionProps> = ({
  spyPrice,
  lastUpdate,
  connectionError
}) => {
  const formatTime = (date: Date | null): string => {
    if (!date) return '--:--:--';
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };
  const formatPrice = (price: number | null): string => {
    if (price === null) return '---.--';
    return price.toFixed(2);
  };
  const getPriceChange = (): {
    value: number;
    percentage: number;
    isPositive: boolean;
  } => {
    // Mock price change calculation (in real app, this would come from API)
    const change = (Math.random() - 0.5) * 10;
    const percentage = spyPrice ? (change / spyPrice * 100) : 0;
    return {
      value: change,
      percentage,
      isPositive: change >= 0
    };
  };
  const priceChange = getPriceChange();
  return <header className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        {/* Title Section */}
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/20 rounded-xl">
            <TrendingUp className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-slate-100">
              SPY Spread Strategies
            </h1>
            <p className="text-slate-400 text-sm lg:text-base">
              Advanced Options Trading Analysis
            </p>
          </div>
        </div>

        {/* Price Information */}
        <div className="flex flex-col sm:flex-row gap-4 lg:gap-6">
          {/* Current Price */}
          <motion.div className="bg-slate-700/30 rounded-xl p-4 min-w-[160px]" whileHover={{
          scale: 1.02
        }} transition={{
          duration: 0.2
        }}>
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-green-400" />
              <span className="text-slate-400 text-sm font-medium">SPY Price</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-100" data-testid="current-price">
                ${formatPrice(spyPrice)}
              </span>
              <div className={`flex items-center gap-1 text-sm font-medium ${priceChange.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                <span>{priceChange.isPositive ? '+' : ''}{formatPrice(priceChange.value)}</span>
                <span>({priceChange.isPositive ? '+' : ''}{priceChange.percentage.toFixed(2)}%)</span>
              </div>
            </div>
          </motion.div>

          {/* Last Update */}
          <motion.div className="bg-slate-700/30 rounded-xl p-4 min-w-[160px]" whileHover={{
          scale: 1.02
        }} transition={{
          duration: 0.2
        }}>
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-blue-400" />
              <span className="text-slate-400 text-sm font-medium">Last Update</span>
            </div>
            <div className="text-lg font-semibold text-slate-100">
              {formatTime(lastUpdate)}
            </div>
            <div className="text-xs text-slate-500">
              {lastUpdate.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            })}
            </div>
          </motion.div>

          {/* Market Status Indicator */}
          <motion.div className="bg-slate-700/30 rounded-xl p-4 min-w-[120px]" whileHover={{
          scale: 1.02
        }} transition={{
          duration: 0.2
        }}>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-slate-400 text-sm font-medium">Market</span>
            </div>
            <div className="text-lg font-semibold text-green-400">
              Open
            </div>
            <div className="text-xs text-slate-500">
              NYSE
            </div>
          </motion.div>
        </div>
      </div>

      {/* Real-time Update Indicator */}
      <motion.div className="mt-4 pt-4 border-t border-slate-700/50" initial={{
      opacity: 0
    }} animate={{
      opacity: 1
    }} transition={{
      delay: 0.5
    }}>
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Real-time data updates every 30 seconds</span>
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      </motion.div>
    </header>;
};
export default HeaderSection;