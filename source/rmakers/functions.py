"""
The rmakers functions.
"""

import collections
import inspect
import types
import typing

import abjad

from . import classes as _classes


def _function_name(frame: types.FrameType | None) -> abjad.Tag:
    assert frame is not None, repr(frame)
    function_name = frame.f_code.co_name
    string = f"rmakers.{function_name}()"
    return abjad.Tag(string)


def _is_component_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Component) for _ in argument)


def _is_container_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Container) for _ in argument)


def _is_container_or_component_list(argument: object) -> bool:
    if isinstance(argument, abjad.Container):
        return True
    return _is_component_list(argument)


def _is_duration_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Duration) for _ in argument)


def _is_integer_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, int) for _ in argument)


def _is_leaf_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Leaf) for _ in argument)


def _is_list_of_leaf_lists(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    for item in argument:
        if _is_leaf_list(item) is False:
            return False
    return True


def _is_pleaf_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Note | abjad.Chord) for _ in argument)


def _is_time_signature_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.TimeSignature) for _ in argument)


def _is_tuplet_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Tuplet) for _ in argument)


def _make_beamable_groups(
    components: collections.abc.Iterable[abjad.Component],
    durations: collections.abc.Iterable[abjad.Duration],
) -> list[list[abjad.Component]]:
    assert _is_component_list(components), repr(components)
    assert _is_duration_list(durations), repr(durations)
    music_duration = abjad.get.duration(components)
    if music_duration != sum(durations):
        message = f"music duration {music_duration} does not equal"
        message += f" total duration {sum(durations)}:\n"
        message += f"   {components}\n"
        message += f"   {durations}"
        raise Exception(message)
    component_to_timespan = []
    start_offset = abjad.duration.offset(0)
    for component in components:
        duration = abjad.get.duration(component)
        stop_offset = start_offset + duration
        timespan = abjad.Timespan(start_offset, stop_offset)
        component_to_timespan.append((component, timespan))
        start_offset = stop_offset
    group_to_target_duration = []
    start_offset = abjad.duration.offset(0)
    for target_duration in durations:
        stop_offset = start_offset + target_duration
        group_timespan = abjad.Timespan(start_offset, stop_offset)
        start_offset = stop_offset
        group = []
        for component, component_timespan in component_to_timespan:
            if component_timespan in group_timespan:
                group.append(component)
        group_to_target_duration.append((group, target_duration))
    beamable_groups = []
    for group, target_duration in group_to_target_duration:
        group_duration = abjad.get.duration(group)
        assert group_duration <= target_duration
        if group_duration == target_duration:
            beamable_groups.append(group)
        else:
            beamable_groups.append([])
    return beamable_groups


def attach_beams_to_runs_by_leaf_list(
    leaf_lists: collections.abc.Iterable[collections.abc.Sequence[abjad.Leaf]],
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Attaches beams to runs in each leaf list in ``leaf_lists``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, beam_rests=False, stemlet_length=None):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 1, 1, -1], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(
        ...         leaf_lists,
        ...         beam_rests=beam_rests,
        ...         stemlet_length=stemlet_length,
        ...     )
        ...     rmakers.swap_trivial_tuplets_for_containers(tuplets)
        ...     score = lilypond_file["Score"]
        ...     abjad.setting(score).autoBeaming = False
        ...     return lilypond_file

    ..  container:: example

        Beams each run in each tuplet:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \time 3/8
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            r16
                            c'16
                            [
                            c'16
                            ]
                        }
                        {
                            \time 4/8
                            c'16
                            r16
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            r16
                            c'16
                            [
                            c'16
                            ]
                        }
                        {
                            \time 3/8
                            c'16
                            r16
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            r16
                        }
                        {
                            \time 4/8
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            r16
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            r16
                        }
                    }
                }
            }

    ..  container:: example

        Set ``beam_rests=True`` and ``stemlet_length=n`` to beam rests with
        stemlets of length ``n``:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(
        ...     pairs, beam_rests=True, stemlet_length=0.75
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 3/8
                            c'16
                            [
                            c'16
                            c'16
                            r16
                            c'16
                            c'16
                            ]
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 4/8
                            c'16
                            [
                            r16
                            c'16
                            c'16
                            c'16
                            r16
                            c'16
                            c'16
                            ]
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 3/8
                            c'16
                            [
                            r16
                            c'16
                            c'16
                            c'16
                            r16
                            ]
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 4/8
                            c'16
                            [
                            c'16
                            c'16
                            r16
                            c'16
                            c'16
                            c'16
                            r16
                            ]
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                    }
                }
            }

    ..  container:: example

        By default, ``rmakers.attach_beams_to_runs_by_leaf_list()`` unbeams input before applying new beams:

        >>> staff = abjad.Staff(r"c'8 [ c'8 c'8 ] c'8 [ c'8 c'8 ] c'8 c'8")
        >>> abjad.setting(staff).autoBeaming = False
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(staff)
            >>> print(string)
            \new Staff
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                [
                c'8
                c'8
                ]
                c'8
                [
                c'8
                c'8
                ]
                c'8
                c'8
            }

        >>> rmakers.attach_beams_to_runs_by_leaf_list([staff[:]])
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(staff)
            >>> print(string)
            \new Staff
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                [
                c'8
                c'8
                c'8
                c'8
                c'8
                c'8
                c'8
                ]
            }

    """
    assert _is_list_of_leaf_lists(leaf_lists), repr(leaf_lists)
    tag = tag.append(_function_name(inspect.currentframe()))
    for leaf_list in leaf_lists:
        detach_beams_from_leaves(leaf_list)
        abjad.beam(
            leaf_list,
            beam_lone_notes=beam_lone_notes,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )


def attach_invisible_music_commands_to_leaves(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    """
    Attaches invisible music commands to each leaf in ``leaves``.
    """
    assert _is_leaf_list(leaves), repr(leaves)
    tag = tag.append(_function_name(inspect.currentframe()))
    tag_1 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COMMAND"))
    literal_1 = abjad.LilyPondLiteral(r"\abjad-invisible-music", site="before")
    tag_2 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COLORING"))
    literal_2 = abjad.LilyPondLiteral(r"\abjad-invisible-music-coloring", site="before")
    for leaf in leaves:
        abjad.attach(literal_1, leaf, tag=tag_1, deactivate=True)
        abjad.attach(literal_2, leaf, tag=tag_2)


def attach_repeat_ties_to_pleaves(
    pleaves: collections.abc.Iterable[abjad.Note | abjad.Chord],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Attaches repeat-tie to each pitched leaf in ``pleaves``.

    ..  container:: example

        Attaches repeat-tie to first pitched leaf in each nonfirst tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)[1:]
        ...     notes = [abjad.select.note(_, 0) for _ in tuplets]
        ...     rmakers.attach_repeat_ties_to_pleaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Attaches repeat-ties to nonfirst notes in each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     notes = [abjad.select.notes(_)[1:] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.attach_repeat_ties_to_pleaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                    }
                }
            }

    """
    assert _is_pleaf_list(pleaves), repr(pleaves)
    tag = tag.append(_function_name(inspect.currentframe()))
    for pleaf in pleaves:
        tie = abjad.RepeatTie()
        abjad.attach(tie, pleaf, tag=tag)


def attach_ties_to_pleaves(
    pleaves: collections.abc.Iterable[abjad.Note | abjad.Chord],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Attaches tie to each pitched pleaf in ``pleaves``.

    ..  container:: example

        Attaches tie to last pitched leaf in each nonlast tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(tuplets)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties the last leaf of nonlast tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, 3, 3, 3], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(tuplets)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(leaves)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            }

    ..  container:: example

        Ties across every other tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, 3, 3, 3], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets[:-1], [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(leaves)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            }

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, -3, 3, 3], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     rmakers.detach_ties_from_leaves(leaves)
        ...     runs = abjad.select.runs(voice)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in runs]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 4/8
                        c'4
                        ~
                        c'16
                        r8.
                        \time 3/8
                        c'8.
                        [
                        ~
                        c'8.
                        ]
                        ~
                        \time 4/8
                        c'4
                        ~
                        c'16
                        r8.
                        \time 3/8
                        c'8.
                        [
                        ~
                        c'8.
                        ]
                    }
                }
            }


    ..  container:: example

        Attaches ties to nonlast notes in each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.detach_ties_from_leaves(notes)
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    assert _is_pleaf_list(pleaves), repr(pleaves)
    tag = tag.append(_function_name(inspect.currentframe()))
    for pleaf in pleaves:
        tie = abjad.Tie()
        abjad.attach(tie, pleaf, tag=tag)


def attach_span_beams_to_runs_across_leaf_lists(
    leaf_lists: collections.abc.Iterable[collections.abc.Iterable[abjad.Leaf]],
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Attaches span beams to runs across ``leaf_lists``.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_span_beams_to_runs_across_leaf_lists(leaf_lists)
        ...     rmakers.swap_trivial_tuplets_for_containers(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 2
                            \time 3/8
                            c'16
                            [
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 1
                            c'16
                        }
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            \time 4/8
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 1
                            c'16
                        }
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            \time 3/8
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 1
                            c'16
                        }
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            \time 4/8
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 0
                            c'16
                            ]
                        }
                    }
                }
            }

    """
    assert _is_list_of_leaf_lists(leaf_lists), repr(leaf_lists)
    tag = tag.append(_function_name(inspect.currentframe()))
    leaves = abjad.select.leaves(leaf_lists)
    detach_beams_from_leaves(leaves)
    durations = [abjad.get.duration(_) for _ in leaf_lists]
    leaves = abjad.select.leaves(leaf_lists)
    abjad.beam(
        leaves,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        durations=durations,
        span_beam_count=1,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def detach_beams_from_leaves(
    leaves: collections.abc.Sequence[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    """
    Detaches beam indicators from each leaf in ``leaves``.

    Beam indicators are ``abjad.StartBeam``, ``abjad.StopBeam``,
    ``abjad.BeamCount``.
    """
    assert _is_leaf_list(leaves), repr(leaves)
    for leaf in leaves:
        abjad.detach(abjad.BeamCount, leaf)
        abjad.detach(abjad.StartBeam, leaf)
        abjad.detach(abjad.StopBeam, leaf)


def detach_ties_from_leaves(leaves: collections.abc.Iterable[abjad.Leaf]) -> None:
    r"""
    Detaches ties from each leaf in ``leaves``.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     notes = abjad.select.notes(voice)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.detach_ties_from_leaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            ~
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            ~
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from select notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = abjad.Voice(tuplets)
        ...     notes = abjad.select.notes(voice)[1:]
        ...     rmakers.attach_repeat_ties_to_pleaves(notes)
        ...     notes = abjad.select.notes(voice)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.detach_ties_from_leaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            \repeatTie
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                            \repeatTie
                        }
                    }
                }
            }

    """
    assert _is_leaf_list(leaves), repr(leaves)
    for leaf in leaves:
        abjad.detach(abjad.Tie, leaf)
        abjad.detach(abjad.RepeatTie, leaf)


def extract_rest_filled_tuplets(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    """
    Extracts each rest-filled tuplet in ``tuplets``.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if tuplet.is_rest_filled() is True:
            abjad.mutate.extract(tuplet)


def extract_trivial_tuplets(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Extracts each trivial tuplet in ``tuplets``.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(voice)[-2:]
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if tuplet.is_trivial():
            abjad.mutate.extract(tuplet)


def override_beam_grow_direction(
    leaf_lists: collections.abc.Iterable[collections.abc.Sequence[abjad.Leaf]],
    *,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Overrides ``Beam.grow-direction`` on first leaf of each leaf list in
    ``leaf_lists``.

    ..  container:: example

        >>> def make_lilypond_file():
        ...     voice = abjad.Voice("c'16 d' r f' g'8")
        ...     rmakers.attach_beams_to_runs_by_leaf_list(
        ...         [voice[:]],
        ...         beam_rests=True,
        ...         stemlet_length=1,
        ...     )
        ...     rmakers.override_beam_grow_direction([voice[:]])
        ...     staff = abjad.Staff([voice])
        ...     score = abjad.Score([staff], name="Score")
        ...     lilypond_file = abjad.LilyPondFile([score])
        ...     return lilypond_file

        >>> lilypond_file = make_lilypond_file()
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \new Staff
                {
                    \new Voice
                    {
                        \override Staff.Stem.stemlet-length = 1
                        \once \override Beam.grow-direction = #left
                        c'16
                        [
                        d'16
                        r16
                        f'16
                        g'8
                        ]
                        \revert Staff.Stem.stemlet-length
                    }
                }
            >>

    """
    assert _is_list_of_leaf_lists(leaf_lists), repr(leaf_lists)
    assert isinstance(beam_rests, bool), repr(beam_rests)
    if stemlet_length is not None:
        assert isinstance(stemlet_length, int | float), repr(stemlet_length)
    tag = tag.append(_function_name(inspect.currentframe()))
    for leaf_list in leaf_lists:
        first_leaf = leaf_list[0]
        last_leaf = leaf_list[-1]
        first_duration = abjad.get.duration(first_leaf)
        last_duration = abjad.get.duration(last_leaf)
        if last_duration < first_duration:
            abjad.override(first_leaf).Beam.grow_direction = abjad.RIGHT
        elif first_duration < last_duration:
            abjad.override(first_leaf).Beam.grow_direction = abjad.LEFT


def override_tuplet_number_text_duration_markup(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    """
    Overrides ``TupletNumber.text`` of each tuplet in ``tuplets``.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    pitch_list = [abjad.NamedPitch("c'")]
    for tuplet in tuplets:
        duration = abjad.get.duration(tuplet)
        components = abjad.makers.make_leaves([pitch_list], [duration])
        if all(isinstance(_, abjad.Note) for _ in components):
            durations = [abjad.get.duration(_) for _ in components]
            strings = [_.lilypond_duration_string() for _ in durations]
            strings = [rf"\rhythm {{ {_} }}" for _ in strings]
            string = " + ".join(strings)
            if "+" in string:
                string = f"{{ {string} }}"
        else:
            string = abjad.illustrators.components_to_score_markup_string(components)
        string = rf"\markup \scale #'(0.75 . 0.75) {string}"
        abjad.override(tuplet).TupletNumber.text = string


def reduce_tuplet_ratios(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    """
    Reduces ratio of each tuplet in ``tuplets``.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        ratio = abjad.Ratio(
            tuplet.multiplier().denominator,
            tuplet.multiplier().numerator,
        )
        tuplet.set_ratio(ratio)


def replace_leaves_with_notes(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Replaces each leaf in ``leaves`` with note.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     components = rmakers.note(durations)
        ...     container = abjad.Container(components)
        ...     rmakers.replace_leaves_with_rests(components)
        ...     rests = container[1:3]
        ...     rmakers.replace_leaves_with_notes(rests)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 7/16
                        r4..
                        \time 3/8
                        c'4.
                        \time 7/16
                        c'4..
                        \time 3/8
                        r4.
                    }
                }
            }

    ..  container:: example

        Changes leaves to notes with inverted composite pattern:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     components = rmakers.note(durations)
        ...     container = abjad.Container(components)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.replace_leaves_with_rests(leaves)
        ...     leaves = abjad.select.get(container[:], [0, -1])
        ...     rmakers.replace_leaves_with_notes(leaves)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 7/16
                        c'4..
                        \time 3/8
                        r4.
                        \time 7/16
                        r4..
                        \time 3/8
                        c'4.
                    }
                }
            }

    """
    assert _is_leaf_list(leaves), repr(leaves)
    tag = tag.append(_function_name(inspect.currentframe()))
    pitch = abjad.NamedPitch("C4")
    for leaf in leaves:
        if isinstance(leaf, abjad.Note):
            continue
        duration = leaf.written_duration()
        note = abjad.Note.from_duration_and_pitch(duration, pitch, tag=tag)
        if leaf.dmp() is not None:
            note.set_dmp(leaf.dmp())
        abjad.mutate.replace(leaf, [note])


def replace_leaves_with_rests(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Replaces each leaf in ``leaves`` with rest.

    ..  container:: example

        Forces first and last logical ties to rest:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     leaves = abjad.select.get(leaves, [0, -1])
        ...     rmakers.replace_leaves_with_rests(leaves)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        r8
                    }
                }
            }

    ..  container:: example

        Forces all logical ties to rest. Then sustains first and last logical ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     container = abjad.Container(tuplets)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.replace_leaves_with_rests(leaves)
        ...     leaves = abjad.select.leaves(container)
        ...     rests = abjad.select.get(leaves[:], [0, -1])
        ...     rmakers.replace_leaves_with_notes(rests)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        c'16
                        r8
                        r8.
                        \time 4/8
                        r4
                        r16
                        r8
                        r16
                        \time 3/8
                        r8
                        r4
                        \time 4/8
                        r16
                        r8
                        r8.
                        c'8
                    }
                }
            }

    ..  container:: example

        Forces every other tuplet to rest:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     leaves = abjad.select.leaves(tuplets)
        ...     rmakers.replace_leaves_with_rests(leaves)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.rewrite_rest_filled_tuplets(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        \time 4/8
                        r2
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        r2
                    }
                }
            }

    ..  container:: example

        Forces the first leaf and the last two leaves to rests:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     leaves = abjad.select.get(leaves, [0, -2, -1])
        ...     rmakers.replace_leaves_with_rests(leaves)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        c'16
                        [
                        c'8
                        ]
                        r8.
                        r8
                    }
                }
            }

    ..  container:: example

        Forces first leaf of every tuplet to rest:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = [abjad.select.leaf(_, 0) for _ in tuplets]
        ...     rmakers.replace_leaves_with_rests(leaves)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        \time 4/8
                        r4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        \time 3/8
                        r8
                        c'4
                        \time 4/8
                        r16
                        c'8
                        [
                        c'8.
                        c'8
                        ]
                    }
                }
            }

    """
    assert _is_leaf_list(leaves), repr(leaves)
    tag = tag.append(_function_name(inspect.currentframe()))
    for leaf in leaves:
        duration = leaf.written_duration()
        rest = abjad.Rest.from_duration(duration, tag=tag)
        if leaf.dmp() is not None:
            rest.set_dmp(leaf.dmp())
        previous_leaf = abjad.get.leaf(leaf, -1)
        next_leaf = abjad.get.leaf(leaf, 1)
        abjad.mutate.replace(leaf, [rest])
        if previous_leaf is not None:
            abjad.detach(abjad.Tie, previous_leaf)
        abjad.detach(abjad.Tie, rest)
        abjad.detach(abjad.RepeatTie, rest)
        if next_leaf is not None:
            abjad.detach(abjad.RepeatTie, next_leaf)


def replace_ties_with_repeat_ties(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
    threshold: bool | abjad.Duration | typing.Callable = True,
) -> None:
    r"""
    Replaces ties attached to ``leaves`` with repeat-ties.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     return lilypond_file

    ..  container:: example

        Attaches tie to last note in each nonlast tuplet:

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Changes ties to repeat-ties:

        >>> leaves = abjad.select.leaves(lilypond_file["Score"])
        >>> rmakers.replace_ties_with_repeat_ties(leaves)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    assert _is_leaf_list(leaves), repr(leaves)
    tag = tag.append(_function_name(inspect.currentframe()))
    if callable(threshold):
        inequality = threshold
    elif threshold in (None, False):

        def inequality(item):
            return item < abjad.Duration(0)

    elif threshold is True:

        def inequality(item):
            return item >= abjad.Duration(0)

    else:
        assert isinstance(threshold, abjad.Duration)

        def inequality(item):
            return item >= threshold

    attach_repeat_ties = []
    for leaf in leaves:
        if abjad.get.has_indicator(leaf, abjad.Tie):
            next_leaf = abjad.get.leaf(leaf, 1)
            if next_leaf is None:
                continue
            if not isinstance(next_leaf, abjad.Chord | abjad.Note):
                continue
            if abjad.get.has_indicator(next_leaf, abjad.RepeatTie):
                continue
            duration = abjad.get.duration(leaf)
            if not inequality(duration):
                continue
            attach_repeat_ties.append(next_leaf)
            abjad.detach(abjad.Tie, leaf)
    for leaf in attach_repeat_ties:
        repeat_tie = abjad.RepeatTie()
        abjad.attach(repeat_tie, leaf, tag=tag)


def respell_leaves_written_duration_and_dmp(
    leaves: collections.abc.Iterable[abjad.Leaf],
    written_duration: abjad.Duration,
) -> None:
    """
    Respells written duration and DMP of each leaf in ``leaves``.
    """
    assert _is_leaf_list(leaves), repr(leaves)
    assert isinstance(written_duration, abjad.Duration), repr(written_duration)
    for leaf in leaves:
        old_duration = leaf.written_duration()
        if written_duration == old_duration:
            continue
        leaf.set_written_duration(written_duration)
        fraction = old_duration / written_duration
        leaf.set_dmp(fraction.as_integer_ratio())


def respell_tuplets_without_dots(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    """
    Respells ``tuplets`` without dots.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    tag = tag.append(_function_name(inspect.currentframe()))
    for tuplet in tuplets:
        tuplet.respell_without_dots()


def rewrite_meter(
    voice: abjad.Voice,
    *,
    boundary_depth: int | None = None,
    reference_meters: collections.abc.Iterable[abjad.Meter] | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Rewrites meter of components in ``voice``.

    ..  container:: example

        Rewrites meter. Uses ``rmakers.wrap_in_time_signature_staff()`` to make
        sure ``voice`` appears together with time signature information in a
        staff.

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, 4], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = rmakers.wrap_in_time_signature_staff(tuplets, time_signatures)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     rmakers.rewrite_meter(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(3, 4), (3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/4
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        c'8
                        [
                        c'8
                        ]
                        ~
                        c'8
                        [
                        c'8
                        ]
                        ~
                        c'8.
                        [
                        c'16
                        ]
                        ~
                        c'8.
                        [
                        c'16
                        ]
                        ~
                        c'4
                        c'4
                    }
                }
            }

    """
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(voice, abjad.Container), repr(voice)
    staff = abjad.get.parentage(voice).parent()
    assert isinstance(staff, abjad.Staff), repr(staff)
    time_signature_voice = staff["TimeSignatureVoice"]
    assert isinstance(time_signature_voice, abjad.Voice)
    if reference_meters is None:
        reference_meters = []
    assert isinstance(reference_meters, list), repr(reference_meters)
    meters, preferred_meters = [], []
    for skip in time_signature_voice:
        time_signature = abjad.get.indicator(skip, abjad.TimeSignature)
        rtc = abjad.meter.make_best_guess_rtc(time_signature.pair)
        meter = abjad.Meter(rtc)
        meters.append(meter)
    durations = [_.duration() for _ in meters]
    split_measures(voice, durations=durations)
    lists = abjad.select.group_by_measure(voice[:])
    assert all(isinstance(_, list) for _ in lists), repr(lists)
    for meter, list_ in zip(meters, lists, strict=True):
        for reference_meter in reference_meters:
            if reference_meter.pair() == meter.pair():
                meter = reference_meter
                break
        preferred_meters.append(meter)
        nontupletted_leaves = []
        for leaf in abjad.iterate.leaves(list_):
            if not abjad.get.parentage(leaf).count(abjad.Tuplet):
                nontupletted_leaves.append(leaf)
        detach_beams_from_leaves(nontupletted_leaves)
        meter.rewrite(
            list_,
            boundary_depth=boundary_depth,
            do_not_rewrite_tuplets=True,
        )
    lists = abjad.select.group_by_measure(voice[:])
    for meter, list_ in zip(preferred_meters, lists, strict=True):
        leaves = abjad.select.leaves(list_, grace=False)
        beat_durations = []
        beat_offsets = meter.depthwise_offset_inventory()[1]
        for start, stop in abjad.sequence.nwise(beat_offsets):
            beat_duration = stop - start
            beat_durations.append(beat_duration)
        beamable_groups = _make_beamable_groups(leaves, beat_durations)
        for beamable_group in beamable_groups:
            if not beamable_group:
                continue
            abjad.beam(
                beamable_group,
                beam_rests=False,
                tag=tag,
            )


def rewrite_rest_filled_tuplets(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
    *,
    spelling: _classes.Spelling | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Rewrites rest-filled tuplets in ``tuplets``.

    ..  container:: example

        Does not rewrite rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [-1], 16, extra_counts=[1])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 5/4
                        {
                            \time 4/16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tuplet 5/4
                        {
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            \time 5/16
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                    }
                }
            }

        Rewrites rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [-1], 16, extra_counts=[1])
        ...     container = abjad.Container(tuplets)
        ...     rmakers.rewrite_rest_filled_tuplets(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 4/16
                        r4
                        r4
                        \time 5/16
                        r4
                        r16
                        r4
                        r16
                    }
                }
            }

        With spelling specifier:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [-1], 16, extra_counts=[1])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     spelling = rmakers.Spelling(increase_monotonic=True)
        ...     rmakers.rewrite_rest_filled_tuplets(tuplets, spelling=spelling)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 4/16
                        r4
                        r4
                        \time 5/16
                        r16
                        r4
                        r16
                        r4
                    }
                }
            }

    ..  container:: example

        Working with ``rewrite_rest_filled_tuplets``.

        Makes rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, -6, -6], 16, extra_counts=[1, 0]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            r4
                            r16
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            r8.
                            c'8.
                            [
                            c'16
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'8
                            r4.
                        }
                    }
                }
            }

        Rewrites rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [3, 3, -6, -6],
        ...         16,
        ...         extra_counts=[1, 0],
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.rewrite_rest_filled_tuplets(tuplets)
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            r2
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            r8.
                            c'8.
                            [
                            c'16
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'8
                            r4.
                        }
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    if spelling is None:
        spelling = _classes.Spelling()
    assert isinstance(spelling, _classes.Spelling), repr(spelling)
    tag = tag.append(_function_name(inspect.currentframe()))
    for tuplet in tuplets:
        if not tuplet.is_rest_filled():
            continue
        duration = abjad.get.duration(tuplet)
        rests = abjad.makers.make_leaves(
            [[]],
            [duration],
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        abjad.mutate.replace(tuplet[:], rests)
        tuplet.set_ratio(abjad.Ratio(1, 1))


def rewrite_sustained_tuplets(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Rewrites sustained tuplets in ``tuplets``.

    ..  container:: example

        Sustained tuplets generalize a class of rhythms composers are likely to
        rewrite:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(leaves)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 4/16
                            c'4.
                        }
                        \tuplet 5/4
                        {
                            c'4
                            ~
                            c'16
                            ~
                        }
                        \tuplet 5/4
                        {
                            c'4
                            ~
                            c'16
                            ~
                        }
                        \tuplet 5/4
                        {
                            c'4
                            c'16
                        }
                    }
                }
            }

        The first three tuplets in the example above qualify as sustained:

            >>> staff = lilypond_file["Score"]
            >>> for tuplet in abjad.select.tuplets(staff):
            ...     abjad.get.is_sustained(tuplet)
            ...
            True
            True
            True
            False

        Tuplets 0 and 1 each contain only a single **tuplet-initial** attack. Tuplet 2
        contains no attack at all. All three fill their duration completely.

        Tuplet 3 contains a **nonintial** attack that rearticulates the tuplet's duration
        midway through the course of the figure. Tuplet 3 does not qualify as sustained.

    ..  container:: example

        Rewrite sustained tuplets like this:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(leaves)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_sustained_tuplets(tuplets)
        ...     tuplets = abjad.select.tuplets(container, level=1)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4
                            ~
                        }
                        \tuplet 5/4
                        {
                            c'4
                            c'16
                        }
                    }
                }
            }

    ..  container:: example

        Rewrite sustained tuplets -- and then extract the trivial tuplets that result --
        like this:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     container = abjad.Container(tuplets)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.attach_ties_to_pleaves(leaves)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_sustained_tuplets(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         components, time_signatures
        ...     )
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 4/16
                        c'4
                        c'4
                        ~
                        c'4
                        ~
                        \tuplet 5/4
                        {
                            c'4
                            c'16
                        }
                    }
                }
            }

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     rmakers.rewrite_sustained_tuplets(tuplets[-2:])
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Sustains every other tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.attach_ties_to_pleaves(notes)
        ...     rmakers.rewrite_sustained_tuplets(tuplets)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        \time 4/8
                        c'2
                        ~
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        c'2
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    tag = tag.append(_function_name(inspect.currentframe()))
    for tuplet in tuplets:
        if not abjad.get.is_sustained(tuplet):
            continue
        duration = abjad.get.duration(tuplet)
        leaves = abjad.select.leaves(tuplet)
        last_leaf = leaves[-1]
        if abjad.get.has_indicator(last_leaf, abjad.Tie):
            last_leaf_has_tie = True
        else:
            last_leaf_has_tie = False
        for leaf in leaves[1:]:
            tuplet.remove(leaf)
        assert len(tuplet) == 1, repr(tuplet)
        if not last_leaf_has_tie:
            abjad.detach(abjad.Tie, tuplet[-1])
        abjad.mutate._set_leaf_duration(tuplet[0], duration, tag=tag)
        tuplet.set_ratio(abjad.Ratio(1, 1))


def select_nongrace_leaves_by_tuplet(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> list[list[abjad.Leaf]]:
    """
    Selects nongrace leaves by tuplet.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    leaf_lists = [abjad.select.leaves(_, grace=False) for _ in tuplets]
    assert _is_list_of_leaf_lists(leaf_lists), repr(leaf_lists)
    return leaf_lists


def split_measures(
    voice: abjad.Voice,
    *,
    durations: list[abjad.Duration] | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    """
    Splits measures in ``voice``.

    Uses ``durations`` when ``durations`` is not none.

    Tries to find time signature information (from the staff that contains
    ``voice``) when ``durations`` is none.
    """
    assert isinstance(voice, abjad.Voice), repr(voice)
    tag = tag.append(_function_name(inspect.currentframe()))
    if not durations:
        staff = abjad.get.parentage(voice).parent()
        assert isinstance(staff, abjad.Staff)
        voice_ = staff["TimeSignatureVoice"]
        assert isinstance(voice_, abjad.Voice)
        durations = [abjad.get.duration(_) for _ in voice_]
    assert _is_duration_list(durations), repr(durations)
    total_duration = sum(durations)
    music_duration = abjad.get.duration(voice)
    if total_duration != music_duration:
        message = f"Total duration of splits is {total_duration!s}"
        message += f" but duration of music is {music_duration!s}:"
        message += f"\ndurations: {durations}."
        message += f"\nvoice: {voice[:]}."
        raise Exception(message)
    abjad.mutate.split(voice[:], durations=durations)


def swap_length_1_tuplets_for_containers(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    """
    Swaps length-1 tuplets in ``tuplets`` for (vanilla) containers.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if len(tuplet) == 1:
            container = abjad.Container()
            abjad.mutate.swap(tuplet, container)


def swap_skip_filled_tuplets_for_containers(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    """
    Swaps skip-filled tuplets in ``tuplets`` for (vanilla) containers.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if all(isinstance(_, abjad.Skip) for _ in tuplet):
            container = abjad.Container()
            abjad.mutate.swap(tuplet, container)


def swap_trivial_tuplets_for_containers(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    r"""
    Swaps trivial tuplets in ``tuplets`` for containers.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(tuplets)[-2:]
        ...     rmakers.swap_trivial_tuplets_for_containers(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if tuplet.is_trivial():
            container = abjad.Container()
            abjad.mutate.swap(tuplet, container)


def toggle_diminished_tuplets(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Toggles prolation of diminished tuplets in ``tuplets``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, toggle_diminished_tuplets=False):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     if toggle_diminished_tuplets is True:
        ...         rmakers.toggle_diminished_tuplets(tuplets)
        ...     tweak_string = r"\tweak text #tuplet-number::calc-fraction-text"
        ...     for tuplet in tuplets:
        ...         abjad.tweak(tuplet, tweak_string)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        Does not toggle diminished tuplets:

        >>> pairs = [(2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs, toggle_diminished_tuplets=False)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Toggles diminished tuplets:

        >>> pairs = [(2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs, toggle_diminished_tuplets=True)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            \time 2/8
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if tuplet.ratio().is_diminished() is True:
            tuplet.toggle_prolation()


def toggle_augmented_tuplets(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Toggles prolation of augmented tuplets in ``tuplets``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, toggle_augmented_tuplets=False):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1], 16, extra_counts=[0, -1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.swap_trivial_tuplets_for_containers(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     if toggle_augmented_tuplets is True:
        ...         rmakers.toggle_augmented_tuplets(tuplets)
        ...     tweak_string = r"\tweak text #tuplet-number::calc-fraction-text"
        ...     for tuplet in tuplets:
        ...         abjad.tweak(tuplet, tweak_string)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        Does not toggle augmented tuplets:

        >>> pairs = [(1, 4), (1, 4), (1, 4), (1, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, toggle_augmented_tuplets=False)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \time 1/4
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Toggles augmented tuplets:

        >>> pairs = [(1, 4), (1, 4), (1, 4), (1, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, toggle_augmented_tuplets=True)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \time 1/4
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if tuplet.ratio().is_augmented() is True:
            tuplet.toggle_prolation()


def trivialize_tuplets(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Trivializes tuplets that can be rewritten as 1:1 in ``tuplets``.

    ..  container:: example

        Leaves trivializable tuplets as-is when no tuplet command is given. The
        tuplets in measures 2 and 4 can be written as trivial tuplets, but they
        are not:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tuplet 3/2
                        {
                            \time 4/8
                            c'4.
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tuplet 3/2
                        {
                            \time 4/8
                            c'4.
                            c'4.
                        }
                    }
                }
            }

        Rewrites trivializable tuplets as trivial (1:1) tuplets when ``trivialize`` is
        true:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.trivialize_tuplets(tuplets)
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                        }
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        tuplet.trivialize()


def tweak_skip_filled_tuplets_stencil_false(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    """
    Tweaks each skip-filled tuplet in ``tuplets`` with ``stencil ##f``.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if all(isinstance(_, abjad.Skip) for _ in tuplet):
            abjad.tweak(tuplet, r"\tweak stencil ##f")


def tweak_trivial_tuplets_stencil_false(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    r"""
    Tweaks trivial tuplets in ``tuplets`` with ``stencil ##f``.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.docs.make_time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.attach_beams_to_runs_by_leaf_list(leaf_lists)
        ...     tuplets = abjad.select.tuplets(tuplets)[-2:]
        ...     rmakers.tweak_trivial_tuplets_stencil_false(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak stencil ##f
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak stencil ##f
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if tuplet.is_trivial():
            abjad.tweak(tuplet, r"\tweak stencil ##f")


def tweak_tuplet_number_text_calc_fraction_text(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> None:
    """
    Tweaks tuplet number text for tuplets in ``argument``. Sets tuplet number
    text equal to ``#tuplet-number::calc-fraction-text`` when any of these
    conditions is true:

      * tuplet is an augmentation (like 3:4), or
      * tuplet is nondyadic (like 4:3), or
      * tuplet multiplier equals 1

    Does not tweak tuplets for which none of these conditions holds.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    for tuplet in tuplets:
        if "text" in vars(abjad.override(tuplet).TupletNumber):
            continue
        if (
            tuplet.ratio().is_augmented()
            or not tuplet.ratio().is_dyadic()
            or tuplet.multiplier() == 1
        ):
            abjad.tweak(tuplet, r"\tweak text #tuplet-number::calc-fraction-text")


def wrap_in_time_signature_staff(
    components: collections.abc.Iterable[abjad.Component],
    time_signatures: collections.abc.Iterable[abjad.TimeSignature],
) -> abjad.Voice:
    """
    Wraps ``components`` in two-voice staff.

    One voice for ``components`` and another voice for ``time_signatures``.

    See ``rmakers.rewrite_meter()`` for examples of this function.
    """
    assert _is_component_list(components), repr(components)
    assert _is_time_signature_list(time_signatures), repr(time_signatures)
    staff = abjad.Staff(simultaneous=True)
    abjad.Score([staff], name="Score")
    time_signature_voice = abjad.Voice(name="TimeSignatureVoice")
    staff.append(time_signature_voice)
    voice = abjad.Voice(name="RhythmMaker.Music")
    staff.append(voice)
    for time_signature in time_signatures:
        duration = time_signature.pair
        skip = abjad.Skip("s1", dmp=duration)
        time_signature_voice.append(skip)
        abjad.attach(time_signature, skip, context="Staff")
    voice.extend(components)
    for tuplet in abjad.iterate.components(voice, abjad.Tuplet):
        assert tuplet.ratio().is_normalized(), repr(tuplet)
        assert len(tuplet), repr(tuplet)
    return voice
