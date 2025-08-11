import sys
sys.path.append('.')

from services.ai_assessment_service import AIAssessmentService
from unittest.mock import Mock
import json

# Create service and mock client
service = AIAssessmentService()
mock_client = Mock()
mock_completion = Mock()
mock_completion.choices = [
    Mock(message=Mock(content=json.dumps({
        "recommendation": "GO",
        "confidence": 78,
        "reasoning": {
            "supporting_factors": [
                "Low VIX indicates stable conditions",
                "SPX above key support level"
            ],
            "risk_factors": [
                "Fed meeting tomorrow",
                "Earnings season approaching"
            ]
        },
        "market_regime": "Low volatility, neutral sentiment"
    })))
]
mock_completion.usage = Mock(
    prompt_tokens=350,
    completion_tokens=100,
    total_tokens=450
)
mock_client.chat.completions.create = Mock(return_value=mock_completion)
service.client = mock_client

# Mock _get_market_data
service._get_market_data = Mock(return_value={
    'spx_price': 5635.50,
    'spx_change': 17.25,
    'technical_indicators': {'rsi_14': 72.4}
})

# Test strategy params
strategy_params = {
    'symbol': 'SPX',
    'strategy_type': 'iron_condor',
    'expiration': '2025-08-15',
    'strikes': {'put_long': 5500, 'put_short': 5520, 'call_short': 5680, 'call_long': 5700},
    'max_profit': 2000,
    'max_loss': 18000,
    'breakeven': [5520, 5680]
}

# Get assessment
assessment = service.assess_strategy(strategy_params)
print(f"Assessment type: {type(assessment)}")
print(f"Assessment keys: {list(assessment.keys()) if isinstance(assessment, dict) else 'Not a dict'}")
print(f"Assessment content: {assessment}")
