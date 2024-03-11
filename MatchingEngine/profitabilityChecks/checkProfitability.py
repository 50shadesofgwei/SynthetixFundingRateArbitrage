import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

class ProfitabilityChecker:
    exchange_fees = {
        "Binance": 0.0004,  # 0.04% fee
        "ByBit": 0.00055,   # 0.055% fee
        "Synthetix": 0    # gas fees handled elsewhere
    }

    def __init__(self):
        pass

    def get_exchange_fee(self, exchange: str) -> float:
        return self.exchange_fees.get(exchange, 0)

    def calculate_position_cost(self, fee_rate: float) -> float:
        capital = get_total_available_capital()
        return capital * fee_rate

    def is_profitable(self, opportunity) -> bool:
        capital = get_total_available_capital()
        long_capital = capital / 2
        short_capital = capital / 2

        long_fee_rate = self.get_exchange_fee(opportunity["long_exchange"])
        short_fee_rate = self.get_exchange_fee(opportunity["short_exchange"])

        long_cost = self.calculate_position_cost(long_capital, long_fee_rate)
        short_cost = self.calculate_position_cost(short_capital, short_fee_rate)

        daily_funding_profit = (long_capital * float(opportunity["long_funding_rate"]) +
                                short_capital * float(opportunity["short_funding_rate"]))
        total_cost = long_cost + short_cost

        return daily_funding_profit - total_cost > 0

    def minimum_profitable_duration(self, opportunity) -> float:
        capital = get_total_available_capital()
        long_capital = capital / 2
        short_capital = capital / 2

        long_fee_rate = self.get_exchange_fee(opportunity["long_exchange"])
        short_fee_rate = self.get_exchange_fee(opportunity["short_exchange"])

        long_cost = self.calculate_position_cost(long_capital, long_fee_rate)
        short_cost = self.calculate_position_cost(short_capital, short_fee_rate)

        daily_funding_profit = (long_capital * float(opportunity["long_funding_rate"]) +
                                short_capital * float(opportunity["short_funding_rate"]))

        total_initial_cost = long_cost + short_cost

        daily_net_profit = daily_funding_profit * 3 - total_initial_cost

        if daily_net_profit <= 0:
            return float('inf')

        days_to_profitability = total_initial_cost / daily_net_profit
        return days_to_profitability

    def calculate_profit(self, opportunity, period_hours: int):
        capital = get_total_available_capital()
        long_capital = capital / 2
        short_capital = capital / 2
        funding_rate_long = float(opportunity["long_funding_rate"])
        funding_rate_short = float(opportunity["short_funding_rate"])
        
        total_profit = (long_capital * funding_rate_long + short_capital * funding_rate_short) * (period_hours / 8)
        return total_profit * 5
    
    def find_most_profitable_opportunity(self, opportunities):
        max_profit = float('-inf')
        most_profitable = None
        for opportunity in opportunities:
            profit = self.calculate_profit(opportunity, 1)
            apy = self.calculate_effective_APY(opportunity)
            if profit > max_profit:
                max_profit = profit
                most_profitable = opportunity

        logger.info(f"best opportunity found, details: {most_profitable}")
        return most_profitable

x = 0.21
y = 0.00032016
z = x-y
a = {
        "long_exchange": "1",
        "short_exchange": "2",
        "symbol": "3",
        "long_funding_rate": x,
        "short_funding_rate": y,
        "funding_rate_differential": z
    }

# test=ProfitabilityChecker()
# b = test.calculate_effective_APY(a)
# print(b)

c = (x * 3) * 365
d = (y * 3) * 365
e = c-d
print(e)