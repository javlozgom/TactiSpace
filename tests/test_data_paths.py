from src import data_paths


def test_data_paths_exposes_normalized_constants():
    assert str(data_paths.DEFAULT_EVENTS_NORMALIZED_PATH).replace("\\", "/").endswith("data/processed/events_normalized.parquet")
    assert str(data_paths.DEFAULT_THREE_SIXTY_NORMALIZED_PATH).replace("\\", "/").endswith("data/processed/three_sixty_normalized.parquet")
    assert str(data_paths.DEFAULT_LINEUPS_NORMALIZED_PATH).replace("\\", "/").endswith("data/processed/lineups_normalized.parquet")
