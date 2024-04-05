import asyncio
from typing import Type, Dict

import streamlit as st

from pyinjective.async_client import AsyncClient
from pyinjective.core.network import Network

from injective_market import _get_markets_and_tokens
from injective_query_executor import PythonSDKInjectiveQueryExecutor

from datetime import datetime
import inspect
import pkgutil
import importlib
from streamlit_pages.streamlite_page import StreamlitPage


def discover_pages() -> Dict[str, Type[StreamlitPage]]:
    # Define the path to the streamlit_pages directory
    path = 'streamlit_pages'

    # Initialize the dictionary
    pages_dict = {}

    # Iterate over all the Python files in the directory
    for (_, name, _) in pkgutil.iter_modules([path]):
        # Import the module
        module = importlib.import_module(f'{path}.{name}')

        # Iterate over all the members of the module
        for _, member in inspect.getmembers(module):
            # Check if the member is a class, and if it is a subclass of StreamlitPage
            if inspect.isclass(member) and issubclass(member, StreamlitPage) and member is not StreamlitPage:
                # Add it to the dictionary with the title as the key
                pages_dict[member.title()] = member

    return pages_dict


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    network = Network.mainnet()
    client = AsyncClient(
        network=network,
    )
    query_executor = PythonSDKInjectiveQueryExecutor(sdk_client=client)
    (
        tokens_map,
        token_symbol_and_denom_map,
        spot_markets_map,
        spot_market_id_to_trading_pair,
        derivative_markets_map,
        derivative_market_id_to_trading_pair
    ) = loop.run_until_complete(_get_markets_and_tokens(query_executor))

    pages_classes = discover_pages()
    pages = {title: page_class(loop=loop,
                               client=client,
                               token_symbol_and_denom_map=token_symbol_and_denom_map,
                               tokens_map=tokens_map,
                               derivative_markets_map=derivative_markets_map) for title, page_class in
             pages_classes.items()}
    pages_options = tuple(pages.keys())

    # Create a button in the sidebar
    refresh_button = st.sidebar.button('Refresh Calculations')
    last_updated_text = st.sidebar.empty()

    # Create a selectbox in the sidebar
    option = st.sidebar.selectbox(
        'Select Page',
        pages_options
    )

    if getattr(pages[option], 'days_lookback_enabled', False):
        days_lookback = st.sidebar.select_slider('Days Lookback', options=[1, 7, 30, 90], value=7)
    else:
        days_lookback = None

    if refresh_button:
        pages[option].refresh_page(days_lookback=days_lookback)
    else:
        pages[option].display_page(days_lookback=days_lookback)
    last_updated_text.text(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")