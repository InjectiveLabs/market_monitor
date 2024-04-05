import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from pyinjective.async_client import AsyncClient
from pyinjective.core.network import Network

from injective_market import _get_markets_and_tokens
from injective_query_executor import PythonSDKInjectiveQueryExecutor
from mongodb import query_mongodb


def _scale_balance(row, tokens_map):
    if row['depositDenom'] != "":
        decimals = getattr(tokens_map.get(row['depositDenom'], {}), "decimals", 0)
        return float(row['balance']) / 10 ** decimals
    return 0


def _scale_disbursed(row, tokens_map):
    if row['disbursedAmount'] != "":
        decimals = getattr(tokens_map.get(row['disbursedDenom'], {}), "decimals", 0)
        return float(row['disbursedAmount']) / 10 ** decimals
    return 0


def _transform_ts(ts):
    if ts:
        ts_seconds = int(ts) / 1e6
        dt = datetime.fromtimestamp(ts_seconds)
        return dt.strftime("%a %b %d %Y %H:%M:%S GMT%z")
    return 0


async def get_insurance_funds(client: AsyncClient):
    insurance_funds = await client.fetch_insurance_funds()
    return insurance_funds


async def get_redemptions(client: AsyncClient):
    # redeemer = "inj14au322k9munkmx5wrchz9q30juf5wjgz2cfqku"
    # redemption_denom = "share4"
    # status = "disbursed"
    redeemer = None
    redemption_denom = None
    status = None
    insurance_redemptions = await client.fetch_redemptions(address=redeemer,
                                                           denom=redemption_denom,
                                                           status=status)
    return insurance_redemptions


async def get_liquidation_trades(days=None, market_id=None):
    days = days or 1
    today = datetime.now()
    end_dt = datetime(today.year, today.month, today.day, 23, 59, 59)
    start_dt = datetime(today.year, today.month, today.day, 0, 0, 0) - timedelta(days=days)
    executed_at_block = {"executedAt": {
        "$gte": start_dt,
        "$lte": end_dt
    }}

    market_id_block = {}
    if market_id:
        market_id_block = {"marketId": market_id}

    pipeline = [
        {
            "$match": dict(
                list({"isLiquidation": True}.items()) +
                list(executed_at_block.items()) +
                list(market_id_block.items()))
        },  # replace with your match condition
        # {"$project": {}},  # replace with your project condition
        # {"$unwind": ""},  # replace with your unwind condition
        # {"$set": {}},  # replace with your set condition
        # {"$project": {}},  # replace with your project condition
    ]

    return await query_mongodb(pipeline=pipeline)
