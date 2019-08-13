import abjad
import typing
from . import specifiers as _specifiers


### CLASSES ###


class Command(object):
    """
    Command baseclass.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Commands"

    __slots__ = ("_selector",)

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, selector: abjad.SelectorTyping = None) -> None:
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls command on ``voice``.
        """
        pass

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification="") -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __hash__(self) -> int:
        """
        Delegates to storage format manager.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector


class BeamCommand(Command):
    """
    Beam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_lone_notes", "_beam_rests", "_stemlet_length")

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping = None,
        *,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        stemlet_length: abjad.Number = None,
    ) -> None:
        super().__init__(selector)
        if beam_lone_notes is not None:
            beam_lone_notes = bool(beam_lone_notes)
        self._beam_lone_notes = beam_lone_notes
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length

    ### SPECIAL METHODS ###

    def __call__(self, voice, tag: str = None) -> None:
        """
        Calls beam command on ``voice``.
        """
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = [selection]
        for selection in selections:
            unbeam()(selection)
            leaves = abjad.select(selection).leaves()
            abjad.beam(
                leaves,
                beam_lone_notes=self.beam_lone_notes,
                beam_rests=self.beam_rests,
                stemlet_length=self.stemlet_length,
                tag=tag,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def beam_lone_notes(self) -> typing.Optional[bool]:
        """
        Is true when command beams lone notes.
        """
        return self._beam_lone_notes

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when beams include rests.
        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length


class BeamGroupsCommand(Command):
    """
    Beam groups command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_lone_notes", "_beam_rests", "_stemlet_length", "_tag")

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping = None,
        *,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        stemlet_length: abjad.Number = None,
        tag: str = None,
    ) -> None:
        super().__init__(selector)
        if beam_lone_notes is not None:
            beam_lone_notes = bool(beam_lone_notes)
        self._beam_lone_notes = beam_lone_notes
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length
        if tag is not None:
            assert isinstance(tag, str), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(self, voice, tag: str = None) -> None:
        """
        Calls beam groups command on ``voice``.
        """
        components: typing.List[abjad.Component] = []
        if not isinstance(voice, abjad.Voice):
            selections = voice
            if self.selector is not None:
                selections = self.selector(selections)
        else:
            assert self.selector is not None
            selections = self.selector(voice)
        unbeam()(selections)
        durations = []
        for selection in selections:
            duration = abjad.inspect(selection).duration()
            durations.append(duration)
        for selection in selections:
            if isinstance(selection, abjad.Selection):
                components.extend(selection)
            elif isinstance(selection, abjad.Tuplet):
                components.append(selection)
            else:
                raise TypeError(selection)
        leaves = abjad.select(components).leaves()
        parts = []
        if tag is not None:
            parts.append(tag)
        if self.tag is not None:
            parts.append(self.tag)
        tag = ":".join(parts)
        abjad.beam(
            leaves,
            beam_lone_notes=self.beam_lone_notes,
            beam_rests=self.beam_rests,
            durations=durations,
            span_beam_count=1,
            stemlet_length=self.stemlet_length,
            tag=tag,
        )

    ### PUBLIC PROPERTIES ###

    @property
    def beam_lone_notes(self) -> typing.Optional[bool]:
        """
        Is true when command beams lone notes.
        """
        return self._beam_lone_notes

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when beams include rests.
        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length

    @property
    def tag(self) -> typing.Optional[str]:
        """
        Gets tag.
        """
        return self._tag


class CacheStateCommand(Command):
    """
    Cache state command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### INITIALIZER ###

    def __init__(self) -> None:
        pass


class DenominatorCommand(Command):
    """
    Denominator command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_denominator",)

    ### INITIALIZER ###

    def __init__(
        self,
        denominator: typing.Union[int, abjad.DurationTyping] = None,
        selector: abjad.SelectorTyping = None,
    ) -> None:
        super().__init__(selector)
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        if denominator is not None:
            prototype = (int, abjad.Duration)
            assert isinstance(denominator, prototype), repr(denominator)
        self._denominator = denominator

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls denominator command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        denominator = self.denominator
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        for tuplet in abjad.select(selection).tuplets():
            if isinstance(denominator, abjad.Duration):
                unit_duration = denominator
                assert unit_duration.numerator == 1
                duration = abjad.inspect(tuplet).duration()
                denominator_ = unit_duration.denominator
                nonreduced_fraction = duration.with_denominator(denominator_)
                tuplet.denominator = nonreduced_fraction.numerator
            elif abjad.mathtools.is_positive_integer(denominator):
                tuplet.denominator = denominator
            else:
                message = f"invalid preferred denominator: {denominator!r}."
                raise Exception(message)

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(self) -> typing.Union[int, abjad.Duration, None]:
        r"""
        Gets preferred denominator.
        """
        return self._denominator


class DurationBracketCommand(Command):
    """
    Duration bracket command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls duration bracket command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            duration_ = abjad.inspect(tuplet).duration()
            markup = duration_.to_score_markup()
            markup = markup.scale((0.75, 0.75))
            abjad.override(tuplet).tuplet_number.text = markup


class ExtractTrivialCommand(Command):
    """
    Extract trivial command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls extract trivial command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        tuplets = abjad.select(selection).tuplets()
        for tuplet in tuplets:
            if tuplet.trivial():
                abjad.mutate(tuplet).extract()


class FeatherBeamCommand(Command):
    """
    Feather beam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_rests", "_selector", "_stemlet_length")

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping = None,
        *,
        beam_rests: bool = None,
        stemlet_length: abjad.Number = None,
    ) -> None:
        super().__init__(selector)
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length

    ### SPECIAL METHODS ###

    def __call__(self, voice, tag: str = None) -> None:
        """
        Calls feather beam command.
        """
        components: typing.List[abjad.Component] = []
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = [selection]
        for selection in selections:
            unbeam()(selection)
            leaves = abjad.select(selection).leaves()
            abjad.beam(
                leaves,
                beam_rests=self.beam_rests,
                stemlet_length=self.stemlet_length,
                tag=tag,
            )
        for selection in selections:
            first_leaf = abjad.select(selection).leaf(0)
            if self._is_accelerando(selection):
                abjad.override(first_leaf).beam.grow_direction = abjad.Right
            elif self._is_ritardando(selection):
                abjad.override(first_leaf).beam.grow_direction = abjad.Left

    ### PRIVATE METHODS ###

    @staticmethod
    def _is_accelerando(selection):
        first_leaf = abjad.select(selection).leaf(0)
        last_leaf = abjad.select(selection).leaf(-1)
        first_duration = abjad.inspect(first_leaf).duration()
        last_duration = abjad.inspect(last_leaf).duration()
        if last_duration < first_duration:
            return True
        return False

    @staticmethod
    def _is_ritardando(selection):
        first_leaf = abjad.select(selection).leaf(0)
        last_leaf = abjad.select(selection).leaf(-1)
        first_duration = abjad.inspect(first_leaf).duration()
        last_duration = abjad.inspect(last_leaf).duration()
        if first_duration < last_duration:
            return True
        return False

    ### PUBLIC PROPERTIES ###

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when feather beams include rests.
        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length


class ForceAugmentationCommand(Command):
    """
    Force augmentation command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls force augmentation command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.augmentation():
                tuplet.toggle_prolation()


class ForceDiminutionCommand(Command):
    """
    Force diminution command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls force diminution command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.diminution():
                tuplet.toggle_prolation()


class ForceFractionCommand(Command):
    """
    Force fraction command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls force fraction command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.force_fraction = True


class ForceNoteCommand(Command):
    r"""
    Note command.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties()[1:3]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    r4..
                    c'4.
                    c'4..
                    r4.
                }
            >>

    ..  container:: example

        Sustains logical ties -1 and -2 to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties()[-2:]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    r4..
                    r4.
                    c'4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes patterned selection of leaves to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties()[1:-1]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    r4..
                    c'4.
                    c'4..
                    r4.
                }
            >>

    ..  container:: example

        Changes patterned selection of leave to notes. Works inverted composite
        pattern:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties().get([0, -1])),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    r4.
                    r4..
                    c'4.
                }
            >>

    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag=None):
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)

        # will need to restore for statal rhythm-makers:
        # logical_ties = abjad.select(selections).logical_ties()
        # logical_ties = list(logical_ties)
        # total_logical_ties = len(logical_ties)
        # previous_logical_ties_produced = self._previous_logical_ties_produced()
        # if self._previous_incomplete_last_note():
        #    previous_logical_ties_produced -= 1

        leaves = abjad.select(selection).leaves()
        for leaf in leaves:
            if isinstance(leaf, abjad.Note):
                continue
            note = abjad.Note("C4", leaf.written_duration, tag=tag)
            if leaf.multiplier is not None:
                note.multiplier = leaf.multiplier
            abjad.mutate(leaf).replace([note])


class ForceRepeatTieCommand(Command):
    """
    Force repeat-tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_threshold",)

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping = None,
        *,
        threshold: typing.Union[
            bool, abjad.IntegerPair, abjad.DurationInequality
        ] = None,
    ) -> None:
        super().__init__(selector)
        threshold_ = threshold
        if isinstance(threshold, tuple) and len(threshold) == 2:
            threshold_ = abjad.DurationInequality(
                operator_string=">=", duration=threshold
            )
        if threshold_ is not None:
            assert isinstance(threshold_, (bool, abjad.DurationInequality))
        self._threshold = threshold_

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls force repeat-tie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        if isinstance(self.threshold, abjad.DurationInequality):
            inequality = self.threshold
        elif self.threshold is True:
            inequality = abjad.DurationInequality(">=", 0)
        else:
            duration = abjad.Duration(self.threshold)
            inequality = abjad.DurationInequality(">=", duration)
        assert isinstance(inequality, abjad.DurationInequality)
        attach_repeat_ties = []
        for leaf in abjad.select(selection).leaves():
            if abjad.inspect(leaf).has_indicator(abjad.Tie):
                next_leaf = abjad.inspect(leaf).leaf(1)
                if next_leaf is None:
                    continue
                if not isinstance(next_leaf, (abjad.Chord, abjad.Note)):
                    continue
                if abjad.inspect(next_leaf).has_indicator(abjad.RepeatTie):
                    continue
                duration = abjad.inspect(leaf).duration()
                if not inequality(duration):
                    continue
                attach_repeat_ties.append(next_leaf)
                abjad.detach(abjad.Tie, leaf)
        for leaf in attach_repeat_ties:
            repeat_tie = abjad.RepeatTie()
            abjad.attach(repeat_tie, leaf)

    ### PUBLIC PROPERTIES ###

    @property
    def threshold(self) -> typing.Union[bool, abjad.DurationInequality, None]:
        """
        Gets threshold.
        """
        return self._threshold


class ForceRestCommand(Command):
    r"""
    Rest command.

    ..  container:: example

        Changes logical ties 1 and 2 to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[1:3]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    r4.
                    r4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes logical ties -1 and -2 to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[-2:]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    c'4.
                    r4..
                    r4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[1:-1]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    r4.
                    r4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests. Works with
        inverted composite pattern:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([0, -1]),
        ...     ),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    r4..
                    c'4.
                    c'4..
                    r4.
                }
            >>

    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(
        self, voice, *, previous_logical_ties_produced=None, tag=None
    ):
        selection = voice
        if self.selector is not None:
            selections = self.selector(
                selection, previous=previous_logical_ties_produced
            )
        # will need to restore for statal rhythm-makers:
        # logical_ties = abjad.select(selections).logical_ties()
        # logical_ties = list(logical_ties)
        # total_logical_ties = len(logical_ties)
        # previous_logical_ties_produced = self._previous_logical_ties_produced()
        # if self._previous_incomplete_last_note():
        #    previous_logical_ties_produced -= 1
        leaves = abjad.select(selections).leaves()
        for leaf in leaves:
            rest = abjad.Rest(leaf.written_duration, tag=tag)
            if leaf.multiplier is not None:
                rest.multiplier = leaf.multiplier
            previous_leaf = abjad.inspect(leaf).leaf(-1)
            next_leaf = abjad.inspect(leaf).leaf(1)
            abjad.mutate(leaf).replace([rest])
            if previous_leaf is not None:
                abjad.detach(abjad.Tie, previous_leaf)
            abjad.detach(abjad.Tie, rest)
            abjad.detach(abjad.RepeatTie, rest)
            if next_leaf is not None:
                abjad.detach(abjad.RepeatTie, next_leaf)


class RepeatTieCommand(Command):
    """
    Repeat-tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls tie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            tie = abjad.RepeatTie()
            abjad.attach(tie, note, tag=tag)


class RewriteDotsCommand(Command):
    """
    Rewrite dots command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls rewrite dots command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.rewrite_dots()


class RewriteMeterCommand(Command):
    """
    Rewrite meter command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_reference_meters",)

    ### INITIALIZER ###

    def __init__(self, *, reference_meters=None) -> None:
        self._reference_meters = reference_meters

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls rewrite meter command.
        """
        assert isinstance(voice, abjad.Voice), repr(voice)
        staff = abjad.inspect(voice).parentage().parent
        assert isinstance(staff, abjad.Staff), repr(staff)
        time_signature_voice = staff["TimeSignatureVoice"]
        assert isinstance(time_signature_voice, abjad.Voice)
        meters = []
        for skip in time_signature_voice:
            time_signature = abjad.inspect(skip).indicator(abjad.TimeSignature)
            meter = abjad.Meter(time_signature)
            meters.append(meter)
        durations = [abjad.Duration(_) for _ in meters]
        reference_meters = self.reference_meters or ()
        command = SplitMeasuresCommand()
        command(voice, durations=durations)
        selections = abjad.select(voice[:]).group_by_measure()
        for meter, selection in zip(meters, selections):
            for reference_meter in reference_meters:
                if str(reference_meter) == str(meter):
                    meter = reference_meter
                    break

            nontupletted_leaves = []
            for leaf in abjad.iterate(selection).leaves():
                if not abjad.inspect(leaf).parentage().count(abjad.Tuplet):
                    nontupletted_leaves.append(leaf)
            unbeam()(nontupletted_leaves)
            abjad.mutate(selection).rewrite_meter(meter, rewrite_tuplets=False)
        selections = abjad.select(voice[:]).group_by_measure()
        for meter, selection in zip(meters, selections):
            leaves = abjad.select(selection).leaves(grace=False)
            beat_durations = []
            beat_offsets = meter.depthwise_offset_inventory[1]
            for start, stop in abjad.sequence(beat_offsets).nwise():
                beat_duration = stop - start
                beat_durations.append(beat_duration)
            beamable_groups = self._make_beamable_groups(
                leaves, beat_durations
            )
            for beamable_group in beamable_groups:
                if not beamable_group:
                    continue
                abjad.beam(
                    beamable_group,
                    beam_rests=False,
                    tag="rmakers.RewriteMeterCommand.__call__",
                )

    ### PRIVATE METHODS ###

    @staticmethod
    def _make_beamable_groups(components, durations):
        music_duration = abjad.inspect(components).duration()
        if music_duration != sum(durations):
            message = f"music duration {music_duration} does not equal"
            message += f" total duration {sum(durations)}:\n"
            message += f"   {components}\n"
            message += f"   {durations}"
            raise Exception(message)
        component_to_timespan = []
        start_offset = abjad.Offset(0)
        for component in components:
            duration = abjad.inspect(component).duration()
            stop_offset = start_offset + duration
            timespan = abjad.Timespan(start_offset, stop_offset)
            pair = (component, timespan)
            component_to_timespan.append(pair)
            start_offset = stop_offset
        group_to_target_duration = []
        start_offset = abjad.Offset(0)
        for target_duration in durations:
            stop_offset = start_offset + target_duration
            group_timespan = abjad.Timespan(start_offset, stop_offset)
            start_offset = stop_offset
            group = []
            for component, component_timespan in component_to_timespan:
                if component_timespan.happens_during_timespan(group_timespan):
                    group.append(component)
            selection = abjad.select(group)
            pair = (selection, target_duration)
            group_to_target_duration.append(pair)
        beamable_groups = []
        for group, target_duration in group_to_target_duration:
            group_duration = abjad.inspect(group).duration()
            assert group_duration <= target_duration
            if group_duration == target_duration:
                beamable_groups.append(group)
            else:
                beamable_groups.append(abjad.select([]))
        return beamable_groups

    ### PUBLIC PROPERTIES ###

    @property
    def reference_meters(self):
        """
        Gets reference meters.
        """
        return self._reference_meters


class RewriteRestFilledCommand(Command):
    """
    Rewrite rest-filled command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_spelling",)

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping = None,
        *,
        spelling: _specifiers.Spelling = None,
    ) -> None:
        super().__init__(selector)
        if spelling is not None:
            assert isinstance(spelling, _specifiers.Spelling)
        self._spelling = spelling

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls rewrite rest-filled command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        if self.spelling is not None:
            increase_monotonic = self.spelling.increase_monotonic
            forbidden_note_duration = self.spelling.forbidden_note_duration
            forbidden_rest_duration = self.spelling.forbidden_rest_duration
        else:
            increase_monotonic = None
            forbidden_note_duration = None
            forbidden_rest_duration = None
        maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.rest_filled():
                continue
            duration = abjad.inspect(tuplet).duration()
            rests = maker([None], [duration])
            abjad.mutate(tuplet[:]).replace(rests)
            tuplet.multiplier = abjad.Multiplier(1)

    ### PUBLIC PROPERTIES ###

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        """
        Gets spelling specifier.
        """
        return self._spelling


class RewriteSustainedCommand(Command):
    """
    Rewrite sustained command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls rewrite sustained command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.sustained():
                continue
            duration = abjad.inspect(tuplet).duration()
            leaves = abjad.select(tuplet).leaves()
            last_leaf = leaves[-1]
            if abjad.inspect(last_leaf).has_indicator(abjad.Tie):
                last_leaf_has_tie = True
            else:
                last_leaf_has_tie = False
            for leaf in leaves[1:]:
                tuplet.remove(leaf)
            assert len(tuplet) == 1, repr(tuplet)
            if not last_leaf_has_tie:
                abjad.detach(abjad.Tie, tuplet[-1])
            tuplet[0]._set_duration(duration)
            tuplet.multiplier = abjad.Multiplier(1)


class SplitMeasuresCommand(Command):
    """
    Split measures command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(
        self,
        voice,
        *,
        durations: typing.Sequence[abjad.DurationTyping] = None,
        tag: str = None,
    ) -> None:
        """
        Calls split measures command.
        """
        if durations is None:
            # TODO: implement abjad.inspect() method for measure durations
            staff = abjad.inspect(voice).parentage().parent
            voice_ = staff["TimeSignatureVoice"]
            durations = [abjad.inspect(_).duration() for _ in voice_]
        total_duration = sum(durations)
        music_duration = abjad.inspect(voice).duration()
        if total_duration != music_duration:
            message = f"Total duration of splits is {total_duration!s}"
            message += f" but duration of music is {music_duration!s}:"
            message += f"\ndurations: {durations}."
            message += f"\nvoice: {voice[:]}."
            raise Exception(message)
        abjad.mutate(voice[:]).split(durations=durations)


class TieCommand(Command):
    """
    Tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls tie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            tie = abjad.Tie()
            abjad.attach(tie, note, tag=tag)


class TrivializeCommand(Command):
    """
    Trivialize command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls trivialize command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.trivialize()


class UnbeamCommand(Command):
    """
    Unbeam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, tag: str = None) -> None:
        """
        Calls unbeam command.
        """
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = selection
        leaves = abjad.select(selections).leaves()
        for leaf in leaves:
            abjad.detach(abjad.BeamCount, leaf)
            abjad.detach(abjad.StartBeam, leaf)
            abjad.detach(abjad.StopBeam, leaf)


class UntieCommand(Command):
    """
    Untie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: str = None) -> None:
        """
        Calls untie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for leaf in abjad.select(selection).leaves():
            abjad.detach(abjad.Tie, leaf)
            abjad.detach(abjad.RepeatTie, leaf)


### FACTORY FUNCTIONS ###


def beam(
    selector: abjad.SelectorTyping = abjad.select()
    .tuplets()
    .map(abjad.select().leaves(grace=False)),
    *,
    beam_lone_notes: bool = None,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
) -> BeamCommand:
    """
    Makes simple beam command.
    """
    return BeamCommand(
        selector,
        beam_rests=beam_rests,
        beam_lone_notes=beam_lone_notes,
        stemlet_length=stemlet_length,
    )


def beam_groups(
    ###selector: typing.Optional[abjad.SelectorTyping] = abjad.select(),
    selector: typing.Optional[abjad.SelectorTyping] = abjad.select()
    .tuplets(level=-1)
    .map(abjad.select().leaves(grace=False)),
    *,
    beam_lone_notes: bool = None,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
    tag: str = None,
) -> BeamGroupsCommand:
    """
    Makes beam divisions together command.
    """
    return BeamGroupsCommand(
        selector,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def cache_state() -> CacheStateCommand:
    """
    Makes cache state command.
    """
    return CacheStateCommand()


def denominator(
    denominator: typing.Union[int, abjad.DurationTyping],
    selector: abjad.SelectorTyping = abjad.select().tuplets(),
) -> DenominatorCommand:
    r"""
    Makes tuplet denominator command.

    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are
        relatively prime when ``denominator`` is set to none. This
        means that ratios like ``6:4`` and ``10:8`` do not arise:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5 {
                        c'16
                        c'4
                    }
                    \times 4/5 {
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set in terms of a unit
        duration when ``denominator`` is set to a duration. The
        setting does not affect the first tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 16)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5 {
                        c'16
                        c'4
                    }
                    \times 8/10 {
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet in terms 32nd notes.
        The setting affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 32)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10 {
                        c'16
                        c'4
                    }
                    \times 16/20 {
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator each tuplet in terms 64th notes. The
        setting affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 64)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 8/10 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 16/20 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 24/20 {
                        c'16
                        c'4
                    }
                    \times 32/40 {
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set directly when
        ``denominator`` is set to a positive integer. This example
        sets the preferred denominator of each tuplet to ``8``. Setting
        does not affect the third tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(8),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 8/10 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5 {
                        c'16
                        c'4
                    }
                    \times 8/10 {
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``12``. Setting
        affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(12),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> moment = abjad.SchemeMoment((1, 28))
        >>> abjad.setting(score).proportional_notation_duration = moment
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
                proportionalNotationDuration = #(ly:make-moment 1 28)
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 12/15 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 12/15 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10 {
                        c'16
                        c'4
                    }
                    \times 12/15 {
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``13``. Setting
        does not affect any tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(13),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = #4.5
            }
            <<
                \new GlobalContext
                {
                    \time 2/16
                    s1 * 1/8
                    \time 4/16
                    s1 * 1/4
                    \time 6/16
                    s1 * 3/8
                    \time 8/16
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5 {
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5 {
                        c'16
                        c'4
                    }
                    \times 4/5 {
                        c'8
                        c'2
                    }
                }
            >>

    """
    return DenominatorCommand(denominator, selector)


def duration_bracket(
    selector: abjad.SelectorTyping = None
) -> DurationBracketCommand:
    """
    Makes duration bracket command.
    """
    return DurationBracketCommand(selector)


def extract_trivial(
    selector: abjad.SelectorTyping = None
) -> ExtractTrivialCommand:
    r"""
    Makes extract trivial command.

    ..  container:: example

        With selector:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(abjad.select().tuplets()[-2:]),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
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
            >>

    """
    return ExtractTrivialCommand(selector)


def feather_beam(
    selector: abjad.SelectorTyping = abjad.select()
    .tuplets()
    .map(abjad.select().leaves(grace=False)),
    *,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
) -> FeatherBeamCommand:
    """
    Makes feather beam command.
    """
    return FeatherBeamCommand(
        selector, beam_rests=beam_rests, stemlet_length=stemlet_length
    )


def force_augmentation(
    selector: abjad.SelectorTyping = None,
) -> ForceAugmentationCommand:
    r"""
    Makes force augmentation command.

    ..  container:: example

        The ``default.ily`` stylesheet included in all Abjad API examples
        includes the following:
        
        ``\override TupletNumber.text = #tuplet-number::calc-fraction-text``

        This means that even simple tuplets format as explicit fractions:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        We can temporarily restore LilyPond's default tuplet numbering like
        this:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> staff = lilypond_file[abjad.Score]
        >>> string = 'tuplet-number::calc-denominator-text'
        >>> abjad.override(staff).tuplet_number.text = string
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletNumber.text = #tuplet-number::calc-denominator-text
            }
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        Which then makes it possible to show that the force fraction
        property cancels LilyPond's default tuplet numbering once again:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.force_fraction(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> staff = lilypond_file[abjad.Score]
        >>> string = 'tuplet-number::calc-denominator-text'
        >>> abjad.override(staff).tuplet_number.text = string
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            \with
            {
                \override TupletNumber.text = #tuplet-number::calc-denominator-text
            }
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    return ForceAugmentationCommand(selector)


def force_diminution(
    selector: abjad.SelectorTyping = None,
) -> ForceDiminutionCommand:
    """
    Makes force diminution command.
    """
    return ForceDiminutionCommand(selector)


def force_fraction(
    selector: abjad.SelectorTyping = None,
) -> ForceFractionCommand:
    """
    Makes force fraction command.
    """
    return ForceFractionCommand(selector)


def force_note(selector: abjad.SelectorTyping,) -> ForceNoteCommand:
    """
    Makes force note command.
    """
    return ForceNoteCommand(selector)


def force_repeat_tie(
    threshold=True, selector: abjad.SelectorTyping = None
) -> ForceRepeatTieCommand:
    """
    Makes force repeat-ties command.
    """
    return ForceRepeatTieCommand(selector, threshold=threshold)


def force_rest(selector: abjad.SelectorTyping) -> ForceRestCommand:
    """
    Makes force rest command.
    """
    return ForceRestCommand(selector)


def repeat_tie(selector: abjad.SelectorTyping = None) -> RepeatTieCommand:
    r"""
    Makes repeat-tie command.

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches repeat-ties to first note in
        nonfirst tuplets:

        >>> selector = abjad.select().tuplets()[1:]
        >>> selector = selector.map(abjad.select().note(0))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> selector = abjad.select().tuplets().get([1], 2)
        >>> selector = selector.map(abjad.select().note(0))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    return RepeatTieCommand(selector)


def rewrite_dots(selector: abjad.SelectorTyping = None) -> RewriteDotsCommand:
    """
    Makes rewrite dots command.
    """
    return RewriteDotsCommand(selector)


def rewrite_meter(*, reference_meters=None) -> RewriteMeterCommand:
    """
    Makes rewrite meter command.
    """
    return RewriteMeterCommand(reference_meters=reference_meters)


def rewrite_rest_filled(
    selector: abjad.SelectorTyping = None,
    spelling: _specifiers.Spelling = None,
) -> RewriteRestFilledCommand:
    r"""
    Makes rewrite rest-filled command.

    ..  container:: example

        Does not rewrite rest-filled tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \times 4/5 {
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        r16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        r16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                }
            >>

        Rewrites rest-filled tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    r4
                    r4
                    r4
                    r16
                    r4
                    r16
                }
            >>

        With spelling specifier:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(
        ...         spelling=rmakers.Spelling(increase_monotonic=True)
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    r4
                    r4
                    r16
                    r4
                    r16
                    r4
                }
            >>

        With selector:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(
        ...         abjad.select().tuplets()[-2:],
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \times 4/5 {
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    r4
                    r16
                    r4
                    r16
                }
            >>

        Note that nonassignable divisions necessitate multiple rests
        even after rewriting.

    """
    return RewriteRestFilledCommand(selector, spelling=spelling)


def rewrite_sustained(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> RewriteSustainedCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        Sustained tuplets generalize a class of rhythms composers are
        likely to rewrite:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'4.
                    }
                    \times 4/5 {
                        c'4
                        ~
                        c'16
                        ~
                    }
                    \times 4/5 {
                        c'4
                        ~
                        c'16
                        ~
                    }
                    \times 4/5 {
                        c'4
                        c'16
                    }
                }
            >>

        The first three tuplets in the example above qualify as sustained:

            >>> staff = lilypond_file[abjad.Score]
            >>> for tuplet in abjad.select(staff).tuplets():
            ...     tuplet.sustained()
            ...
            True
            True
            True
            False

        Tuplets 0 and 1 each contain only a single **tuplet-initial**
        attack. Tuplet 2 contains no attack at all. All three fill their
        duration completely.

        Tuplet 3 contains a **nonintial** attack that rearticulates the
        tuplet's duration midway through the course of the figure. Tuplet 3
        does not qualify as sustained.

    ..  container:: example

        Rewrite sustained tuplets like this:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4
                        ~
                    }
                    \times 4/5 {
                        c'4
                        c'16
                    }
                }
            >>

    ..  container:: example

        Rewrite sustained tuplets -- and then extract the trivial tuplets
        that result -- like this:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.beam(),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                    \time 4/16
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    c'4
                    c'4
                    ~
                    c'4
                    ~
                    \times 4/5 {
                        c'4
                        c'16
                    }
                }
            >>

    ..  container:: example

        With selector:

        >>> selector = abjad.select().notes()[:-1]
        >>> selector = abjad.select().tuplets().map(selector)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.rewrite_sustained(
        ...         abjad.select().tuplets()[-2:],
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/2 {
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/2 {
                        c'4
                    }
                }
            >>

    """
    return RewriteSustainedCommand(selector)


def split_measures() -> SplitMeasuresCommand:
    """
    Makes split measures command.
    """
    return SplitMeasuresCommand()


def tie(selector: abjad.SelectorTyping = None) -> TieCommand:
    r"""
    Makes tie command.

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE. Attaches ties notes in selection:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(abjad.select().notes()[5:15]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches ties to last note in nonlast
        tuplets:

        >>> selector = abjad.select().tuplets()[:-1]
        >>> selector = selector.map(abjad.select().note(-1))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> selector = abjad.select().tuplets().get([0], 2)
        >>> selector = selector.map(abjad.select().note(-1))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE:

        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(5, 2)]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ... )
        >>> divisions = [(4, 8), (4, 8), (4, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/8
                    s1 * 1/2
                    \time 4/8
                    s1 * 1/2
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/7 {
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                    }
                    \times 4/7 {
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                    }
                    \times 4/7 {
                        c'2
                        ~
                        c'8
                        c'4
                    }
                }
            >>

    ..  container:: example

        TIE-WITHIN-DIVISIONS RECIPE:

        >>> selector = abjad.select().tuplets()
        >>> nonlast_notes = abjad.select().notes()[:-1]
        >>> selector = selector.map(nonlast_notes)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.untie(selector),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> selector = abjad.select().tuplets().get([0], 2)
        >>> selector = selector.map(abjad.select().notes()[:-1])
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    return TieCommand(selector=selector)


def trivialize(selector: abjad.SelectorTyping = None) -> TrivializeCommand:
    """
    Makes trivialize command.
    """
    return TrivializeCommand(selector)


def unbeam(
    selector: abjad.SelectorTyping = abjad.select().leaves()
) -> UnbeamCommand:
    """
    Makes unbeam command.
    """
    return UnbeamCommand(selector)


def untie(selector: abjad.SelectorTyping = None) -> UntieCommand:
    r"""
    Makes untie command.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select
        notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(abjad.select().notes()[:-1]),
        ...     rmakers.untie(abjad.select().notes().get([0], 4)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        ~
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        ~
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        ~
                        c'8
                        ~
                        ]
                    }
                    \times 2/3 {
                        c'8
                        ~
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from
        select notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(abjad.select().notes()[1:]),
        ...     rmakers.untie(abjad.select().notes().get([0], 4)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        \repeatTie
                        c'8
                        \repeatTie
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        \repeatTie
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        \repeatTie
                        c'8
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        \repeatTie
                        c'8
                        \repeatTie
                        ]
                    }
                    \times 2/3 {
                        c'8
                        [
                        c'8
                        \repeatTie
                        c'8
                        \repeatTie
                        ]
                    }
                    \times 2/3 {
                        c'8
                        \repeatTie
                        [
                        c'8
                        c'8
                        \repeatTie
                        ]
                    }
                }
            >>

    """
    return UntieCommand(selector=selector)
