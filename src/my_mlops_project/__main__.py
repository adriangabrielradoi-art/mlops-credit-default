"""Entry point for ``python -m my_mlops_project``.

Kedro projects expose a CLI by delegating to ``kedro.framework.cli``.
Running ``python -m my_mlops_project`` from the project root is
equivalent to ``kedro run`` invoked from inside this package, so a user
who has the package installed but no global ``kedro`` shim can still
trigger pipelines.

TODO(week_3_lab): wire this to ``kedro.framework.cli.main`` once Kedro
is fully installed and the project is bootstrapped with
``kedro new`` / ``kedro install``. For the moment this is a placeholder
that prints a friendly hint.
"""

# Standard-library import; ``sys.exit`` lets us return a non-zero exit
# code if the entry point is invoked before Kedro is wired up.
import sys


def main() -> None:
    """Print a hint and exit non-zero.

    This is the placeholder entry point. Once Kedro is wired in, replace
    the body with::

        from kedro.framework.cli import main as kedro_main
        kedro_main()

    Args:
        (none)

    Returns:
        None. Side effect: writes a hint to stderr and exits with
        status 1 so CI catches accidental invocations of the unwired
        entry point.
    """
    # Write to stderr so this message does not pollute stdout pipelines
    # that may capture program output downstream.
    sys.stderr.write(
        "my_mlops_project entry point is not yet wired to Kedro.\n"
        "See src/my_mlops_project/__main__.py TODO.\n"
    )
    # Exit code 1 communicates "intentional failure" to shell scripts.
    sys.exit(1)


# Standard guard so ``python -m my_mlops_project`` runs ``main()`` while
# ``import my_mlops_project.__main__`` does nothing.
if __name__ == "__main__":
    main()
