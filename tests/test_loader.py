import pytest

from hydra_lsp.loader import ConfigLoader


@pytest.fixture(autouse=True, scope="session")
def loader():
    return ConfigLoader()


def test_load_config(loader: ConfigLoader):
    config = loader.load("tests/artifacts/local_path.yaml")

    assert config is not None
    assert config.get("local_path") == "/my/mnt/disk"


def test_dot_access(loader: ConfigLoader):
    config = loader.load("tests/artifacts/config_materials.yaml")

    assert config.get("local_path") == "/my/mnt/disk"
    assert config.get("defaults") == ["local_path", "_self_"]
    assert config.get("trainer.accelerator") == "gpu"
    assert config.get("data.loader.pin_memory") is True


def test_inheritance(loader: ConfigLoader):
    config = loader.load("tests/artifacts/config_ldm_precompute_dataset.yaml")

    assert config.get("data.original_image_size") == [1024, 1024]
    assert config.get("data.nb_chn") == 10
    assert config.get("data.dataset.train.data_len") == -1
