"""The master homebrew switch: Sieg's Guide house rules are OPT-IN, default off.

Ruling (Daniel, 2026-10-02): the generator's default output is real Pathfinder 1e plus real
published / third-party subsystems (Path of War, Spheres, psionics, mythic, occult). Every house
rule from Sieg's Guide stays in the code but runs only when the request carries `homebrew: true`.

Two layers, one owner:

* `fold_legacy_flags` runs once, at the top of `generate_random_char`. With homebrew off it forces
  the five pre-existing per-rule flags (`homebrew_feat_amount`, `inherents`, `professions`,
  `trainers`, `misc_homebrew_rules`) and the optimizer's `house_rules` off, so the ~40 readers of
  those flags need no change. With homebrew on the flags pass through untouched -- they can still
  switch an individual rule off, which is how the goldens and the clients' presets keep working.
* `homebrew_on` is the gate for the house rules that never had a flag of their own: the feat tax
  and the free combat feats, the free Skill Unlock, mechanical flaws, the martial-path roll for
  non-initiators and the Metzofitz style chains. Absent attribute -> off, so a bare test fake is
  plain PF1e, matching `skill_ranks.misc_homebrew_enabled`.

Combined caster level is NOT here: the backend's per-class caster level is already RAW. The sum
across spellbooks is a renderer rule, and the renderers read the payload's `homebrew` key for it.
"""

_OFF_STRINGS = ('', 'n', 'no', 'false', '0', 'none', 'off')


def homebrew_requested(value):
    """The named `homebrew` input as a bool. Absent / None / a falsy string -> off."""
    if value is None or value is False:
        return False
    if value is True:
        return True
    return str(value).strip().lower() not in _OFF_STRINGS


def fold_legacy_flags(homebrew, *, homebrew_feat_amount, inherents, professions_flag,
                      trainers_flag, misc_homebrew_rules, house_rules):
    """The six legacy house-rule inputs as they apply under the master switch."""
    if homebrew:
        return dict(homebrew_feat_amount=homebrew_feat_amount, inherents=inherents,
                    professions_flag=professions_flag, trainers_flag=trainers_flag,
                    misc_homebrew_rules=misc_homebrew_rules, house_rules=house_rules)
    return dict(homebrew_feat_amount='N', inherents='N', professions_flag='N',
                trainers_flag='N', misc_homebrew_rules='N', house_rules=None)


def homebrew_on(character):
    """True when this character is being generated under Sieg's Guide house rules."""
    return bool(getattr(character, 'homebrew', False))
