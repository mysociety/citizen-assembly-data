from enum import Enum
from pathlib import Path
from typing import Iterator

import pandas as pd
from pydantic import BaseModel, Field, computed_field, model_validator
from ruamel.yaml import YAML
from slugify import slugify
from typing_extensions import Self


class YamlModel(BaseModel):
    @classmethod
    def from_df(cls, df: pd.DataFrame) -> Iterator[Self]:
        """
        Create a list of models from a dataframe
        """
        for row in df.to_dict(orient="records"):
            yield cls(**row)

    def to_yaml(self, parent_path: Path, unique_id_field: str = "unique_id"):
        dest = parent_path / (getattr(self, unique_id_field) + ".yaml")
        dest.parent.mkdir(parents=True, exist_ok=True)
        yaml = YAML()
        data = self.model_dump()
        data.pop(unique_id_field)
        with dest.open("w") as f:
            yaml.dump(data, f)

    class Config:
        use_enum_values = True


OptionalStr = str | None


class AuthorityType(str, Enum):
    LOCAL_AUTHORITY = "Local Authority"
    NATION = "Nation"
    OTHER = "Other"
    NHS = "NHS"


class AssemblyStatus(str, Enum):
    FINISHED = "Finished"
    ONGOING = "Ongoing"
    FUTURE = "Future"


class AssemblyInfo(YamlModel):
    authority_type: AuthorityType
    local_authority_code: OptionalStr
    org_name: str
    report_url: OptionalStr
    report_pdf_url: str
    faciliator: OptionalStr
    assembly_status: AssemblyStatus
    assembly_year: int
    number_participants: int | None
    assembly_description: str
    thematic_grouping: str
    source_notes: OptionalStr
    data_source: str | None = Field(..., description="The source of the data")

    @computed_field
    @property
    def unique_id(self) -> str:
        """
        Unique ID is a combination of a rough slug of the
        uthority name, assembly year, and thematic_grouping
        """
        if self.authority_type == AuthorityType.LOCAL_AUTHORITY:
            org_slug = f"la-{self.local_authority_code}"
        elif self.authority_type == AuthorityType.NATION:
            org_slug = f"n-{slugify(self.org_name)}"
        else:
            org_slug = f"org-{slugify(self.org_name)}"

        return (
            f"{org_slug}-{self.assembly_year}-{slugify(self.thematic_grouping)}".lower()
        )

    @model_validator(mode="after")
    def check_local_authority_details(self):
        if self.authority_type == AuthorityType.LOCAL_AUTHORITY:
            if not self.local_authority_code:
                raise ValueError("local_authority_code must be present for LAs.")
        return self
