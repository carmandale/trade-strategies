import React, { useState } from 'react'
import { Brain, Loader2, AlertCircle, Wifi, WifiOff } from 'lucide-react'
import { AIAssessmentService, StrategyParams, AIAssessment } from '../services/aiAssessmentService'

interface AIAssessmentButtonProps {
  strategy: StrategyParams
  onAssessmentComplete: (assessment: AIAssessment) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'secondary' | 'outline'
  className?: string
}

export const AIAssessmentButton: React.FC<AIAssessmentButtonProps> = ({
  strategy,
  onAssessmentComplete,
  disabled = false,
  size = 'md',
  variant = 'primary',
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [serviceHealthy, setServiceHealthy] = useState<boolean | null>(null)

  // Check service health on first interaction
  const checkServiceHealth = async () => {
    if (serviceHealthy === null) {
      const healthy = await AIAssessmentService.isServiceHealthy()
      setServiceHealthy(healthy)
      return healthy
    }
    return serviceHealthy
  }

  const handleAssessment = async () => {
    if (isLoading || disabled) return

    setIsLoading(true)
    setError(null)

    try {
      // Check service health first
      const healthy = await checkServiceHealth()
      if (!healthy) {
        throw new Error('AI assessment service is currently unavailable')
      }

      const assessment = await AIAssessmentService.assessStrategy(strategy)
      onAssessmentComplete(assessment)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Assessment failed'
      setError(errorMessage)
      
      // Auto-clear error after 5 seconds
      setTimeout(() => setError(null), 5000)
    } finally {
      setIsLoading(false)
    }
  }

  // Size classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  }

  // Variant classes
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white border-blue-600',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white border-gray-600',
    outline: 'bg-white hover:bg-gray-50 text-blue-600 border-blue-600 hover:border-blue-700'
  }

  const iconSize = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-6 h-6' : 'w-5 h-5'

  return (
    <div className="flex flex-col items-start">
      <button
        onClick={handleAssessment}
        disabled={disabled || isLoading}
        className={`
          inline-flex items-center gap-2 font-medium rounded-md border transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${sizeClasses[size]}
          ${variantClasses[variant]}
          ${className}
        `}
        aria-label={isLoading ? 'Analyzing strategy with AI' : 'Analyze with AI'}
        aria-describedby={error ? 'ai-assessment-error' : undefined}
      >
        {/* Icon */}
        {isLoading ? (
          <Loader2 className={`${iconSize} animate-spin`} />
        ) : serviceHealthy === false ? (
          <WifiOff className={iconSize} />
        ) : serviceHealthy === null ? (
          <Brain className={iconSize} />
        ) : (
          <>
            <Brain className={iconSize} />
            <Wifi className="w-3 h-3 text-green-400" />
          </>
        )}

        {/* Button text */}
        {isLoading ? (
          <span>Analyzing...</span>
        ) : serviceHealthy === false ? (
          <span>Service Offline</span>
        ) : (
          <span>Analyze with AI</span>
        )}
      </button>

      {/* Error message */}
      {error && (
        <div 
          id="ai-assessment-error"
          className="mt-2 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2 max-w-sm"
          role="alert"
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}