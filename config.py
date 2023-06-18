import os
from dataclasses import dataclass

import config_dev


@dataclass
class Config:
    try:
        from config_dev import token, admin_ids
        token: str = config_dev.token
        admin_id: int = config_dev.admin_ids

    except ImportError:
        token: str = os.environ.get('TOKEN')
        admin_id: int = os.environ['admin_ids']
        pass
