import time

from liquidations import get_redemptions, _transform_ts, _scale_disbursed
from streamlit_pages.streamlite_page import StreamlitPage
import asyncio
import streamlit as st
import pandas as pd
from pyinjective.async_client import AsyncClient


class RedemptionsPage(StreamlitPage):
    def __init__(self,
                 loop: asyncio.AbstractEventLoop,
                 client: AsyncClient,
                 **kwargs):
        super().__init__(**kwargs)
        self.event_loop = loop
        self.client = client
        self.token_symbol_and_denom_map = kwargs.get('token_symbol_and_denom_map')
        self.tokens_map = kwargs.get('tokens_map')

    def display_page(self, *args, **kwargs):
        st.empty()
        redemptions = self.event_loop.run_until_complete(get_redemptions(self.client))
        redemptions_df = pd.DataFrame(redemptions['redemptionSchedules'])
        redemptions_df = redemptions_df.set_index('redemptionId')
        # pool_token_to_market_map = pd.Series(insurance_funds_df['marketTicker'].values,
        #                                      index=insurance_funds_df['poolTokenDenom']).to_dict()
        # redemptions_df.insert(6, 'poolMarketTicker', redemptions_df['redemptionDenom'].map(pool_token_to_market_map))
        redemptions_df.insert(8, 'disbursedTicker',
                              redemptions_df['disbursedDenom'].map(self.token_symbol_and_denom_map.inv))
        redemptions_df['claimableRedemptionTime'] = redemptions_df['claimableRedemptionTime'].apply(_transform_ts)
        redemptions_df['requestedAt'] = redemptions_df['requestedAt'].apply(_transform_ts)
        redemptions_df['disbursedAt'] = redemptions_df['disbursedAt'].apply(_transform_ts)
        redemptions_df['disbursedAmount'] = redemptions_df.apply(lambda row: _scale_disbursed(row, self.tokens_map),
                                                                 axis=1)
        days_lookback = kwargs.get('days_lookback')
        if days_lookback:
            start_date = pd.Timestamp.now() - pd.Timedelta(days=days_lookback)
            redemptions_df = redemptions_df[pd.to_datetime(redemptions_df['requestedAt']) >= start_date]
        st.dataframe(redemptions_df, use_container_width=True)

    def refresh_page(self, *args, **kwargs):
        self.display_page(*args, **kwargs)

    @classmethod
    def title(cls):
        return 'Redemptions'

    days_lookback_enabled = True
