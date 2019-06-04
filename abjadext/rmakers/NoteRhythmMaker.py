import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .BurnishSpecifier import BurnishSpecifier
from .DurationSpecifier import DurationSpecifier
from .RhythmMaker import RhythmMaker
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


class NoteRhythmMaker(RhythmMaker):
    r"""
    Note rhythm-maker.

    ..  container:: example

        Makes notes equal to the duration of input divisions. Adds ties where
        necessary:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

        >>> divisions = [(5, 8), (3, 8)]
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
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'2
                    ~
                    c'8
                    c'4.
                }
            >>

    Usage follows the two-step configure-once / call-repeatedly pattern shown
    here.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_burnish_specifier",)

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_specifier: BeamSpecifier = None,
        burnish_specifier: BurnishSpecifier = None,
        division_masks: typings.MasksTyping = None,
        duration_specifier: DurationSpecifier = None,
        logical_tie_masks: typings.MasksTyping = None,
        tag: str = None,
        tie_specifier: TieSpecifier = None,
        tuplet_specifier: TupletSpecifier = None,
    ) -> None:
        RhythmMaker.__init__(
            self,
            beam_specifier=beam_specifier,
            duration_specifier=duration_specifier,
            division_masks=division_masks,
            logical_tie_masks=logical_tie_masks,
            tag=tag,
            tie_specifier=tie_specifier,
            tuplet_specifier=tuplet_specifier,
        )
        if burnish_specifier is not None:
            assert isinstance(burnish_specifier, BurnishSpecifier)
        self._burnish_specifier = burnish_specifier

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> typing.List[abjad.Selection]:
        """
        Calls note rhythm-maker on ``divisions``.

        ..  container:: example

            Calls rhythm-maker on divisions:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()
            >>> divisions = [(5, 8), (3, 8)]
            >>> result = rhythm_maker(divisions)
            >>> for x in result:
            ...     x
            Selection([Note("c'2"), Note("c'8")])
            Selection([Note("c'4.")])

        """
        return RhythmMaker.__call__(
            self, divisions, previous_state=previous_state
        )

    def __format__(self, format_specification="") -> str:
        """
        Formats note rhythm-maker.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()
            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.NoteRhythmMaker()

        """
        return super().__format__(format_specification=format_specification)

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.NoteRhythmMaker()
            NoteRhythmMaker()

        """
        return super().__repr__()

    ### PRIVATE METHODS ###

    def _apply_burnish_specifier(self, selections):
        if self.burnish_specifier is None:
            return selections
        elif self.burnish_specifier.outer_divisions_only:
            selections = self._burnish_outer_divisions(selections)
        else:
            selections = self._burnish_each_division(selections)
        return selections

    def _burnish_each_division(self, selections):
        message = "NoteRhythmMaker does not yet implement"
        message += " burnishing each division."
        raise NotImplementedError(message)

    def _burnish_outer_divisions(self, selections):
        left_classes = self.burnish_specifier.left_classes
        left_counts = self.burnish_specifier.left_counts
        right_classes = self.burnish_specifier.right_classes
        right_counts = self.burnish_specifier.right_counts
        if left_counts:
            assert len(left_counts) == 1, repr(left_counts)
            left_count = left_counts[0]
        else:
            left_count = 0
        if right_counts:
            assert len(right_counts) == 1, repr(right_counts)
            right_count = right_counts[0]
        else:
            right_count = 0
        if left_count + right_count <= len(selections):
            middle_count = len(selections) - (left_count + right_count)
        elif left_count <= len(selections):
            right_count = len(selections) - left_count
            middle_count = 0
        else:
            left_count = len(selections)
            right_count = 0
            middle_count = 0
        assert left_count + middle_count + right_count == len(selections)
        new_selections = []
        left_classes = abjad.CyclicTuple(left_classes)
        for i, selection in enumerate(selections[:left_count]):
            target_class = left_classes[i]
            new_selection = self._cast_selection(selection, target_class)
            new_selections.append(new_selection)
        if right_count:
            for selection in selections[left_count:-right_count]:
                new_selections.append(selection)
            right_classes = abjad.CyclicTuple(right_classes)
            for i, selection in enumerate(selections[-right_count:]):
                target_class = right_classes[i]
                new_selection = self._cast_selection(selection, target_class)
                new_selections.append(new_selection)
        else:
            for selection in selections[left_count:]:
                new_selections.append(selection)
        return new_selections

    def _cast_selection(self, selection, target_class):
        new_selection = []
        for leaf in selection:
            new_leaf = target_class(leaf, tag=self.tag)
            if not isinstance(new_leaf, (abjad.Chord, abjad.Note)):
                abjad.detach(abjad.TieIndicator, new_leaf)
                abjad.detach(abjad.RepeatTie, new_leaf)
            new_selection.append(new_leaf)
        new_selection = abjad.select(new_selection)
        return new_selection

    def _make_music(self, divisions):
        selections = []
        duration_specifier = self._get_duration_specifier()
        tie_specifier = self._get_tie_specifier()
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=duration_specifier.increase_monotonic,
            forbidden_note_duration=duration_specifier.forbidden_note_duration,
            forbidden_rest_duration=duration_specifier.forbidden_rest_duration,
            repeat_ties=tie_specifier.repeat_ties,
            tag=self.tag,
        )
        for division in divisions:
            if duration_specifier.spell_metrically is True or (
                duration_specifier.spell_metrically == "unassignable"
                and not abjad.mathtools.is_assignable_integer(
                    division.numerator
                )
            ):
                meter = abjad.Meter(division)
                rhythm_tree_container = meter.root_node
                durations = [_.duration for _ in rhythm_tree_container]
            else:
                durations = [division]
            selection = leaf_maker(pitches=0, durations=durations)
            if (
                1 < len(selection)
                and abjad.inspect(selection[0]).logical_tie().is_trivial
            ):
                abjad.tie(selection[:], repeat=tie_specifier.repeat_ties)
            selections.append(selection)
        selections = self._apply_burnish_specifier(selections)
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def beam_specifier(self) -> typing.Optional[BeamSpecifier]:
        r"""
        Gets beam specifier.

        ..  container:: example

            Beams each division:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 32), (5, 32)]
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
                        \time 5/32
                        s1 * 5/32
                        \time 5/32
                        s1 * 5/32
                    }
                    \new RhythmicStaff
                    {
                        c'8
                        ~
                        [
                        c'32
                        ]
                        c'8
                        ~
                        [
                        c'32
                        ]
                    }
                >>

        ..  container:: example

            Beams divisions together:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 32), (5, 32)]
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
                        \time 5/32
                        s1 * 5/32
                        \time 5/32
                        s1 * 5/32
                    }
                    \new RhythmicStaff
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8
                        ~
                        [
                        \set stemLeftBeamCount = 3
                        \set stemRightBeamCount = 1
                        c'32
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 1
                        c'8
                        ~
                        \set stemLeftBeamCount = 3
                        \set stemRightBeamCount = 0
                        c'32
                        ]
                    }
                >>

        ..  container:: example

            Makes no beams:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=False,
            ...         beam_each_division=False,
            ...         ),
            ...     )

            >>> divisions = [(5, 32), (5, 32)]
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
                        \time 5/32
                        s1 * 5/32
                        \time 5/32
                        s1 * 5/32
                    }
                    \new RhythmicStaff
                    {
                        c'8
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                    }
                >>

        """
        return super().beam_specifier

    @property
    def burnish_specifier(self) -> typing.Optional[BurnishSpecifier]:
        r"""
        Gets burnish specifier.

        ..  container:: example

            Burnishes nothing:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'8
                        c'4
                        c'4
                        c'2
                        ~
                        c'8
                    }
                >>

        ..  container:: example

            Forces leaves of first division to be rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         outer_divisions_only=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r8
                        c'4
                        c'4
                        c'2
                        ~
                        c'8
                    }
                >>

        ..  container:: example

            Forces leaves of first two divisions to be rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[2],
            ...         outer_divisions_only=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r8
                        r4
                        c'4
                        c'2
                        ~
                        c'8
                    }
                >>

        ..  container:: example

            Forces leaves of first and last divisions to rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         right_classes=[abjad.Rest],
            ...         right_counts=[1],
            ...         outer_divisions_only=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r8
                        c'4
                        c'4
                        r2
                        r8
                    }
                >>

        ..  note:: Currently only works when ``outer_divisions_only`` is true.

        """
        return self._burnish_specifier

    @property
    def division_masks(self) -> typing.Optional[typings.MasksTyping]:
        r"""
        Gets division masks.

        ..  container:: example

            No division masks:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        c'2
                        c'4.
                    }
                >>

        ..  container:: example

            Silences every other division:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     division_masks=[
            ...         abjadext.rmakers.SilenceMask(
            ...             pattern=abjad.index([0], 2),
            ...             ),
            ...         ],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        c'4.
                        r2
                        c'4.
                    }
                >>

        ..  container:: example

            Silences every output division:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     division_masks=[abjadext.rmakers.silence([0], 1)],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r4.
                        r2
                        r4.
                    }
                >>

        ..  container:: example

            Silences every output division and uses multimeasure rests:

            >>> mask = abjadext.rmakers.SilenceMask(
            ...     pattern=abjad.index_all(),
            ...     use_multimeasure_rests=True,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     division_masks=[mask],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        R1 * 1/2
                        R1 * 3/8
                        R1 * 1/2
                        R1 * 3/8
                    }
                >>

        ..  container:: example

            Silences every other output division except for the first and last:

            >>> pattern_1 = abjad.index([0], 2)
            >>> pattern_2 = abjad.index([0, -1])
            >>> pattern = pattern_1 & ~pattern_2
            >>> mask = abjadext.rmakers.SilenceMask(
            ...     pattern=pattern,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     division_masks=[mask],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        r2
                        c'4.
                        c'4
                    }
                >>

        """
        return super().division_masks

    @property
    def duration_specifier(self) -> typing.Optional[DurationSpecifier]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

            >>> divisions = [(5, 8), (3, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'8
                        c'4.
                    }
                >>

        ..  container:: example

            Forbids notes with written duration greater than or equal to
            ``1/2``:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=(1, 2),
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (3, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'4
                        ~
                        c'8
                        c'4.
                    }
                >>

        ..  container:: example

            Spells all divisions metrically when ``spell_metrically`` is true:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         spell_metrically=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (6, 16), (9, 16)]
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
                        \time 6/16
                        s1 * 3/8
                        \time 9/16
                        s1 * 9/16
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'4
                        ~
                        c'4
                        c'8.
                        ~
                        [
                        c'8.
                        ]
                        c'8.
                        ~
                        [
                        c'8.
                        ~
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Spells only unassignable durations metrically when
            ``spell_metrically`` is ``'unassignable'``:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         spell_metrically='unassignable',
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (6, 16), (9, 16)]
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
                        \time 6/16
                        s1 * 3/8
                        \time 9/16
                        s1 * 9/16
                    }
                    \new RhythmicStaff
                    {
                        c'2.
                        c'4.
                        c'8.
                        ~
                        [
                        c'8.
                        ~
                        c'8.
                        ]
                    }
                >>

            ``9/16`` is spelled metrically because it is unassignable.
            The other durations are spelled with the fewest number of symbols
            possible.

        ..  container:: example

            Rewrites meter:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         rewrite_meter=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (6, 16), (9, 16)]
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
                        \time 6/16
                        s1 * 3/8
                        \time 9/16
                        s1 * 9/16
                    }
                    \new RhythmicStaff
                    {
                        c'2.
                        c'4.
                        c'4.
                        ~
                        c'8.
                    }
                >>

        """
        return super().duration_specifier

    @property
    def logical_tie_masks(self) -> typing.Optional[typings.MasksTyping]:
        r"""
        Gets logical tie masks.

        ..  container:: example

            No logical tie masks:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        c'2
                        c'4.
                    }
                >>

        ..  container:: example

            Silences every other logical tie:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     logical_tie_masks=abjadext.rmakers.silence([0], 2),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        c'4.
                        r2
                        c'4.
                    }
                >>

        ..  container:: example

            Silences all logical ties:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     logical_tie_masks=abjadext.rmakers.silence([0], 1),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r4.
                        r2
                        r4.
                    }
                >>

        """
        return super().logical_tie_masks

    @property
    def tag(self):
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tag='NOTE_RHYTHM_MAKER',
            ...     )

            >>> divisions = [(5, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'2 %! NOTE_RHYTHM_MAKER
                    ~
                    c'8 %! NOTE_RHYTHM_MAKER
                    c'4. %! NOTE_RHYTHM_MAKER
                }
            >>

        """
        return super().tag

    @property
    def tie_specifier(self) -> typing.Optional[TieSpecifier]:
        r"""
        Gets tie specifier.

        ..  container:: example

            Does not tie across divisions:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=False,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        c'2
                        c'4.
                    }
                >>

        ..  container:: example

            Ties across divisions:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'4.
                        ~
                        c'2
                        ~
                        c'4.
                    }
                >>

        ..  container:: example

            Patterns ties across divisions:

            >>> pattern = abjad.Pattern(
            ...     indices=[0],
            ...     period=2,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=pattern,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'4.
                        c'2
                        ~
                        c'4.
                    }
                >>

        ..  container:: example

            Uses repeat ties:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         repeat_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (9, 16), (5, 16)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 9/16
                        s1 * 9/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        \repeatTie
                        c'2
                        \repeatTie
                        c'16
                        \repeatTie
                        c'4
                        \repeatTie
                        c'16
                        \repeatTie
                    }
                >>

        ..  container:: example

            Strips all ties:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         strip_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(7, 16), (1, 4), (5, 16)]
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
                        \time 7/16
                        s1 * 7/16
                        \time 1/4
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'4..
                        c'4
                        c'4
                        c'16
                    }
                >>

        ..  container:: example

            Spells durations metrically and then strips all ties:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         spell_metrically=True,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         strip_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(7, 16), (1, 4), (5, 16)]
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
                        \time 7/16
                        s1 * 7/16
                        \time 1/4
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'8.
                        [
                        c'8
                        c'8
                        ]
                        c'4
                        c'8.
                        [
                        c'8
                        ]
                    }
                >>

        """
        return super().tie_specifier

    @property
    def tuplet_specifier(self) -> typing.Optional[TupletSpecifier]:
        r"""
        Gets tuplet specifier.

        ..  container:: example

            Spells tuplets as diminutions:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

            >>> divisions = [(5, 14), (3, 7)]
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
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        s1 * 5/14
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        s1 * 3/7
                    }
                    \new RhythmicStaff
                    {
                        \tweak edge-height #'(0.7 . 0)
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \times 4/7 {
                            c'2.
                        }
                    }
                >>

        ..  container:: example

            Spells tuplets as augmentations:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...         ),
            ...     )

            >>> divisions = [(5, 14), (3, 7)]
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
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        s1 * 5/14
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        s1 * 3/7
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tweak edge-height #'(0.7 . 0)
                        \times 8/7 {
                            c'4
                            ~
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tweak edge-height #'(0.7 . 0)
                        \times 8/7 {
                            c'4.
                        }
                    }
                >>

        """
        return super().tuplet_specifier
