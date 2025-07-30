import React from 'react';
import { motion } from 'framer-motion';
import { Target, TrendingUp, Zap, AlertTriangle, Activity } from 'lucide-react';
import { SpreadConfig } from './SPYSpreadStrategiesApp';
import { calculateDelta, calculateTimeToExpiration, getExpirationDate, findStrikeForDelta, DELTA_STRATEGIES } from '../../utils/optionsCalculations';
interface StrikePriceConfigSectionProps {
  spreadConfig: SpreadConfig;
  setSpreadConfig: (config: SpreadConfig) => void;
  currentPrice: number;
}
const StrikePriceConfigSection: React.FC<StrikePriceConfigSectionProps> = ({
  spreadConfig,
  setSpreadConfig,
  currentPrice
}) => {
  const updateSpreadConfig = (field: keyof SpreadConfig, value: number) => {
    setSpreadConfig({
      ...spreadConfig,
      [field]: value
    });
  };

  // Calculate time to expiration (assuming weekly options for now)
  const timeToExpiration = calculateTimeToExpiration(getExpirationDate('weekly'));
  
  // Function to calculate delta for a given strike
  const calculateStrikeDelta = (strike: number, isCall: boolean): number => {
    return calculateDelta(currentPrice, strike, timeToExpiration, 0.05, 0.20, isCall);
  };

  // Function to format delta display
  const formatDelta = (delta: number): string => {
    return `Δ${(delta * 100).toFixed(0)}`;
  };

  // Function to apply delta strategy presets
  const applyDeltaStrategy = (strategy: typeof DELTA_STRATEGIES[0]) => {
    if (!strategy.putDelta || !strategy.callDelta) return;
    
    const putStrike = findStrikeForDelta(currentPrice, strategy.putDelta, timeToExpiration, 0.05, 0.20, false);
    const callStrike = findStrikeForDelta(currentPrice, strategy.callDelta, timeToExpiration, 0.05, 0.20, true);
    
    // Update Iron Condor strikes based on delta
    setSpreadConfig({
      ...spreadConfig,
      ironCondorPutShort: putStrike,
      ironCondorPutLong: putStrike - 10,
      ironCondorCallShort: callStrike,
      ironCondorCallLong: callStrike + 10
    });
  };
  const validateBullCall = (): {
    isValid: boolean;
    error?: string;
  } => {
    if (spreadConfig.bullCallLower >= spreadConfig.bullCallUpper) {
      return {
        isValid: false,
        error: 'Lower strike must be less than upper strike'
      };
    }
    return {
      isValid: true
    };
  };
  const validateIronCondor = (): {
    isValid: boolean;
    error?: string;
  } => {
    const {
      ironCondorPutLong,
      ironCondorPutShort,
      ironCondorCallShort,
      ironCondorCallLong
    } = spreadConfig;
    if (ironCondorPutLong >= ironCondorPutShort) {
      return {
        isValid: false,
        error: 'Put long strike must be less than put short strike'
      };
    }
    if (ironCondorCallShort >= ironCondorCallLong) {
      return {
        isValid: false,
        error: 'Call short strike must be less than call long strike'
      };
    }
    if (ironCondorPutShort >= ironCondorCallShort) {
      return {
        isValid: false,
        error: 'Put short must be less than call short strike'
      };
    }
    return {
      isValid: true
    };
  };
  const validateButterfly = (): {
    isValid: boolean;
    error?: string;
  } => {
    if (spreadConfig.butterflyLower >= spreadConfig.butterflyBody || spreadConfig.butterflyBody >= spreadConfig.butterflyUpper) {
      return {
        isValid: false,
        error: 'Strikes must be in ascending order'
      };
    }
    return {
      isValid: true
    };
  };
  const getDistanceFromCurrent = (strike: number): string => {
    const distance = strike - currentPrice;
    const percentage = distance / currentPrice * 100;
    return `${distance > 0 ? '+' : ''}${distance.toFixed(2)} (${percentage.toFixed(1)}%)`;
  };
  const bullCallValidation = validateBullCall();
  const ironCondorValidation = validateIronCondor();
  const butterflyValidation = validateButterfly();
  return <div className="space-y-6">
      {/* Section Header */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-slate-100 mb-2">Strike Configuration</h2>
        <p className="text-slate-400 text-sm">Set strike prices for each strategy</p>
        <div className="mt-3 text-xs text-slate-500">
          Current SPY: <span className="text-blue-400 font-medium">${currentPrice.toFixed(2)}</span>
          <span className="ml-4 text-slate-600">•</span>
          <span className="ml-2">Time to Exp: <span className="text-green-400 font-medium">{(timeToExpiration * 365).toFixed(1)} days</span></span>
        </div>
      </div>

      {/* Delta Strategy Presets */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Delta Strategy Presets</h3>
            <p className="text-xs text-slate-400">Quick setup based on target delta values</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          {DELTA_STRATEGIES.map((strategy, index) => (
            <button
              key={index}
              onClick={() => applyDeltaStrategy(strategy)}
              className="bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 rounded-lg p-3 text-left transition-all duration-200 hover:border-blue-500/50"
            >
              <div className="text-sm font-medium text-slate-100">{strategy.name}</div>
              <div className="text-xs text-slate-400 mt-1">{strategy.description}</div>
              {strategy.putDelta && strategy.callDelta && (
                <div className="text-xs text-blue-300 mt-1">
                  Put: {formatDelta(strategy.putDelta)} • Call: {formatDelta(strategy.callDelta)}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Bull Call Spread */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
      scale: 1.01
    }} transition={{
      duration: 0.2
    }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Bull Call Spread</h3>
            <p className="text-xs text-slate-400">Bullish limited risk strategy</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Lower Strike (Long Call)
            </label>
            <input type="number" step="0.5" value={spreadConfig.bullCallLower} onChange={e => updateSpreadConfig('bullCallLower', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all duration-200" />
            <div className="mt-1 text-xs text-slate-500 flex justify-between">
              <span>{getDistanceFromCurrent(spreadConfig.bullCallLower)}</span>
              <span className="text-green-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.bullCallLower, true))}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Upper Strike (Short Call)
            </label>
            <input type="number" step="0.5" value={spreadConfig.bullCallUpper} onChange={e => updateSpreadConfig('bullCallUpper', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all duration-200" />
            <div className="mt-1 text-xs text-slate-500 flex justify-between">
              <span>{getDistanceFromCurrent(spreadConfig.bullCallUpper)}</span>
              <span className="text-green-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.bullCallUpper, true))}
              </span>
            </div>
          </div>

          {!bullCallValidation.isValid && <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg p-2">
              <AlertTriangle className="w-4 h-4" />
              {bullCallValidation.error}
            </div>}

          <div className="bg-slate-700/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Spread Width</div>
            <div className="text-sm font-medium text-slate-100">
              ${(spreadConfig.bullCallUpper - spreadConfig.bullCallLower).toFixed(2)}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Iron Condor */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
      scale: 1.01
    }} transition={{
      duration: 0.2
    }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Target className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Iron Condor</h3>
            <p className="text-xs text-slate-400">Neutral range-bound strategy</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-300">Put Side</h4>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Long Put</label>
              <input type="number" step="0.5" value={spreadConfig.ironCondorPutLong} onChange={e => updateSpreadConfig('ironCondorPutLong', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all duration-200" />
              <div className="mt-1 text-xs text-purple-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.ironCondorPutLong, false))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Short Put</label>
              <input type="number" step="0.5" value={spreadConfig.ironCondorPutShort} onChange={e => updateSpreadConfig('ironCondorPutShort', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all duration-200" />
              <div className="mt-1 text-xs text-purple-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.ironCondorPutShort, false))}
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-300">Call Side</h4>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Short Call</label>
              <input type="number" step="0.5" value={spreadConfig.ironCondorCallShort} onChange={e => updateSpreadConfig('ironCondorCallShort', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all duration-200" />
              <div className="mt-1 text-xs text-purple-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.ironCondorCallShort, true))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Long Call</label>
              <input type="number" step="0.5" value={spreadConfig.ironCondorCallLong} onChange={e => updateSpreadConfig('ironCondorCallLong', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all duration-200" />
              <div className="mt-1 text-xs text-purple-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.ironCondorCallLong, true))}
              </div>
            </div>
          </div>
        </div>

        {!ironCondorValidation.isValid && <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg p-2 mt-4">
            <AlertTriangle className="w-4 h-4" />
            {ironCondorValidation.error}
          </div>}

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-slate-700/30 rounded-lg p-2">
            <div className="text-xs text-slate-400">Profit Zone</div>
            <div className="text-xs font-medium text-slate-100">
              ${spreadConfig.ironCondorPutShort} - ${spreadConfig.ironCondorCallShort}
            </div>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-2">
            <div className="text-xs text-slate-400">Zone Width</div>
            <div className="text-xs font-medium text-slate-100">
              ${(spreadConfig.ironCondorCallShort - spreadConfig.ironCondorPutShort).toFixed(2)}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Butterfly Spread */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
      scale: 1.01
    }} transition={{
      duration: 0.2
    }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-yellow-500/20 rounded-lg">
            <Zap className="w-5 h-5 text-yellow-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Butterfly Spread</h3>
            <p className="text-xs text-slate-400">Neutral limited risk/reward</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Lower Wing Strike
            </label>
            <input type="number" step="0.5" value={spreadConfig.butterflyLower} onChange={e => updateSpreadConfig('butterflyLower', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 focus:border-yellow-500/50 transition-all duration-200" />
            <div className="mt-1 text-xs text-slate-500 flex justify-between">
              <span>{getDistanceFromCurrent(spreadConfig.butterflyLower)}</span>
              <span className="text-yellow-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.butterflyLower, true))}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Body Strike (2x)
            </label>
            <input type="number" step="0.5" value={spreadConfig.butterflyBody} onChange={e => updateSpreadConfig('butterflyBody', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 focus:border-yellow-500/50 transition-all duration-200" />
            <div className="mt-1 text-xs text-slate-500 flex justify-between">
              <span>{getDistanceFromCurrent(spreadConfig.butterflyBody)}</span>
              <span className="text-yellow-300 font-mono">
                {formatDelta(calculateStrikeDelta(spreadConfig.butterflyBody, true))}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Upper Wing Strike
            </label>
            <input type="number" step="0.5" value={spreadConfig.butterflyUpper} onChange={e => updateSpreadConfig('butterflyUpper', parseFloat(e.target.value) || 0)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 focus:border-yellow-500/50 transition-all duration-200" />
            <div className="mt-1 text-xs text-slate-500">
              {getDistanceFromCurrent(spreadConfig.butterflyUpper)}
            </div>
          </div>

          {!butterflyValidation.isValid && <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg p-2">
              <AlertTriangle className="w-4 h-4" />
              {butterflyValidation.error}
            </div>}

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-700/30 rounded-lg p-2">
              <div className="text-xs text-slate-400">Wing Spread</div>
              <div className="text-xs font-medium text-slate-100">
                ${(spreadConfig.butterflyBody - spreadConfig.butterflyLower).toFixed(2)}
              </div>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-2">
              <div className="text-xs text-slate-400">Total Width</div>
              <div className="text-xs font-medium text-slate-100">
                ${(spreadConfig.butterflyUpper - spreadConfig.butterflyLower).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>;
};
export default StrikePriceConfigSection;