"""
The rmakers classes.
"""

from __future__ import annotations

import dataclasses
import typing

import abjad


def _is_duration(argument: object) -> bool:
    return isinstance(argument, abjad.Duration)


def _is_integer_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, int) for _ in argument)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Incise:
    """
    Incise.
    """

    talea_denominator: int
    body_proportion: tuple[int, ...] = (1,)
    fill_with_rests: bool = False
    outer_tuplets_only: bool = False
    prefix_counts: list[int] = dataclasses.field(default_factory=list)
    prefix_talea: list[int] = dataclasses.field(default_factory=list)
    suffix_counts: list[int] = dataclasses.field(default_factory=list)
    suffix_talea: list[int] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        assert isinstance(self.body_proportion, tuple), repr(self.body_proportion)
        assert isinstance(self.fill_with_rests, bool), repr(self.fill_with_rests)
        assert isinstance(self.outer_tuplets_only, bool), repr(self.outer_tuplets_only)
        assert _is_integer_list(self.prefix_talea)
        assert _is_integer_list(self.prefix_counts)
        if 0 < len(self.prefix_talea):
            assert 0 < len(self.prefix_counts)
        assert _is_integer_list(self.suffix_talea)
        assert _is_integer_list(self.suffix_counts)
        if 0 < len(self.suffix_talea):
            assert 0 < len(self.suffix_counts)
        assert isinstance(self.talea_denominator, int), repr(self.talea_denominator)
        assert abjad.math.is_nonnegative_integer_power_of_two(self.talea_denominator)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Interpolation:
    """
    Interpolation.
    """

    start_duration: abjad.Duration = abjad.Duration(1, 8)
    stop_duration: abjad.Duration = abjad.Duration(1, 16)
    written_duration: abjad.Duration = abjad.Duration(1, 16)

    def __post_init__(self) -> None:
        assert _is_duration(self.start_duration), repr(self.start_duration)
        assert _is_duration(self.stop_duration), repr(self.stop_duration)
        assert _is_duration(self.written_duration), repr(self.written_duration)

    def reverse(self) -> Interpolation:
        """
        Swaps start duration and stop duration of interpolation.

        ..  container:: example

            >>> interpolation = rmakers.Interpolation(
            ...     start_duration=abjad.Duration(1, 4),
            ...     stop_duration=abjad.Duration(1, 16),
            ...     written_duration=abjad.Duration(1, 16),
            ... )

            >>> interpolation = interpolation.reverse()
            >>> interpolation.start_duration
            Duration(numerator=1, denominator=16)

            >>> interpolation.stop_duration
            Duration(numerator=1, denominator=4)

        """
        return Interpolation(
            start_duration=self.stop_duration,
            stop_duration=self.start_duration,
            written_duration=self.written_duration,
        )


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Spelling:
    r"""
    Duration spelling.

    ..  container:: example

        Decreases monotically:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

        >>> lilypond_file = make_lilypond_file([(3, 4), (3, 4)])
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
                        c'4
                        ~
                        c'16
                        [
                        c'8
                        ]
                        ~
                        c'8.
                        c'4
                        ~
                        c'16
                        c'4
                    }
                }
            }

    ..  container:: example

        Increases monotically:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

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
                        \time 3/4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'8
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

    ..  container:: example

        Forbids note durations equal to ``1/4`` or greater:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [1, 1, 1, 1, 4, -4],
        ...         16,
        ...         spelling=rmakers.Spelling(
        ...             forbidden_note_duration=abjad.Duration(1, 4)
        ...         ),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

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
                        \time 3/4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        ]
                        r4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        ]
                        r4
                    }
                }
            }

    ..  container:: example

        Forbids rest durations equal to ``1/4`` or greater:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [1, 1, 1, 1, 4, -4],
        ...         16,
        ...         spelling=rmakers.Spelling(
        ...             forbidden_rest_duration=abjad.Duration(1, 4)
        ...         ),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

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
                        \time 3/4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        r8
                        r8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        r8
                        r8
                    }
                }
            }

    ..  container:: example

        Spells nonassignable durations with monontonically decreasing durations:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (5, 8), (5, 8)]
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
                        \time 5/8
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                    }
                }
            }

    ..  container:: example

        Spells nonassignable durations with monontonically increasing durations:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (5, 8), (5, 8)]
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
                        \time 5/8
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                    }
                }
            }

    ..  container:: example

        Forbids durations equal to ``1/4`` or greater:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [1, 1, 1, 1, 4, 4], 16,
        ...         spelling=rmakers.Spelling(
        ...             forbidden_note_duration=abjad.Duration(1, 4)
        ...         ),
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
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
                        \time 3/4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        c'8
                        ~
                        c'8
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        c'8
                        ~
                        c'8
                        ]
                    }
                }
            }

        Rewrites forbidden durations with smaller durations tied together.

    """

    forbidden_note_duration: abjad.Duration | None = None
    forbidden_rest_duration: abjad.Duration | None = None
    increase_monotonic: bool = False

    def __post_init__(self):
        if self.forbidden_note_duration is not None:
            assert _is_duration(self.forbidden_note_duration), repr(
                self.forbidden_note_duration
            )
        if self.forbidden_rest_duration is not None:
            assert _is_duration(self.forbidden_rest_duration), repr(
                self.forbidden_rest_duration
            )
        assert isinstance(self.increase_monotonic, bool), repr(self.increase_monotonic)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Talea:
    """
    Talea.

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [2, 1, 3, 2, 4, 1, 1],
        ...     16,
        ...     preamble=[1, 1, 1, 1],
        ... )

    ..  container:: example

        Equal to weight of counts:

        >>> rmakers.Talea([1, 2, 3, 4], 16).period()
        10

        Rests make no difference:

        >>> rmakers.Talea([1, 2, -3, 4], 16).period()
        10

        Denominator makes no difference:

        >>> rmakers.Talea([1, 2, -3, 4], 32).period()
        10

        Preamble makes no difference:

        >>> talea = rmakers.Talea(
        ...     [1, 2, -3, 4],
        ...     32,
        ...     preamble=[1, 1, 1],
        ... )

        >>> talea.period()
        10

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [2, 1, 3, 2, 4, 1, 1],
        ...     16,
        ...     preamble=[1, 1, 1, 1],
        ... )

        >>> talea.preamble
        [1, 1, 1, 1]

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [16, -4, 16],
        ...     16,
        ...     preamble=[1],
        ... )

        >>> for i, duration in enumerate(talea):
        ...     duration
        ...
        Duration(numerator=1, denominator=16)
        Duration(numerator=1, denominator=1)
        Duration(numerator=-1, denominator=4)
        Duration(numerator=1, denominator=1)

    """

    counts: list[int | str]
    denominator: int
    end_counts: list[int] = dataclasses.field(default_factory=list)
    # TODO: change `preamble` to `preamble_counts`
    preamble: list[int] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        assert isinstance(self.counts, list), repr(self.counts)
        for count in self.counts:
            assert isinstance(count, int) or count in "+-", repr(count)
        assert abjad.math.is_positive_integer_power_of_two(self.denominator)
        assert _is_integer_list(self.end_counts), repr(self.end_counts)
        assert _is_integer_list(self.preamble), repr(self.preamble)

    def __contains__(self, argument: int) -> bool:
        """
        Is true when talea contains ``argument``.

        ..  container:: example

            With preamble:

            >>> talea = rmakers.Talea([10],16,preamble=[1, -1, 1])
            >>> for i in range(1, 23 + 1):
            ...     i, i in talea
            ...
            (1, True)
            (2, True)
            (3, True)
            (4, False)
            (5, False)
            (6, False)
            (7, False)
            (8, False)
            (9, False)
            (10, False)
            (11, False)
            (12, False)
            (13, True)
            (14, False)
            (15, False)
            (16, False)
            (17, False)
            (18, False)
            (19, False)
            (20, False)
            (21, False)
            (22, False)
            (23, True)

        """
        assert isinstance(argument, int), repr(argument)
        assert 0 < argument, repr(argument)
        if self.preamble:
            preamble = [abs(_) for _ in self.preamble]
            cumulative = abjad.math.cumulative_sums(preamble)[1:]
            if argument in cumulative:
                return True
            preamble_weight = abjad.math.weight(preamble, start=0)
        else:
            preamble_weight = 0
        if self.counts is not None:
            counts = []
            for count in self.counts:
                assert isinstance(count, int)
                counts.append(abs(count))
        else:
            counts = []
        cumulative = abjad.math.cumulative_sums(counts)[:-1]
        argument -= preamble_weight
        argument %= self.period()
        return argument in cumulative

    # TODO: how do you typehint `argument`?
    def __getitem__(self, argument) -> tuple[int, int] | list[tuple[int, int]]:
        """
        Gets item or slice identified by ``argument``.

        Gets item at index:

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea[0]
            (1, 16)

            >>> talea[1]
            (1, 16)

        ..  container:: example

            Gets items in slice:

            >>> for duration in talea[:6]:
            ...     duration
            ...
            (1, 16)
            (1, 16)
            (1, 16)
            (1, 16)
            (2, 16)
            (1, 16)

            >>> for duration in talea[2:8]:
            ...     duration
            ...
            (1, 16)
            (1, 16)
            (2, 16)
            (1, 16)
            (3, 16)
            (2, 16)

        """
        preamble: list[int | str] = list(self.preamble)
        counts = list(self.counts)
        counts_ = abjad.CyclicTuple(preamble + counts)
        if isinstance(argument, int):
            count = counts_.__getitem__(argument)
            return (count, self.denominator)
        elif isinstance(argument, slice):
            counts_ = counts_.__getitem__(argument)
            result = [(count, self.denominator) for count in counts_]
            return result
        raise ValueError(argument)

    def __iter__(self) -> typing.Iterator[abjad.Duration]:
        """
        Iterates talea.

        ..  container:: example

            >>> talea = rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16, preamble=[1, 1, 1, 1])
            >>> for duration in talea:
            ...     duration
            ...
            Duration(numerator=1, denominator=16)
            Duration(numerator=1, denominator=16)
            Duration(numerator=1, denominator=16)
            Duration(numerator=1, denominator=16)
            Duration(numerator=1, denominator=8)
            Duration(numerator=1, denominator=16)
            Duration(numerator=3, denominator=16)
            Duration(numerator=1, denominator=8)
            Duration(numerator=1, denominator=4)
            Duration(numerator=1, denominator=16)
            Duration(numerator=1, denominator=16)

        """
        for count in self.preamble or []:
            duration = abjad.Duration(count, self.denominator)
            yield duration
        for item in self.counts or []:
            assert isinstance(item, int)
            duration = abjad.Duration(item, self.denominator)
            yield duration

    def __len__(self) -> int:
        """
        Gets length.

        ..  container:: example

            >>> talea = rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16)
            >>> len(talea)
            7

        Defined equal to length of counts.
        """
        return len(self.counts or [])

    # TODO: FIXME
    def advance(self, weight: int) -> Talea:
        """
        Advances talea by ``weight``.

        ..  container:: example

            >>> talea = rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16, preamble=[1, 1, 1, 1])
            >>> talea.counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(0).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(1).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(2).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(3).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(4).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(5).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(6).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(7).counts
            [2, 1, 3, 2, 4, 1, 1]

            >>> talea.advance(8).counts
            [2, 1, 3, 2, 4, 1, 1]

        """
        assert isinstance(weight, int), repr(weight)
        if weight < 0:
            raise Exception(f"weight {weight} must be nonnegative.")
        if weight == 0:
            return dataclasses.replace(self)
        preamble: list[int] = list(self.preamble)
        counts = []
        for count in self.counts:
            assert isinstance(count, int), repr(count)
            counts.append(count)
        if weight < abjad.math.weight(preamble, start=0):
            consumed, remaining = abjad.sequence.split(
                preamble,
                [weight],
                overhang=True,
            )
            preamble_ = remaining
        elif weight == abjad.math.weight(preamble, start=0):
            preamble_ = []
        else:
            assert abjad.math.weight(preamble, start=0) < weight
            weight -= abjad.math.weight(preamble, start=0)
            preamble = counts[:]
            while True:
                if weight <= abjad.math.weight(preamble, start=0):
                    break
                preamble += counts
            if abjad.math.weight(preamble, start=0) == weight:
                consumed, remaining = preamble[:], []
            else:
                consumed, remaining = abjad.sequence.split(
                    preamble,
                    [weight],
                    overhang=True,
                )
            preamble_ = remaining
        return dataclasses.replace(
            self,
            # TODO: remove typehinting problem that comes with removing list():
            counts=list(counts),
            denominator=self.denominator,
            preamble=preamble_,
        )

    def period(self) -> int:
        """
        Gets period of talea.

        ..  container:: example

            Equal to weight of counts:

            >>> rmakers.Talea([1, 2, 3, 4], 16).period()
            10

            Rests make no difference:

            >>> rmakers.Talea([1, 2, -3, 4], 16).period()
            10

            Denominator makes no difference:

            >>> rmakers.Talea([1, 2, -3, 4], 32).period()
            10

            Preamble makes no difference:

            >>> talea = rmakers.Talea(
            ...     [1, 2, -3, 4],
            ...     32,
            ...     preamble=[1, 1, 1],
            ... )

            >>> talea.period()
            10

        """
        counts = []
        for count in self.counts:
            if isinstance(count, str):
                raise ValueError("can not calculate period.")
            else:
                counts.append(count)
        return abjad.math.weight(counts, start=0)
