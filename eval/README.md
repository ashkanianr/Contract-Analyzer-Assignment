# Evaluation

Run the compliance analyzer on the sample contract and compare to a reference JSON.

## Setup

From project root, with backend dependencies installed and `GOOGLE_API_KEY` set:

```bash
set PYTHONPATH=.
python eval/run_eval.py
```

## What it does

1. Loads `Sample Contract.pdf` and the reference `eval/reference/sample_contract_expected.json`.
2. Runs the full pipeline (parse → preprocess → compliance analyzer).
3. **Schema check**: Validates output with Pydantic (PASS/FAIL).
4. **State comparison**: Compares `compliance_state` for each of the 5 questions to the reference; reports match count (e.g. 4/5).

Exit code 0 if schema passes and state match count ≥ 3; otherwise 1.

## Reference file

Create or edit `eval/reference/sample_contract_expected.json`. It must contain an array of 5 objects (or an object with `"items"`: array of 5) with fields: `compliance_question`, `compliance_state`, `relevant_quotes`, `rationale`. You can generate it by running the analyzer once on the sample contract and saving the output, or by hand-authoring from the contract.
