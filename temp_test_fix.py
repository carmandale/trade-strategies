# Let me check if the test can be fixed with proper mocking
import sys
sys.path.append('.')

from unittest.mock import Mock, patch
from services.ai_assessment_service import AIAssessmentService
import json

# Test if we can properly mock the service
service = AIAssessmentService()
mock_client = Mock()
mock_completion = Mock()
mock_completion.choices = [
    Mock(message=Mock(content=json.dumps({
        "recommendation": "GO",
        "confidence": 78,
        "reasoning": {
            "supporting_factors": ["test1", "test2"],
            "risk_factors": ["risk1", "risk2"]
        },
        "market_regime": "Test mode"
    })))
]
mock_completion.usage = Mock(
    prompt_tokens=350,
    completion_tokens=100,
    total_tokens=450
)
mock_client.chat.completions.create = Mock(return_value=mock_completion)

# Inject the mock client directly into the service instance
service.client = mock_client

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

# Mock market data method
service._get_market_data = Mock(return_value={
    'spx_price': 5635.50,
    'spx_change': 17.25,
    'technical_indicators': {'rsi_14': 72.4}
})

# Test the assessment
assessment = service.assess_strategy(strategy_params)
print(f"Assessment result: {assessment}")
print(f"Mock called: {mock_client.chat.completions.create.called}")
