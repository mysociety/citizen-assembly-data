from enum import Enum
from pathlib import Path

from data_common.helpers.url import Url
from pydantic import BaseModel, Field, computed_field, model_validator
from ruamel.yaml import YAML
from slugify import slugify
from typing_extensions import Self

from .reports import fetch_valid_pdf, is_valid_pdf_file


class YamlModel(BaseModel):
    @classmethod
    def from_yaml(cls, file: Path) -> Self:
        yaml = YAML(typ="safe")
        return cls.model_validate(yaml.load(file))

    class Config:
        use_enum_values = True


OptionalStr = str | None
OptionalUrl = Url | None


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
    url: OptionalUrl
    report_pdf_url: OptionalUrl
    faciliator: OptionalStr
    assembly_status: AssemblyStatus
    assembly_year: int
    number_participants: int | None
    assembly_description: str
    thematic_grouping: str
    source_notes: OptionalStr
    data_source: str | None = Field(..., description="The source of the data")
    licence_notes: OptionalStr = Field(
        default=None, description="CC licence/copyright notes"
    )

    @computed_field
    @property
    def cached_report_url(self) -> str | None:
        """
        Return a link to the cached report in github
        """
        github_base = (
            "https://raw.githubusercontent.com/mysociety/citizen-assembly-data/main/"
        )
        if self.assembly_status != AssemblyStatus.FINISHED:
            return None
        return github_base + "data/raw/reports/" + self.unique_id + ".pdf"

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

    @property
    def cache_pdf_path(self) -> Path:
        return Path("data", "raw", "reports", f"{self.unique_id}.pdf")

    def fetch_pdf(self):
        if self.report_pdf_url is None:
            raise ValueError("report_pdf_url must be present")

        self.cache_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        fetch_valid_pdf(self.report_pdf_url, self.cache_pdf_path)

    @model_validator(mode="after")
    def backed_up_pdf(self):
        if self.assembly_status != AssemblyStatus.FINISHED:
            return self

        if self.cache_pdf_path.exists():
            if (e := is_valid_pdf_file(self.cache_pdf_path)) is True:
                return self
            elif isinstance(e, Exception):
                raise ValueError(f"Invalid cached pdf at {self.cache_pdf_path}") from e

        if not self.cache_pdf_path.exists():
            if self.report_pdf_url is None:
                raise ValueError("report_pdf_url must be present")
            self.fetch_pdf()

        return self
