import os
from dataclasses import dataclass


@dataclass
class Config:

    token: str = os.environ['token']
    admin_id: int = int(os.environ['admin_ids'])
