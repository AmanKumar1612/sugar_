from pydantic import BaseModel
from pydantic import HttpUrl


class WebsiteRequest(
    BaseModel
):
    url: HttpUrl