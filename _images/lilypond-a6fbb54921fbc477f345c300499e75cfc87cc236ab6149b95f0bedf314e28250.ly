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
            \tuplet 6/5
            {
                \time 5/16
                c'8.
                r8.
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 4/5
            {
                c'8.
                [
                c'16
                ]
            }
        }
    }
}