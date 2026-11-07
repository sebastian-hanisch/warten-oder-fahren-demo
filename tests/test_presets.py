"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import wof_constants as C
import wof_evaluation as ev
import wof_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(first["rate"], first["K"], first["seed"], first["tau"], first["thr"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_constants_are_consistent():
    assert set(C.TAU_KEYS) <= set(C.POLICIES) and all(k + "S" in C.POLICIES for k in ("W0", "W20", "Winf"))
    assert [C.POLICIES[k][1] for k in C.TAU_KEYS] == list(C.TAUS) and C.TAUS == tuple(sorted(C.TAUS))
    assert C.DEFAULT_TAU == len(C.TAUS) - 1 and C.RATE_MIN <= C.DEFAULT_RATE <= C.RATE_MAX and C.K_MIN <= C.DEFAULT_K <= C.K_MAX
    assert all(C.RATE_MIN <= r <= C.RATE_MAX and C.K_MIN <= k <= C.K_MAX for r, k in C.CELLS) and C.THRESHOLD == C.REVENUE
