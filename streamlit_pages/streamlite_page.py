from abc import ABC, abstractmethod


class StreamlitPage(ABC):
    def __init__(self, *args, **kwargs):
        ...

    @abstractmethod
    def display_page(self, *args, **kwargs):
        ...

    @abstractmethod
    def refresh_page(self, *args, **kwargs):
        ...

    @classmethod
    @abstractmethod
    def title(cls):
        ...
