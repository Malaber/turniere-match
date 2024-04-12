from dataclasses import dataclass

import yaml


@dataclass
class Config:
    username: str
    password: str
    tournament_code: str
    main_instance_url: str
    remote_instance_url: str


class MatchConfiguredToNotRunError(Exception):
    pass


def read_config() -> Config:
    with open("config.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        if "DO_NOT_RUN_MATCH" in data:
            raise MatchConfiguredToNotRunError
    return Config(**data)
