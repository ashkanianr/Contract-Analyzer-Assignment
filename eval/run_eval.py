"""
Evaluation script: run pipeline on golden PDF, compare to reference JSON.
Reports: schema pass (Y/N), state match count (e.g. 4/5).
Run from project root with PYTHONPATH=. (e.g. set PYTHONPATH=. && python eval/run_eval.py).
"""
import json
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.compliance.analyzer import run_compliance_analysis
from backend.compliance.schema import ComplianceResult
from backend.parsing import parse_pdf, prepare_for_analysis


def main():
    sample_pdf = PROJECT_ROOT / "Sample Contract.pdf"
    reference_path = PROJECT_ROOT / "eval" / "reference" / "sample_contract_expected.json"
    if not sample_pdf.exists():
        print("ERROR: Sample Contract.pdf not found at", sample_pdf)
        sys.exit(1)
    if not reference_path.exists():
        print("ERROR: Reference JSON not found at", reference_path)
        sys.exit(1)

    print("Loading reference...")
    with open(reference_path, encoding="utf-8") as f:
        ref_data = json.load(f)
    ref_items = ref_data.get("items", ref_data) if isinstance(ref_data, dict) else ref_data
    if len(ref_items) != 5:
        print("ERROR: Reference must have 5 items")
        sys.exit(1)

    print("Parsing PDF...")
    full_text, page_count = parse_pdf(sample_pdf)
    prepared, _ = prepare_for_analysis(full_text)
    print(f"Prepared text length: {len(prepared)} chars (~{len(prepared)//4} tokens)")

    print("Running compliance analysis...")
    try:
        result = run_compliance_analysis(prepared)
    except Exception as e:
        print("SCHEMA: FAIL –", e)
        sys.exit(1)

    # Schema check: already passed if we got ComplianceResult
    print("SCHEMA: PASS")

    # State comparison
    model_items = result.items
    matches = 0
    for i in range(5):
        ref_state = (ref_items[i].get("compliance_state") or "").strip()
        model_state = model_items[i].compliance_state.value
        if ref_state.lower() == model_state.lower():
            matches += 1
            print(f"  Q{i+1}: MATCH ({model_state})")
        else:
            print(f"  Q{i+1}: MISMATCH ref={ref_state} model={model_state}")
    print(f"STATE MATCH: {matches}/5")
    sys.exit(0 if matches >= 3 else 1)


if __name__ == "__main__":
    main()
