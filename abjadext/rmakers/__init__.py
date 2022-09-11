"""
Tools for rhythm construction.
"""
from ._version import __version__, __version_info__
from .rmakers import (
    AccelerandoRhythmMaker,
    Assignment,
    BeamCommand,
    BeamGroupsCommand,
    Bind,
    CacheStateCommand,
    Command,
    EvenDivisionRhythmMaker,
    FeatherBeamCommand,
    ForceNoteCommand,
    ForceRestCommand,
    GraceContainerCommand,
    Incise,
    IncisedRhythmMaker,
    Interpolation,
    InvisibleMusicCommand,
    Match,
    MultipliedDurationRhythmMaker,
    NoteRhythmMaker,
    RewriteMeterCommand,
    RewriteSustainedCommand,
    RhythmMaker,
    Spelling,
    SplitMeasuresCommand,
    Stack,
    Talea,
    TaleaRhythmMaker,
    TieCommand,
    TremoloContainerCommand,
    TupletRhythmMaker,
    UnbeamCommand,
    WrittenDurationCommand,
    _wrap_music_in_time_signature_staff,
    accelerando,
    accelerando_function,
    after_grace_container,
    assign,
    beam,
    beam_function,
    beam_groups,
    beam_groups_function,
    before_grace_container,
    bind,
    cache_state,
    denominator,
    denominator_function,
    duration_bracket,
    duration_bracket_function,
    even_division,
    example,
    extract_trivial,
    extract_trivial_function,
    feather_beam,
    feather_beam_function,
    force_augmentation,
    force_diminution,
    force_fraction,
    force_fraction_function,
    force_note,
    force_repeat_tie,
    force_repeat_tie_function,
    force_rest,
    force_rest_function,
    incised,
    interpolate,
    invisible_music,
    multiplied_duration,
    nongrace_leaves_in_each_tuplet,
    nongrace_leaves_in_each_tuplet_function,
    note,
    note_function,
    on_beat_grace_container,
    reduce_multiplier,
    reduce_multiplier_function,
    repeat_tie,
    repeat_tie_function,
    rewrite_dots,
    rewrite_meter,
    rewrite_meter_function,
    rewrite_rest_filled,
    rewrite_rest_filled_function,
    rewrite_sustained,
    split_measures,
    split_measures_function,
    stack,
    talea,
    tie,
    tremolo_container,
    trivialize,
    trivialize_function,
    tuplet,
    tuplet_function,
    unbeam,
    unbeam_function,
    untie,
    written_duration,
)

__all__ = [
    "__version__",
    "__version_info__",
    "example",
    # commands:
    "BeamCommand",
    "BeamGroupsCommand",
    "CacheStateCommand",
    "Command",
    "FeatherBeamCommand",
    "ForceNoteCommand",
    "ForceRestCommand",
    "GraceContainerCommand",
    "InvisibleMusicCommand",
    "RewriteMeterCommand",
    "RewriteSustainedCommand",
    "SplitMeasuresCommand",
    "TieCommand",
    "TremoloContainerCommand",
    "UnbeamCommand",
    "WrittenDurationCommand",
    "after_grace_container",
    "beam",
    "beam_function",
    "beam_groups",
    "beam_groups_function",
    "before_grace_container",
    "cache_state",
    "denominator",
    "denominator_function",
    "duration_bracket",
    "duration_bracket_function",
    "extract_trivial",
    "extract_trivial_function",
    "feather_beam",
    "feather_beam_function",
    "force_augmentation",
    "force_diminution",
    "force_fraction",
    "force_fraction_function",
    "force_note",
    "force_repeat_tie",
    "force_repeat_tie_function",
    "force_rest",
    "force_rest_function",
    "invisible_music",
    "nongrace_leaves_in_each_tuplet",
    "nongrace_leaves_in_each_tuplet_function",
    "on_beat_grace_container",
    "reduce_multiplier",
    "reduce_multiplier_function",
    "repeat_tie",
    "repeat_tie_function",
    "rewrite_dots",
    "rewrite_meter",
    "rewrite_meter_function",
    "rewrite_rest_filled",
    "rewrite_rest_filled_function",
    "rewrite_sustained",
    "split_measures",
    "split_measures_function",
    "tie",
    "tremolo_container",
    "trivialize",
    "trivialize_function",
    "unbeam",
    "unbeam_function",
    "untie",
    "written_duration",
    # makers:
    "AccelerandoRhythmMaker",
    "EvenDivisionRhythmMaker",
    "IncisedRhythmMaker",
    "MultipliedDurationRhythmMaker",
    "NoteRhythmMaker",
    "RhythmMaker",
    "TaleaRhythmMaker",
    "TupletRhythmMaker",
    "_wrap_music_in_time_signature_staff",
    "accelerando",
    "accelerando_function",
    "even_division",
    "incised",
    "multiplied_duration",
    "note",
    "note_function",
    "talea",
    "tuplet",
    "tuplet_function",
    # specifiers:
    "Incise",
    "Interpolation",
    "Spelling",
    "Talea",
    "interpolate",
    # stack:
    "Assignment",
    "Bind",
    "Match",
    "Stack",
    "assign",
    "bind",
    "stack",
]
