
from typing import Optional
from pandas import DataFrame
import requests
from utils.settings import env
from pydantic import BaseModel

session = requests.Session()
session.headers = dict(Authorization=env.API_KEY)

class Endpoint(BaseModel):

    cur_page:int = 1
    response: object = None
    df: object = None
    verbose:bool = False
    url: str = None

    def clear(self):
        self.cur_page = 1
        return self
