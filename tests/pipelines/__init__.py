"""Tests for sub-pipelines.

One sub-package per pipeline (data_quality/, data_cleaning/, ...).
Conventions:

- Each test module is named ``test_<thing>.py`` so pytest discovers it.
- Tests should call node functions directly from ``nodes.py``; do NOT
  import Kedro to test pure-Python nodes.
- Fixtures shared across pipelines live in ``tests/conftest.py``.
"""
