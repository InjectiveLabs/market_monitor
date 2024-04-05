from open_interest import get_open_interest
from streamlit_pages.streamlite_page import StreamlitPage
import asyncio
import streamlit as st
import pandas as pd
from pyinjective.async_client import AsyncClient


class InsuranceFundsPage(StreamlitPage):
    def __init__(self, loop: asyncio.AbstractEventLoop, client: AsyncClient, **kwargs):
        super().__init__(**kwargs)
        self.event_loop = loop
        self.client = client
        self.token_symbol_and_denom_map = kwargs.get('token_symbol_and_denom_map')
        self.tokens_map = kwargs.get('tokens_map')
        self.derivative_markets_map = kwargs.get('derivative_markets_map')

    def display_page(self, *args, **kwargs):
        st.empty()
        open_interest = self.event_loop.run_until_complete(get_open_interest(self.client, self.derivative_markets_map))

        open_interest_df = pd.DataFrame(
            [{'Trading Pair': k, 'Longs Notional': v[0], 'Shorts Notional': v[1]} for k, v in open_interest.items()])

        st.write(open_interest_df)

    def refresh_page(self, *args, **kwargs):
        self.display_page(*args, **kwargs)

    @classmethod
    def title(cls):
        return 'Open Interest'
