import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronUp, TestTube } from 'lucide-react';
import { verifier, VerificationResult } from '../utils/accuracyVerification';
import runEdgeCaseTests from '../utils/edgeCaseTests';

export const AccuracyReport: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState<VerificationResult[]>([]);
  const [summary, setSummary] = useState({ total: 0, passed: 0, failed: 0, successRate: 0 });

  useEffect(() => {
    // Update results every second
    const interval = setInterval(() => {
      setResults([...verifier.getResults()]);
      setSummary(verifier.getSummary());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const getStatusIcon = (passed: boolean) => {
    if (passed) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
    return <XCircle className="w-4 h-4 text-red-400" />;
  };

  const getSummaryColor = () => {
    if (summary.successRate === 100) return 'text-green-400';
    if (summary.successRate >= 80) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-lg px-4 py-2 flex items-center gap-2 hover:bg-slate-700/90 transition-all"
      >
        <AlertCircle className="w-4 h-4 text-blue-400" />
        <span className="text-sm font-medium text-slate-100">
          Accuracy Report
        </span>
        <span className={`text-xs font-bold ${getSummaryColor()}`}>
          {summary.successRate.toFixed(0)}%
        </span>
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
      </button>

      {/* Report Panel */}
      {isOpen && (
        <div className="mt-2 bg-slate-800/95 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4 max-h-96 overflow-y-auto">
          {/* Summary */}
          <div className="mb-3 pb-3 border-b border-slate-700/50">
            <h3 className="text-sm font-semibold text-slate-100 mb-2">Verification Summary</h3>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-slate-700/30 rounded px-2 py-1">
                <div className="text-slate-400">Total</div>
                <div className="font-medium text-slate-100">{summary.total}</div>
              </div>
              <div className="bg-green-900/20 rounded px-2 py-1">
                <div className="text-green-400">Passed</div>
                <div className="font-medium text-green-300">{summary.passed}</div>
              </div>
              <div className="bg-red-900/20 rounded px-2 py-1">
                <div className="text-red-400">Failed</div>
                <div className="font-medium text-red-300">{summary.failed}</div>
              </div>
            </div>
          </div>

          {/* Results List */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-300">Verification Details</h4>
            {results.length === 0 ? (
              <p className="text-xs text-slate-500">No verifications yet...</p>
            ) : (
              results.map((result, index) => (
                <div
                  key={index}
                  className={`text-xs p-2 rounded ${
                    result.passed ? 'bg-green-900/10' : 'bg-red-900/10'
                  } border ${
                    result.passed ? 'border-green-800/30' : 'border-red-800/30'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {getStatusIcon(result.passed)}
                    <div className="flex-1">
                      <div className="font-medium text-slate-100">{result.name}</div>
                      <div className="mt-1 text-slate-400">
                        Expected: <span className="text-slate-300">{result.expected}</span>
                      </div>
                      <div className="text-slate-400">
                        Actual: <span className="text-slate-300">{result.actual}</span>
                      </div>
                      {result.error && (
                        <div className="mt-1 text-red-400 text-xs">{result.error}</div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => {
                runEdgeCaseTests();
                setResults([...verifier.getResults()]);
                setSummary(verifier.getSummary());
              }}
              className="flex-1 bg-blue-700/50 hover:bg-blue-600/50 text-blue-300 text-xs py-1 px-2 rounded transition-all flex items-center justify-center gap-1"
            >
              <TestTube className="w-3 h-3" />
              Run Edge Tests
            </button>
            <button
              onClick={() => {
                verifier.clear();
                setResults([]);
                setSummary({ total: 0, passed: 0, failed: 0, successRate: 0 });
              }}
              className="flex-1 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 text-xs py-1 px-2 rounded transition-all"
            >
              Clear Results
            </button>
          </div>
        </div>
      )}
    </div>
  );
};