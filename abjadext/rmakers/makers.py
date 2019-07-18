import abjad
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .AccelerandoRhythmMaker import AccelerandoRhythmMaker
from .EvenDivisionRhythmMaker import EvenDivisionRhythmMaker
from .IncisedRhythmMaker import IncisedRhythmMaker
from .NoteRhythmMaker import NoteRhythmMaker
from .TaleaRhythmMaker import TaleaRhythmMaker
from .TupletRhythmMaker import TupletRhythmMaker


### FACTORY FUNCTIONS ###


def accelerando(
    *commands: _commands.Command,
    divisions: abjad.Expression = None,
    duration_specifier: _specifiers.Duration = None,
    interpolations: typing.Union[
        _specifiers.Interpolation, typing.Sequence[_specifiers.Interpolation]
    ] = None,
    tag: str = None,
) -> AccelerandoRhythmMaker:
    """
    Makes accelerando rhythm-maker.
    """
    return AccelerandoRhythmMaker(
        *commands,
        divisions=divisions,
        duration_specifier=duration_specifier,
        interpolations=interpolations,
        tag=tag,
    )


def even_division(
    *commands: _commands.Command,
    denominator: typing.Union[str, int] = "from_counts",
    denominators: typing.Sequence[int] = [8],
    divisions: abjad.Expression = None,
    duration_specifier: _specifiers.Duration = None,
    extra_counts_per_division: typing.Sequence[int] = None,
    tag: str = None,
) -> EvenDivisionRhythmMaker:
    """
    Makes even-division rhythm-maker.
    """
    return EvenDivisionRhythmMaker(
        *commands,
        denominator=denominator,
        denominators=denominators,
        divisions=divisions,
        duration_specifier=duration_specifier,
        extra_counts_per_division=extra_counts_per_division,
        tag=tag,
    )


def incised(
    *commands: _commands.Command,
    divisions: abjad.Expression = None,
    duration_specifier: _specifiers.Duration = None,
    extra_counts_per_division: typing.Sequence[int] = None,
    incise_specifier: _specifiers.Incise = None,
    replace_rests_with_skips: bool = None,
    tag: str = None,
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        *commands,
        divisions=divisions,
        duration_specifier=duration_specifier,
        extra_counts_per_division=extra_counts_per_division,
        incise_specifier=incise_specifier,
        replace_rests_with_skips=replace_rests_with_skips,
        tag=tag,
    )


def note() -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker()


def talea(
    *commands: _commands.Command,
    curtail_ties: bool = None,
    divisions: abjad.Expression = None,
    duration_specifier: _specifiers.Duration = None,
    extra_counts_per_division: abjad.IntegerSequence = None,
    read_talea_once_only: bool = None,
    tag: str = None,
    talea: _specifiers.Talea = _specifiers.Talea(counts=[1], denominator=16),
) -> TaleaRhythmMaker:
    """
    Makes talea rhythm-maker.
    """
    return TaleaRhythmMaker(
        *commands,
        curtail_ties=curtail_ties,
        divisions=divisions,
        duration_specifier=duration_specifier,
        extra_counts_per_division=extra_counts_per_division,
        read_talea_once_only=read_talea_once_only,
        tag=tag,
        talea=talea,
    )


def tuplet(
    *commands: _commands.Command,
    denominator: typing.Union[int, abjad.DurationTyping] = None,
    divisions: abjad.Expression = None,
    duration_specifier: _specifiers.Duration = None,
    tag: str = None,
    tuplet_ratios: abjad.RatioSequenceTyping = None,
) -> TupletRhythmMaker:
    """
    Makes tuplet rhythm-maker.
    """
    return TupletRhythmMaker(
        *commands,
        denominator=denominator,
        divisions=divisions,
        duration_specifier=duration_specifier,
        tag=tag,
        tuplet_ratios=tuplet_ratios,
    )
