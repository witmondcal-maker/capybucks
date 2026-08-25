# API reference

Public names re-exported from `import capybucks as cb`. Identifiers stay
in English in every locale. Docstrings below are the contract.

```{eval-rst}
.. autofunction:: capybucks.download

.. autoclass:: capybucks.Ticker
   :members:
   :undoc-members:
   :show-inheritance:

.. autoexception:: capybucks.CapybucksError
   :show-inheritance:

.. autoexception:: capybucks.ProviderError
   :show-inheritance:

.. autoexception:: capybucks.RateLimitError
   :show-inheritance:

.. autoexception:: capybucks.MissingAPIKey
   :show-inheritance:

.. autoexception:: capybucks.SymbolNotFound
   :show-inheritance:

.. autoexception:: capybucks.ProviderNotFound
   :show-inheritance:

.. autoexception:: capybucks.NoProviderError
   :show-inheritance:

.. autoexception:: capybucks.MultiDownloadError
   :show-inheritance:

.. autoexception:: capybucks.StreamingNotSupportedError
   :show-inheritance:

.. automodule:: capybucks.ta
   :members:

.. automodule:: capybucks.calendars
   :members:

.. autoclass:: capybucks.async_api.AsyncTicker
   :members:
   :undoc-members:
```
