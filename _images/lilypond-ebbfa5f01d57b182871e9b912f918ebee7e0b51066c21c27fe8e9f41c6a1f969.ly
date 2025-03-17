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
            \tuplet 10/8
            {
                \time 2/16
                c'32
                [
                c'8
                ]
            }
            \tuplet 20/16
            {
                \time 4/16
                c'16
                c'4
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 20/24
            {
                \time 6/16
                c'16
                c'4
            }
            \tuplet 40/32
            {
                \time 8/16
                c'8
                c'2
            }
        }
    }
}