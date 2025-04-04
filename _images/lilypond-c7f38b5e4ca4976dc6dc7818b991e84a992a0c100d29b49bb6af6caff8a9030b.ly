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
                [
                c'8
                ]
            }
        }
    }
}