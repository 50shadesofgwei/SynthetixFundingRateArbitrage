from binance.enums import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

ALL_MARKETS = [
    'ETHUSDT',
    'BTCUSDT'
]

def is_long_trade(position_amount: float) -> bool:
    try:
        if position_amount > 0:
            is_long = True
        elif position_amount < 0:
            is_long = False
        return is_long
    
    except Exception as e:
        logger.error(f"OKXPositionControllerUtils - Failed to determine whether position amount indicated a long or a short. Amount={position_amount}, Error: {e}")
        return None

def get_order_from_opportunity(opportunity, is_long: bool):
    try:
        side = 'buy' if is_long else 'sell'
        order_without_amount = {
            'symbol': opportunity['symbol'] + '-USDT-SWAP',
            'side': side,         # if long, side:buy; if short side : sellopen is sell
            'posSide':get_side(side),
            'type': ORDER_TYPE_MARKET,
            'quantity': 0.0
        }
        return order_without_amount

    except Exception as e:
        logger.error(f"OKXPositionControllerUtils - Failed to extract order details from opportunity. Error: {e}")
        return None

def add_amount_to_order(order_without_amount, amount: float) -> dict:
    try:
        order_with_amount = order_without_amount.copy()
        order_with_amount['quantity'] = abs(round(amount, 1))# TODO:round up or ceil? Round n digit should concern lotSize?
        return order_with_amount

    except Exception as e:
        logger.error(f"OKXPositionControllerUtils - Failed to add order to amount. Error: {e}")
        return None

def parse_trade_data_from_response(response) -> dict:
    try:
        trade_data = {
            "exchange": "OKX",
            "symbol": response['symbol'],
            "side": response['side'],
            "size": response['executedQty'],
            "liquidation_price": response['liquidationPrice']
        }
        return trade_data

    except Exception as e:
        logger.error(f"OKXPositionControllerUtils - Failed to extract trade data from response. Error: {e}")
        return None

def calculate_adjusted_trade_size(opportunity, is_long: bool, trade_size: float, leverage_factor: int) -> float:
        try:
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(opportunity['symbol'].split('-')[0], trade_size)
            trade_size_with_leverage = trade_size_in_asset * leverage_factor
            adjusted_trade_size_raw = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            adjusted_trade_size = round(adjusted_trade_size_raw, 3)

            return adjusted_trade_size

        except Exception as e:
            logger.error(f"OKXPositionControllerUtils - Failed to calculate adjusted trade size. Error: {e}")
            return None

def get_side(side: str) -> str:
    # lower case
    if side == "sell":
        return "short"
    elif side == "buy":
        return "long"
    else:
        logger.error(f"OKXPositionControllerUtils - get_side given invalid argument: {side}")
        return None

def is_expected_api_response_format_for_new_order(response: dict) -> bool:
    if not isinstance(response, dict) or 'orderId' not in response['data'][0]:
        logger.error("OKXPositionController - Invalid response structure from new_order.")
        return False
    else:
        return True
