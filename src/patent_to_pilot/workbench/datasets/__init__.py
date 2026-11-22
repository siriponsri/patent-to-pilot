"""PTP-2026-11-21/G02 dataset contracts: metadata registry, read-only schema inspection, runtime adapters.

Runtime code imports ``registry``, ``inspect``, ``loaders`` and ``adapters``. Labels live only in
``evaluator`` (evaluator-side). No dataset is downloaded or opened by importing this package.
"""
