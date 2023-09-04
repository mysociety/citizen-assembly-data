from pathlib import Path

import pandas as pd

from .models import AssemblyInfo

data_folder = Path("data", "raw", "assemblies")
dest_folder = Path("data", "packages", "citizens_assembly_register")


def get_items():
    for file in data_folder.glob("*.yaml"):
        yield AssemblyInfo.from_yaml(file)


def load_items():
    df = pd.DataFrame.from_records([item.model_dump() for item in get_items()])
    df.to_parquet(dest_folder / "register.parquet")
