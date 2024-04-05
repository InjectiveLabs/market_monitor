from liquidations import get_insurance_funds, _scale_balance
from streamlit_pages.streamlite_page import StreamlitPage
import asyncio
import time
import streamlit as st
import pandas as pd
from pyinjective.async_client import AsyncClient


class InsuranceFundsPage(StreamlitPage):
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
        insurance_funds = self.event_loop.run_until_complete(get_insurance_funds(self.client))

        insurance_funds_df = pd.DataFrame(insurance_funds['funds'])
        insurance_funds_df.insert(3, 'depositDenomName', insurance_funds_df['depositDenom'].map(
            self.token_symbol_and_denom_map.inv))
        insurance_funds_df['balance'] = insurance_funds_df.apply(lambda row: _scale_balance(row, self.tokens_map), axis=1)
        st.dataframe(insurance_funds_df, use_container_width=True)

    def refresh_page(self, *args, **kwargs):
        self.display_page(*args, **kwargs)

    @classmethod
    def title(cls):
        return 'Insurance Funds'
