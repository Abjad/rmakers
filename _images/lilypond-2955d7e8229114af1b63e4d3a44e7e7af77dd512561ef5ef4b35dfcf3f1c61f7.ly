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