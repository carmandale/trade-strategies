# Options Pricing Service Documentation

## Overview

The Options Pricing Service provides accurate options pricing using the Black-Scholes model, which accounts for strike price, time to expiration, volatility, interest rates, and underlying price. This service is used to calculate option prices, Greeks, implied volatility, and spread prices for various option strategies.

## Black-Scholes Model

The Black-Scholes model is a mathematical model for pricing options contracts. It assumes that the price of the underlying asset follows a geometric Brownian motion with constant drift and volatility. The model provides a closed-form solution for European-style options.

### Key Assumptions

- The option is European-style (can only be exercised at expiration)
- No dividends are paid during the option's life (our implementation accounts for dividends)
- Markets are efficient (no arbitrage opportunities)
- No transaction costs or taxes
- The risk-free rate and volatility are constant
- The returns on the underlying asset are normally distributed

### Formula

For a call option:
```
C = S * e^(-q*t) * N(d1) - K * e^(-r*t) * N(d2)
```

For a put option:
```
P = K * e^(-r*t) * N(-d2) - S * e^(-q*t) * N(-d1)
```

Where:
- C = Call option price
- P = Put option price
- S = Current price of the underlying asset
- K = Strike price
- r = Risk-free interest rate
- q = Dividend yield
- t = Time to expiration (in years)
- N() = Cumulative distribution function of the standard normal distribution
- d1 = (ln(S/K) + (r - q + σ²/2) * t) / (σ * √t)
- d2 = d1 - σ * √t
- σ = Volatility of the underlying asset

## Greeks

The Greeks measure the sensitivity of option prices to various factors:

- **Delta**: Measures the rate of change of the option price with respect to changes in the underlying asset's price
- **Gamma**: Measures the rate of change of delta with respect to changes in the underlying asset's price
- **Theta**: Measures the rate of change of the option price with respect to the passage of time
- **Vega**: Measures the rate of change of the option price with respect to changes in volatility
- **Rho**: Measures the rate of change of the option price with respect to changes in the risk-free interest rate

## Spread Pricing

The service supports pricing for various option spreads:

- **Bull Call Spread**: Buy a lower strike call, sell a higher strike call
- **Bear Call Spread**: Sell a lower strike call, buy a higher strike call
- **Bull Put Spread**: Sell a higher strike put, buy a lower strike put
- **Bear Put Spread**: Buy a higher strike put, sell a lower strike put
- **Iron Condor**: Sell a put spread and a call spread (four legs)
- **Butterfly**: Buy a lower strike option, sell two middle strike options, buy a higher strike option

## Probability of Profit

The service calculates the probability of profit for various option strategies based on the normal distribution of returns. For example, for an iron condor, the probability of profit is the probability that the underlying price at expiration will be between the short put and short call strikes.

## Usage Examples

### Calculate Option Price

```python
from services.options_pricing_service import OptionsPricingService

# Initialize the service
options_pricing = OptionsPricingService(risk_free_rate=0.05)

# Calculate call option price
call_price = options_pricing.calculate_option_price(
    option_type='call',
    underlying_price=100.0,
    strike_price=100.0,
    days_to_expiration=30,
    volatility=0.2,
    dividend_yield=0.0
)

print(f"Call option price: ${call_price:.2f}")
```

### Calculate Greeks

```python
# Calculate Greeks for a call option
greeks = options_pricing.calculate_greeks(
    option_type='call',
    underlying_price=100.0,
    strike_price=100.0,
    days_to_expiration=30,
    volatility=0.2,
    dividend_yield=0.0
)

print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Theta: {greeks['theta']:.4f}")
print(f"Vega: {greeks['vega']:.4f}")
print(f"Rho: {greeks['rho']:.4f}")
```

### Calculate Spread Prices

```python
# Calculate prices for an iron condor
iron_condor = options_pricing.calculate_spread_prices(
    spread_type='iron_condor',
    underlying_price=100.0,
    strikes=[90.0, 95.0, 105.0, 110.0],
    days_to_expiration=30,
    volatility=0.2,
    dividend_yield=0.0
)

print(f"Net credit: ${iron_condor['net_credit']:.2f}")
print(f"Max profit: ${iron_condor['max_profit']:.2f}")
print(f"Max loss: ${iron_condor['max_loss']:.2f}")
print(f"Lower breakeven: ${iron_condor['lower_breakeven']:.2f}")
print(f"Upper breakeven: ${iron_condor['upper_breakeven']:.2f}")
```

### Calculate Probability of Profit

```python
# Calculate probability of profit for an iron condor
pop = options_pricing.calculate_probability_of_profit(
    spread_type='iron_condor',
    underlying_price=100.0,
    strikes=[90.0, 95.0, 105.0, 110.0],
    days_to_expiration=30,
    volatility=0.2,
    dividend_yield=0.0
)

print(f"Probability of profit: {pop * 100:.2f}%")
```

## Implementation Details

The service is implemented in Python using NumPy and SciPy for numerical calculations. The Black-Scholes formula is implemented using the cumulative normal distribution function from SciPy.

Implied volatility is calculated using the Newton-Raphson method, which is an iterative numerical method for finding the roots of a function. In this case, we're finding the volatility that makes the Black-Scholes price equal to the market price.

## Limitations

- The Black-Scholes model assumes European-style options, which can only be exercised at expiration
- The model assumes constant volatility, which is not always the case in real markets
- The model does not account for early exercise of American-style options
- The probability of profit calculations assume a lognormal distribution of returns, which may not always be accurate

## Future Enhancements

- Support for American-style options using binomial or trinomial tree models
- Implementation of a volatility surface for more accurate pricing
- Support for more exotic options (e.g., barrier options, Asian options)
- Integration with real-time market data for more accurate pricing

