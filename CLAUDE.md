## Testing Policy
- Every bug fix or feature must be accompanied by at least one unit test that would have caught the bug or verifies the new behavior
- Backend: add tests to the relevant file in backend/tests/ and run with:
    python -m pytest backend/tests/<test_file>.py -v
- Flutter: add widget/unit tests in mobile_flutter/test/ and run with:
    cd mobile_flutter && flutter test
- Run the full suite (pytest backend/tests/) before committing if changes touch shared code (models, services, routers)
- Do not commit if any tests fail — fix the failure first
- For Flutter UI changes, at minimum verify with flutter analyze before committing; note any behaviors that can only be confirmed visually
