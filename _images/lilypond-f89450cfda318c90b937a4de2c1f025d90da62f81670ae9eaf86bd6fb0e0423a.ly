\version "2.19.83"
\language "english"
\include "abjad.ily"
\layout
{
    \context
    {
        \Score
        proportionalNotationDuration = \musicLength 1*1/24
    }
}

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