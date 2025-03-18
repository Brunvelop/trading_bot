import os
import time
import logging
from typing import Dict, List, Optional, Any, Union, Tuple

import ccxt
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

class BaseExchangeAPI:
    """
    Base class for interacting with cryptocurrency exchange APIs.
    
    This class provides a unified interface for various exchange operations
    like creating orders, fetching prices, and managing account information.
    It uses the CCXT library to standardize interactions across different exchanges.
    """
    
    def __init__(self, exchange_id: str, api_key: str, api_secret: str, options: Dict[str, Any]):
        """
        Initialize the exchange API wrapper.
        
        Args:
            exchange_id: The CCXT exchange identifier (e.g., 'binance', 'kraken')
            api_key: Environment variable name containing the API key
            api_secret: Environment variable name containing the API secret
            options: Additional options to pass to the CCXT exchange constructor
        """
        self.exchange_id: str = exchange_id
        self.api_key: str = api_key
        self.api_secret: str = api_secret
        self.options: Dict[str, Any] = options
        self.exchange: Optional[ccxt.Exchange] = None
        self.logger = logging.getLogger(f"ExchangeAPI-{exchange_id}")
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Initialize the connection
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """
        Initialize the connection to the exchange API.
        This method is called during initialization and can be used to reconnect.
        """
        try:
            self.logger.info(f"Initializing connection to {self.exchange_id}")
            load_dotenv()  # Ensure environment variables are loaded
            
            # Get API credentials from environment variables
            api_key = os.getenv(self.api_key)
            api_secret = os.getenv(self.api_secret)
            
            if not api_key or not api_secret:
                self.logger.warning(f"Missing API credentials for {self.exchange_id}")
            
            # Create the exchange instance
            self.exchange = getattr(ccxt, self.exchange_id)({
                'apiKey': api_key,
                'secret': api_secret,
                **self.options
            })
            
            self.logger.info(f"Successfully connected to {self.exchange_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize connection to {self.exchange_id}: {str(e)}")
            raise
    
    def _ensure_connection(self) -> ccxt.Exchange:
        """
        Ensure that the connection to the exchange is established.
        If not, attempt to initialize it.
        
        Returns:
            The CCXT exchange instance
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        if self.exchange is None:
            self._initialize_connection()
            
        if self.exchange is None:
            raise ConnectionError(f"Could not establish connection to {self.exchange_id}")
            
        return self.exchange
    
    def _execute_with_retry(self, operation: str, func, *args, **kwargs) -> Any:
        """
        Execute an API operation with retry logic.
        
        Args:
            operation: Name of the operation for logging
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            Exception: If all retries fail
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                self.logger.debug(f"Executing {operation} (attempt {retries + 1}/{self.max_retries})")
                return func(*args, **kwargs)
            except ccxt.NetworkError as e:
                retries += 1
                last_error = e
                self.logger.warning(f"Network error during {operation}: {str(e)}. Retrying in {self.retry_delay}s ({retries}/{self.max_retries})")
                time.sleep(self.retry_delay)
            except ccxt.ExchangeError as e:
                retries += 1
                last_error = e
                self.logger.warning(f"Exchange error during {operation}: {str(e)}. Retrying in {self.retry_delay}s ({retries}/{self.max_retries})")
                time.sleep(self.retry_delay)
            except Exception as e:
                # For other exceptions, don't retry
                self.logger.error(f"Error during {operation}: {str(e)}")
                raise
        
        self.logger.error(f"Failed to execute {operation} after {self.max_retries} attempts: {str(last_error)}")
        raise last_error

    def create_order(self, pair: str, order_type: str, side: str, amount: float, price: float, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Create a new order on the exchange.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            order_type: Type of order ('market', 'limit', etc.)
            side: Order side ('buy' or 'sell')
            amount: Amount to buy or sell
            price: Order price
            params: Additional parameters specific to the exchange
            
        Returns:
            Exchange response containing order details
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = f"create_{side}_{order_type}_order_{pair}"
        
        self.logger.info(f"Creating {side} {order_type} order for {amount} {pair} at price {price}")
        return self._execute_with_retry(
            operation,
            exchange.create_order,
            pair, order_type, side, amount, price, params
        )

    def get_latest_price(self, pair: str) -> float:
        """
        Get the latest price for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Latest price as a float
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = f"get_latest_price_{pair}"
        
        self.logger.info(f"Fetching latest price for {pair}")
        ticker = self._execute_with_retry(
            operation,
            exchange.fetch_ticker,
            pair
        )
        
        return ticker['last']

    def get_account_balance(self, currency: str) -> float:
        """
        Get the account balance for a specific currency.
        
        Args:
            currency: Currency code (e.g., 'BTC', 'USD')
            
        Returns:
            Account balance as a float
            
        Raises:
            Various exceptions depending on the error
            KeyError: If the currency is not found in the balance
        """
        exchange = self._ensure_connection()
        operation = "get_account_balance"
        
        self.logger.info(f"Fetching account balance for {currency}")
        try:
            balance = self._execute_with_retry(
                operation,
                exchange.fetch_balance
            )
            
            if currency not in balance['total']:
                self.logger.warning(f"Currency {currency} not found in balance")
                return 0.0
                
            return balance['total'][currency]
        except KeyError as e:
            self.logger.error(f"Currency {currency} not found in balance: {str(e)}")
            return 0.0

    def get_bars(self, pair: str, timeframe: str, limit: int) -> List[List[float]]:
        """
        Get OHLCV (Open, High, Low, Close, Volume) bars for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            timeframe: Timeframe for the bars (e.g., '1m', '1h', '1d')
            limit: Number of bars to retrieve
            
        Returns:
            List of OHLCV bars in reverse chronological order
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = f"get_bars_{pair}_{timeframe}"
        
        self.logger.info(f"Fetching {limit} {timeframe} bars for {pair}")
        bars = self._execute_with_retry(
            operation,
            exchange.fetch_ohlcv,
            pair, timeframe=timeframe, limit=limit
        )
        
        # Return bars in reverse chronological order (newest first)
        return bars[::-1]

    def get_order(self, order_id: str, symbol: str = '') -> Dict[str, Any]:
        """
        Get details of a specific order.
        
        Args:
            order_id: Order ID
            symbol: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Order details
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = f"get_order_{order_id}"
        
        self.logger.info(f"Fetching order {order_id} for {symbol}")
        return self._execute_with_retry(
            operation,
            exchange.fetch_order,
            order_id, symbol
        )

    def cancel_order(self, id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            id: Order ID
            symbol: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Cancellation result
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = f"cancel_order_{id}"
        
        self.logger.info(f"Cancelling order {id} for {symbol}")
        return self._execute_with_retry(
            operation,
            exchange.cancel_order,
            id, symbol
        )
    
    def fetch_trades(self, pair: str, since: Optional[int] = None, limit: Optional[int] = None, params: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        """
        Fetch recent trades for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            since: Timestamp in milliseconds to fetch trades from
            limit: Maximum number of trades to fetch
            params: Additional parameters specific to the exchange
            
        Returns:
            List of trades
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = f"fetch_trades_{pair}"
        
        self.logger.info(f"Fetching trades for {pair} (since: {since}, limit: {limit})")
        return self._execute_with_retry(
            operation,
            exchange.fetch_trades,
            pair, since, limit, params
        )
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get information about the exchange.
        
        Returns:
            Exchange information
            
        Raises:
            Various exceptions depending on the error
        """
        exchange = self._ensure_connection()
        operation = "get_exchange_info"
        
        self.logger.info(f"Fetching exchange information for {self.exchange_id}")
        return {
            'id': exchange.id,
            'name': exchange.name,
            'has': exchange.has,
            'timeframes': exchange.timeframes if hasattr(exchange, 'timeframes') else {},
            'rate_limits': exchange.rateLimit if hasattr(exchange, 'rateLimit') else None
        }


class KrakenAPI(BaseExchangeAPI):
    """
    API wrapper for the Kraken exchange.
    """
    
    def __init__(self):
        """
        Initialize the Kraken API wrapper.
        """
        super().__init__('kraken', 'KRAKEN_API_KEY', 'KRAKEN_API_SECRET', {
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })


class OKXAPI(BaseExchangeAPI):
    """
    API wrapper for the OKX exchange.
    """
    
    def __init__(self, api_key: str = 'OKX_API_KEY', api_secret: str = 'OKX_API_SECRET'):
        """
        Initialize the OKX API wrapper.
        
        Args:
            api_key: Environment variable name containing the API key
            api_secret: Environment variable name containing the API secret
        """
        super().__init__('okex', api_key, api_secret, options={
            'password': os.getenv('OKX_PASSWORD'),
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })


class BinanceAPI(BaseExchangeAPI):
    """
    API wrapper for the Binance exchange.
    """
    
    def __init__(self):
        """
        Initialize the Binance API wrapper.
        """
        super().__init__('binance', 'BINANCE_API_KEY', 'BINANCE_API_SECRET', {
            'enableRateLimit': True,
            'options':{
                'defaultType': 'spot',
            }
        })


class BitgetAPI(BaseExchangeAPI):
    """
    API wrapper for the Bitget exchange.
    """
    
    def __init__(self, api_key: str = 'BITGET_API_KEY', api_secret: str = 'BITGET_API_SECRET'):
        """
        Initialize the Bitget API wrapper.
        
        Args:
            api_key: Environment variable name containing the API key
            api_secret: Environment variable name containing the API secret
        """
        super().__init__('bitget', api_key, api_secret, options={
            'password': os.getenv('BITGET_API_PASSWORD')
        })
