from APICaller.GMX.GMXCallerUtils import *
from GlobalUtils.globalUtils import *
from TxExecution.GMX.GMXPositionControllerUtils import *
from gmx_python_sdk.scripts.v2.order.order_argument_parser import (
    OrderArgumentParser
)
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder
from gmx_python_sdk.scripts.v2.order.create_decrease_order import DecreaseOrder
from gmx_python_sdk.scripts.v2.get.get_open_positions import GetOpenPositions
from gmx_python_sdk.scripts.v2.gmx_utils import *
from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory
from APICaller.GMX.GMXContractUtils import *
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason
set_paths()


class GMXPositionController:
    def __init__(self):
        self.config = ARBITRUM_CONFIG_OBJECT
        self.config.set_config(PATH_TO_GMX_CONFIG_FILE)
        self.leverage = float(os.getenv('TRADE_LEVERAGE'))

    def execute_trade(self, opportunity: dict, is_long: bool, trade_size: float):
        try:
            symbol = opportunity['symbol']
            trade_size_with_leverage = trade_size * self.leverage
            parameters = get_params_object_from_opportunity_dict(
                opportunity,
                is_long,
                trade_size_with_leverage
            )
            order_parameters = OrderArgumentParser(
                    self.config,
                    is_increase=True
                ).process_parameters_dictionary(
                    parameters
            )

            IncreaseOrder(
                config=self.config,
                market_key=order_parameters['market_key'],
                collateral_address=order_parameters['start_token_address'],
                index_token_address=order_parameters['index_token_address'],
                is_long=order_parameters['is_long'],
                size_delta=order_parameters['size_delta'],
                initial_collateral_delta_amount=(
                    order_parameters['initial_collateral_delta']
                ),
                slippage_percent=order_parameters['slippage_percent'],
                swap_path=order_parameters['swap_path'],
                debug_mode=True
            )

            time.sleep(4)
            if self.was_position_opened_successfully(
                symbol,
                is_long
            ):
                logger.info(f"GMXPositionController - Trade executed: symbol={symbol} side={'Long' if is_long else 'Short'}, Size USD={trade_size_with_leverage}")
                try:
                    position_object = self.get_position_object(
                    opportunity,
                    is_long,
                    trade_size_with_leverage
                    )
                    return position_object
                except Exception as ie:
                    logger.error(f"ByBitPositionController - Failed to build position object, despite trade executing successfully for symbol {symbol}. Error: {ie}")
                    return position_object 
            else:
                logger.info("GMXPositionController - Order not filled after 4 seconds.")
                return None

        except Exception as e:
            logger.error(f'GMXPositionController - Failed to execute trade for symbol {symbol}. Error: {e}')
            return None

    def close_position(self, symbol: str, reason: str = None):
        try:
            out_token = "USDC"
            slippage_percent = 0.003
            amount_of_position_to_close = 1
            amount_of_collateral_to_remove = 1
            market = ''

            position = self.get_open_positions()
            for key, position in position.items():
                is_long = position['is_long']
                market = key
            
        
            
            position_as_nested_dict = {
                market: position
            }

            order_parameters = transform_open_position_to_order_parameters(
                self.config,
                position_as_nested_dict,
                symbol,
                is_long,
                slippage_percent,
                out_token,
                amount_of_position_to_close,
                amount_of_collateral_to_remove)

            DecreaseOrder(
                config=self.config,
                market_key=order_parameters['market_key'],
                collateral_address=order_parameters['collateral_address'],
                index_token_address=order_parameters['index_token_address'],
                is_long=order_parameters['is_long'],
                size_delta=order_parameters['size_delta'],
                initial_collateral_delta_amount=(
                    order_parameters['initial_collateral_delta']
                ),
                slippage_percent=order_parameters['slippage_percent'],
                swap_path=order_parameters['swap_path'],
                debug_mode=False
            )

            time.sleep(5)
            if not self.was_position_closed_successfully(symbol, is_long):
                logger.error(f'GMXPositionController - Position not closed after 5 second delay.')
                return None
        
        except Exception as e:
            logger.error(f"GMXPositionController - Error closing position for {symbol}. Error: {e}", exc_info=True)
            return None

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_available_collateral(self) -> float:
        try:
            usdc_balance = get_arbitrum_usdc_balance()
            return usdc_balance
        
        except Exception as e:
            logger.error(f"GMXPositionController - Error getting available USDC balance from smart contract. Error: {e}")
            return None

    def was_position_opened_successfully(self, symbol: str, is_long: bool) -> bool:
        try:
            open_positions = self.get_open_positions()

            for key, position in open_positions.items():
                position_symbol = position['market_symbol'][0]
                position_is_long = position['is_long']
                
                if position_symbol == symbol and position_is_long == is_long:
                    return True

            return False
        except Exception as e:
            logger.error(f"GMXPositionController - Error checking if position was opened successfully for {symbol}. Error: {e}")
            return False
    
    def was_position_closed_successfully(self, symbol: str, is_long: bool) -> bool:
        try:
            open_positions = self.get_open_positions()
            if len(open_positions) == 0:
                return True

            for key, position in open_positions.items():
                position_symbol = position['market_symbol'][0]
                position_is_long = position['is_long']
                
                if position_symbol == symbol and position_is_long == is_long:
                    if position['position_size'] != 0:
                        return False

            # TODO - implement better checks here
            logger.info(f'GMXPositionController - No conditions met while checking if position closed, returning True')
            return True
        except Exception as e:
            logger.error(f"GMXPositionController - Error checking if position was opened successfully for {symbol}. Error: {e}")
            return False


    def get_open_positions(self) -> dict:
        try:
            address: str = self.config.user_wallet_address
            positions = GetOpenPositions(config=self.config, address=address).get_data()

            if len(positions) > 0:
                return positions
            else:
                return {}

        except Exception as e:
            logger.error(f"GMXPositionController - Failed to get open positions: {e}")
            return None

    def get_open_position_for_symbol(self, symbol: str) -> dict:
        try:
            positions = self.get_open_positions()
            for key, position in positions.items():
                position_symbol = position['market_symbol'][0]
                
                if position_symbol == symbol:
                    return position
                else:
                    continue
            
            return None

        except Exception as e:
            logger.error(f"GMXPositionController - Failed to get open position for symbol {symbol}. Error: {e}", exc_info=True)
            return None

    def is_already_position_open(self) -> bool:
        try:
            address = self.config.user_wallet_address
            positions = GetOpenPositions(config=self.config, address=address).get_data()
            if len(positions) > 0:
                return True
            else:
                return False

        except KeyError as ke:
            logger.error(f"GMXPositionController - KeyError while checking if position is open: {ke}")
            return None
        except TypeError as te:
            logger.error(f"GMXPositionController - TypeError while checking if position is open: {te}")
            return None
        except Exception as e:
            logger.error(f"GMXPositionController - Error while checking if position is open: {e}", exc_info=True)
            return None
    
    def get_position_object(self, opportunity: dict, is_long: bool, size_usd: float) -> dict:
        try:
            symbol = opportunity['symbol']
            side = 'Long' if is_long else 'Short'
            liquidation_price = self.client.get_liquidation_price()

            return {
                'exchange': 'GMX',
                'symbol': symbol,
                'side': side,
                'size': size_usd,
                'liquidation_price': liquidation_price
            }
        
        except Exception as e:
            logger.error(f"GMXPositionController - Failed to generate position object for {symbol}. Error: {e}")
            return None

