"""
Regression.
"""


def test():
    r"""
    Regression.

    ..  container:: example

        REGRESSION: Very long ties are preserved when ``extract_trivial`` is
        true:

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

    ..  container:: example

        REGRESSION. Works when talea advances by period of talea:

        >>> talea = rmakers.Talea([1, 2, 3, 4], 16)
        >>> talea.counts
        [1, 2, 3, 4]

        >>> talea.advance(10).counts
        [1, 2, 3, 4]

        >>> talea.advance(20).counts
        [1, 2, 3, 4]

    ..  container:: example

        REGRESSION #907a. Rewrites trivializable tuplets even when tuplets
        contain multiple ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.trivialize(voice)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets[:-1]]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
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
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                            ~
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

        REGRESSION #907b. Rewrites trivializable tuplets even when tuplets
        contain very long ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = abjad.duration.durations(time_signatures)
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.trivialize(voice)
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(voice)
        ...     rmakers.tweak_tuplet_number_text_calc_fraction_text(voice)
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
                            ~
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            ~
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            ~
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            ~
                            c'4
                        }
                    }
                }
            }


    """
    pass
