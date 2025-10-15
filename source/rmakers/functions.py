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


def beam_across_leaf_lists(
    leaf_lists: collections.abc.Iterable[collections.abc.Iterable[abjad.Leaf]],
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Beams across ``leaf_lists`` with single span beam.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_across_leaf_lists(leaf_lists)
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
    unbeam_leaves(leaves)
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


def beam_runs(
    leaf_lists: collections.abc.Iterable[collections.abc.Sequence[abjad.Leaf]],
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Beams runs in each leaf list in ``leaf_lists``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, beam_rests=False, stemlet_length=None):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 1, 1, -1], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_runs(
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

        By default, ``rmakers.beam_runs()`` unbeams input before applying new beams:

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

        >>> rmakers.beam_runs([staff[:]])
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
        unbeam_leaves(leaf_list)
        abjad.beam(
            leaf_list,
            beam_lone_notes=beam_lone_notes,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )


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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_runs(leaf_lists)
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


# TODO: rename
def force_augmentation(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Spells each tuplet in ``tuplets`` as an augmentation.

    ..  container:: example

        >>> def make_lilypond_file(pairs, force_augmentation=False):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_runs(leaf_lists)
        ...     if force_augmentation is True:
        ...         rmakers.force_augmentation(tuplets)
        ...     tweak_string = r"\tweak text #tuplet-number::calc-fraction-text"
        ...     for tuplet in tuplets:
        ...         abjad.tweak(tuplet, tweak_string)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        Without forced augmentation:

        >>> pairs = [(2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs, force_augmentation=False)
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

        With forced augmentation:

        >>> pairs = [(2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs, force_augmentation=True)
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
        if not tuplet.ratio().is_augmented():
            tuplet.toggle_prolation()


# TODO: rename
def force_diminution(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Spells each tuplet in ``tuplets`` as diminution.

    ..  container:: example

        >>> def make_lilypond_file(pairs, force_diminution=False):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1], 16, extra_counts=[0, -1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_runs(leaf_lists)
        ...     rmakers.swap_trivial_tuplets_for_containers(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     if force_diminution is True:
        ...         rmakers.force_diminution(tuplets)
        ...     tweak_string = r"\tweak text #tuplet-number::calc-fraction-text"
        ...     for tuplet in tuplets:
        ...         abjad.tweak(tuplet, tweak_string)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        Without forced diminution (default):

        >>> pairs = [(1, 4), (1, 4), (1, 4), (1, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, force_diminution=False)
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

        With forced diminution (default):

        >>> pairs = [(1, 4), (1, 4), (1, 4), (1, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, force_diminution=True)
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
        if not tuplet.ratio().is_diminished():
            tuplet.toggle_prolation()


# TODO: rename to `replace_leaves_with_notes`
def force_note(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Replaces each leaf in ``leaves`` with note.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     components = rmakers.note(durations)
        ...     container = abjad.Container(components)
        ...     rmakers.force_rest(components)
        ...     rests = container[1:3]
        ...     rmakers.force_note(rests)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     components = rmakers.note(durations)
        ...     container = abjad.Container(components)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.force_rest(leaves)
        ...     leaves = abjad.select.get(container[:], [0, -1])
        ...     rmakers.force_note(leaves)
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


# TODO: rename to `replace_ties_with_repeat_ties`
def force_repeat_tie(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
    threshold: bool | abjad.Duration | typing.Callable = True,
) -> None:
    r"""
    Replaces ties attached to ``leaves`` with repeat-ties.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
        >>> rmakers.force_repeat_tie(leaves)
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


# TODO: rename to `replace_leaves_with_rests`
def force_rest(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Replaces each leaf in ``leaves`` with rest.

    ..  container:: example

        Forces first and last logical ties to rest:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     leaves = abjad.select.get(leaves, [0, -1])
        ...     rmakers.force_rest(leaves)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     container = abjad.Container(tuplets)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.force_rest(leaves)
        ...     leaves = abjad.select.leaves(container)
        ...     rests = abjad.select.get(leaves[:], [0, -1])
        ...     rmakers.force_note(rests)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     leaves = abjad.select.leaves(tuplets)
        ...     rmakers.force_rest(leaves)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     leaves = abjad.select.get(leaves, [0, -2, -1])
        ...     rmakers.force_rest(leaves)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = [abjad.select.leaf(_, 0) for _ in tuplets]
        ...     rmakers.force_rest(leaves)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.beam_runs(leaf_lists)
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


# TODO: rename to `tag_each_leaf_as_invisible_music`
def invisible_music(
    leaves: collections.abc.Iterable[abjad.Leaf],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    """
    Makes ``argument`` invisible.
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


# TODO: rename to `make_interpolation`
def interpolate(
    start_duration: abjad.Duration,
    stop_duration: abjad.Duration,
    written_duration: abjad.Duration,
) -> _classes.Interpolation:
    """
    Makes interpolation.
    """
    return _classes.Interpolation(
        start_duration,
        stop_duration,
        written_duration,
    )


# TODO: rename to `select_nongrace_leaves_in_each_tuplet` & clean up typehint
def nongrace_leaves_in_each_tuplet(
    tuplets: collections.abc.Iterable[abjad.Tuplet],
) -> list[list[abjad.Leaf]]:
    """
    Selects nongrace leaves in each tuplet in ``tuplets``.
    """
    assert _is_tuplet_list(tuplets), repr(tuplets)
    leaf_lists = [abjad.select.leaves(_, grace=False) for _ in tuplets]
    assert _is_list_of_leaf_lists(leaf_lists), repr(leaf_lists)
    return leaf_lists


# TODO: rename with verb
def on_beat_grace_container(
    voice: abjad.Voice,
    voice_name: str,
    nongrace_leaf_lists: collections.abc.Iterable[collections.abc.Iterable[abjad.Leaf]],
    counts: collections.abc.Sequence[int],
    *,
    grace_leaf_duration: abjad.Duration | None = None,
    grace_polyphony_command: abjad.VoiceNumber = abjad.VoiceNumber(1),
    nongrace_polyphony_command: abjad.VoiceNumber = abjad.VoiceNumber(2),
    tag: abjad.Tag = abjad.Tag(),
    talea: _classes.Talea = _classes.Talea([1], 8),
) -> None:
    r"""
    Makes on-beat grace containers.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     notes = abjad.select.notes(notes)
        ...     groups = [[_] for _ in notes]
        ...     rmakers.on_beat_grace_container(
        ...         voice,
        ...         "RhythmMaker.Music",
        ...         groups,
        ...         [2, 4],
        ...         grace_leaf_duration=abjad.Duration(1, 28)
        ...     )
        ...     components = abjad.mutate.eject_contents(voice)
        ...     music_voice = abjad.Voice(components, name="RhythmMaker.Music")
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         [music_voice], time_signatures, includes=["abjad.ily"]
        ...     )
        ...     staff = lilypond_file["Staff"]
        ...     abjad.override(staff).TupletBracket.direction = abjad.UP
        ...     abjad.override(staff).TupletBracket.staff_padding = 5
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
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
                    \override TupletBracket.direction = #up
                    \override TupletBracket.staff-padding = 5
                }
                {
                    \context Voice = "Voice"
                    {
                        \context Voice = "RhythmMaker.Music"
                        {
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/3
                            {
                                \time 3/4
                                c'4
                                <<
                                    \context Voice = "On_Beat_Grace_Container"
                                    {
                                        \set fontSize = #-3
                                        \slash
                                        \voiceOne
                                        <
                                            \tweak font-size 0
                                            \tweak transparent ##t
                                            c'
                                        >8 * 10/21
                                        [
                                        (
                                        c'8 * 10/21
                                        )
                                        ]
                                    }
                                    \context Voice = "RhythmMaker.Music"
                                    {
                                        \voiceTwo
                                        c'4
                                    }
                                >>
                                <<
                                    \context Voice = "On_Beat_Grace_Container"
                                    {
                                        \set fontSize = #-3
                                        \slash
                                        \voiceOne
                                        <
                                            \tweak font-size 0
                                            \tweak transparent ##t
                                            c'
                                        >8 * 10/21
                                        [
                                        (
                                        c'8 * 10/21
                                        c'8 * 10/21
                                        c'8 * 10/21
                                        )
                                        ]
                                    }
                                    \context Voice = "RhythmMaker.Music"
                                    {
                                        \voiceTwo
                                        c'4
                                    }
                                >>
                                <<
                                    \context Voice = "On_Beat_Grace_Container"
                                    {
                                        \set fontSize = #-3
                                        \slash
                                        \voiceOne
                                        <
                                            \tweak font-size 0
                                            \tweak transparent ##t
                                            c'
                                        >8 * 10/21
                                        [
                                        (
                                        c'8 * 10/21
                                        )
                                        ]
                                    }
                                    \context Voice = "RhythmMaker.Music"
                                    {
                                        \voiceTwo
                                        c'4
                                    }
                                >>
                                \oneVoice
                                c'4
                            }
                        }
                    }
                }
            }

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5], 16)
        ...     voice = abjad.Voice(tuplets)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     logical_ties = abjad.select.logical_ties(voice)
        ...     leaf_lists = [list(_) for _ in logical_ties]
        ...     rmakers.on_beat_grace_container(
        ...         voice,
        ...         "RhythmMaker.Music",
        ...         leaf_lists,
        ...         [6, 2],
        ...         grace_leaf_duration=abjad.Duration(1, 28)
        ...     )
        ...     components = abjad.mutate.eject_contents(voice)
        ...     music_voice = abjad.Voice(components, name="RhythmMaker.Music")
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         [music_voice], time_signatures, includes=["abjad.ily"]
        ...     )
        ...     return lilypond_file

        >>> pairs = [(3, 4), (3, 4)]
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
                        \context Voice = "RhythmMaker.Music"
                        {
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \time 3/4
                                    \voiceTwo
                                    c'4
                                    ~
                                    c'16
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                    ~
                                    c'16
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'8
                                    ~
                                    c'8.
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                    ~
                                    c'16
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                        }
                    }
                }
            }

    """
    assert _is_integer_list(counts), repr(counts)
    assert _is_list_of_leaf_lists(nongrace_leaf_lists), repr(nongrace_leaf_lists)
    assert isinstance(voice, abjad.Voice), repr(voice)
    assert isinstance(voice_name, str), repr(voice_name)
    assert isinstance(talea, _classes.Talea), repr(talea)
    assert isinstance(grace_polyphony_command, abjad.VoiceNumber), repr(
        grace_polyphony_command
    )
    assert isinstance(nongrace_polyphony_command, abjad.VoiceNumber), repr(
        nongrace_polyphony_command
    )
    tag = tag.append(_function_name(inspect.currentframe()))
    if voice_name:
        voice.set_name(voice_name)
    counts_cycle = abjad.CyclicTuple(counts)
    start = 0
    for i, nongrace_leaves in enumerate(nongrace_leaf_lists):
        assert all(isinstance(_, abjad.Leaf) for _ in nongrace_leaves), repr(
            nongrace_leaves
        )
        count = counts_cycle[i]
        if not count:
            continue
        stop = start + count
        pitch_list = [abjad.NamedPitch("c'")]
        durations = abjad.duration.durations(list(talea[start:stop]))
        leaves = abjad.makers.make_leaves([pitch_list], durations)
        grace_leaves = [_ for _ in leaves if isinstance(_, abjad.Leaf)]
        abjad.on_beat_grace_container(
            grace_leaves,
            nongrace_leaves,
            grace_leaf_duration=grace_leaf_duration,
            grace_polyphony_command=grace_polyphony_command,
            nongrace_polyphony_command=nongrace_polyphony_command,
            tag=tag,
        )


def override_beam_grow_direction(
    leaf_lists: collections.abc.Iterable[collections.abc.Sequence[abjad.Leaf]],
    *,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Overrides ``Beam.grow-direction`` on first leaf in each leaf list in
    ``leaf_lists``.

    ..  container:: example

        >>> def make_lilypond_file():
        ...     voice = abjad.Voice("c'16 d' r f' g'8")
        ...     rmakers.beam_runs([voice[:]], beam_rests=True, stemlet_length=1)
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
        """
        unbeam_leaves(leaf_list)
        abjad.beam(
            leaf_list,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )
        """
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


# TODO: rename to `attach_repeat_tie_to_each_leaf`
def repeat_tie(
    pleaves: collections.abc.Iterable[abjad.Note | abjad.Chord],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Attaches repeat-ties to pitched leaves in ``pleaves``.

    ..  container:: example

        Attaches repeat-tie to first pitched leaf in each nonfirst tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)[1:]
        ...     notes = [abjad.select.note(_, 0) for _ in tuplets]
        ...     rmakers.repeat_tie(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     notes = [abjad.select.notes(_)[1:] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.repeat_tie(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, 4], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = rmakers.wrap_in_time_signature_staff(tuplets, time_signatures)
        ...     rmakers.beam_runs(leaf_lists)
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
        unbeam_leaves(nontupletted_leaves)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_sustained_tuplets(tuplets)
        ...     tuplets = abjad.select.tuplets(container, level=1)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     container = abjad.Container(tuplets)
        ...     rmakers.beam_runs(leaf_lists)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained_tuplets(tuplets[-2:])
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained_tuplets(tuplets)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_runs(leaf_lists)
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


# TODO: rename to `attach_tie_to_each_pleaf`
def tie(
    pleaves: collections.abc.Iterable[abjad.Note | abjad.Chord],
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Attaches ties to pitched leaves in ``argument``.

    ..  container:: example

        Attaches tie to last pitched leaf in each nonlast tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(tuplets)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, 3, 3, 3], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(tuplets)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, 3, 3, 3], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets[:-1], [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [5, -3, 3, 3], 16)
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     rmakers.untie_leaves(leaves)
        ...     runs = abjad.select.runs(voice)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in runs]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.tie(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     notes = abjad.sequence.flatten(notes)
        ...     rmakers.untie_leaves(notes)
        ...     rmakers.tie(notes)
        ...     rmakers.beam_runs(leaf_lists)
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


# TODO: rename to `make_time_signatures()` and move to docs.py
def time_signatures(
    pairs: collections.abc.Iterable[tuple[int, int]],
) -> list[abjad.TimeSignature]:
    """
    Makes time signatures from ``pairs``.

    Documentation helper.
    """
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    return [abjad.TimeSignature(_) for _ in pairs]


# TODO: rename with verb
def tremolo_container(
    pleaves: collections.abc.Iterable[abjad.Note | abjad.Chord],
    count: int,
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Replaces pitched leaves in ``argument`` with tremolo containers.

    ..  container:: example

        Repeats figures two times each:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [4])
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     groups = [abjad.select.get(_, [0, -1]) for _ in notes]
        ...     notes = abjad.sequence.flatten(groups)
        ...     rmakers.tremolo_container(notes, 2)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     containers = abjad.select.components(voice, abjad.TremoloContainer)
        ...     result = [abjad.slur(_) for _ in containers]
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 4), (3, 4)]
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
                        \repeat tremolo 2
                        {
                            \time 4/4
                            c'16
                            (
                            c'16
                            )
                        }
                        c'4
                        c'4
                        \repeat tremolo 2
                        {
                            c'16
                            (
                            c'16
                            )
                        }
                        \repeat tremolo 2
                        {
                            \time 3/4
                            c'16
                            (
                            c'16
                            )
                        }
                        c'4
                        \repeat tremolo 2
                        {
                            c'16
                            (
                            c'16
                            )
                        }
                    }
                }
            }

        Repeats figures four times each:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [4])
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     groups = [abjad.select.get(_, [0, -1]) for _ in notes]
        ...     notes = abjad.sequence.flatten(groups)
        ...     rmakers.tremolo_container(notes, 4)
        ...     rmakers.extract_trivial_tuplets(tuplets)
        ...     containers = abjad.select.components(voice, abjad.TremoloContainer)
        ...     result = [abjad.slur(_) for _ in containers]
        ...     rmakers.docs.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 4), (3, 4)]
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
                        \repeat tremolo 4
                        {
                            \time 4/4
                            c'32
                            (
                            c'32
                            )
                        }
                        c'4
                        c'4
                        \repeat tremolo 4
                        {
                            c'32
                            (
                            c'32
                            )
                        }
                        \repeat tremolo 4
                        {
                            \time 3/4
                            c'32
                            (
                            c'32
                            )
                        }
                        c'4
                        \repeat tremolo 4
                        {
                            c'32
                            (
                            c'32
                            )
                        }
                    }
                }
            }

    """
    assert _is_pleaf_list(pleaves), repr(pleaves)
    assert isinstance(count, int), repr(count)
    tag = tag.append(_function_name(inspect.currentframe()))
    pitch = abjad.NamedPitch("c'")
    for pleaf in pleaves:
        container_duration = pleaf.written_duration()
        note_duration = container_duration / (2 * count)
        left_note = abjad.Note.from_duration_and_pitch(note_duration, pitch)
        right_note = abjad.Note.from_duration_and_pitch(note_duration, pitch)
        container = abjad.TremoloContainer(count, [left_note, right_note], tag=tag)
        abjad.mutate.replace(pleaf, container)


def trivialize_tuplets(tuplets: collections.abc.Iterable[abjad.Tuplet]) -> None:
    r"""
    Trivializes tuplets that can be rewritten as 1:1 in ``tuplets``.

    ..  container:: example

        Leaves trivializable tuplets as-is when no tuplet command is given. The
        tuplets in measures 2 and 4 can be written as trivial tuplets, but they
        are not:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
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
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_runs(leaf_lists)
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


# TODO: rename with `detach_`
def unbeam_leaves(
    leaves: collections.abc.Sequence[abjad.Leaf],
    *,
    smart: bool = False,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    r"""
    Unbeams each leaf in ``leaves``.

    Adjusts adjacent start- and stop-beams when ``smart=True``.

    ..  container:: example

        Unbeams 1 note:

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[:1], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        [
                        e'8
                        f'8
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[1:2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[2:3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        ]
                        e'8
                        f'8
                        [
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[3:4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        ]
                        f'8
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[4:5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        f'8
                        ]
                        g'8
                        a'8
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[5:6], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        f'8
                        g'8
                        ]
                        a'8
                    }
                }
            >>

    ..  container:: example

        Unbeams 2 notes:

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[:2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[1:3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        f'8
                        [
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[2:4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        ]
                        e'8
                        f'8
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[3:5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        ]
                        f'8
                        g'8
                        a'8
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[4:], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        f'8
                        ]
                        g'8
                        a'8
                    }
                }
            >>

    ..  container:: example

        Unbeams 1 note:

        >>> voice = abjad.Voice("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[:1], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        ]
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(voice[1:2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        ]
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[2:3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[3:4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[4:5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    a'8
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[5:6], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    a'8
                }
            >>

    ..  container:: example

        Unbeams 2 notes:

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[:2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    d'8
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[1:3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    d'8
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[2:4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[3:5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    a'8
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam_leaves(staff[4:], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    a'8
                }
            >>

    """
    assert _is_leaf_list(leaves), repr(leaves)
    assert isinstance(smart, bool), repr(smart)
    leaf: abjad.Leaf | None
    for leaf in leaves:
        abjad.detach(abjad.BeamCount, leaf)
        abjad.detach(abjad.StartBeam, leaf)
        abjad.detach(abjad.StopBeam, leaf)
    if smart is True:
        tag = tag.append(_function_name(inspect.currentframe()))
        unmatched_start_beam = False
        leaf = leaves[0]
        leaf = abjad.get.leaf(leaf, -1)
        if leaf is not None:
            if abjad.get.has_indicator(leaf, abjad.StopBeam):
                pass
            elif abjad.get.has_indicator(leaf, abjad.StartBeam):
                abjad.detach(abjad.StartBeam, leaf)
            else:
                while True:
                    leaf = abjad.get.leaf(leaf, -1)
                    if leaf is None:
                        break
                    if abjad.get.has_indicator(leaf, abjad.StopBeam):
                        break
                    if abjad.get.has_indicator(leaf, abjad.StartBeam):
                        unmatched_start_beam = True
                        break
        unmatched_stop_beam = False
        leaf = leaves[-1]
        leaf = abjad.get.leaf(leaf, 1)
        if leaf is not None:
            if abjad.get.has_indicator(leaf, abjad.StartBeam):
                pass
            elif abjad.get.has_indicator(leaf, abjad.StopBeam):
                abjad.detach(abjad.StopBeam, leaf)
            else:
                while True:
                    leaf = abjad.get.leaf(leaf, 1)
                    if leaf is None:
                        break
                    if abjad.get.has_indicator(leaf, abjad.StartBeam):
                        break
                    if abjad.get.has_indicator(leaf, abjad.StopBeam):
                        unmatched_stop_beam = True
                        break
        if unmatched_start_beam is True:
            leaf = leaves[0]
            leaf = abjad.get.leaf(leaf, -1)
            assert leaf is not None
            abjad.attach(abjad.StopBeam(), leaf, tag=tag)
        if unmatched_stop_beam is True:
            leaf = leaves[-1]
            leaf = abjad.get.leaf(leaf, 1)
            assert leaf is not None
            abjad.attach(abjad.StartBeam(), leaf, tag=tag)


# TODO: rename with `detach_`
def untie_leaves(leaves: collections.abc.Iterable[abjad.Leaf]) -> None:
    r"""
    Unties leaves in ``argument``.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     lilypond_file = rmakers.docs.make_example_lilypond_file(
        ...         tuplets, time_signatures
        ...     )
        ...     voice = lilypond_file["Voice"]
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.tie(notes)
        ...     notes = abjad.select.notes(voice)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.untie_leaves(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     leaf_lists = [_[:] for _ in tuplets]
        ...     voice = abjad.Voice(tuplets)
        ...     notes = abjad.select.notes(voice)[1:]
        ...     rmakers.repeat_tie(notes)
        ...     notes = abjad.select.notes(voice)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.untie_leaves(notes)
        ...     rmakers.beam_runs(leaf_lists)
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
