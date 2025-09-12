"""
Makers.
"""

import dataclasses
import inspect
import math
import typing

import abjad

from . import classes as _classes


def _all_are_durations(durations: typing.Sequence[abjad.Duration]):
    return all(isinstance(_, abjad.Duration) for _ in durations)


def _all_are_proportions(proportions: typing.Sequence[tuple[int, ...]]):
    for proportion in proportions:
        if not isinstance(proportion, tuple):
            return False
        if not all(isinstance(_, int) for _ in proportion):
            return False
    return True


def _apply_ties_to_split_notes(
    tuplets,
    unscaled_end_counts,
    unscaled_preamble,
    unscaled_talea,
    talea,
):
    leaves = abjad.select.leaves(tuplets)
    written_durations = [leaf.written_duration() for leaf in leaves]
    written_durations = list(written_durations)
    total_duration = abjad.sequence.weight(written_durations)
    preamble_weights = []
    if unscaled_preamble:
        preamble_weights = []
        for numerator in unscaled_preamble:
            pair = (numerator, talea.denominator)
            duration = abjad.Duration(*pair)
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
        for numerator in unscaled_talea:
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
    if unscaled_end_counts:
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
    Changes ``durations`` to pairs sharing least common denominator.

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
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    denominators = [_.denominator for _ in durations]
    lcd = abjad.math.least_common_multiple(*denominators)
    fractions = [_.as_fraction() for _ in durations]
    pairs = [abjad.duration.pair_with_denominator(_, lcd) for _ in fractions]
    return pairs


def _fix_rounding_error(
    notes: typing.Sequence[abjad.Note],
    total_duration: abjad.Duration,
    interpolation: _classes.Interpolation,
) -> None:
    assert all(isinstance(_, abjad.Note) for _ in notes), repr(notes)
    assert isinstance(total_duration, abjad.Duration), repr(total_duration)
    assert isinstance(interpolation, _classes.Interpolation), repr(interpolation)
    old_duration = abjad.get.duration(notes)
    # duration = old_duration.as_value_duration()
    duration = old_duration
    if not duration == total_duration:
        nonlast_leaf_duration = abjad.get.duration(notes[:-1])
        needed_duration = total_duration - nonlast_leaf_duration
        fraction = needed_duration / interpolation.written_duration
        pair = (fraction.numerator, fraction.denominator)
        notes[-1].set_multiplier(pair)


def _function_name(frame):
    function_name = frame.f_code.co_name
    string = f"rmakers.{function_name}()"
    return abjad.Tag(string)


def _get_interpolations(interpolations, previous_state):
    specifiers_ = interpolations
    if specifiers_ is None:
        specifiers_ = abjad.CyclicTuple([_classes.Interpolation()])
    elif isinstance(specifiers_, _classes.Interpolation):
        specifiers_ = abjad.CyclicTuple([specifiers_])
    else:
        specifiers_ = abjad.CyclicTuple(specifiers_)
    string = "durations_consumed"
    durations_consumed = previous_state.get(string, 0)
    specifiers_ = abjad.sequence.rotate(specifiers_, n=-durations_consumed)
    specifiers_ = abjad.CyclicTuple(specifiers_)
    return specifiers_


def _interpolate_cosine(y1: float, y2: float, mu: float) -> float:
    assert isinstance(y1, float), repr(y1)
    assert isinstance(y2, float), repr(y2)
    assert isinstance(mu, float), repr(mu)
    mu2 = (1 - math.cos(mu * math.pi)) / 2
    return y1 * (1 - mu2) + y2 * mu2


def _interpolate_divide(
    total_duration: abjad.Duration,
    start_duration: abjad.Duration,
    stop_duration: abjad.Duration,
    exponent: str | float = "cosine",
) -> str | list[float]:
    """
    Divides ``total_duration`` into durations computed from interpolating between
    ``start_duration`` and ``stop_duration``.

    ..  container:: example

        >>> rmakers.functions._interpolate_divide(
        ...     total_duration=abjad.Duration(10, 1),
        ...     start_duration=abjad.Duration(1, 1),
        ...     stop_duration=abjad.Duration(1, 1),
        ...     exponent=1,
        ... )
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        >>> sum(_)
        10.0

        >>> rmakers.functions._interpolate_divide(
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
    assert isinstance(exponent, str | float), repr(exponent)
    zero = abjad.Duration(0)
    if total_duration <= zero:
        raise ValueError("Total duration must be positive.")
    if start_duration <= zero or stop_duration <= zero:
        raise Exception("Both 'start_duration' and 'stop_duration' must be positive.")
    if total_duration < (stop_duration + start_duration):
        return "too small"
    float_durations = []
    partial_sum = 0.0
    while partial_sum < float(total_duration):
        if exponent == "cosine":
            float_duration = _interpolate_cosine(
                float(start_duration),
                float(stop_duration),
                partial_sum / float(total_duration),
            )
        else:
            float_duration = _interpolate_exponential(
                start_duration,
                stop_duration,
                partial_sum / float(total_duration),
                exponent,
            )
        float_durations.append(float_duration)
        partial_sum += float_duration
    float_durations = [
        _ * float(total_duration) / sum(float_durations) for _ in float_durations
    ]
    return float_durations


def _interpolate_exponential(y1, y2, mu, exponent=1) -> float:
    """
    Interpolates between ``y1`` and ``y2`` at position ``mu``.

    ..  container:: example

        Exponents equal to 1 leave durations unscaled:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.functions._interpolate_exponential(100, 200, mu, exponent=1)
        ...
        100.0
        125.0
        150.0
        175.0
        200.0

        Exponents greater than 1 generate ritardandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.functions._interpolate_exponential(100, 200, mu, exponent=2)
        ...
        100.0
        106.25
        125.0
        156.25
        200.0

        Exponents less than 1 generate accelerandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.functions._interpolate_exponential(100, 200, mu, exponent=0.5)
        ...
        100.0
        150.0
        170.71067811865476
        186.60254037844388
        200.0

    """
    result = float(y1) * (1 - mu**exponent) + float(y2) * mu**exponent
    return result


def _make_accelerando(
    duration: abjad.Duration,
    interpolations: typing.Sequence[_classes.Interpolation],
    index: int,
    *,
    tag: abjad.Tag = abjad.Tag(),
) -> abjad.Tuplet:
    """
    Makes notes with LilyPond multipliers equal to ``duration``.

    Total number of notes not specified: total duration is specified instead.

    Selects interpolation specifier at ``index`` in ``interpolations``.

    Computes duration multipliers interpolated from interpolation specifier start to
    stop.

    Sets note written durations according to interpolation specifier.
    """
    assert isinstance(duration, abjad.Duration)
    assert all(isinstance(_, _classes.Interpolation) for _ in interpolations)
    assert isinstance(index, int)
    interpolation = interpolations[index]
    float_durations = _interpolate_divide(
        total_duration=duration,
        start_duration=interpolation.start_duration,
        stop_duration=interpolation.stop_duration,
    )
    if float_durations == "too small":
        pitches = abjad.makers.make_pitches([0])
        components = abjad.makers.make_notes(pitches, [duration], tag=tag)
        tuplet = abjad.Tuplet("1:1", components, tag=tag)
        return tuplet
    assert not isinstance(float_durations, str)
    durations = _round_durations(float_durations, 2**10)
    notes = []
    pitch = abjad.NamedPitch(0)
    for i, duration_ in enumerate(durations):
        written_duration = interpolation.written_duration
        fraction = duration_ / written_duration
        pair = (fraction.numerator, fraction.denominator)
        note = abjad.Note.from_duration_and_pitch(
            written_duration,
            pitch,
            multiplier=pair,
            tag=tag,
        )
        notes.append(note)
    assert all(isinstance(_, abjad.Note) for _ in notes), repr(notes)
    _fix_rounding_error(notes, duration, interpolation)
    tuplet = abjad.Tuplet("1:1", notes, tag=tag)
    return tuplet


def _make_components(
    durations: list[abjad.Duration],
    increase_monotonic: bool = False,
    forbidden_note_duration: abjad.Duration | None = None,
    forbidden_rest_duration: abjad.Duration | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf | abjad.Tuplet]:
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
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
    assert all(isinstance(_, abjad.Leaf | abjad.Tuplet) for _ in components)
    return components


def _make_incised_duration_lists(
    pairs,
    prefix_talea,
    prefix_counts,
    suffix_talea,
    suffix_counts,
    extra_counts,
    incise,
):
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    duration_lists, prefix_talea_index, suffix_talea_index = [], 0, 0
    for pair_index, pair in enumerate(pairs):
        prefix_length = prefix_counts[pair_index]
        suffix_length = suffix_counts[pair_index]
        start = prefix_talea_index
        stop = prefix_talea_index + prefix_length
        prefix = prefix_talea[start:stop]
        start = suffix_talea_index
        stop = suffix_talea_index + suffix_length
        suffix = suffix_talea[start:stop]
        prefix_talea_index += prefix_length
        suffix_talea_index += suffix_length
        prolation_addendum = extra_counts[pair_index]
        numerator = pair[0] + (prolation_addendum % pair[0])
        duration_list = _make_duration_list(numerator, prefix, suffix, incise)
        duration_lists.append(duration_list)
    for duration_list in duration_lists:
        assert all(isinstance(_, abjad.Duration) for _ in duration_list)
    return duration_lists


def _make_middle_durations(middle_duration, incise):
    assert isinstance(middle_duration, abjad.Duration), repr(middle_duration)
    assert middle_duration.denominator == 1, repr(middle_duration)
    assert isinstance(incise, _classes.Incise), repr(incise)
    durations = []
    if not (incise.fill_with_rests):
        if not incise.outer_tuplets_only:
            if abjad.Duration(0) < middle_duration:
                if incise.body_proportion is not None:
                    shards = abjad.math.divide_integer_by_proportion(
                        middle_duration.numerator, incise.body_proportion
                    )
                    assert all(isinstance(_, abjad.Fraction) for _ in shards), repr(
                        shards
                    )
                    durations_ = [abjad.Duration(*_.as_integer_ratio()) for _ in shards]
                    durations.extend(durations_)
                else:
                    durations.append(middle_duration)
        else:
            if abjad.Duration(0) < middle_duration:
                durations.append(middle_duration)
    else:
        if not incise.outer_tuplets_only:
            if abjad.Duration(0) < middle_duration:
                durations.append(-abs(middle_duration))
        else:
            if abjad.Duration(0) < middle_duration:
                durations.append(-abs(middle_duration))
    assert isinstance(durations, list)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    return durations


def _make_talea_numerator_lists(
    pairs: list[tuple[int, int]],
    preamble: abjad.CyclicTuple,
    talea: abjad.CyclicTuple,
    extra_counts: abjad.CyclicTuple,
    end_counts: abjad.CyclicTuple,
    read_talea_once_only: bool,
):
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    assert isinstance(preamble, abjad.CyclicTuple), repr(preamble)
    assert all(isinstance(_, int) for _ in preamble), repr(preamble)
    assert isinstance(talea, abjad.CyclicTuple), repr(talea)
    assert all(isinstance(_, int | str) for _ in talea), repr(talea)
    assert isinstance(extra_counts, abjad.CyclicTuple), repr(extra_counts)
    assert all(isinstance(_, int) for _ in extra_counts), repr(extra_counts)
    assert isinstance(end_counts, abjad.CyclicTuple), repr(end_counts)
    assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
    assert isinstance(read_talea_once_only, bool), repr(read_talea_once_only)
    for count in talea:
        assert isinstance(count, int) or count in "+-", repr(talea)
    if "+" in talea or "-" in talea:
        assert not preamble, repr(preamble)
    prolated_pairs = _make_prolated_pairs(pairs, extra_counts)
    pairs = []
    for item in prolated_pairs:
        if isinstance(item, tuple):
            pairs.append(item)
        else:
            pairs.append(item.pair)
    if not preamble and not talea:
        raise Exception("DO WE EVER GET HERE")
        return pairs, None
    prolated_numerators = [_[0] for _ in pairs]
    expanded_talea = None
    if "-" in talea or "+" in talea:
        total_weight = sum(prolated_numerators)
        talea_ = list(talea)
        if "-" in talea:
            index = talea_.index("-")
        else:
            index = talea_.index("+")
        talea_[index] = 0
        explicit_weight = sum([abs(_) for _ in talea_])
        implicit_weight = total_weight - explicit_weight
        if "-" in talea:
            implicit_weight *= -1
        talea_[index] = implicit_weight
        expanded_talea = tuple(talea_)
        talea = abjad.CyclicTuple(expanded_talea)
    numerator_lists = _split_talea_extended_to_weights(
        preamble, read_talea_once_only, talea, prolated_numerators
    )
    if end_counts:
        end_weight = abjad.sequence.weight(end_counts)
        numerator_list_weights = [abjad.sequence.weight(_) for _ in numerator_lists]
        counts = abjad.sequence.flatten(numerator_lists)
        counts_weight = abjad.sequence.weight(counts)
        assert end_weight <= counts_weight, repr(end_counts)
        left = counts_weight - end_weight
        right = end_weight
        counts = abjad.sequence.split(counts, [left, right])
        counts = counts[0] + list(end_counts)
        assert abjad.sequence.weight(counts) == counts_weight
        numerator_lists = abjad.sequence.partition_by_weights(
            counts, numerator_list_weights
        )
    for numerator_list in numerator_lists:
        assert all(isinstance(_, int) for _ in numerator_list), repr(numerator_list)
    return numerator_lists, expanded_talea


def _make_duration_list(numerator, prefix, suffix, incise, *, is_note_filled=True):
    numerator = abjad.Duration(numerator)
    prefix = [abjad.Duration(_) for _ in prefix]
    suffix = [abjad.Duration(_) for _ in suffix]
    prefix_weight = abjad.math.weight(prefix, start=abjad.Duration(0))
    suffix_weight = abjad.math.weight(suffix, start=abjad.Duration(0))
    middle_duration = numerator - prefix_weight - suffix_weight
    assert isinstance(middle_duration, abjad.Duration), repr(middle_duration)
    if numerator < prefix_weight:
        weights = [numerator]
        prefix = abjad.sequence.split(prefix, weights, cyclic=False, overhang=False)[0]
    middle_durations = _make_middle_durations(middle_duration, incise)
    suffix_space = numerator - prefix_weight
    if suffix_space <= abjad.Duration(0):
        suffix = []
    elif suffix_space < suffix_weight:
        weights = [suffix_space]
        suffix = abjad.sequence.split(suffix, weights, cyclic=False, overhang=False)[0]
    assert all(isinstance(_, abjad.Duration) for _ in prefix), repr(prefix)
    assert all(isinstance(_, abjad.Duration) for _ in suffix), repr(suffix)
    duration_list = prefix + middle_durations + suffix
    assert all(isinstance(_, abjad.Duration) for _ in duration_list), repr(
        duration_list
    )
    return duration_list


def _make_outer_tuplets_only_incised_duration_lists(
    pairs,
    prefix_talea,
    prefix_counts,
    suffix_talea,
    suffix_counts,
    extra_counts,
    incise,
):
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
    prefix_length, suffix_length = prefix_counts[0], suffix_counts[0]
    start = prefix_talea_index
    stop = prefix_talea_index + prefix_length
    prefix = prefix_talea[start:stop]
    start = suffix_talea_index
    stop = suffix_talea_index + suffix_length
    suffix = suffix_talea[start:stop]
    if len(pairs) == 1:
        prolation_addendum = extra_counts[0]
        numerator = getattr(pairs[0], "numerator", pairs[0][0])
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_duration_list(numerator, prefix, suffix, incise)
        numeric_map.append(numeric_map_part)
    else:
        prolation_addendum = extra_counts[0]
        if isinstance(pairs[0], tuple):
            numerator = pairs[0][0]
        else:
            numerator = pairs[0].numerator
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_duration_list(numerator, prefix, (), incise)
        numeric_map.append(numeric_map_part)
        for i, pair in enumerate(pairs[1:-1]):
            index = i + 1
            prolation_addendum = extra_counts[index]
            numerator = pair[0]
            numerator += prolation_addendum % numerator
            numeric_map_part = _make_duration_list(numerator, (), (), incise)
            numeric_map.append(numeric_map_part)
        try:
            index = i + 2
            prolation_addendum = extra_counts[index]
        except UnboundLocalError:
            index = 1 + 2
            prolation_addendum = extra_counts[index]
        if isinstance(pairs[-1], tuple):
            numerator = pairs[-1][0]
        else:
            numerator = pairs[-1].numerator
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_duration_list(numerator, (), suffix, incise)
        numeric_map.append(numeric_map_part)
    return numeric_map


def _make_prolated_pairs(pairs, extra_counts):
    prolated_pairs = []
    for i, pair in enumerate(pairs):
        if not extra_counts:
            prolated_pairs.append(pair)
            continue
        prolation_addendum = extra_counts[i]
        numerator = pair[0]
        if 0 <= prolation_addendum:
            prolation_addendum %= numerator
        else:
            # NOTE: do not remove the following (nonfunctional) if-else;
            #       preserved for backwards compatability.
            use_old_extra_counts_logic = False
            if use_old_extra_counts_logic:
                prolation_addendum %= numerator
            else:
                prolation_addendum %= -numerator
        numerator, denominator = pair
        prolated_pair = (numerator + prolation_addendum, denominator)
        prolated_pairs.append(prolated_pair)
    assert all(isinstance(_, tuple) for _ in prolated_pairs)
    return prolated_pairs


def _make_state_dictionary(
    *,
    durations_consumed,
    logical_ties_produced,
    previous_durations_consumed,
    previous_incomplete_last_note,
    previous_logical_ties_produced,
    state,
):
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
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert isinstance(extra_counts, list), repr(extra_counts)
    assert all(isinstance(_, int) for _ in extra_counts), repr(extra_counts)
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
    scaled_end_counts_cycle = abjad.CyclicTuple(
        [multiplier * _ for _ in advanced_talea.end_counts]
    )
    scaled_extra_counts_cycle = abjad.CyclicTuple(
        [multiplier * _ for _ in rotated_extra_counts]
    )
    scaled_preamble_cycle = abjad.CyclicTuple(
        [multiplier * _ for _ in advanced_talea.preamble]
    )
    scaled_talea_counts_cycle = abjad.CyclicTuple(
        [multiplier * _ for _ in advanced_talea.counts]
    )
    numerator_lists, expanded_talea = _make_talea_numerator_lists(
        scaled_pairs,
        scaled_preamble_cycle,
        scaled_talea_counts_cycle,
        scaled_extra_counts_cycle,
        scaled_end_counts_cycle,
        read_talea_once_only,
    )
    if expanded_talea is not None:
        unscaled_talea = expanded_talea
    else:
        unscaled_talea = advanced_talea.counts
    talea_weight_consumed = sum(abjad.sequence.weight(_) for _ in numerator_lists)
    duration_lists = [[abjad.Duration(_, lcd) for _ in n] for n in numerator_lists]
    leaf_lists = []
    for duration_list in duration_lists:
        leaf_list = _make_components(
            duration_list,
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        leaf_lists.append(leaf_list)
    if not scaled_extra_counts_cycle:
        tuplets = [abjad.Tuplet("1:1", _) for _ in leaf_lists]
    else:
        durations_ = abjad.duration.durations(scaled_pairs)
        tuplets = _package_tuplets(durations_, leaf_lists, tag=tag)
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
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
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


@dataclasses.dataclass(frozen=True)
class _PreparedIncisedCounts:

    prefix_talea: abjad.CyclicTuple
    suffix_talea: abjad.CyclicTuple
    extra_counts: abjad.CyclicTuple

    def __post_init__(self):
        assert all(isinstance(_, int) for _ in self.prefix_talea)
        assert all(isinstance(_, int) for _ in self.suffix_talea)
        assert all(isinstance(_, int) for _ in self.extra_counts)

    def scale(self, multiplier, scaled_pairs, lcd):
        scaled_counts = _PreparedIncisedCounts(
            prefix_talea=abjad.CyclicTuple([multiplier * _ for _ in self.prefix_talea]),
            suffix_talea=abjad.CyclicTuple([multiplier * _ for _ in self.suffix_talea]),
            extra_counts=abjad.CyclicTuple([multiplier * _ for _ in self.extra_counts]),
        )
        return _ScaledIncisedCounts(
            pairs=scaled_pairs,
            lcd=lcd,
            counts=scaled_counts,
        )


@dataclasses.dataclass(frozen=True)
class _ScaledIncisedCounts:
    pairs: list[tuple[int, int]]
    lcd: int
    counts: _PreparedIncisedCounts


@dataclasses.dataclass(frozen=True)
class _PreparedIncisedInput:

    prefix_talea: abjad.CyclicTuple
    prefix_counts: abjad.CyclicTuple
    suffix_talea: abjad.CyclicTuple
    suffix_counts: abjad.CyclicTuple
    extra_counts: abjad.CyclicTuple

    def __post_init__(self):
        assert all(isinstance(_, int) for _ in self.prefix_talea)
        assert all(isinstance(_, int) for _ in self.prefix_counts)
        assert all(isinstance(_, int) for _ in self.suffix_talea)
        assert all(isinstance(_, int) for _ in self.suffix_counts)


def _prepare_incised_input(incise, extra_counts):
    cyclic_prefix_talea = abjad.CyclicTuple(incise.prefix_talea)
    cyclic_prefix_counts = abjad.CyclicTuple(incise.prefix_counts or (0,))
    cyclic_suffix_talea = abjad.CyclicTuple(incise.suffix_talea)
    cyclic_suffix_counts = abjad.CyclicTuple(incise.suffix_counts or (0,))
    cyclic_extra_counts = abjad.CyclicTuple(extra_counts or (0,))
    return _PreparedIncisedInput(
        prefix_talea=cyclic_prefix_talea,
        prefix_counts=cyclic_prefix_counts,
        suffix_talea=cyclic_suffix_talea,
        suffix_counts=cyclic_suffix_counts,
        extra_counts=cyclic_extra_counts,
    )


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


def _scale_rhythm_maker_input(
    durations: list[abjad.Duration],
    talea_denominator: int,
    counts: _PreparedIncisedCounts,
) -> _ScaledIncisedCounts:
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert isinstance(talea_denominator, int), repr(talea_denominator)
    assert isinstance(counts, _PreparedIncisedCounts), repr(counts)
    durations_ = durations[:]
    dummy_duration = abjad.Duration(1, talea_denominator)
    durations_.append(dummy_duration)
    scaled_pairs = _durations_to_lcm_pairs(durations_)
    dummy_pair = scaled_pairs.pop()
    lcd = dummy_pair[1]
    multiplier = lcd / talea_denominator
    assert abjad.math.is_integer_equivalent(multiplier)
    multiplier = int(multiplier)
    assert isinstance(counts, _PreparedIncisedCounts), repr(counts)
    scaled_incised_input = counts.scale(multiplier, scaled_pairs, lcd)
    return scaled_incised_input


def _split_talea_extended_to_weights(preamble, read_talea_once_only, talea, weights):
    assert all(isinstance(_, int) for _ in preamble), repr(preamble)
    assert all(isinstance(_, int) for _ in talea), repr(talea)
    assert all(isinstance(_, int) for _ in weights), repr(weights)
    assert abjad.math.all_are_positive_integers(weights)
    preamble_weight = abjad.math.weight(preamble, start=0)
    talea_weight = abjad.math.weight(talea, start=0)
    weight = abjad.math.weight(weights, start=0)
    if read_talea_once_only and preamble_weight + talea_weight < weight:
        message = f"{preamble!s} + {talea!s} is too short"
        message += f" to read {weights} once."
        raise Exception(message)
    if weight <= preamble_weight:
        talea = list(preamble)
        talea = abjad.sequence.truncate(talea, weight=weight)
    else:
        weight -= preamble_weight
        talea = abjad.sequence.repeat_to_weight(talea, weight)
        talea = list(preamble) + list(talea)
    talea = abjad.sequence.split(talea, weights, cyclic=True)
    return talea


def accelerando(
    durations: typing.Sequence[abjad.Duration],
    *interpolations: typing.Sequence[abjad.Duration],
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
        ...     tuplets = rmakers.accelerando(durations, *interpolations)
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
        >>> interpolations = [[(1, 8), (1, 20), (1, 16)]]
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
        >>> interpolations = [[(1, 20), (1, 8), (1, 16)]]
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
        >>> interpolations = [[(1, 8), (1, 20), (1, 16)], [(1, 20), (1, 8), (1, 16)]]
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
        >>> interpolations = [[(1, 8), (1, 20), (1, 16)]]
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
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    # TODO: eventually assert that every interpolation is a list of duration objects
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_durations = abjad.duration.durations(list(interpolation))
        interpolation_ = _classes.Interpolation(*interpolation_durations)
        interpolations_.append(interpolation_)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    interpolations_ = _get_interpolations(interpolations_, previous_state)
    tuplets = []
    for i, duration in enumerate(durations):
        tuplet = _make_accelerando(duration, interpolations_, i, tag=tag)
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
    durations: typing.Sequence[abjad.Duration],
    denominators: typing.Sequence[int],
    *,
    extra_counts: typing.Sequence[int] | None = None,
    previous_state: dict | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one even-division tuplet for each duration in ``durations``.

    Basic example:

    ..  container:: example

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
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(denominators, list), repr(denominators)
    assert all(isinstance(_, int) for _ in denominators), repr(denominators)
    if extra_counts is None:
        extra_counts = [0]
    assert isinstance(extra_counts, list), repr(extra_counts)
    assert all(isinstance(_, int) for _ in extra_counts), repr(extra_counts)
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
        assert abjad.math.is_positive_integer_power_of_two(note_duration.denominator)
        unprolated_note_count = None
        pitches = abjad.makers.make_pitches([0])
        if tuplet_duration < 2 * note_duration:
            note_durations = [tuplet_duration]
        else:
            unprolated_note_count = tuplet_duration / note_duration
            unprolated_note_count = int(unprolated_note_count)
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
    durations: typing.Sequence[abjad.Duration],
    *,
    body_proportion: tuple[int, ...] = (1,),
    extra_counts: typing.Sequence[int] | None = None,
    fill_with_rests: bool = False,
    outer_tuplets_only: bool = False,
    prefix_counts: typing.Sequence[int] | None = None,
    prefix_talea: typing.Sequence[int] | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    suffix_counts: typing.Sequence[int] | None = None,
    suffix_talea: typing.Sequence[int] | None = None,
    tag: abjad.Tag | None = None,
    talea_denominator: int | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one incised tuplet for each duration in  ``durations``.

    Set ``prefix_talea=[-1]`` with ``prefix_counts=[1]`` to incise a rest at
    the start of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         talea_denominator=16,
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
        ...         prefix_talea=[-1],
        ...         prefix_counts=[2],
        ...         talea_denominator=16,
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
        ...         prefix_talea=[1],
        ...         prefix_counts=[1],
        ...         talea_denominator=16,
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
        ...         prefix_talea=[1],
        ...         prefix_counts=[2],
        ...         talea_denominator=16,
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
        ...         extra_counts=[1],
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
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
        ...         body_proportion=(1, 1),
        ...         talea_denominator=16,
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

    Set ``body_proportion=(1, 1, 1)`` to divide the middle part of each tuplet ``1:1:1``:

    ..  container:: example

        TODO. Allow nested tuplets to clean up notation:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         body_proportion=(1, 1, 1),
        ...         talea_denominator=16,
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
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    if prefix_talea is None:
        prefix_talea = []
    assert isinstance(prefix_talea, list), repr(prefix_talea)
    if prefix_counts is None:
        prefix_counts = []
    assert isinstance(prefix_counts, list), repr(prefix_counts)
    if suffix_talea is None:
        suffix_talea = []
    assert isinstance(suffix_talea, list), repr(suffix_talea)
    if suffix_counts is None:
        suffix_counts = []
    assert isinstance(suffix_counts, list), repr(suffix_counts)
    incise = _classes.Incise(
        body_proportion=body_proportion,
        fill_with_rests=fill_with_rests,
        outer_tuplets_only=outer_tuplets_only,
        prefix_talea=prefix_talea,
        prefix_counts=prefix_counts,
        suffix_talea=suffix_talea,
        suffix_counts=suffix_counts,
        talea_denominator=talea_denominator,
    )
    prepared_incise_input = _prepare_incised_input(incise, extra_counts)
    prepared_incise_counts = _PreparedIncisedCounts(
        prefix_talea=prepared_incise_input.prefix_talea,
        suffix_talea=prepared_incise_input.suffix_talea,
        extra_counts=prepared_incise_input.extra_counts,
    )
    talea_denominator = incise.talea_denominator
    assert isinstance(talea_denominator, int), repr(talea_denominator)
    scaled_incised_counts = _scale_rhythm_maker_input(
        durations,
        talea_denominator,
        prepared_incise_counts,
    )
    assert isinstance(scaled_incised_counts, _ScaledIncisedCounts)
    if incise.outer_tuplets_only:
        duration_lists = _make_outer_tuplets_only_incised_duration_lists(
            scaled_incised_counts.pairs,
            scaled_incised_counts.counts.prefix_talea,
            prepared_incise_input.prefix_counts,
            scaled_incised_counts.counts.suffix_talea,
            prepared_incise_input.suffix_counts,
            scaled_incised_counts.counts.extra_counts,
            incise,
        )
    else:
        duration_lists = _make_incised_duration_lists(
            scaled_incised_counts.pairs,
            scaled_incised_counts.counts.prefix_talea,
            prepared_incise_input.prefix_counts,
            scaled_incised_counts.counts.suffix_talea,
            prepared_incise_input.suffix_counts,
            scaled_incised_counts.counts.extra_counts,
            incise,
        )
    component_lists = []
    for duration_list in duration_lists:
        duration_list = [_ for _ in duration_list if _ != abjad.Duration(0)]
        duration_list_ = []
        for duration in duration_list:
            fraction = duration.as_fraction()
            fraction = abjad.Fraction(fraction, scaled_incised_counts.lcd)
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
    durations = abjad.duration.durations(scaled_incised_counts.pairs)
    tuplets = _package_tuplets(durations, component_lists, tag=tag)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
    return tuplets


def multiplied_duration(
    durations: typing.Sequence[abjad.Duration],
    prototype: type = abjad.Note,
    *,
    duration: abjad.Duration = abjad.Duration(1, 1),
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf]:
    r"""
    Makes one leaf with multiplier for each duration in ``durations``.

    ..  container:: example

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> components = rmakers.multiplied_duration(durations)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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

    ..  container:: example

        Makes multiplied-duration whole notes when ``duration`` is unset:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> components = rmakers.multiplied_duration(durations)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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

        Makes multiplied-duration half notes when ``duration=abjad.Duration(1, 2)``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> duration = abjad.Duration(1, 2)
        >>> components = rmakers.multiplied_duration(durations, duration=duration)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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

        Makes multiplied-duration quarter notes when ``duration=abjad.Duration(1, 4)``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> duration = abjad.Duration(1, 4)
        >>> components = rmakers.multiplied_duration(durations, duration=duration)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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

    ..  container:: example

        Makes multiplied-duration notes when ``prototype`` is unset:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> components = rmakers.multiplied_duration(durations)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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

    ..  container:: example

        Makes multiplied-duration rests when ``prototype=abjad.Rest``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> components = rmakers.multiplied_duration(durations, abjad.Rest)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                        r1 * 1/4
                        \time 3/16
                        r1 * 3/16
                        \time 5/8
                        r1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        r1 * 1/3
                    }
                }
            }

    ..  container:: example

        Makes multiplied-duration multimeasures rests when
        ``prototype=abjad.MultimeasureRest``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> components = rmakers.multiplied_duration(durations, abjad.MultimeasureRest)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                        R1 * 1/4
                        \time 3/16
                        R1 * 3/16
                        \time 5/8
                        R1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        R1 * 1/3
                    }
                }
            }

    ..  container:: example

        Makes multiplied-duration skips when ``prototype=abjad.Skip``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = abjad.duration.durations(time_signatures)
        >>> components = rmakers.multiplied_duration(durations, abjad.Skip)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert isinstance(duration, abjad.Duration), repr(duration)
    leaf: abjad.Leaf
    leaves = []
    pitch = abjad.NamedPitch("c'")
    for duration_ in durations:
        pair = duration_.numerator, duration_.denominator
        fraction = abjad.Fraction(*pair) / duration.as_fraction()
        denominator = abjad.math.least_common_multiple(pair[1], fraction.denominator)
        pair = abjad.duration.pair_with_denominator(fraction, denominator)
        if prototype is abjad.Note:
            leaf = abjad.Note.from_duration_and_pitch(
                duration,
                pitch,
                multiplier=pair,
                tag=tag,
            )
        elif prototype is abjad.Rest:
            leaf = abjad.Rest.from_duration(duration, multiplier=pair, tag=tag)
        elif prototype is abjad.MultimeasureRest:
            leaf = abjad.MultimeasureRest.from_duration(
                duration,
                multiplier=pair,
                tag=tag,
            )
        else:
            assert prototype is abjad.Skip
            leaf = abjad.Skip.from_duration(duration, multiplier=pair, tag=tag)
        leaves.append(leaf)
    return leaves


def note(
    durations: typing.Sequence[abjad.Duration],
    *,
    spelling: _classes.Spelling = _classes.Spelling(),
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf | abjad.Tuplet]:
    r"""
    Makes one note for every duration in ``durations``.

    Silences every other logical tie:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                        r2
                        \time 3/8
                        c'4.
                        \time 4/8
                        r2
                        \time 3/8
                        c'4.
                    }
                }
            }

    ..  container:: example

        Forces rest at every logical tie:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (5, 8)]
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
                        r2
                        \time 3/8
                        r4.
                        \time 4/8
                        r2
                        \time 5/8
                        r2
                        r8
                    }
                }
            }

    ..  container:: example

        Force-rests every other note, except for the first and last:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)[1:-1]
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
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
                        r2
                        \time 3/8
                        c'4.
                        \time 2/8
                        c'4
                    }
                }
            }

    ..  container:: example

        Beams the notes in each duration:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     logical_ties = abjad.select.logical_ties(voice, pitched=True)
        ...     rmakers.beam(logical_ties)
        ...     return lilypond_file

        >>> pairs = [(5, 32), (5, 32)]
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
                        \time 5/32
                        c'8
                        [
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        ]
                    }
                }
            }

    ..  container:: example

        Beams notes grouped by ``durations``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     logical_ties = abjad.select.logical_ties(voice)
        ...     rmakers.beam_groups(logical_ties)
        ...     return lilypond_file

        >>> pairs = [(5, 32), (5, 32)]
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
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        \time 5/32
                        c'8
                        [
                        ~
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
                }
            }

    ..  container:: example

        Makes no beams:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 32), (5, 32)]
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
                        \time 5/32
                        c'8
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                    }
                }
            }

    ..  container:: example

        Does not tie across ``durations``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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

    ..  container:: example

        Ties across ``durations``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in logical_ties]
        ...     rmakers.tie(leaves)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                        ~
                        \time 3/8
                        c'4.
                        ~
                        \time 4/8
                        c'2
                        ~
                        \time 3/8
                        c'4.
                    }
                }
            }

    ..  container:: example

        Ties across every other logical tie:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)[:-1]
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in logical_ties]
        ...     rmakers.tie(leaves)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                        ~
                        \time 3/8
                        c'4.
                        \time 4/8
                        c'2
                        ~
                        \time 3/8
                        c'4.
                    }
                }
            }

    ..  container:: example

        Strips all ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     rmakers.untie(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(7, 16), (1, 4), (5, 16)]
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
                        \time 1/4
                        c'4
                        \time 5/16
                        c'4
                        c'16
                    }
                }
            }

    ..  container:: example

        Spells tuplets as diminutions:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     abjad.makers.tweak_tuplet_bracket_edge_height(nested_music)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 14), (3, 7)]
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
                        \tuplet 14/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 5/14
                            c'2
                            ~
                            c'8
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 7/4
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 3/7
                            c'2.
                        }
                    }
                }
            }

    ..  container:: example

        Spells tuplets as augmentations:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     rmakers.force_augmentation(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     abjad.makers.tweak_tuplet_bracket_edge_height(components)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(components)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 14), (3, 7)]
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
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 5/14
                            c'4
                            ~
                            c'16
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 3/7
                            c'4.
                        }
                    }
                }
            }

    ..  container:: example

        Forces rest in logical tie 0:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_tie = abjad.select.logical_tie(container, 0)
        ...     rmakers.force_rest(logical_tie)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        r2
                        r8
                        \time 2/8
                        c'4
                        c'4
                        \time 5/8
                        c'2
                        ~
                        c'8
                    }
                }
            }

    ..  container:: example

        Forces rests in first two logical ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_tie = abjad.select.logical_ties(container)[:2]
        ...     rmakers.force_rest(logical_tie)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        r2
                        r8
                        \time 2/8
                        r4
                        c'4
                        \time 5/8
                        c'2
                        ~
                        c'8
                    }
                }
            }

    ..  container:: example

        Forces rests in first and last logical ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        r2
                        r8
                        \time 2/8
                        c'4
                        c'4
                        \time 5/8
                        r2
                        r8
                    }
                }
            }

    ..  container:: example

        Rewrites meter:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     voice = rmakers.wrap_in_time_signature_staff(components, time_signatures)
        ...     rmakers.rewrite_meter(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 4), (6, 16), (9, 16)]
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
                        c'2.
                        \time 6/16
                        c'4.
                        \time 9/16
                        c'4.
                        ~
                        c'8.
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    lists = []
    for duration in durations:
        list_ = abjad.makers.make_leaves(
            [[abjad.NamedPitch("c'")]],
            [duration],
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        lists.append(list(list_))
    components = abjad.sequence.flatten(lists)
    assert all(isinstance(_, abjad.Leaf | abjad.Tuplet) for _ in components)
    return components


def talea(
    durations: typing.Sequence[abjad.Duration],
    counts: typing.Sequence[int | str],
    denominator: int,
    *,
    advance: int = 0,
    end_counts: typing.Sequence[int] | None = None,
    extra_counts: typing.Sequence[int] | None = None,
    preamble: typing.Sequence[int] | None = None,
    previous_state: dict | None = None,
    read_talea_once_only: bool = False,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Reads ``counts`` cyclically and makes one tuplet for each duration in
    ``durations``.

    Repeats talea of 1/16, 2/16, 3/16, 4/16:

    ..  container:: example

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

        ..  container:: example

            REGRESSION. End counts leave 5-durated tie in tact:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = abjad.duration.durations(time_signatures)
            ...     tuplets = rmakers.talea(durations, [6], 16, end_counts=[1])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 8), (3, 8)]
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
                            c'4
                            ~
                            c'16
                            [
                            c'16
                            ]
                        }
                    }
                }

    """
    assert isinstance(durations, list), repr(durations)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert isinstance(counts, list), repr(counts)
    assert all(isinstance(_, int | str) for _ in counts), repr(counts)
    assert isinstance(denominator, int), repr(denominator)
    assert isinstance(advance, int), repr(advance)
    if end_counts is None:
        end_counts = []
    assert isinstance(end_counts, list), repr(end_counts)
    assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
    if extra_counts is None:
        extra_counts = []
    assert isinstance(extra_counts, list), repr(extra_counts)
    assert all(isinstance(_, int) for _ in extra_counts), repr(extra_counts)
    if preamble is None:
        preamble = []
    assert isinstance(preamble, list), repr(preamble)
    assert all(isinstance(_, int) for _ in preamble), repr(preamble)
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
    durations: typing.Sequence[abjad.Duration],
    proportions: typing.Sequence[tuple[int, ...]],
    *,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one tuplet for each duration in ``durations``.

    Makes tuplets with ``3:2`` ratios:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(3, 2)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, -1), (3, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

    ..  container:: example

        Beams each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1, 1, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (3, 8), (6, 8), (4, 8)]
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
                            \time 5/8
                            c'4
                            c'4
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 6/8
                            c'4
                            c'4
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
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

        Beams each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1, 1, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (3, 8), (6, 8), (4, 8)]
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
                            \time 5/8
                            c'4
                            c'4
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 6/8
                            c'4
                            c'4
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
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

        Beams tuplets together:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1, 2, 1, 1), (3, 1, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     rmakers.beam_groups(tuplets)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (3, 8), (6, 8), (4, 8)]
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
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            \time 5/8
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                            c'4
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            \time 6/8
                            c'8
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                            c'4
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                        \tuplet 5/4
                        {
                            \time 4/8
                            c'4.
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties nothing:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, -2, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16)]
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
                            \time 1/2
                            c'4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'8
                            r4
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties across all tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, -2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16)]
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
                            \time 1/2
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'8
                            r4
                            c'8
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties across every other tuplet:

        >>> def make_lilypond_file(durations):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, -2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
                            \time 1/2
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'8
                            r4
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8
                            [
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 8/5
                        {
                            c'8
                            r4
                            c'8
                        }
                    }
                }
            }

    ..  container:: example

        Makes diminished tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 1)])
        ...     container = abjad.Container(tuplets)
        ...     rmakers.force_diminution(container)
        ...     rmakers.beam(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (4, 8)]
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
                            c'4
                            c'8
                        }
                        \tuplet 3/2
                        {
                            c'4
                            c'8
                        }
                        \tuplet 3/2
                        {
                            \time 4/8
                            c'2
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Makes augmented tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.force_augmentation(voice)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (4, 8)]
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
                        \tuplet 3/4
                        {
                            \time 2/8
                            c'8
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'8
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            \time 4/8
                            c'4
                            c'8
                        }
                    }
                }
            }

    ..  container:: example

        Makes diminished tuplets and does not rewrite dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.force_diminution(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 8/7
                        {
                            \time 7/16
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Makes diminished tuplets and rewrites dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.force_diminution(voice)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 8/7
                        {
                            \time 7/16
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Makes augmented tuplets and does not rewrite dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.force_augmentation(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            \time 3/8
                            c'8
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/7
                        {
                            \time 7/16
                            c'8
                            c'8
                        }
                    }
                }
            }

    ..  container:: example

        Makes augmented tuplets and rewrites dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.force_augmentation(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            \time 3/8
                            c'8
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/7
                        {
                            \time 7/16
                            c'8
                            c'8
                        }
                    }
                }
            }

    ..  container:: example

        Leaves trivializable tuplets as-is when ``trivialize`` is false:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(3, -2), (1,), (-2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Rewrites trivializable tuplets when ``trivialize`` is true. Measures 2 and 4
        contain trivial tuplets with 1:1 ratios. To remove these trivial tuplets, set
        ``extract_trivial`` as shown in the next example:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(3, -2), (1,), (-2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.trivialize(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'8.
                            c'8.
                        }
                    }
                }
            }

        REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when both are
        true. Measures 2 and 4 are first rewritten as trivial but then supplied again
        with nontrivial prolation when removing dots. The result is that measures 2 and 4
        carry nontrivial prolation with no dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(3, -2), (1,), (-2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.trivialize(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'8
                            c'8
                        }
                    }
                }
            }

    ..  container:: example

        Leaves trivial tuplets as-is when ``extract_trivial`` is false:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Extracts trivial tuplets when ``extract_trivial`` is true. Measures 2 and 4 in
        the example below now contain only a flat list of notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            c'4.
                            ~
                        }
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                        ~
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            c'4.
                            ~
                        }
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            }

        .. note:: Flattening trivial tuplets makes it possible
            subsequently to rewrite the meter of the untupletted notes.

    ..  container:: example

        REGRESSION: Very long ties are preserved when ``extract_trivial`` is true:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.tie(notes)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            ~
                            c'4.
                            ~
                        }
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ]
                        ~
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            ~
                            c'4.
                            ~
                        }
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ]
                    }
                }
            }

    ..  container:: example

        Force-rests every other tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(4, 1)])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.extract_trivial(container)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(container)
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
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'2
                            c'8
                        }
                        \time 4/8
                        r2
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'2
                            c'8
                        }
                        \time 4/8
                        r2
                    }
                }
            }


    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are relatively
        prime when ``denominator`` is set to none. This means that ratios like
        ``6:4`` and ``10:8`` do not arise:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
                        \tuplet 5/4
                        {
                            \time 4/16
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 6/16
                            c'8
                            c'2
                        }
                        \tuplet 5/4
                        {
                            \time 8/16
                            c'8
                            c'2
                        }
                    }
                }
            }

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tag = abjad.Tag("TUPLET_RHYTHM_MAKER")
        ...     tuplets = rmakers.tuplet(durations, [(3, 2)], tag=tag)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice, tag=tag)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
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
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 5/4
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                            \time 1/2
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tweak text #tuplet-number::calc-fraction-text
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 5/3
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                            \time 3/8
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tweak text #tuplet-number::calc-fraction-text
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 1/1
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                            \time 5/16
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            [
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            ]
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tweak text #tuplet-number::calc-fraction-text
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 1/1
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            [
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            ]
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                    }
                }
            }

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [_.duration() for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(3, 2)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [_.duration() for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, -1), (3, 1)])
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

    ..  container:: example

        Makes length-1 tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [_.duration() for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1,)])
        ...     abjad.makers.tweak_tuplet_bracket_edge_height(tuplets)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(tuplets)
        ...     container = abjad.Container(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(1, 5), (1, 4), (1, 6), (7, 9)]
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
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \tweak edge-height #'(0.7 . 0)
                            \tuplet 5/4
                            {
                                #(ly:expect-warning "strange time signature found")
                                \time 1/5
                                c'4
                            }
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 1/4
                            c'4
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \tweak edge-height #'(0.7 . 0)
                            \tuplet 6/4
                            {
                                #(ly:expect-warning "strange time signature found")
                                \time 1/6
                                c'4
                            }
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \tweak edge-height #'(0.7 . 0)
                            \tuplet 9/8
                            {
                                #(ly:expect-warning "strange time signature found")
                                \time 7/9
                                c'2..
                            }
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert _all_are_durations(durations), repr(durations)
    assert _all_are_proportions(proportions), repr(proportions)
    tuplets = []
    proportions_cycle = abjad.CyclicTuple(proportions)
    for i, duration in enumerate(durations):
        proportion = proportions_cycle[i]
        tuplet = abjad.makers.make_tuplet(duration, proportion, tag=tag)
        tuplet.normalize_ratio()
        tuplets.append(tuplet)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    return tuplets
