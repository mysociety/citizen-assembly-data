from pathlib import Path

import pandas as pd
from ruamel.yaml import YAML

from .models import AssemblyInfo

data_folder = Path("data", "raw", "assemblies")
dest_folder = Path("data", "packages", "citizens_assembly_register")


def load_items():
    yaml = YAML()
    items: list[AssemblyInfo] = []
    for file in data_folder.glob("*.yaml"):
        data = yaml.load(file)
        item = AssemblyInfo.model_validate(data)
        items.append(item)

    df = pd.DataFrame.from_records([item.model_dump() for item in items])
    df.to_parquet(dest_folder / "register.parquet")
