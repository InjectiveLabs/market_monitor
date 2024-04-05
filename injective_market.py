from typing import Dict, Mapping, Tuple
from bidict import bidict
from pyinjective.core.market import DerivativeMarket, SpotMarket
from pyinjective.core.token import Token
from dataclasses import dataclass
from decimal import Decimal

from injective_query_executor import PythonSDKInjectiveQueryExecutor


@dataclass(frozen=True)
class InjectiveToken:
    unique_symbol: str
    native_token: Token

    @property
    def denom(self) -> str:
        return self.native_token.denom

    @property
    def symbol(self) -> str:
        return self.native_token.symbol

    @property
    def name(self) -> str:
        return self.native_token.name

    @property
    def decimals(self) -> int:
        return self.native_token.decimals

    def value_from_chain_format(self, chain_value: Decimal) -> Decimal:
        scaler = Decimal(f"1e{-self.decimals}")
        return chain_value * scaler

    def value_from_special_chain_format(self, chain_value: Decimal) -> Decimal:
        scaler = Decimal(f"1e{-self.decimals - 18}")
        return chain_value * scaler


@dataclass(frozen=True)
class InjectiveSpotMarket:
    market_id: str
    base_token: InjectiveToken
    quote_token: InjectiveToken
    native_market: SpotMarket

    def trading_pair(self):
        return f"{self.base_token.unique_symbol}-{self.quote_token.unique_symbol}"

    def quantity_from_chain_format(self, chain_quantity: Decimal) -> Decimal:
        return self.base_token.value_from_chain_format(chain_value=chain_quantity)

    def price_from_chain_format(self, chain_price: Decimal) -> Decimal:
        scaler = Decimal(f"1e{self.base_token.decimals - self.quote_token.decimals}")
        return chain_price * scaler

    def quantity_from_special_chain_format(self, chain_quantity: Decimal) -> Decimal:
        quantity = chain_quantity / Decimal("1e18")
        return self.quantity_from_chain_format(chain_quantity=quantity)

    def price_from_special_chain_format(self, chain_price: Decimal) -> Decimal:
        price = chain_price / Decimal("1e18")
        return self.price_from_chain_format(chain_price=price)

    def min_price_tick_size(self) -> Decimal:
        return self.price_from_chain_format(chain_price=self.native_market.min_price_tick_size)

    def min_quantity_tick_size(self) -> Decimal:
        return self.quantity_from_chain_format(chain_quantity=self.native_market.min_quantity_tick_size)

    def maker_fee_rate(self) -> Decimal:
        return self.native_market.maker_fee_rate

    def taker_fee_rate(self) -> Decimal:
        return self.native_market.taker_fee_rate


@dataclass(frozen=True)
class InjectiveDerivativeMarket:
    market_id: str
    quote_token: InjectiveToken
    native_market: DerivativeMarket

    def base_token_symbol(self):
        ticker_base, _ = self.native_market.ticker.split("/")
        return ticker_base

    def trading_pair(self):
        ticker_base, _ = self.native_market.ticker.split("/")
        return f"{ticker_base}-{self.quote_token.unique_symbol}"

    def quantity_from_chain_format(self, chain_quantity: Decimal) -> Decimal:
        return chain_quantity

    def price_from_chain_format(self, chain_price: Decimal) -> Decimal:
        scaler = Decimal(f"1e{-self.quote_token.decimals}")
        return chain_price * scaler

    def quantity_from_special_chain_format(self, chain_quantity: Decimal) -> Decimal:
        quantity = chain_quantity / Decimal("1e18")
        return self.quantity_from_chain_format(chain_quantity=quantity)

    def price_from_special_chain_format(self, chain_price: Decimal) -> Decimal:
        price = chain_price / Decimal("1e18")
        return self.price_from_chain_format(chain_price=price)

    def min_price_tick_size(self) -> Decimal:
        return self.price_from_chain_format(chain_price=self.native_market.min_price_tick_size)

    def min_quantity_tick_size(self) -> Decimal:
        return self.quantity_from_chain_format(chain_quantity=self.native_market.min_quantity_tick_size)

    def maker_fee_rate(self) -> Decimal:
        return self.native_market.maker_fee_rate

    def taker_fee_rate(self) -> Decimal:
        return self.native_market.taker_fee_rate

    def oracle_base(self) -> str:
        return self.native_market.oracle_base

    def oracle_quote(self) -> str:
        return self.native_market.oracle_quote

    def oracle_type(self) -> str:
        return self.native_market.oracle_type


async def _get_markets_and_tokens(
        query_executor: PythonSDKInjectiveQueryExecutor
) -> Tuple[
    Dict[str, InjectiveToken],
    Mapping[str, str],
    Dict[str, InjectiveSpotMarket],
    Mapping[str, str],
    Dict[str, InjectiveDerivativeMarket],
    Mapping[str, str]
]:
    tokens_map = {}
    token_symbol_and_denom_map = bidict()
    spot_markets_map = {}
    derivative_markets_map = {}
    spot_market_id_to_trading_pair = bidict()
    derivative_market_id_to_trading_pair = bidict()

    spot_markets: Dict[str, SpotMarket] = await query_executor.spot_markets()
    derivative_markets: Dict[str, DerivativeMarket] = await query_executor.derivative_markets()
    tokens: Dict[str, Token] = await query_executor.tokens()

    for unique_symbol, injective_native_token in tokens.items():
        token = InjectiveToken(
            unique_symbol=unique_symbol,
            native_token=injective_native_token
        )
        tokens_map[token.denom] = token
        token_symbol_and_denom_map[unique_symbol] = token.denom

    for market in spot_markets.values():
        try:
            parsed_market = InjectiveSpotMarket(
                market_id=market.id,
                base_token=tokens_map[market.base_token.denom],
                quote_token=tokens_map[market.quote_token.denom],
                native_market=market
            )

            spot_market_id_to_trading_pair[parsed_market.market_id] = parsed_market.trading_pair()
            spot_markets_map[parsed_market.market_id] = parsed_market
        except KeyError:
            self.logger().debug(f"The spot market {market.id} will be excluded because it could not "
                                f"be parsed ({market})")
            continue

    for market in derivative_markets.values():
        try:
            parsed_market = InjectiveDerivativeMarket(
                market_id=market.id,
                quote_token=tokens_map[market.quote_token.denom],
                native_market=market,
            )

            if parsed_market.trading_pair() in derivative_market_id_to_trading_pair.inverse:
                self.logger().debug(
                    f"The derivative market {market.id} will be excluded because there is other"
                    f" market with trading pair {parsed_market.trading_pair()} ({market})")
                continue
            derivative_market_id_to_trading_pair[parsed_market.market_id] = parsed_market.trading_pair()
            derivative_markets_map[parsed_market.market_id] = parsed_market
        except KeyError:
            self.logger().debug(f"The derivative market {market.id} will be excluded because it could"
                                f" not be parsed ({market})")
            continue

    return (
        tokens_map,
        token_symbol_and_denom_map,
        spot_markets_map,
        spot_market_id_to_trading_pair,
        derivative_markets_map,
        derivative_market_id_to_trading_pair
    )
