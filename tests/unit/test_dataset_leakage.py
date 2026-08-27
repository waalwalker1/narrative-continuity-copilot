"""
Unit tests verifying dataset train/held-out split isolation and manifest integrity.
"""

from pathlib import Path
import json
import pytest

from tools.synthetic_stories.generator import SyntheticStoryGenerator, save_synthetic_dataset


def test_train_held_out_splits_are_strictly_disjoint(tmp_path: Path) -> None:
    manifest = save_synthetic_dataset(tmp_path)

    train_ids = set(manifest["train_story_ids"])
    held_out_ids = set(manifest["held_out_story_ids"])

    assert len(train_ids) > 0
    assert len(held_out_ids) > 0
    assert train_ids.isdisjoint(held_out_ids), "Train and held-out story IDs must be disjoint"
    assert manifest["story_packs_count"] == len(train_ids) + len(held_out_ids)
    assert manifest["story_packs_count"] >= 48
    assert manifest["held_out_cases_count"] >= 144


def test_dataset_manifest_has_valid_corpus_hash(tmp_path: Path) -> None:
    manifest = save_synthetic_dataset(tmp_path)

    assert "corpus_sha256" in manifest
    assert len(manifest["corpus_sha256"]) == 64
    assert manifest["total_cases_count"] == manifest["train_cases_count"] + manifest["held_out_cases_count"]
