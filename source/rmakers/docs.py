import collections

import abjad


def _is_component_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Component) for _ in argument)


def _is_time_signature_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.TimeSignature) for _ in argument)


def attach_time_signatures(
    voice: abjad.Voice,
    time_signatures: collections.abc.Iterable[abjad.TimeSignature],
) -> None:
    """
    Attaches ``time_signatures`` to leaves in ``voice``.
    """
    assert all(isinstance(_, abjad.TimeSignature) for _ in time_signatures)
    leaves = abjad.select.leaves(voice, grace=False)
    durations = [_.duration() for _ in time_signatures]
    parts = abjad.select.partition_by_durations(leaves, durations)
    previous_time_signature = None
    for time_signature, part in zip(time_signatures, parts, strict=True):
        if time_signature != previous_time_signature:
            leaf = abjad.select.leaf(part, 0)
            abjad.detach(abjad.TimeSignature, leaf)
            abjad.attach(time_signature, leaf)
        previous_time_signature = time_signature


def make_example_lilypond_file(
    components: collections.abc.Iterable[abjad.Component],
    time_signatures: collections.abc.Iterable[abjad.TimeSignature],
    *,
    includes: collections.abc.Iterable[str] | None = None,
) -> abjad.LilyPondFile:
    """
    Makes example LilyPond file.
    """
    assert _is_component_list(components), repr(components)
    assert _is_time_signature_list(time_signatures), repr(time_signatures)
    if includes is None:
        includes = []
    assert all(isinstance(_, str) for _ in includes), repr(includes)
    lilypond_file = abjad.illustrators.components(components, time_signatures)
    includes = [rf'\include "{_}"' for _ in includes]
    lilypond_file.items[0:0] = includes
    staff = lilypond_file["Staff"]
    staff.set_lilypond_type("RhythmicStaff")
    abjad.override(staff).Clef.stencil = False
    return lilypond_file
