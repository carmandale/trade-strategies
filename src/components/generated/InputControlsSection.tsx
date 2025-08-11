import React from 'react';
import { motion } from 'framer-motion';
import { Calendar, Hash, Clock, Play, Loader2 } from 'lucide-react';
interface InputControlsSectionProps {
  selectedDate: Date;
  setSelectedDate: (date: Date) => void;
  contracts: number;
  setContracts: (contracts: number) => void;
  entryTime: string;
  setEntryTime: (time: string) => void;
  exitTime: string;
  setExitTime: (time: string) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  currentPrice: number;
}
const InputControlsSection: React.FC<InputControlsSectionProps> = ({
  selectedDate,
  setSelectedDate,
  contracts,
  setContracts,
  entryTime,
  setEntryTime,
  exitTime,
  setExitTime,
  onAnalyze,
  isAnalyzing,
  currentPrice
}) => {
  const formatDateForInput = (date: Date): string => {
    // Format date as YYYY-MM-DD in local timezone to avoid day shift
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(e.target.value);
    setSelectedDate(newDate);
  };
  const handleContractsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 1;
    setContracts(Math.max(1, Math.min(100, value)));
  };
  const validateTimeOrder = (): boolean => {
    return entryTime < exitTime;
  };
  return <div className="space-y-6">
      {/* Section Header */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-slate-100 mb-2">Trading Parameters</h2>
        <p className="text-slate-400 text-sm">Configure your analysis settings</p>
      </div>

      {/* Date Selection */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
      scale: 1.01
    }} transition={{
      duration: 0.2
    }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Calendar className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Analysis Date</h3>
            <p className="text-xs text-slate-400">Select trading date</p>
          </div>
        </div>
        
        <input type="date" value={formatDateForInput(selectedDate)} onChange={handleDateChange} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200" />
      </motion.div>

      {/* Contracts Input */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
      scale: 1.01
    }} transition={{
      duration: 0.2
    }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <Hash className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Contracts</h3>
            <p className="text-xs text-slate-400">Number of contracts (1-100)</p>
          </div>
        </div>
        
        <input type="number" min="1" max="100" value={contracts} onChange={handleContractsChange} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all duration-200" placeholder="Enter number of contracts" />
        
        <div className="mt-2 text-xs text-slate-500">
          Total notional: ${(contracts * 100 * currentPrice).toLocaleString()}
        </div>
      </motion.div>

      {/* Time Selection */}
      <motion.div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6" whileHover={{
      scale: 1.01
    }} transition={{
      duration: 0.2
    }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Clock className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">Trading Hours</h3>
            <p className="text-xs text-slate-400">Entry and exit times</p>
          </div>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Entry Time
            </label>
            <input type="time" value={entryTime} onChange={e => setEntryTime(e.target.value)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all duration-200" />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Exit Time
            </label>
            <input type="time" value={exitTime} onChange={e => setExitTime(e.target.value)} className="w-full bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all duration-200" />
          </div>
          
          {!validateTimeOrder() && <div className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg p-2">
              Exit time must be after entry time
            </div>}
        </div>
      </motion.div>

      {/* Analyze Button */}
      <motion.button onClick={onAnalyze} disabled={isAnalyzing || !validateTimeOrder()} className={`w-full py-4 px-6 rounded-2xl font-semibold text-white transition-all duration-300 ${isAnalyzing || !validateTimeOrder() ? 'bg-slate-600/50 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-xl'}`} whileHover={!isAnalyzing && validateTimeOrder() ? {
      scale: 1.02
    } : {}} whileTap={!isAnalyzing && validateTimeOrder() ? {
      scale: 0.98
    } : {}}>
        <div className="flex items-center justify-center gap-3">
          {isAnalyzing ? <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing Strategies...</span>
            </> : <>
              <Play className="w-5 h-5" />
              <span>Analyze Strategies</span>
            </>}
        </div>
      </motion.button>

      {/* Quick Stats */}
      <div className="bg-slate-800/30 backdrop-blur-sm border border-slate-700/30 rounded-2xl p-4">
        <h4 className="text-sm font-medium text-slate-300 mb-3">Quick Stats</h4>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-700/30 rounded-lg p-2">
            <div className="text-slate-400">Trading Window</div>
            <div className="text-slate-100 font-medium">
              {validateTimeOrder() ? `${((new Date(`2000-01-01T${exitTime}`).getTime() - new Date(`2000-01-01T${entryTime}`).getTime()) / (1000 * 60 * 60)).toFixed(1)}h` : 'Invalid'}
            </div>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-2">
            <div className="text-slate-400">Market Day</div>
            <div className="text-slate-100 font-medium">
              {selectedDate.toLocaleDateString('en-US', {
              weekday: 'short'
            })}
            </div>
          </div>
        </div>
      </div>
    </div>;
};
export default InputControlsSection;