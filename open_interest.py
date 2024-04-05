from decimal import Decimal
from typing import List, Dict
from dataclasses import dataclass
from pyinjective.async_client import AsyncClient


@dataclass
class PositionsForMarket:
    longs: List[Dict]
    shorts: List[Dict]


async def get_open_interest(client: AsyncClient, derivative_markets_map):
    positions = await client.fetch_chain_positions()
    positions_for_market = dict()
    open_interest = dict()
    derivative_markets = await client.all_derivative_markets()
    prices = {}
    for position in positions['state']:
        market_id = position['marketId']
        if market_id not in prices:
            market = derivative_markets.get(market_id)
            if not market:
                print(f"Market not found for market_id: {market_id}")
                continue
            price = await client.fetch_oracle_price(market.oracle_base, market.oracle_quote, market.oracle_type)
            prices[market_id] = Decimal(price['price'])

        if market_id not in positions_for_market:
            positions_for_market[market_id] = PositionsForMarket([], [])
        if position['position']['isLong']:
            positions_for_market[market_id].longs.append(position)
        else:
            positions_for_market[market_id].shorts.append(position)

    def notional_from_position(position, derivative_market):
        quantity_scaled = derivative_market.quantity_from_special_chain_format(Decimal(position['quantity']))
        # price_scaled = derivative_market.price_from_special_chain_format(Decimal(position['entryPrice']))
        # return quantity_scaled * price_scaled
        return quantity_scaled * prices[derivative_market.market_id]

    for market_id, positions in positions_for_market.items():
        derivative_market = derivative_markets_map.get(market_id)
        if not derivative_market:
            print(f"Market not found for market_id: {market_id}")
            continue
        total_long_notionals = sum(notional_from_position(pos['position'], derivative_market) for pos in positions.longs)
        total_short_notionals = sum(notional_from_position(pos['position'], derivative_market) for pos in positions.shorts)
        open_interest[derivative_market.trading_pair()] = (
            total_long_notionals,
            total_short_notionals
        )
    return open_interest
