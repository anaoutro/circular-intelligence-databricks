# Contributing

Use synthetic examples and explain changes to business rules before changing expected results.

1. Create a branch from main.
2. Run `python scripts/check_repository.py` and `python -m unittest discover -s tests -v`.
3. If policy changes, regenerate the fixture with python scripts/generate_data.py and inspect the result diff. If the notebook changes, execute it in Databricks and verify replay behavior.
4. Update documentation and record only checks actually executed in the pull request.

The local Python model is a reference implementation; it does not execute PySpark or Delta. Platform execution is required to validate platform behavior.
