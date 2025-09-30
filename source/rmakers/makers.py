"""
Makers.
"""

import inspect
import math
import types
import typing

import abjad

from . import classes as _classes


def _apply_ties_to_split_notes(
    tuplets: list[abjad.Tuplet],
    unscaled_end_counts: list[int],
    unscaled_preamble_counts: list[int],
    unscaled_talea_counts: list[int],
    talea: _classes.Talea,
) -> None:
    assert _is_integer_list(unscaled_end_counts), repr(unscaled_end_counts)
    assert _is_integer_list(unscaled_preamble_counts), repr(unscaled_preamble_counts)
    assert _is_integer_list(unscaled_talea_counts), repr(unscaled_talea_counts)
    assert isinstance(talea, _classes.Talea), repr(talea)
    leaves = abjad.select.leaves(tuplets)
    written_durations = [leaf.written_duration() for leaf in leaves]
    total_duration = abjad.math.weight(written_durations, start=abjad.Duration(0))
    preamble_weights = []
    if unscaled_preamble_counts:
        for count in unscaled_preamble_counts:
            duration = abjad.Duration(count, talea.denominator)
            weight = abs(duration)
            preamble_weights.append(weight)
    preamble_duration = sum(preamble_weights, start=abjad.Duration(0))
    if total_duration <= preamble_duration:
        preamble_parts = abjad.sequence.partition_by_weights(
            written_durations,
            weights=preamble_weights,
            allow_part_weights=abjad.MORE,
            cyclic=True,
            overhang=True,
        )
        talea_parts = []
    else:
        assert preamble_duration < total_duration
        preamble_parts = abjad.sequence.partition_by_weights(
            written_durations,
            weights=preamble_weights,
            allow_part_weights=abjad.EXACT,
            cyclic=False,
            overhang=False,
        )
        talea_weights = []
        for numerator in unscaled_talea_counts:
            pair = (numerator, talea.denominator)
            weight = abs(abjad.Duration(*pair))
            talea_weights.append(weight)
        preamble_length = len(abjad.sequence.flatten(preamble_parts))
        talea_written_durations = written_durations[preamble_length:]
        talea_parts = abjad.sequence.partition_by_weights(
            talea_written_durations,
            weights=talea_weights,
            allow_part_weights=abjad.MORE,
            cyclic=True,
            overhang=True,
        )
    parts = preamble_parts + talea_parts
    part_durations = abjad.sequence.flatten(parts)
    assert part_durations == list(written_durations)
    counts = [len(part) for part in parts]
    parts = abjad.sequence.partition_by_counts(leaves, counts)
    for i, part in enumerate(parts):
        if any(isinstance(_, abjad.Rest) for _ in part):
            continue
        if len(part) == 1:
            continue
        abjad.tie(part)
    # TODO: this will need to be generalized and better tested:
    if 0 < len(unscaled_end_counts):
        total = len(unscaled_end_counts)
        end_leaves = leaves[-total:]
        for leaf in reversed(end_leaves):
            previous_leaf = abjad.get.leaf(leaf, -1)
            if previous_leaf is not None:
                abjad.detach(abjad.Tie, previous_leaf)


def _durations_to_lcm_pairs(
    durations: list[abjad.Duration],
) -> list[tuple[int, int]]:
    """
    Changes ``durations`` to pairs sharing LCM denominator.

    ..  container:: example

        >>> items = [abjad.Duration(2, 4), 3, (5, 16)]
        >>> durations = abjad.duration.durations(items)
        >>> result = rmakers.makers._durations_to_lcm_pairs(durations)
        >>> for x in result:
        ...     x
        ...
        (8, 16)
        (48, 16)
        (5, 16)

    """
    assert _is_duration_list(durations), repr(durations)
    denominators = [_.denominator for _ in durations]
    lcm = abjad.math.least_common_multiple(*denominators)
    fractions = [_.as_fraction() for _ in durations]
    pairs = [abjad.duration.pair_with_denominator(_, lcm) for _ in fractions]
    return pairs


def _fix_rounding_error(
    notes: typing.Sequence[abjad.Note],
    total_duration: abjad.Duration,
    interpolation: _classes.Interpolation,
) -> None:
    assert all(isinstance(_, abjad.Note) for _ in notes), repr(notes)
    assert isinstance(total_duration, abjad.Duration), repr(total_duration)
    assert isinstance(interpolation, _classes.Interpolation), repr(interpolation)
    if abjad.get.duration(notes) != total_duration:
        nonlast_leaf_duration = abjad.get.duration(notes[:-1])
        needed_duration = total_duration - nonlast_leaf_duration
        multiplier = needed_duration / interpolation.written_duration
        notes[-1].set_dmp(multiplier.as_integer_ratio())


def _function_name(frame: types.FrameType | None) -> abjad.Tag:
    assert frame is not None, repr(frame)
    function_name = frame.f_code.co_name
    string = f"rmakers.{function_name}()"
    return abjad.Tag(string)


def _interpolate_cosine(y1: float, y2: float, mu: float) -> float:
    assert isinstance(y1, float), repr(y1)
    assert isinstance(y2, float), repr(y2)
    assert isinstance(mu, float), repr(mu)
    mu2 = (1 - math.cos(mu * math.pi)) / 2
    result = y1 * (1 - mu2) + y2 * mu2
    assert isinstance(result, float)
    return result


def _interpolate_divide(
    total_duration: abjad.Duration,
    start_duration: abjad.Duration,
    stop_duration: abjad.Duration,
    exponent: str | float = "cosine",
) -> list[float]:
    """
    Divides ``total_duration`` into durations computed from interpolating between
    ``start_duration`` and ``stop_duration``.

    ..  container:: example

        >>> rmakers.makers._interpolate_divide(
        ...     total_duration=abjad.Duration(10, 1),
        ...     start_duration=abjad.Duration(1, 1),
        ...     stop_duration=abjad.Duration(1, 1),
        ...     exponent=1,
        ... )
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        >>> sum(_)
        10.0

        >>> rmakers.makers._interpolate_divide(
        ...     total_duration=abjad.Duration(10, 1),
        ...     start_duration=abjad.Duration(5, 1),
        ...     stop_duration=abjad.Duration(1, 1),
        ... )
        [4.798..., 2.879..., 1.326..., 0.995...]
        >>> sum(_)
        10.0

    Set ``exponent`` to ``'cosine'`` for cosine interpolation.

    Set ``exponent`` to a numeric value for exponential interpolation with
    ``exponent`` as the exponent.

    Scales resulting durations so that their sum equals ``total_duration`` exactly.
    """
    assert isinstance(total_duration, abjad.Duration), repr(total_duration)
    assert isinstance(start_duration, abjad.Duration), repr(start_duration)
    assert isinstance(stop_duration, abjad.Duration), repr(stop_duration)
    assert isinstance(exponent, str | float | int), repr(exponent)
    zero = abjad.Duration(0)
    if total_duration <= zero:
        raise ValueError("Total duration must be positive.")
    if start_duration <= zero or stop_duration <= zero:
        raise Exception("Both 'start_duration' and 'stop_duration' must be positive.")
    if total_duration < (stop_duration + start_duration):
        return []
    float_durations = []
    partial_sum = 0.0
    while partial_sum < float(total_duration):
        if isinstance(exponent, str):
            assert exponent == "cosine"
            float_duration = _interpolate_cosine(
                float(start_duration),
                float(stop_duration),
                partial_sum / float(total_duration),
            )
        else:
            float_duration = _interpolate_exponential(
                float(start_duration),
                float(stop_duration),
                partial_sum / float(total_duration),
                exponent,
            )
        float_durations.append(float_duration)
        partial_sum += float_duration
    float_durations = [
        _ * float(total_duration) / sum(float_durations) for _ in float_durations
    ]
    return float_durations


def _interpolate_exponential(
    y1: float,
    y2: float,
    mu: float,
    exponent: float = 1,
) -> float:
    """
    Interpolates between ``y1`` and ``y2`` at position ``mu``.

    ..  container:: example

        Exponents equal to 1 leave durations unscaled:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.makers._interpolate_exponential(100, 200, mu, exponent=1)
        ...
        100.0
        125.0
        150.0
        175.0
        200.0

        Exponents greater than 1 generate ritardandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.makers._interpolate_exponential(100, 200, mu, exponent=2)
        ...
        100.0
        106.25
        125.0
        156.25
        200.0

        Exponents less than 1 generate accelerandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.makers._interpolate_exponential(100, 200, mu, exponent=0.5)
        ...
        100.0
        150.0
        170.71067811865476
        186.60254037844388
        200.0

    """
    result = float(y1) * (1 - mu**exponent) + float(y2) * mu**exponent
    assert isinstance(result, float)
    return result


def _is_duration_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Duration) for _ in argument)


def _is_fraction_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Fraction) for _ in argument)


def _is_integer_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, int) for _ in argument)


def _is_integer_pair_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    for item in argument:
        if not isinstance(item, tuple):
            return False
        if not len(item) == 2:
            return False
        if not all(isinstance(_, int) for _ in item):
            return False
    return True


def _is_integer_tuple_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    for item in argument:
        if not isinstance(item, tuple):
            return False
        if not all(isinstance(_, int) for _ in item):
            return False
    return True


def _is_integer_or_string_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, int | str) for _ in argument)


def _is_leaf_or_tuplet_list(argument: object) -> bool:
    if not isinstance(argument, list):
        return False
    return all(isinstance(_, abjad.Leaf | abjad.Tuplet) for _ in argument)


def _make_accelerando(
    total_duration: abjad.Duration,
    interpolations: typing.Sequence[_classes.Interpolation],
    index: int,
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> abjad.Tuplet:
    """
    Makes notes with LilyPond multipliers; notes sum to ``total_duration``.

    Total number of notes not specified: total duration is specified instead.

    Selects interpolation specifier at ``index`` in ``interpolations``.

    Computes duration multipliers interpolated from interpolation specifier start to
    stop.

    Sets note written durations according to interpolation specifier.
    """
    assert isinstance(total_duration, abjad.Duration)
    assert all(isinstance(_, _classes.Interpolation) for _ in interpolations)
    assert isinstance(index, int)
    interpolations_cycle = abjad.CyclicTuple(interpolations)
    interpolation = interpolations_cycle[index]
    note_durations_as_floats = _interpolate_divide(
        total_duration=total_duration,
        start_duration=interpolation.start_duration,
        stop_duration=interpolation.stop_duration,
    )
    if note_durations_as_floats == []:
        pitches = abjad.makers.make_pitches([0])
        components = abjad.makers.make_notes(pitches, [total_duration], tag=tag)
        tuplet = abjad.Tuplet("1:1", components, tag=tag)
        return tuplet
    note_durations = _round_durations(note_durations_as_floats, 2**10)
    notes = []
    pitch = abjad.NamedPitch(0)
    for i, duration in enumerate(note_durations):
        duration_multiplier = duration / interpolation.written_duration
        note = abjad.Note.from_duration_and_pitch(
            interpolation.written_duration,
            pitch,
            dmp=duration_multiplier.as_integer_ratio(),
            tag=tag,
        )
        notes.append(note)
    assert all(isinstance(_, abjad.Note) for _ in notes), repr(notes)
    _fix_rounding_error(notes, total_duration, interpolation)
    tuplet = abjad.Tuplet("1:1", notes, tag=tag)
    return tuplet


def _make_components(
    durations: list[abjad.Duration],
    increase_monotonic: bool = False,
    forbidden_note_duration: abjad.Duration | None = None,
    forbidden_rest_duration: abjad.Duration | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf | abjad.Tuplet]:
    assert _is_duration_list(durations), repr(durations)
    assert all(_ != 0 for _ in durations), repr(durations)
    components: list[abjad.Leaf | abjad.Tuplet] = []
    for duration in durations:
        if abjad.Duration(0) < duration:
            pitch_list = [abjad.NamedPitch("c'")]
        else:
            pitch_list = []
        components_ = abjad.makers.make_leaves(
            [pitch_list],
            [abs(duration)],
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        components.extend(components_)
    assert _is_leaf_or_tuplet_list(components), repr(components)
    return components


def _make_incised_duration_lists(
    pairs: list[tuple[int, int]],
    prefix_talea: list[int],
    prefix_counts: list[int],
    suffix_talea: list[int],
    suffix_counts: list[int],
    extra_counts: list[int],
    incise: _classes.Incise,
) -> list[list[abjad.Duration]]:
    assert _is_integer_pair_list(pairs), repr(pairs)
    assert _is_integer_list(prefix_talea)
    assert _is_integer_list(prefix_counts)
    assert _is_integer_list(suffix_talea)
    assert _is_integer_list(suffix_counts)
    assert _is_integer_list(extra_counts)
    prefix_talea_cycle = abjad.CyclicTuple(prefix_talea)
    prefix_counts_cycle = abjad.CyclicTuple(prefix_counts)
    suffix_talea_counts_cycle = abjad.CyclicTuple(suffix_talea)
    suffix_counts_cycle = abjad.CyclicTuple(suffix_counts)
    extra_counts_cycle = abjad.CyclicTuple(extra_counts)
    duration_lists, prefix_talea_index, suffix_talea_index = [], 0, 0
    for pair_index, pair in enumerate(pairs):
        prefix_length = prefix_counts_cycle[pair_index]
        suffix_count = suffix_counts_cycle[pair_index]
        start = prefix_talea_index
        stop = prefix_talea_index + prefix_length
        prefix = prefix_talea_cycle[start:stop]
        start = suffix_talea_index
        stop = suffix_talea_index + suffix_count
        suffix = suffix_talea_counts_cycle[start:stop]
        prefix_talea_index += prefix_length
        suffix_talea_index += suffix_count
        extra_count = extra_counts_cycle[pair_index]
        numerator = pair[0] + (extra_count % pair[0])
        duration_list = _make_duration_list(
            numerator,
            list(prefix),
            list(suffix),
            incise,
        )
        duration_lists.append(duration_list)
    for duration_list in duration_lists:
        assert all(isinstance(_, abjad.Duration) for _ in duration_list)
    return duration_lists


def _make_middle_durations(
    middle_duration: abjad.Duration,
    incise: _classes.Incise,
) -> list[abjad.Duration]:
    assert isinstance(middle_duration, abjad.Duration), repr(middle_duration)
    assert middle_duration.denominator == 1, repr(middle_duration)
    assert isinstance(incise, _classes.Incise), repr(incise)
    durations = []
    if incise.fill_with_rests is False:
        if incise.outer_tuplets_only is False:
            if abjad.Duration(0) < middle_duration:
                if incise.body_proportion is not None:
                    fractions = abjad.math.divide_integer_by_proportion(
                        middle_duration.numerator,
                        incise.body_proportion,
                    )
                    assert _is_fraction_list(fractions), repr(fractions)
                    durations_ = abjad.duration.durations(fractions)
                    durations.extend(durations_)
                else:
                    durations.append(middle_duration)
        else:
            if abjad.Duration(0) < middle_duration:
                durations.append(middle_duration)
    else:
        if incise.outer_tuplets_only is False:
            if abjad.Duration(0) < middle_duration:
                durations.append(-abs(middle_duration))
        else:
            if abjad.Duration(0) < middle_duration:
                durations.append(-abs(middle_duration))
    assert _is_duration_list(durations), repr(durations)
    return durations


def _make_talea_numerator_lists(
    pairs: list[tuple[int, int]],
    preamble_counts: list[int],
    talea_counts: list[int | str],
    extra_counts: list[int],
    end_counts: list[int],
    *,
    read_talea_once_only: bool,
) -> tuple[list[list[int]], list[int] | None]:
    assert _is_integer_pair_list(pairs), repr(pairs)
    assert _is_integer_list(preamble_counts), repr(preamble_counts)
    assert _is_integer_or_string_list(talea_counts), repr(talea_counts)
    assert _is_integer_list(extra_counts), repr(extra_counts)
    assert _is_integer_list(end_counts), repr(end_counts)
    assert isinstance(read_talea_once_only, bool), repr(read_talea_once_only)
    if len(extra_counts) == 0:
        prolated_pairs = pairs
    else:
        prolated_pairs = _make_prolated_pairs(pairs, extra_counts)
    prolated_numerators = [_[0] for _ in prolated_pairs]
    expanded_talea = None
    talea_integer_counts = []
    if "-" in talea_counts or "+" in talea_counts:
        assert len(preamble_counts) == 0, repr(preamble_counts)
        prolated_numerator_weight = sum(prolated_numerators)
        talea_counts_copy = list(talea_counts)
        if "-" in talea_counts:
            index = talea_counts.index("-")
        else:
            index = talea_counts.index("+")
        talea_counts_copy[index] = 0
        explicit_weight = 0
        for count in talea_counts_copy:
            assert isinstance(count, int), repr(count)
            explicit_weight = explicit_weight + abs(count)
        implicit_weight = prolated_numerator_weight - explicit_weight
        if "-" in talea_counts:
            implicit_weight *= -1
        talea_counts_copy[index] = implicit_weight
        expanded_talea = []
        for n in talea_counts_copy:
            assert isinstance(n, int), repr(n)
            expanded_talea.append(n)
        talea_integer_counts = expanded_talea
    else:
        for n in talea_counts:
            assert isinstance(n, int), repr(n)
            talea_integer_counts.append(n)
    numerator_lists = _split_talea_extended_to_weights(
        preamble_counts,
        prolated_numerators,
        talea_integer_counts,
        read_talea_once_only=read_talea_once_only,
    )
    if 0 < len(end_counts):
        end_weight = abjad.math.weight(end_counts, start=0)
        numerator_list_weights = [
            abjad.math.weight(_, start=0) for _ in numerator_lists
        ]
        numerators = abjad.sequence.flatten(numerator_lists)
        numerators_weight = abjad.math.weight(numerators, start=0)
        assert end_weight <= numerators_weight, repr(end_counts)
        left_weight = numerators_weight - end_weight
        numerator_lists = abjad.sequence.split(numerators, [left_weight, end_weight])
        numerators = numerator_lists[0] + end_counts
        assert abjad.math.weight(numerators, start=0) == numerators_weight
        numerator_lists = abjad.sequence.partition_by_weights(
            numerators,
            numerator_list_weights,
        )
    assert all(_is_integer_list(_) for _ in numerator_lists), repr(numerator_lists)
    return numerator_lists, expanded_talea


def _make_duration_list(
    numerator: int,
    prefix_counts: list[int],
    suffix_counts: list[int],
    incise: _classes.Incise,
    *,
    is_note_filled: bool = True,
) -> list[abjad.Duration]:
    numerator_duration = abjad.Duration(numerator)
    assert _is_integer_list(prefix_counts), repr(prefix_counts)
    assert _is_integer_list(suffix_counts), repr(suffix_counts)
    prefix_durations = [abjad.Duration(_) for _ in prefix_counts]
    suffix_durations = [abjad.Duration(_) for _ in suffix_counts]
    prefix_weight = abjad.math.weight(prefix_durations, start=abjad.Duration(0))
    suffix_weight = abjad.math.weight(suffix_durations, start=abjad.Duration(0))
    middle_duration = numerator_duration - prefix_weight - suffix_weight
    assert isinstance(middle_duration, abjad.Duration), repr(middle_duration)
    if numerator_duration < prefix_weight:
        weights = [numerator_duration]
        prefix_durations = abjad.sequence.split(
            prefix_durations, weights, cyclic=False, overhang=False
        )[0]
    middle_durations = _make_middle_durations(middle_duration, incise)
    suffix_space = numerator_duration - prefix_weight
    if suffix_space <= abjad.Duration(0):
        suffix_durations = []
    elif suffix_space < suffix_weight:
        weights = [suffix_space]
        suffix_durations = abjad.sequence.split(
            suffix_durations, weights, cyclic=False, overhang=False
        )[0]
    assert all(isinstance(_, abjad.Duration) for _ in prefix_durations), repr(
        prefix_durations
    )
    assert all(isinstance(_, abjad.Duration) for _ in suffix_durations), repr(
        suffix_durations
    )
    duration_list = prefix_durations + middle_durations + suffix_durations
    assert all(isinstance(_, abjad.Duration) for _ in duration_list), repr(
        duration_list
    )
    return duration_list


def _make_outer_tuplets_only_incised_duration_lists(
    scaled_pairs: list[tuple[int, int]],
    scaled_prefix_talea_counts: list[int],
    scaled_suffix_talea_counts: list[int],
    scaled_extra_counts: list[int],
    incise: _classes.Incise,
) -> list[list[abjad.Duration]]:
    assert _is_integer_pair_list(scaled_pairs), repr(scaled_pairs)
    assert _is_integer_list(scaled_prefix_talea_counts)
    assert _is_integer_list(scaled_suffix_talea_counts)
    assert _is_integer_list(scaled_extra_counts)
    scaled_prefix_talea_counts_cycle = abjad.CyclicTuple(scaled_prefix_talea_counts)
    prefix_counts_cycle = abjad.CyclicTuple(incise.prefix_counts or [0])
    scaled_suffix_talea_counts_cycle = abjad.CyclicTuple(scaled_suffix_talea_counts)
    suffix_counts_cycle = abjad.CyclicTuple(incise.suffix_counts or [0])
    scaled_extra_counts_cycle = abjad.CyclicTuple(scaled_extra_counts)
    duration_lists, prefix_talea_index, suffix_talea_index = [], 0, 0
    prefix_count = prefix_counts_cycle[0]
    suffix_count = suffix_counts_cycle[0]
    start = prefix_talea_index
    stop = prefix_talea_index + prefix_count
    prefix_talea_counts = scaled_prefix_talea_counts_cycle[start:stop]
    start = suffix_talea_index
    stop = suffix_talea_index + suffix_count
    suffix_talea_counts = scaled_suffix_talea_counts_cycle[start:stop]
    if len(scaled_pairs) == 1:
        extra_count = scaled_extra_counts_cycle[0]
        numerator = scaled_pairs[0][0]
        numerator += extra_count % numerator
        duration_list = _make_duration_list(
            numerator,
            list(prefix_talea_counts),
            list(suffix_talea_counts),
            incise,
        )
        duration_lists.append(duration_list)
    else:
        extra_count = scaled_extra_counts_cycle[0]
        if isinstance(scaled_pairs[0], tuple):
            numerator = scaled_pairs[0][0]
        else:
            numerator = scaled_pairs[0].numerator
        numerator += extra_count % numerator
        duration_list = _make_duration_list(
            numerator,
            list(prefix_talea_counts),
            [],
            incise,
        )
        duration_lists.append(duration_list)
        for i, scaled_pair in enumerate(scaled_pairs[1:-1]):
            index = i + 1
            extra_count = scaled_extra_counts_cycle[index]
            numerator = scaled_pair[0]
            numerator += extra_count % numerator
            duration_list = _make_duration_list(numerator, [], [], incise)
            duration_lists.append(duration_list)
        try:
            index = i + 2
            extra_count = scaled_extra_counts_cycle[index]
        except UnboundLocalError:
            index = 1 + 2
            extra_count = scaled_extra_counts_cycle[index]
        if isinstance(scaled_pairs[-1], tuple):
            numerator = scaled_pairs[-1][0]
        else:
            numerator = scaled_pairs[-1].numerator
        numerator += extra_count % numerator
        duration_list = _make_duration_list(
            numerator,
            [],
            list(suffix_talea_counts),
            incise,
        )
        duration_lists.append(duration_list)
    return duration_lists


def _make_prolated_pairs(
    pairs: list[tuple[int, int]],
    extra_counts: list[int],
) -> list[tuple[int, int]]:
    extra_counts_cycle = abjad.CyclicTuple(extra_counts)
    prolated_pairs = []
    for i, pair in enumerate(pairs):
        numerator = pair[0]
        extra_count = extra_counts_cycle[i]
        if 0 <= extra_count:
            extra_count %= numerator
        else:
            # NOTE: do not remove the following (nonfunctional) if-else;
            #       preserved for backwards compatability.
            use_old_extra_counts_logic = False
            if use_old_extra_counts_logic:
                extra_count %= numerator
            else:
                extra_count %= -numerator
        numerator, denominator = pair
        prolated_pair = (numerator + extra_count, denominator)
        prolated_pairs.append(prolated_pair)
    assert _is_integer_pair_list(prolated_pairs), repr(prolated_pairs)
    return prolated_pairs


def _make_state_dictionary(
    *,
    durations_consumed: int,
    logical_ties_produced: int,
    previous_durations_consumed: int,
    previous_incomplete_last_note: int,
    previous_logical_ties_produced: int,
    state: dict,
) -> dict:
    durations_consumed_ = previous_durations_consumed + durations_consumed
    state["durations_consumed"] = durations_consumed_
    logical_ties_produced_ = previous_logical_ties_produced + logical_ties_produced
    if previous_incomplete_last_note:
        logical_ties_produced_ -= 1
    state["logical_ties_produced"] = logical_ties_produced_
    state = dict(sorted(state.items()))
    return state


def _make_talea_tuplets(
    durations: list[abjad.Duration],
    extra_counts: list[int],
    previous_state: dict,
    read_talea_once_only: bool,
    spelling: _classes.Spelling,
    state: dict,
    talea: _classes.Talea,
    tag: abjad.Tag,
) -> list[abjad.Tuplet]:
    assert _is_duration_list(durations), repr(durations)
    assert _is_integer_list(extra_counts)
    assert isinstance(previous_state, dict), repr(previous_state)
    assert isinstance(read_talea_once_only, bool), repr(read_talea_once_only)
    assert isinstance(talea, _classes.Talea), repr(talea)
    talea_weight_consumed = previous_state.get("talea_weight_consumed", 0)
    assert isinstance(talea_weight_consumed, int), repr(talea_weight_consumed)
    advanced_talea = talea.advance(talea_weight_consumed)
    durations_consumed = previous_state.get("durations_consumed", 0)
    assert isinstance(durations_consumed, int), repr(durations_consumed)
    rotated_extra_counts = abjad.sequence.rotate(extra_counts, -durations_consumed)
    durations_ = durations[:]
    dummy_duration = abjad.Duration(1, talea.denominator)
    durations_.append(dummy_duration)
    scaled_pairs = _durations_to_lcm_pairs(durations_)
    dummy_pair = scaled_pairs.pop()
    lcd = dummy_pair[1]
    multiplier = lcd / talea.denominator
    assert abjad.math.is_integer_equivalent(multiplier)
    multiplier = int(multiplier)
    scaled_end_counts = [multiplier * _ for _ in advanced_talea.end_counts]
    scaled_extra_counts = [multiplier * _ for _ in rotated_extra_counts]
    scaled_preamble_counts = [multiplier * _ for _ in advanced_talea.preamble]
    scaled_talea_counts = [multiplier * _ for _ in advanced_talea.counts]
    numerator_lists, expanded_talea = _make_talea_numerator_lists(
        scaled_pairs,
        scaled_preamble_counts,
        scaled_talea_counts,
        scaled_extra_counts,
        scaled_end_counts,
        read_talea_once_only=read_talea_once_only,
    )
    unscaled_talea = []
    if expanded_talea is not None:
        unscaled_talea = expanded_talea
    else:
        for count in advanced_talea.counts:
            assert isinstance(count, int)
            unscaled_talea.append(count)
    talea_weight_consumed = sum(abjad.math.weight(_, start=0) for _ in numerator_lists)
    component_lists = []
    for numerator_list in numerator_lists:
        duration_list = [abjad.Duration(_, lcd) for _ in numerator_list]
        component_list = _make_components(
            duration_list,
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        component_lists.append(component_list)
    if scaled_extra_counts == []:
        tuplets = [abjad.Tuplet("1:1", _) for _ in component_lists]
    else:
        durations_ = abjad.duration.durations(scaled_pairs)
        tuplets = _package_tuplets(durations_, component_lists, tag=tag)
    _apply_ties_to_split_notes(
        tuplets,
        advanced_talea.end_counts,
        advanced_talea.preamble,
        unscaled_talea,
        talea,
    )
    for tuplet in abjad.iterate.components(tuplets, abjad.Tuplet):
        tuplet.normalize_ratio()
    assert isinstance(state, dict)
    advanced_talea = _classes.Talea(
        counts=list(advanced_talea.counts),
        denominator=talea.denominator,
        end_counts=list(advanced_talea.end_counts),
        preamble=list(advanced_talea.preamble),
    )
    if "+" in advanced_talea.counts or "-" in advanced_talea.counts:
        pass
    elif talea_weight_consumed not in advanced_talea:
        last_leaf = abjad.get.leaf(tuplets, -1)
        if isinstance(last_leaf, abjad.Note):
            state["incomplete_last_note"] = True
    string = "talea_weight_consumed"
    assert isinstance(previous_state, dict)
    state[string] = previous_state.get(string, 0)
    state[string] += talea_weight_consumed
    return tuplets


def _package_tuplets(
    durations: list[abjad.Duration],
    component_lists: list[list[abjad.Leaf | abjad.Tuplet]],
    *,
    tag: abjad.Tag,
) -> list[abjad.Tuplet]:
    assert _is_duration_list(durations), repr(durations)
    assert isinstance(tag, abjad.Tag), repr(tag)
    prototype = (abjad.Leaf, abjad.Tuplet)
    for item in component_lists:
        assert all(isinstance(_, prototype) for _ in item), repr(item)
    tuplets = []
    for duration, component_list in zip(durations, component_lists, strict=True):
        multiplier = duration / abjad.get.duration(component_list)
        ratio = abjad.Ratio(multiplier.denominator, multiplier.numerator)
        tuplet = abjad.Tuplet(ratio, component_list, tag=tag)
        tuplets.append(tuplet)
    return tuplets


def _round_durations(
    float_durations: typing.Sequence[float],
    denominator: int,
) -> list[abjad.Duration]:
    assert all(isinstance(_, float) for _ in float_durations), repr(float_durations)
    assert isinstance(denominator, int), repr(denominator)
    durations = []
    for float_duration in float_durations:
        numerator = int(round(float_duration * denominator))
        duration = abjad.Duration(numerator, denominator)
        durations.append(duration)
    return durations


def _split_talea_extended_to_weights(
    preamble_counts: list[int],
    prolated_numerators: list[int],
    talea_counts: list[int],
    *,
    read_talea_once_only: bool,
) -> list[list[int]]:
    assert _is_integer_list(preamble_counts), repr(preamble_counts)
    assert _is_integer_list(talea_counts), repr(talea_counts)
    assert _is_integer_list(prolated_numerators), repr(prolated_numerators)
    assert abjad.math.all_are_positive_integers(prolated_numerators)
    preamble_weight = abjad.math.weight(preamble_counts, start=0)
    talea_weight = abjad.math.weight(talea_counts, start=0)
    prolated_numerator_weight = abjad.math.weight(prolated_numerators, start=0)
    if (
        read_talea_once_only is True
        and preamble_weight + talea_weight < prolated_numerator_weight
    ):
        message = f"{preamble_counts!s} + {talea_counts!s} is too short"
        message += f" to read {prolated_numerators} once."
        raise Exception(message)
    if prolated_numerator_weight <= preamble_weight:
        talea_counts = abjad.sequence.truncate(
            preamble_counts,
            weight=prolated_numerator_weight,
        )
    else:
        prolated_numerator_weight -= preamble_weight
        talea_counts = abjad.sequence.repeat_to_weight(
            talea_counts,
            prolated_numerator_weight,
        )
        talea_counts = preamble_counts + talea_counts
    numerator_lists = abjad.sequence.split(
        talea_counts,
        prolated_numerators,
        cyclic=True,
    )
    return numerator_lists


def accelerando(
    durations: list[abjad.Duration],
    interpolations: list[_classes.Interpolation],
    *,
    previous_state: dict | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one accelerando (or ritardando) for each duration in ``durations``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, interpolations):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.accelerando(durations, interpolations)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.feather_beam(voice)
        ...     rmakers.duration_bracket(voice)
        ...     rmakers.swap_length_1(voice)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.padding = 2
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     return lilypond_file

    ..  container:: example

        Makes accelerandi:

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> durations = abjad.duration.durations([(1, 8), (1, 20), (1, 16)])
        >>> interpolation = rmakers.Interpolation(*durations)
        >>> interpolations = [interpolation]
        >>> lilypond_file = make_lilypond_file(pairs, interpolations)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                }
            }

    ..  container:: example

        Makes ritardandi:

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> durations = abjad.duration.durations([(1, 20), (1, 8), (1, 16)])
        >>> interpolation = rmakers.Interpolation(*durations)
        >>> lilypond_file = make_lilypond_file(pairs, [interpolation])
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                }
            }

    ..  container:: example

        Makes accelerandi and ritardandi, alternatingly:

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> duration_lists = [
        ...     abjad.duration.durations([(1, 8), (1, 20), (1, 16)]),
        ...     abjad.duration.durations([(1, 20), (1, 8), (1, 16)]),
        ... ]
        >>> interpolations = [rmakers.Interpolation(*_) for _ in duration_lists]
        >>> lilypond_file = make_lilypond_file(pairs, interpolations)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                }
            }

    ..  container:: example

        Populates short duration with single note:

        >>> pairs = [(5, 8), (3, 8), (1, 8)]
        >>> durations = abjad.duration.durations([(1, 8), (1, 20), (1, 16)])
        >>> interpolation = rmakers.Interpolation(*durations)
        >>> lilypond_file = make_lilypond_file(pairs, [interpolation])
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) { \rhythm { 2 } + \rhythm { 8 } }
                        \tuplet 1/1
                        {
                            \time 5/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 61/32
                            [
                            c'16 * 115/64
                            c'16 * 49/32
                            c'16 * 5/4
                            c'16 * 33/32
                            c'16 * 57/64
                            c'16 * 13/16
                            c'16 * 25/32
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        {
                            \time 1/8
                            c'8
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert _is_duration_list(durations), repr(durations)
    assert isinstance(interpolations, list), repr(interpolations)
    class_ = _classes.Interpolation
    assert all(isinstance(_, class_) for _ in interpolations), repr(interpolations)
    assert isinstance(spelling, _classes.Spelling), repr(spelling)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    durations_consumed = previous_state.get("durations_consumed", 0)
    interpolations = abjad.sequence.rotate(interpolations, n=-durations_consumed)
    tuplets = []
    for i, duration in enumerate(durations):
        tuplet = _make_accelerando(duration, interpolations, i, tag=tag)
        tuplets.append(tuplet)
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        durations_consumed=len(durations),
        logical_ties_produced=logical_ties_produced,
        previous_durations_consumed=previous_state.get("durations_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    components, tuplets = abjad.mutate.eject_contents(voice), []
    for component in components:
        assert isinstance(component, abjad.Tuplet)
        abjad.attach("FEATHER_BEAM_CONTAINER", tuplet)
        tuplets.append(component)
    state.clear()
    state.update(new_state)
    return tuplets


def even_division(
    durations: list[abjad.Duration],
    denominators: list[int],
    *,
    extra_counts: list[int] | None = None,
    previous_state: dict | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one even-division tuplet for each duration in ``durations``.

    ..  container:: example

        Basic example:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[0, 0, 1])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.force_diminution(voice)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(5, 16), (6, 16), (6, 16)]
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
                        \tuplet 8/5
                        {
                            \time 5/16
                            c'4
                            c'4
                        }
                        \time 6/16
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Understanding the ``denominators`` argument to ``rmakers.even_division()``.

        ..  container:: example

            Fills tuplets with 16th notes and 8th notes, alternately:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(durations, [16, 8])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                            \time 3/16
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            \time 3/4
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                }

        ..  container:: example

            Fills tuplets with 8th notes:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(durations, [8])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                            \time 3/16
                            c'8.
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            \time 3/4
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            c'8
                            c'8
                            ]
                        }
                    }
                }

            (Fills tuplets less than twice the duration of an eighth note with a single
            attack.)

        ..  container:: example

            Fills tuplets with quarter notes:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(durations, [4])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                            \time 3/16
                            c'8.
                            \time 3/8
                            c'4.
                            \time 3/4
                            c'4
                            c'4
                            c'4
                        }
                    }
                }

            (Fills tuplets less than twice the duration of a quarter note with a single
            attack.)

        ..  container:: example

            Fills tuplets with half notes:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(durations, [2])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                            \time 3/16
                            c'8.
                            \time 3/8
                            c'4.
                            \time 3/4
                            c'2.
                        }
                    }
                }

            (Fills tuplets less than twice the duration of a half note with a single
            attack.)

    ..  container:: example

        Using ``rmakers.even_division()`` with the ``extra_counts`` keyword.

        ..  container:: example

            Adds extra counts to tuplets according to a pattern of three elements:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[0, 1, 2]
            ...     )
            ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8), (3, 8)]
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
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/6
                            {
                                c'16
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 8/6
                            {
                                c'16
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/6
                            {
                                c'16
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                        }
                    }
                }

        ..  container:: example

            **Modular handling of positive values.** Denote by ``unprolated_note_count``
            the number counts included in a tuplet when ``extra_counts`` is set to zero.
            Then extra counts equals ``extra_counts % unprolated_note_count`` when
            ``extra_counts`` is positive.

            This is likely to be intuitive; compare with the handling of negative values,
            below.

            For positive extra counts, the modulus of transformation of a tuplet with six
            notes is six:

            >>> import math
            >>> unprolated_note_count = 6
            >>> modulus = unprolated_note_count
            >>> extra_counts = list(range(12))
            >>> labels = []
            >>> for count in extra_counts:
            ...     modular_count = count % modulus
            ...     label = rf"\markup {{ {count:3} becomes {modular_count:2} }}"
            ...     labels.append(label)

            Which produces the following pattern of changes:

            >>> def make_lilypond_file(pairs, extra_counts):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=extra_counts
            ...     )
            ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = 12 * [(6, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts)
            >>> staff = lilypond_file["Staff"]
            >>> abjad.override(staff).TextScript.staff_padding = 7
            >>> leaves = abjad.select.leaves(staff)
            >>> groups = abjad.select.group_by_measure(leaves)
            >>> for group, label in zip(groups, labels, strict=True):
            ...     markup = abjad.Markup(label)
            ...     abjad.attach(markup, group[0], direction=abjad.UP)
            ...

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
                        \override TextScript.staff-padding = 7
                    }
                    {
                        \context Voice = "Voice"
                        {
                            \time 6/16
                            c'16
                            ^ \markup {   0 becomes  0 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/6
                            {
                                c'16
                                ^ \markup {   1 becomes  1 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 8/6
                            {
                                c'16
                                ^ \markup {   2 becomes  2 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 9/6
                            {
                                c'16
                                ^ \markup {   3 becomes  3 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/6
                            {
                                c'16
                                ^ \markup {   4 becomes  4 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 11/6
                            {
                                c'16
                                ^ \markup {   5 becomes  5 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            c'16
                            ^ \markup {   6 becomes  0 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/6
                            {
                                c'16
                                ^ \markup {   7 becomes  1 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 8/6
                            {
                                c'16
                                ^ \markup {   8 becomes  2 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 9/6
                            {
                                c'16
                                ^ \markup {   9 becomes  3 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/6
                            {
                                c'16
                                ^ \markup {  10 becomes  4 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 11/6
                            {
                                c'16
                                ^ \markup {  11 becomes  5 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                        }
                    }
                }

            This modular formula ensures that rhythm-maker ``denominators`` are always
            respected: a very large number of extra counts never causes a
            ``16``-denominated tuplet to result in 32nd- or 64th-note rhythms.

        ..  container:: example

            **Modular handling of negative values.** Denote by ``unprolated_note_count``
            the number of counts included in a tuplet when ``extra_counts`` is set to
            zero. Further, let ``modulus = ceiling(unprolated_note_count / 2)``. Then
            extra counts equals ``-(abs(extra_counts) % modulus)`` when ``extra_counts``
            is negative.

            For negative extra counts, the modulus of transformation of a tuplet with six
            notes is three:

            >>> import math
            >>> unprolated_note_count = 6
            >>> modulus = math.ceil(unprolated_note_count / 2)
            >>> extra_counts = [0, -1, -2, -3, -4, -5, -6, -7, -8]
            >>> labels = []
            >>> for count in extra_counts:
            ...     modular_count = -(abs(count) % modulus)
            ...     label = rf"\markup {{ {count:3} becomes {modular_count:2} }}"
            ...     labels.append(label)

            Which produces the following pattern of changes:

            >>> def make_lilypond_file(pairs, extra_counts):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=extra_counts
            ...     )
            ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = 9 * [(6, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts)
            >>> staff = lilypond_file["Staff"]
            >>> abjad.override(staff).TextScript.staff_padding = 8
            >>> leaves = abjad.select.leaves(staff)
            >>> groups = abjad.select.group_by_measure(leaves)
            >>> for group, label in zip(groups, labels, strict=True):
            ...     markup = abjad.Markup(label)
            ...     abjad.attach(markup, group[0], direction=abjad.UP)
            ...

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
                        \override TextScript.staff-padding = 8
                    }
                    {
                        \context Voice = "Voice"
                        {
                            \time 6/16
                            c'16
                            ^ \markup {   0 becomes  0 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/6
                            {
                                c'16
                                ^ \markup {  -1 becomes -1 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 4/6
                            {
                                c'16
                                ^ \markup {  -2 becomes -2 }
                                [
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            c'16
                            ^ \markup {  -3 becomes  0 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/6
                            {
                                c'16
                                ^ \markup {  -4 becomes -1 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 4/6
                            {
                                c'16
                                ^ \markup {  -5 becomes -2 }
                                [
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            c'16
                            ^ \markup {  -6 becomes  0 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/6
                            {
                                c'16
                                ^ \markup {  -7 becomes -1 }
                                [
                                c'16
                                c'16
                                c'16
                                c'16
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 4/6
                            {
                                c'16
                                ^ \markup {  -8 becomes -2 }
                                [
                                c'16
                                c'16
                                c'16
                                ]
                            }
                        }
                    }
                }

            This modular formula ensures that rhythm-maker ``denominators`` are
            always respected: a very small number of extra counts never causes
            a ``16``-denominated tuplet to result in 8th- or quarter-note
            rhythms.

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert _is_duration_list(durations), repr(durations)
    assert _is_integer_list(denominators), repr(denominators)
    if extra_counts is None:
        extra_counts = [0]
    assert _is_integer_list(extra_counts), repr(extra_counts)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    tuplets = []
    assert isinstance(previous_state, dict)
    durations_consumed = previous_state.get("durations_consumed", 0)
    denominators_ = list(denominators)
    denominators_ = abjad.sequence.rotate(denominators_, -durations_consumed)
    cyclic_denominators = abjad.CyclicTuple(denominators_)
    extra_counts_ = extra_counts or [0]
    extra_counts__ = list(extra_counts_)
    extra_counts__ = abjad.sequence.rotate(extra_counts__, -durations_consumed)
    cyclic_extra_counts = abjad.CyclicTuple(extra_counts__)
    for i, duration in enumerate(durations):
        tuplet_duration = duration
        if not abjad.math.is_positive_integer_power_of_two(tuplet_duration.denominator):
            raise Exception(f"nondyadic durations not implemented: {tuplet_duration}")
        denominator_ = cyclic_denominators[i]
        extra_count = cyclic_extra_counts[i]
        note_duration = abjad.Duration(1, denominator_)
        assert note_duration.is_dyadic()
        unprolated_note_count = None
        pitches = abjad.makers.make_pitches([0])
        if tuplet_duration < 2 * note_duration:
            note_durations = [tuplet_duration]
        else:
            unprolated_note_count_fraction = tuplet_duration / note_duration
            unprolated_note_count = int(unprolated_note_count_fraction)
            unprolated_note_count = unprolated_note_count or 1
            if 0 < extra_count:
                modulus = unprolated_note_count
                extra_count = extra_count % modulus
            elif extra_count < 0:
                modulus = int(math.ceil(unprolated_note_count / 2.0))
                extra_count = abs(extra_count) % modulus
                extra_count *= -1
            note_count = unprolated_note_count + extra_count
            note_durations = note_count * [note_duration]
        notes = abjad.makers.make_notes(pitches, note_durations, tag=tag)
        multiplier = tuplet_duration / abjad.get.duration(notes)
        ratio = abjad.Ratio(multiplier.denominator, multiplier.numerator)
        tuplet = abjad.Tuplet(ratio, notes, tag=tag)
        if unprolated_note_count is not None:
            multiplier_numerator = tuplet.ratio().denominator
            multiplier_denominator = tuplet.ratio().numerator
            if multiplier_denominator < note_count:
                scalar = note_count / multiplier_denominator
                assert scalar == int(scalar)
                scalar = int(scalar)
                multiplier_denominator *= scalar
                multiplier_numerator *= scalar
                ratio_ = abjad.Ratio(multiplier_denominator, multiplier_numerator)
                tuplet.set_ratio(ratio_)
                assert tuplet.ratio().numerator == note_count
        tuplets.append(tuplet)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        durations_consumed=len(durations),
        logical_ties_produced=logical_ties_produced,
        previous_durations_consumed=previous_state.get("durations_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    components, tuplets = abjad.mutate.eject_contents(voice), []
    for component in components:
        assert isinstance(component, abjad.Tuplet)
        tuplets.append(component)
    state.clear()
    state.update(new_state)
    return tuplets


def incised(
    durations: list[abjad.Duration],
    talea_denominator: int,
    *,
    body_proportion: tuple[int, ...] = (1,),
    extra_counts: typing.Sequence[int] | None = None,
    fill_with_rests: bool = False,
    outer_tuplets_only: bool = False,
    prefix_counts: list[int] | None = None,
    prefix_talea: list[int] | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    suffix_counts: list[int] | None = None,
    suffix_talea: list[int] | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one incised tuplet for each duration in  ``durations``.

    ..  container:: example

        Set ``prefix_talea=[-1]`` with ``prefix_counts=[1]`` to incise a rest
        at the start of each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        r16
                        c'4
                        r16
                        c'4
                        r16
                        c'4
                        r16
                        c'4
                    }
                }
            }

    Set ``prefix_talea=[-1]`` with ``prefix_counts=[2]`` to incise 2 rests at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[2],
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        r16
                        r16
                        c'8.
                        r16
                        r16
                        c'8.
                        r16
                        r16
                        c'8.
                        r16
                        r16
                        c'8.
                    }
                }
            }

    Set ``prefix_talea=[1]`` with ``prefix_counts=[1]`` to incise 1 note at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         prefix_talea=[1],
        ...         prefix_counts=[1],
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        c'16
                        c'4
                        c'16
                        c'4
                        c'16
                        c'4
                        c'16
                        c'4
                    }
                }
            }

    Set ``prefix_talea=[1]`` with ``prefix_counts=[2]`` to incise 2 notes at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         prefix_talea=[1],
        ...         prefix_counts=[2],
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                    }
                }
            }

    Incise rests at the beginning and end of each tuplet like this:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         extra_counts=[1],
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...     )
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \tuplet 6/5
                        {
                            \time 5/16
                            r16
                            c'4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            c'4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            c'4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            c'4
                            r16
                        }
                    }
                }
            }

    Set ``body_proportion=(1, 1)`` to divide the middle part of each tuplet ``1:1``:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         body_proportion=(1, 1),
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                    }
                }
            }

    ..  container:: example

        Set ``body_proportion=(1, 1, 1)`` to divide the middle part of each
        tuplet ``1:1:1``:

        TODO. Allow nested tuplets to clean up notation:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         talea_denominator=16,
        ...         body_proportion=(1, 1, 1),
        ...     )
        ...     abjad.makers.tweak_tuplet_bracket_edge_height(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            \time 5/16
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert _is_duration_list(durations)
    assert isinstance(talea_denominator, int), repr(talea_denominator)
    if extra_counts is None:
        extra_counts = [0]
    assert _is_integer_list(extra_counts), repr(extra_counts)
    incise = _classes.Incise(
        talea_denominator,
        body_proportion=body_proportion,
        fill_with_rests=fill_with_rests,
        outer_tuplets_only=outer_tuplets_only,
        prefix_talea=prefix_talea or [],
        prefix_counts=prefix_counts or [],
        suffix_talea=suffix_talea or [],
        suffix_counts=suffix_counts or [],
    )
    duration = abjad.Duration(1, incise.talea_denominator)
    scaled_pairs = _durations_to_lcm_pairs(durations + [duration])
    lcm = scaled_pairs.pop()[1]
    multiplier = lcm / incise.talea_denominator
    assert abjad.math.is_integer_equivalent(multiplier)
    multiplier = int(multiplier)
    scaled_prefix_talea_counts = [multiplier * _ for _ in incise.prefix_talea]
    scaled_suffix_talea_counts = [multiplier * _ for _ in incise.suffix_talea]
    scaled_extra_counts = [multiplier * _ for _ in extra_counts]
    if incise.outer_tuplets_only:
        duration_lists = _make_outer_tuplets_only_incised_duration_lists(
            scaled_pairs,
            scaled_prefix_talea_counts,
            scaled_suffix_talea_counts,
            scaled_extra_counts,
            incise,
        )
    else:
        duration_lists = _make_incised_duration_lists(
            scaled_pairs,
            scaled_prefix_talea_counts,
            incise.prefix_counts or [0],
            scaled_suffix_talea_counts,
            incise.suffix_counts or [0],
            scaled_extra_counts,
            incise,
        )
    component_lists = []
    for duration_list in duration_lists:
        duration_list_ = []
        for duration in duration_list:
            if duration == abjad.Duration(0):
                continue
            fraction = duration.as_fraction()
            fraction = abjad.Fraction(fraction, lcm)
            pair = fraction.as_integer_ratio()
            duration = abjad.Duration(*pair)
            duration_list_.append(duration)
        components = _make_components(
            duration_list_,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            increase_monotonic=spelling.increase_monotonic,
            tag=tag,
        )
        component_lists.append(components)
    durations = abjad.duration.durations(scaled_pairs)
    tuplets = _package_tuplets(durations, component_lists, tag=tag)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
    return tuplets


def multiplied_duration(
    durations: list[abjad.Duration],
    written_duration: abjad.Duration = abjad.Duration(1, 1),
    *,
    tag: abjad.Tag | None = None,
) -> list[abjad.Note]:
    r"""
    Makes one note with ``written_duration`` and duration multiplier for each
    duration in ``durations``.

    ..  container:: example

        >>> def make_lilypond_file(durations, written_duration):
        ...     components = rmakers.multiplied_duration(durations, written_duration)
        ...     integer_ratios = [_.as_integer_ratio() for _ in durations]
        ...     time_signatures = rmakers.time_signatures(integer_ratios)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

    ..  container:: example

        Makes whole notes with duration multipliers:

        >>> durations = abjad.duration.durations([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> written_duration = abjad.Duration(1)
        >>> lilypond_file = make_lilypond_file(durations, written_duration)
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
                        \time 1/4
                        c'1 * 1/4
                        \time 3/16
                        c'1 * 3/16
                        \time 5/8
                        c'1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        c'1 * 1/3
                    }
                }
            }

        Makes half notes with duration multipliers:

        >>> written_duration = abjad.Duration(1, 2)
        >>> lilypond_file = make_lilypond_file(durations, written_duration)
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
                        \time 1/4
                        c'2 * 2/4
                        \time 3/16
                        c'2 * 6/16
                        \time 5/8
                        c'2 * 10/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        c'2 * 2/3
                    }
                }
            }

        Makes quarter notes with duration multipliers:

        >>> written_duration = abjad.Duration(1, 4)
        >>> lilypond_file = make_lilypond_file(durations, written_duration)
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
                        \time 1/4
                        c'4 * 4/4
                        \time 3/16
                        c'4 * 12/16
                        \time 5/8
                        c'4 * 20/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        c'4 * 4/3
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert isinstance(written_duration, abjad.Duration), repr(written_duration)
    notes = []
    pitch = abjad.NamedPitch("c'")
    for duration in durations:
        multiplier = duration / written_duration
        denominators = [duration.denominator, multiplier.denominator]
        denominator = abjad.math.least_common_multiple(*denominators)
        dmp = abjad.duration.pair_with_denominator(multiplier, denominator)
        note = abjad.Note.from_duration_and_pitch(
            written_duration,
            pitch,
            dmp=dmp,
            tag=tag,
        )
        notes.append(note)
    return notes


def note(
    durations: list[abjad.Duration],
    *,
    spelling: _classes.Spelling = _classes.Spelling(),
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf | abjad.Tuplet]:
    r"""
    Makes one or more notes (or tuplets) for every duration in ``durations``.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     notes = rmakers.note(durations)
        ...     lilypond_file = rmakers.example(notes, time_signatures)
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
                        c'2
                        \time 3/8
                        c'4.
                        \time 4/8
                        c'2
                        \time 3/8
                        c'4.
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert isinstance(spelling, _classes.Spelling), repr(spelling)
    components = []
    for duration in durations:
        components_ = abjad.makers.make_leaves(
            [[abjad.NamedPitch("c'")]],
            [duration],
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        components.extend(components_)
    assert _is_leaf_or_tuplet_list(components), repr(components)
    return components


def talea(
    durations: list[abjad.Duration],
    counts: list[int | str],
    denominator: int,
    *,
    advance: int = 0,
    end_counts: list[int] | None = None,
    extra_counts: list[int] | None = None,
    preamble: list[int] | None = None,
    previous_state: dict | None = None,
    read_talea_once_only: bool = False,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Reads ``counts`` cyclically and makes one tuplet for each duration in
    ``durations``.

    ..  container:: example

        Repeats talea of 1/16, 2/16, 3/16, 4/16:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
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
                        c'8
                        ]
                    }
                }
            }

    ..  container:: example

        Using ``rmakers.talea()`` with the ``extra_counts`` keyword.

        >>> def make_lilypond_file(pairs, extra_counts):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [1, 2, 3, 4],
        ...         16,
        ...         extra_counts=extra_counts,
        ...     )
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.swap_trivial(voice)
        ...     return lilypond_file

        ..  container:: example

            **#1.** Set ``extra_counts=[0, 1]`` to add one extra count to every
            other tuplet:

            >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts=[0, 1])
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
                                \time 3/8
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            \tuplet 9/8
                            {
                                \time 4/8
                                c'4
                                c'16
                                [
                                c'8
                                c'8
                                ]
                                ~
                            }
                            {
                                \time 3/8
                                c'16
                                c'4
                                c'16
                            }
                            \tuplet 9/8
                            {
                                \time 4/8
                                c'8
                                [
                                c'8.
                                ]
                                c'4
                            }
                        }
                    }
                }

        ..  container:: example

            **#2.** Set ``extra_counts=[0, 2]`` to add two extra counts to
            every other tuplet:

            >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts=[0, 2])
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
                                \time 3/8
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            \tuplet 5/4
                            {
                                \time 4/8
                                c'4
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            {
                                \time 3/8
                                c'4
                                c'16
                                [
                                c'16
                                ]
                                ~
                            }
                            \tuplet 5/4
                            {
                                \time 4/8
                                c'16
                                [
                                c'8.
                                ]
                                c'4
                                c'16
                                [
                                c'16
                                ]
                            }
                        }
                    }
                }

        ..  container:: example

            **#3.** Set ``extra_counts=[0, -1]`` to remove one count from every
            other tuplet:

            >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts=[0, -1])
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
                                \time 3/8
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/8
                            {
                                \time 4/8
                                c'4
                                c'16
                                [
                                c'8
                                ]
                            }
                            {
                                \time 3/8
                                c'8.
                                [
                                c'8.
                                ]
                                ~
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/8
                            {
                                \time 4/8
                                c'16
                                [
                                c'16
                                c'8
                                c'8.
                                ]
                            }
                        }
                    }
                }

    ..  container:: example

        **Reading talea once only.** Set ``read_talea_once_only=True`` to raise
        an exception if input durations exceed that of a single reading of
        talea. The effect is to ensure that a talea is long enough to cover all
        durations without repeating. Useful when, for example, interpolating
        from short durations to long durations.

    ..  container:: example

        Using ``rmakers.talea()`` with the ``preamble`` keyword.

        ..  container:: example

            Preamble less than total duration:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.talea(
            ...         durations, [8, -4, 8], 32, preamble=[1, 1, 1, 1]
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
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
                            c'32
                            [
                            c'32
                            c'32
                            c'32
                            ]
                            c'4
                            \time 4/8
                            r8
                            c'4
                            c'8
                            ~
                            \time 3/8
                            c'8
                            r8
                            c'8
                            ~
                            \time 4/8
                            c'8
                            c'4
                            r8
                        }
                    }
                }

        .. container:: example

            Preamble more than total duration; ignores counts:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.talea(
            ...         durations, [8, -4, 8], 32, preamble=[32, 32, 32, 32]
            ...     )
            ...     container = abjad.Container(tuplets)
            ...     rmakers.beam(container)
            ...     rmakers.extract_trivial(container)
            ...     components = abjad.mutate.eject_contents(container)
            ...     lilypond_file = rmakers.example(components, time_signatures)
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
                            c'4.
                            ~
                            \time 4/8
                            c'2
                            ~
                            \time 3/8
                            c'8
                            c'4
                            ~
                            \time 4/8
                            c'2
                        }
                    }
                }

    ..  container:: example

        Using ``rmakers.talea()`` with the ``end_counts`` keyword.

        ..  container:: example

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.talea(
            ...         durations, [8, -4, 8], 32, end_counts=[1, 1, 1, 1]
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
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
                            c'4
                            r8
                            \time 4/8
                            c'4
                            c'4
                            \time 3/8
                            r8
                            c'4
                            \time 4/8
                            c'4
                            r8
                            c'32
                            [
                            c'32
                            c'32
                            c'32
                            ]
                        }
                    }
                }

    """
    assert _is_duration_list(durations), repr(durations)
    assert _is_integer_or_string_list(counts), repr(counts)
    assert isinstance(denominator, int), repr(denominator)
    assert isinstance(advance, int), repr(advance)
    if end_counts is None:
        end_counts = []
    if extra_counts is None:
        extra_counts = []
    assert _is_integer_list(extra_counts), repr(extra_counts)
    if preamble is None:
        preamble = []
    assert _is_integer_list(preamble), repr(preamble)
    if previous_state is None:
        previous_state = {}
    assert isinstance(previous_state, dict)
    assert isinstance(read_talea_once_only, bool), repr(read_talea_once_only)
    assert isinstance(spelling, _classes.Spelling), repr(spelling)
    if state is None:
        state = {}
    assert isinstance(state, dict), repr(state)
    if tag is None:
        tag = abjad.Tag()
    assert isinstance(tag, abjad.Tag), repr(tag)
    tag = tag.append(_function_name(inspect.currentframe()))
    talea = _classes.Talea(
        counts=counts,
        denominator=denominator,
        end_counts=end_counts,
        preamble=preamble,
    )
    talea = talea.advance(advance)
    tuplets = _make_talea_tuplets(
        durations,
        extra_counts,
        previous_state,
        read_talea_once_only,
        spelling,
        state,
        talea,
        tag,
    )
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        durations_consumed=len(durations),
        logical_ties_produced=logical_ties_produced,
        previous_durations_consumed=previous_state.get("durations_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    abjad.mutate.eject_contents(voice)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    state.clear()
    state.update(new_state)
    return tuplets


def tuplet(
    durations: list[abjad.Duration],
    proportions: list[tuple[int, ...]],
    *,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Reads ``proportions`` cyclically and makes one tuplet for each duration in
    ``durations``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, proportions):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, proportions)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        Makes tuplets with ``3:2`` ratios:

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> proportions = [(3, 2)]
        >>> lilypond_file = make_lilypond_file(pairs, proportions)
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
                            \time 1/2
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8.
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> proportions = [(1, -1), (3, 1)]
        >>> lilypond_file = make_lilypond_file(pairs, proportions)
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
                            \time 1/2
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'4.
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 8/5
                        {
                            \time 5/16
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 8/5
                        {
                            c'4.
                            c'8
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert _is_duration_list(durations), repr(durations)
    assert _is_integer_tuple_list(proportions), repr(proportions)
    tuplets = []
    proportions_cycle = abjad.CyclicTuple(proportions)
    for i, duration in enumerate(durations):
        proportion = proportions_cycle[i]
        tuplet = abjad.makers.make_tuplet(duration, proportion, tag=tag)
        tuplet.normalize_ratio()
        tuplets.append(tuplet)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    return tuplets
