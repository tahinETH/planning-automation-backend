# Backend regression contract

These requirements apply only to AI agents changing the Planning Automation
backend repository. They do not apply to sibling projects or global agent
behavior. The shipped application code and reviewed business rules are
authoritative; never loosen a test merely to make changed behavior pass.

## Definition of done

1. Add or update a meaningful regression example for every behavior, calculation,
   permission, persistence, import, planning, report or delivery change. A defect
   fix must retain a test that fails without the fix.
2. Run the relevant focused tests while developing and `python -m pytest -q`
   before completion, using the repository virtual environment when available.
3. When this repository is inside the combined planning workspace and
   `../scripts/test_change_impact.py` exists, select and run the connected areas
   with that tool and validate the map after changing test or source boundaries.
4. Ravi behavior changes must keep `app/ravi/knowledge/topics.json` and its
   regression coverage synchronized with the shipped implementation.
5. Report the checks run and their outcomes, failures believed to be unrelated,
   and any staging or live-model acceptance that remains unverified. Do not claim
   completion while a required check is omitted without clearly stating why.
