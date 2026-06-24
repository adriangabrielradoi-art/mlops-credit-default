"""Node functions for the `data_quality` pipeline.

Great Expectations (GE 1.x) data unit testing for the UCI Credit Card Default
dataset. Two pure-Python nodes:

1. ``validate_credit_data`` — builds a GE suite from parameters, runs it against
   the raw frame, and returns the (unchanged) data plus a tidy results report.
2. ``gate_on_quality`` — inspects the report and raises if any expectation
   failed, halting the pipeline ("fail loud" before bad data reaches cleaning).

Splitting validate from gate means the report is ALWAYS saved (even on failure),
unlike a single node that raises mid-execution. Reference pattern:
`_knowledge/great_expectations_data_validation.py` and the Week-1 lab
`data_unit_tests` Kedro node.

Class reference: Week 1.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.core.validation_definition import ValidationDefinition


def _build_suite(context, params: dict[str, Any]):
    """Assemble a GE Expectation Suite from the ``data_quality`` parameters.

    The suite encodes what a *valid* batch looks like: a fixed column count,
    numeric bounds, allowed category codes, and non-null key columns. It is
    parameter-driven so the rules live in ``parameters.yml``, not in code.

    Args:
        context: An active (ephemeral) GE Data Context.
        params: The ``data_quality`` params block (expected_column_count,
            ranges, value_sets, not_null).

    Returns:
        A saved ``ExpectationSuite`` ready to pair with a batch.
    """
    # Fresh named suite registered with the context.
    suite = context.suites.add(gx.ExpectationSuite(name="credit_quality_suite"))

    # Table-level: the dataset must have exactly the expected number of columns
    # (a dropped/added column is a classic broken-batch signal).
    suite.add_expectation(
        gxe.ExpectTableColumnCountToEqual(value=params["expected_column_count"])
    )

    # Numeric sanity bounds (row-level): every value must fall in [min, max].
    for column, bounds in params["ranges"].items():
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeBetween(
                column=column,
                min_value=bounds.get("min"),
                max_value=bounds.get("max"),  # None => no upper bound
            )
        )

    # Categorical value sets (row-level): every value must be an allowed code.
    for column, allowed in params["value_sets"].items():
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeInSet(column=column, value_set=allowed)
        )

    # Key columns must never be null.
    for column in params["not_null"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    suite.save()
    return suite


def validate_credit_data(
    raw_data: pd.DataFrame, params: dict[str, Any]
) -> tuple[pd.DataFrame, dict]:
    """Run the GE suite against the raw data and return the data + a report.

    The data is passed through UNCHANGED (this is validation, not cleaning) so
    the downstream ``validated_data`` is the raw frame in a typed parquet form.

    Args:
        raw_data: The raw credit DataFrame (loaded from the .xls with real-name
            headers).
        params: The ``data_quality`` params block.

    Returns:
        A tuple ``(validated_data, ge_report)`` where ``validated_data`` is the
        unchanged frame and ``ge_report`` is a JSON-serialisable dict with the
        overall success flag and one entry per expectation.
    """
    # An ephemeral context keeps GE fully in-memory — nothing written to disk.
    context = gx.get_context(mode="ephemeral")
    suite = _build_suite(context, params)

    # Wire the run: pandas source -> dataframe asset -> whole-frame batch.
    data_source = context.data_sources.add_pandas("credit_source")
    data_asset = data_source.add_dataframe_asset("credit_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("credit_batch")

    # A validation definition pairs the batch with the suite — the runnable unit.
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(name="credit_validation", data=batch_definition, suite=suite)
    )

    # Execute: the DataFrame is supplied at run time as a batch parameter.
    results = validation_definition.run(batch_parameters={"dataframe": raw_data})

    # Flatten the GE result object into a tidy, JSON-serialisable report.
    payload = results.to_json_dict()
    rows = []
    for result in payload.get("results", []):
        config = result.get("expectation_config", {})
        kwargs = config.get("kwargs", {})
        rows.append(
            {
                "expectation": config.get("type"),
                "column": kwargs.get("column", ""),
                "success": bool(result.get("success")),
            }
        )
    ge_report = {
        "success": bool(results.success),
        "n_expectations": len(rows),
        "n_failed": sum(1 for r in rows if not r["success"]),
        "results": rows,
    }
    return raw_data, ge_report


def gate_on_quality(ge_report: dict) -> None:
    """Halt the pipeline if any data-quality expectation failed.

    The report has already been saved by the time this runs, so failures are
    inspectable in ``data/08_reporting/ge_report.json`` even when we raise.

    Args:
        ge_report: The report dict from ``validate_credit_data``.

    Raises:
        ValueError: If one or more expectations failed (a broken batch).
    """
    if not ge_report["success"]:
        # Collect the names of the failed expectations for a useful message.
        failures = [
            f"{r['expectation']}({r['column']})"
            for r in ge_report["results"]
            if not r["success"]
        ]
        raise ValueError(
            "Data quality gate FAILED — "
            f"{ge_report['n_failed']}/{ge_report['n_expectations']} expectations "
            f"failed: {failures}. Pipeline halted before cleaning."
        )

    # All good — the batch is trustworthy.
    print(
        f"Data quality gate PASSED — all {ge_report['n_expectations']} "
        "expectations met."
    )
