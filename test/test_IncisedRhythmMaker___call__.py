import abjad
from abjadext import rmakers


def test_IncisedRhythmMaker___call___01():

    incise_specifier = rmakers.Incise(
        prefix_talea=[-8],
        prefix_counts=[0, 1],
        suffix_talea=[-1],
        suffix_counts=[1],
        talea_denominator=32,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'16.
                    r32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    c'4
                    ~
                    c'16.
                    r32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'16.
                    r32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    c'4
                    ~
                    c'16.
                    r32
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___02():

    incise_specifier = rmakers.Incise(
        prefix_talea=[-8],
        prefix_counts=[1, 2, 3, 4],
        suffix_talea=[-1],
        suffix_counts=[1],
        talea_denominator=32,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    c'4
                    ~
                    c'16.
                    r32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    r4
                    c'16.
                    r32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    r4
                    r8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    r4
                    r8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___03():

    incise_specifier = rmakers.Incise(
        prefix_talea=[-1],
        prefix_counts=[1],
        suffix_talea=[-8],
        suffix_counts=[1, 2, 3],
        talea_denominator=32,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r32
                    c'4
                    ~
                    c'16.
                    r4
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r32
                    c'16.
                    r4
                    r4
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r32
                    r4
                    r4
                    r16.
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___04():

    incise_specifier = rmakers.Incise()

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___05():

    incise_specifier = rmakers.Incise(
        prefix_talea=[-1],
        prefix_counts=[1],
        suffix_talea=[-1],
        suffix_counts=[1],
        talea_denominator=8,
    )

    maker = rmakers.IncisedRhythmMaker(
        incise_specifier=incise_specifier, extra_counts_per_division=[1, 0, 3]
    )

    divisions = [(4, 8), (4, 8), (4, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
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
                \times 4/5 {
                    r8
                    c'4.
                    r8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r8
                    c'4
                    r8
                }
                \times 4/7 {
                    r8
                    c'2
                    ~
                    c'8
                    r8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___06():

    incise_specifier = rmakers.Incise(
        prefix_talea=[8],
        prefix_counts=[0, 1],
        suffix_talea=[1],
        suffix_counts=[1],
        talea_denominator=32,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'16.
                    c'32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    ~
                    c'16.
                    c'32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'16.
                    c'32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    ~
                    c'16.
                    c'32
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___07():

    incise_specifier = rmakers.Incise(
        prefix_talea=[8],
        prefix_counts=[1, 2, 3, 4],
        suffix_talea=[1],
        suffix_counts=[1],
        talea_denominator=32,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    ~
                    c'16.
                    c'32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    c'16.
                    c'32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    c'8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___08():

    incise_specifier = rmakers.Incise(
        prefix_talea=[1],
        prefix_counts=[1],
        suffix_talea=[8],
        suffix_counts=[1, 2, 3],
        talea_denominator=32,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'32
                    c'4
                    ~
                    c'16.
                    c'4
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'32
                    c'16.
                    c'4
                    c'4
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'32
                    c'4
                    c'4
                    c'16.
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___09():

    incise_specifier = rmakers.Incise()

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___10():

    incise_specifier = rmakers.Incise(
        prefix_talea=[1],
        prefix_counts=[1],
        suffix_talea=[1],
        suffix_counts=[1],
        talea_denominator=8,
    )

    maker = rmakers.IncisedRhythmMaker(
        incise_specifier=incise_specifier, extra_counts_per_division=[1, 0, 3]
    )

    divisions = [(4, 8), (4, 8), (4, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
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
                \times 4/5 {
                    c'8
                    c'4.
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'8
                    c'4
                    c'8
                }
                \times 4/7 {
                    c'8
                    c'2
                    ~
                    c'8
                    c'8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___11():
    """
    Incises outer divisions only.
    """

    incise_specifier = rmakers.Incise(
        prefix_talea=[-8],
        prefix_counts=[2],
        suffix_talea=[-3],
        suffix_counts=[4],
        talea_denominator=32,
        outer_divisions_only=True,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    r4
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    r16.
                    r16.
                    r16.
                    r16.
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___12():
    """
    Incises outer divisions only.
    """

    incise_specifier = rmakers.Incise(
        prefix_talea=[-1],
        prefix_counts=[20],
        suffix_talea=[-1],
        suffix_counts=[2],
        talea_denominator=4,
        outer_divisions_only=True,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r4
                    r4
                    r8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'8
                    r4
                    r4
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___13():
    """
    Unincised notes.
    """

    incise_specifier = rmakers.Incise(outer_divisions_only=True)

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___14():
    """
    Incises outer divisions only.
    """

    incise_specifier = rmakers.Incise(
        prefix_talea=[-1],
        prefix_counts=[1],
        suffix_talea=[-1],
        suffix_counts=[1],
        talea_denominator=8,
        outer_divisions_only=True,
    )

    maker = rmakers.IncisedRhythmMaker(
        incise_specifier=incise_specifier, extra_counts_per_division=[1, 0, 3]
    )

    divisions = [(4, 8), (4, 8), (4, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
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
                \times 4/5 {
                    r8
                    c'2
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                }
                \times 4/7 {
                    c'2.
                    r8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___15():
    """
    Incises outer divisions only. Fills with rests.
    """

    incise_specifier = rmakers.Incise(
        prefix_talea=[8],
        prefix_counts=[2],
        suffix_talea=[3],
        suffix_counts=[4],
        talea_denominator=32,
        outer_divisions_only=True,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'16.
                    c'16.
                    c'16.
                    c'16.
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___16():
    """
    Incises outer divisions only. Fills with rests.
    """

    incise_specifier = rmakers.Incise(
        prefix_talea=[1],
        prefix_counts=[20],
        suffix_talea=[1],
        suffix_counts=[2],
        talea_denominator=4,
        outer_divisions_only=True,
    )

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'4
                    c'4
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'8
                    c'4
                    c'4
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___17():
    """
    Unincised rests.
    """

    incise_specifier = rmakers.Incise(outer_divisions_only=True)

    maker = rmakers.IncisedRhythmMaker(incise_specifier=incise_specifier)

    divisions = [(5, 8), (5, 8), (5, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
                \time 5/8
                s1 * 5/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                    ~
                    c'8
                }
            }
        >>
        """
    ), print(format(score))


def test_IncisedRhythmMaker___call___18():
    """
    Incises outer divisions only. Fills with rests.
    """

    incise_specifier = rmakers.Incise(
        prefix_talea=[1],
        prefix_counts=[1],
        suffix_talea=[1],
        suffix_counts=[1],
        talea_denominator=8,
        outer_divisions_only=True,
    )

    maker = rmakers.IncisedRhythmMaker(
        incise_specifier=incise_specifier, extra_counts_per_division=[1, 0, 3]
    )

    divisions = [(4, 8), (4, 8), (4, 8)]
    selections = maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
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
                \times 4/5 {
                    c'8
                    c'2
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'2
                }
                \times 4/7 {
                    c'2.
                    c'8
                }
            }
        >>
        """
    ), print(format(score))
