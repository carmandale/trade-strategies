import React from 'react'
import { CheckCircle, AlertTriangle, XCircle, Clock, Database } from 'lucide-react'
import { AIAssessment, AIAssessmentService } from '../services/aiAssessmentService'

interface AIAssessmentResultProps {
  assessment: AIAssessment
  className?: string
}

export const AIAssessmentResult: React.FC<AIAssessmentResultProps> = ({
  assessment,
  className = ''
}) => {
  const { recommendation, confidence, reasoning, market_regime, cached, timestamp } = assessment

  // Get formatted styles using service utility
  const { badgeColor, confidenceColor, icon } = AIAssessmentService.formatAssessment(assessment)

  // Get recommendation icon component
  const getRecommendationIcon = () => {
    const iconProps = { className: "w-5 h-5" }
    switch (recommendation) {
      case 'GO':
        return <CheckCircle {...iconProps} className="w-5 h-5 text-green-600" />
      case 'CAUTION':
        return <AlertTriangle {...iconProps} className="w-5 h-5 text-yellow-600" />
      case 'NO-GO':
        return <XCircle {...iconProps} className="w-5 h-5 text-red-600" />
      default:
        return null
    }
  }

  // Format timestamp for display
  const formatTimestamp = (ts?: string) => {
    if (!ts) return null
    try {
      return new Date(ts).toLocaleString()
    } catch {
      return ts
    }
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
      {/* Header with recommendation and confidence */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {getRecommendationIcon()}
          <div>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${badgeColor}`}>
              {icon} {recommendation}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-lg font-bold ${confidenceColor}`}>
            {confidence}% confident
          </div>
          {cached && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Database className="w-3 h-3" />
              <span>Cached</span>
            </div>
          )}
        </div>
      </div>

      {/* Market regime */}
      {market_regime && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-800">
          <div className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
            Market Environment
          </div>
          <div className="text-sm text-blue-700 dark:text-blue-300">
            {market_regime}
          </div>
        </div>
      )}

      {/* Supporting factors */}
      {reasoning.supporting_factors && reasoning.supporting_factors.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              Supporting Factors
            </span>
          </div>
          <ul className="space-y-1 ml-6">
            {reasoning.supporting_factors.map((factor, index) => (
              <li key={index} className="text-sm text-green-700 dark:text-green-300 flex items-start gap-2">
                <span className="text-green-600 mt-1">•</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risk factors */}
      {reasoning.risk_factors && reasoning.risk_factors.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-orange-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              Risk Factors
            </span>
          </div>
          <ul className="space-y-1 ml-6">
            {reasoning.risk_factors.map((factor, index) => (
              <li key={index} className="text-sm text-orange-700 dark:text-orange-300 flex items-start gap-2">
                <span className="text-orange-600 mt-1">•</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Timestamp */}
      {timestamp && (
        <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>Assessment from {formatTimestamp(timestamp)}</span>
          </div>
        </div>
      )}
    </div>
  )
}