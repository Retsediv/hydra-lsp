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
    result = {}
    if "defaults" in data:
        base_folder = "/".join(config_path.split("/")[:-1])

        for default_file_path in data["defaults"]:
            # TODO: Account for _self_ position in defaults list
            if default_file_path == "_self_":
                continue

            default_file_path = os.path.join(base_folder, f"{default_file_path}.yaml")
            default_data = load_yaml_config(default_file_path)
            result.update(default_data)

    data.update(result)
    return data


class HydraConfig:
    """
    Stores: YAML keys and values pairs
    """

    def __init__(self, config: Dict):
        self.config = config

    def set(self, key: str, value: str):
        raise NotImplementedError

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


class ConfigLoader:
    """
    Load a Hydra YAML config file, looks for _defaults and loads respective files

    NOTE: This is a very simple implementation, should be extended to support more features
    """

    def __init__(self):
        pass

    def load(self, config_path: str) -> HydraConfig:
        """
        Load the config from the file
        """
        logger.info(f"Loaded config: {config_path}")
        return HydraConfig(load_yaml_config(config_path))


if __name__ == "__main__":
    config_loader = ConfigLoader()
    config = config_loader.load("examples/config_ldm_precompute_dataset.yaml")
    print(json.dumps(config.config, indent=2))

    print("data: ", config.get("data"))
    print("data.loader: ", config.get("data.loader"))
    print("data.loader.batch_size: ", config.get("data.loader.batch_size"))
