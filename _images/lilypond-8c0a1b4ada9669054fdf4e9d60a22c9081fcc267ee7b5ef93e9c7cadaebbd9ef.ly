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