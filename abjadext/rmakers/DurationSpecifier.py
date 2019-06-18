import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier


class DurationSpecifier(object):
    """
    Duration specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_forbidden_note_duration",
        "_forbidden_rest_duration",
        "_increase_monotonic",
        "_rewrite_meter",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        forbidden_note_duration: abjad.DurationTyping = None,
        forbidden_rest_duration: abjad.DurationTyping = None,
        increase_monotonic: bool = None,
        rewrite_meter: bool = None,
    ) -> None:
        if forbidden_note_duration is None:
            forbidden_note_duration_ = None
        else:
            forbidden_note_duration_ = abjad.Duration(forbidden_note_duration)
        self._forbidden_note_duration = forbidden_note_duration_
        if forbidden_rest_duration is None:
            forbidden_rest_duration_ = None
        else:
            forbidden_rest_duration_ = abjad.Duration(forbidden_rest_duration)
        self._forbidden_rest_duration = forbidden_rest_duration_
        if increase_monotonic is not None:
            increase_monotonic = bool(increase_monotonic)
        self._increase_monotonic = increase_monotonic
        if rewrite_meter is not None:
            rewrite_meter = bool(rewrite_meter)
        self._rewrite_meter = rewrite_meter

    ### SPECIAL METHODS ###

    def __call__(
        self,
        selections: typing.Sequence[abjad.Selection],
        divisions: typing.Sequence[abjad.NonreducedFraction],
        *,
        tag: str = None,
    ) -> typing.List[abjad.Selection]:
        """
        Calls duration specifier.
        """
        if self.rewrite_meter is True:
            selections = DurationSpecifier._rewrite_meter_(
                selections, divisions
            )
        return list(selections)

    def __format__(self, format_specification="") -> str:
        """
        Formats duration specifier.

        ..  container:: example

            >>> specifier = abjadext.rmakers.DurationSpecifier()
            >>> abjad.f(specifier)
            abjadext.rmakers.DurationSpecifier()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.DurationSpecifier()
            DurationSpecifier()

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    @staticmethod
    def _rewrite_meter_(
        selections,
        meters,
        reference_meters=None,
        rewrite_tuplets=False,
        repeat_ties=False,
    ):
        meters = [abjad.Meter(_) for _ in meters]
        durations = [abjad.Duration(_) for _ in meters]
        reference_meters = reference_meters or ()
        selections = DurationSpecifier._split_at_measure_boundaries(
            selections, meters, repeat_ties=repeat_ties
        )
        lengths = [len(_) for _ in selections]
        staff = abjad.Staff(selections)
        assert sum(durations) == abjad.inspect(staff).duration()
        selections = staff[:].partition_by_durations(durations)
        for meter, selection in zip(meters, selections):
            time_signature = abjad.TimeSignature(meter)
            leaf = abjad.inspect(selection).leaf(0)
            abjad.attach(time_signature, leaf)
            container = abjad.Container()
            abjad.mutate(selection).wrap(container)
            for reference_meter in reference_meters:
                if str(reference_meter) == str(meter):
                    meter = reference_meter
                    break

            nontupletted_leaves = []
            for leaf in abjad.iterate(container).leaves():
                if not abjad.inspect(leaf).parentage().count(abjad.Tuplet):
                    nontupletted_leaves.append(leaf)
            BeamSpecifier._detach_all_beams(nontupletted_leaves)

            abjad.mutate(container[:]).rewrite_meter(
                meter, rewrite_tuplets=rewrite_tuplets, repeat_ties=repeat_ties
            )
            leaves = abjad.select(container).leaves(
                do_not_iterate_grace_containers=True
            )
            beat_durations = []
            beat_offsets = meter.depthwise_offset_inventory[1]
            for start, stop in abjad.sequence(beat_offsets).nwise():
                beat_duration = stop - start
                beat_durations.append(beat_duration)
            beamable_groups = BeamSpecifier._make_beamable_groups(
                leaves, beat_durations
            )
            # print(leaves, 'LEAVES')
            # print(beat_durations, 'BEATS')
            for beamable_group in beamable_groups:
                if not beamable_group:
                    continue
                abjad.beam(
                    beamable_group,
                    beam_rests=False,
                    tag="rmakers.DurationSpecifier._rewrite_meter_",
                )
        selections = []
        for container in staff:
            selection = container[:]
            for component in selection:
                component._parent = None
            for leaf in abjad.iterate(selection).leaves():
                abjad.detach(abjad.TimeSignature, leaf)
            selections.append(selection)
        return selections

    @staticmethod
    def _split_at_measure_boundaries(selections, meters, repeat_ties=False):
        meters = [abjad.Meter(_) for _ in meters]
        durations = [abjad.Duration(_) for _ in meters]
        selections = abjad.sequence(selections).flatten(depth=-1)
        meter_duration = sum(durations)
        music_duration = sum(abjad.inspect(_).duration() for _ in selections)
        if not meter_duration == music_duration:
            message = f"Duration of meters is {meter_duration!s}"
            message += f" but duration of selections is {music_duration!s}:"
            message += f"\nmeters: {meters}."
            message += f"\nmusic: {selections}."
            raise Exception(message)
        voice = abjad.Voice(selections)
        abjad.mutate(voice[:]).split(
            durations=durations, tie_split_notes=True, repeat_ties=repeat_ties
        )
        components = abjad.mutate(voice).eject_contents()
        component_durations = [abjad.inspect(_).duration() for _ in components]
        parts = abjad.sequence(component_durations)
        parts = parts.partition_by_weights(
            weights=durations, allow_part_weights=abjad.Exact
        )
        part_lengths = [len(_) for _ in parts]
        parts = abjad.sequence(components).partition_by_counts(
            counts=part_lengths, overhang=abjad.Exact
        )
        selections = [abjad.select(_) for _ in parts]
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def increase_monotonic(self) -> typing.Optional[bool]:
        r"""
        Is true when all durations spell as a tied series of monotonically
        increasing values.

        ..  container:: example

            Decreases monotically:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=False,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        [
                        c'8
                        ~
                        ]
                        c'8.
                        c'4
                        ~
                        c'16
                        c'4
                    }
                >>

        ..  container:: example

            Increases monotically:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=True,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
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
                        ~
                        ]
                        c'4
                        c'4
                    }
                >>

        """
        return self._increase_monotonic

    @property
    def forbidden_note_duration(self) -> typing.Optional[abjad.Duration]:
        r"""
        Gets forbidden note duration.

        ..  container:: example

            Forbids note durations equal to ``1/4`` or greater:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=(1, 4),
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, -4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
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
                >>

        """
        return self._forbidden_note_duration

    @property
    def forbidden_rest_duration(self) -> typing.Optional[abjad.Duration]:
        r"""
        Gets forbidden rest duration.

        ..  container:: example

            Forbids rest durations equal to ``1/4`` or greater:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_rest_duration=(1, 4),
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, -4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
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
                >>

        """
        return self._forbidden_rest_duration

    @property
    def rewrite_meter(self) -> typing.Optional[bool]:
        """
        Is true when all output divisions rewrite meter.

        ..  container:: example

            >>> specifier = abjadext.rmakers.DurationSpecifier()
            >>> specifier.rewrite_meter is None
            True

        """
        return self._rewrite_meter
