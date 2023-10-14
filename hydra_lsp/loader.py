import json
import logging
import os
from typing import Dict

import yaml

logger = logging.getLogger(__name__)


def load_yaml_config(config_path: str) -> Dict:
    logger.info("Loading config from: {}".format(config_path))

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        # TODO: Notify diagnostics module
        logger.warning("Config file not found: {}".format(config_path))
        return {}

    # Recursively load default file (config inheritance)
    if "defaults" in data:
        base_folder = "/".join(config_path.split("/")[:-1])

        for default_file_path in data["defaults"]:
            default_file_path = os.path.join(base_folder, f"{default_file_path}.yaml")
            default_data = load_yaml_config(default_file_path)

            default_data.update(data)
            data = default_data

    return data


class ConfigLoader:
    """
    Load a Hydra YAML config file, looks for _defaults and loads respective files
    Stores: YAML keys and values pairs

    NOTE: This is a very simple implementation, should be extended to support more features
    """

    def __init__(self, config_path: str):
        self.config_path: str = config_path
        self.config: Dict = {}
        self.reload()

    def reload(self) -> None:
        """
        Reload the config from the file
        """
        self.config = load_yaml_config(self.config_path)
        logger.info(f"Reloaded config: {self.config}")

    def get(self, key: str):
        """
        Get a value from the config:
            1. Using a standard dict notation (e.g. config["data"])
            2. Using a dot notation (e.g. config["data.loader"])

        Will return None if the key is not found
        """
        if "." not in key:
            return self.config.get(key)

        # nested case
        value = self.config
        for k in key.split("."):
            value = value.get(k)

        return value


if __name__ == "__main__":
    config_loader = ConfigLoader("examples/config_ldm_precompute_dataset.yaml")
    print(json.dumps(config_loader.config, indent=2))

    print("data: ", config_loader.get("data"))
    print("data.loader: ", config_loader.get("data.loader"))
    print("data.loader.batch_size: ", config_loader.get("data.loader.batch_size"))
