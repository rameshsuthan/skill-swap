"""Explicitly reset fictional profiles; preserves proposals and advances revision."""

import json

from skillswap.repository import Repository
from skillswap.settings import ROOT, Settings

r = Repository(Settings().domain_db)
print(
    f"Seeded {r.seed_demo(json.loads((ROOT / 'data/demo_cohort.json').read_text()))} fictional profiles."
)
