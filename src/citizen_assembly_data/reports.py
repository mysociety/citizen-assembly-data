import tempfile
from pathlib import Path
from typing import Literal

import pypdf
import requests
from data_common.helpers.url import Url

UrlLike = Url | str


def is_valid_pdf_file(file: Path) -> Literal[True] | Exception:
    try:
        pypdf.PdfReader(str(file))
        return True
    except Exception as e:
        return e


def fetch_pdf_from_url(url: UrlLike, dest_path: Path):
    """
    Check if we've already loaded this url
    """
    url = Url(url)

    print(f"Downloading {url}")
    # download the pdf
    bytes_content = requests.get(url).content
    dest_path.write_bytes(bytes_content)
    return dest_path


def fetch_valid_pdf(url: UrlLike, dest_path: Path):
    """
    Check if we've already loaded this url
    """

    # get the path of a tempfile
    with tempfile.NamedTemporaryFile() as f:
        temp_path = Path(f.name)
        fetch_pdf_from_url(url, temp_path)
        if (e := is_valid_pdf_file(temp_path)) is True:
            dest_path.write_bytes(temp_path.read_bytes())
        elif isinstance(e, Exception):
            # delete the temp file
            temp_path.unlink()
            raise ValueError(f"Invalid pdf at {url}") from e
    return dest_path
