import collections

import abjad


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
