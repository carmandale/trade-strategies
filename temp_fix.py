# Fix the test method properly
test_content = '''    def test_assess_strategy_success(self, service, strategy_params, market_data, mock_openai_client):
        """Test successful strategy assessment."""
        # Inject mock client directly into service
        service.client = mock_openai_client
        
        # Mock cache to ensure fresh API call
        with patch.object(service, '_get_cached_assessment', return_value=None):
            with patch.object(service, '_get_market_data', return_value=market_data):
                assessment = service.assess_strategy(strategy_params)
        
        assert assessment is not None
        assert assessment["recommendation"] == "GO"
        assert assessment["confidence"] == 78
        assert len(assessment["reasoning"]["supporting_factors"]) == 2
        assert len(assessment["reasoning"]["risk_factors"]) == 2
        assert assessment["market_regime"] == "Low volatility, neutral sentiment"
        
        # Verify OpenAI was called
        mock_openai_client.chat.completions.create.assert_called_once()'''

# Read the file
with open('tests/test_ai_assessment_service.py', 'r') as f:
    content = f.read()

# Find and replace the test method
import re
pattern = r'    def test_assess_strategy_success\(.*?\n        mock_openai_client\.chat\.completions\.create\.assert_called_once\(\)'
replacement = test_content

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('tests/test_ai_assessment_service.py', 'w') as f:
    f.write(new_content)

print("Fixed test method")
