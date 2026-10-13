
import pytest

from runtime.growth_experiments import (
    conclude_experiment,
    create_experiment,
    experiment_summary,
    get_experiment,
    load_experiments,
    record_observation,
    start_experiment,
)


def test_full_lifecycle(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    exp = create_experiment(ledger, "Question titles lift CTR", "ctr",
                            ["control", "question"], exp_id="exp-1")
    assert exp.status == "draft"
    start_experiment(ledger, "exp-1")
    for v, vals in {"control": [0.02, 0.021, 0.019],
                    "question": [0.04, 0.043, 0.041]}.items():
        for x in vals:
            record_observation(ledger, "exp-1", v, x)
    done = conclude_experiment(ledger, "exp-1")
    assert done.status == "concluded"
    assert done.winner == "question"
    assert "question mean 0.041333" in done.conclusion_reason
    assert "control=0.02" in done.conclusion_reason


def test_conclude_refuses_thin_samples(tmp_path):
    ledger = tmp_path / "l.jsonl"
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="e")
    start_experiment(ledger, "e")
    record_observation(ledger, "e", "b", 99.0)  # one big number ≠ a result
    with pytest.raises(SystemExit, match="insufficient samples"):
        conclude_experiment(ledger, "e")


def test_record_requires_running_and_known_variant(tmp_path):
    ledger = tmp_path / "l.jsonl"
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="e")
    with pytest.raises(SystemExit, match="status draft"):
        record_observation(ledger, "e", "a", 1.0)
    start_experiment(ledger, "e")
    with pytest.raises(SystemExit, match="unknown variant"):
        record_observation(ledger, "e", "nope", 1.0)


def test_create_validation(tmp_path):
    ledger = tmp_path / "l.jsonl"
    with pytest.raises(SystemExit, match="at least 2 variants"):
        create_experiment(ledger, "h", "m", ["only"])
    with pytest.raises(SystemExit, match="unique"):
        create_experiment(ledger, "h", "m", ["a", "a"])
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="dup")
    with pytest.raises(SystemExit, match="already exists"):
        create_experiment(ledger, "h", "m", ["a", "b"], exp_id="dup")


def test_ledger_replays_and_double_conclude_fails(tmp_path):
    ledger = tmp_path / "l.jsonl"
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="e")
    start_experiment(ledger, "e")
    for i in range(3):
        record_observation(ledger, "e", "a", 1.0 + i * 0.001)
        record_observation(ledger, "e", "b", 0.5)
    conclude_experiment(ledger, "e")
    replayed = get_experiment(ledger, "e")
    assert replayed.winner == "a"
    assert replayed.variants["a"].values == [1.0, 1.001, 1.002]
    with pytest.raises(SystemExit, match="already concluded"):
        conclude_experiment(ledger, "e")


def test_unknown_experiment_and_empty_ledger(tmp_path):
    assert load_experiments(tmp_path / "missing.jsonl") == {}
    with pytest.raises(SystemExit, match="unknown experiment"):
        get_experiment(tmp_path / "l.jsonl", "ghost")


def test_nonfinite_measurement_rejected(tmp_path):
    ledger = tmp_path / "l.jsonl"
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="e")
    start_experiment(ledger, "e")
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(SystemExit, match="finite"):
            record_observation(ledger, "e", "a", bad)
    assert get_experiment(ledger, "e").variants["a"].values == []


def test_sub_rounding_margin_picks_real_winner(tmp_path):
    ledger = tmp_path / "l.jsonl"
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="e")
    start_experiment(ledger, "e")
    for _ in range(3):
        record_observation(ledger, "e", "a", 0.1234567)
        record_observation(ledger, "e", "b", 0.1234561)
    done = conclude_experiment(ledger, "e")
    assert done.winner == "a"  # differs below the old 6-decimal rounding


def test_summary_shape(tmp_path):
    ledger = tmp_path / "l.jsonl"
    create_experiment(ledger, "h", "m", ["a", "b"], exp_id="e")
    s = experiment_summary(get_experiment(ledger, "e"))
    assert s["status"] == "draft" and s["winner"] is None
    assert s["variants"]["a"] == {"samples": 0, "mean": None}
