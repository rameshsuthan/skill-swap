import argparse

from skillswap.repository import Repository
from skillswap.scenarios import memory_alternatives
from skillswap.settings import Settings

p = argparse.ArgumentParser()
p.add_argument("scenario", choices=["remove-nina-window", "timezone-change", "memory-alternatives"])
a = p.parse_args()
r = Repository(Settings().domain_db)
if a.scenario == "remove-nina-window":
    r.remove_availability("nina", "2026-10-27")
elif a.scenario == "memory-alternatives":
    memory_alternatives(r)
else:
    r.update_profile("maya", timezone="America/New_York", availability=[])
print("Fictional dataset revised; staged proposals require fresh approval.")
