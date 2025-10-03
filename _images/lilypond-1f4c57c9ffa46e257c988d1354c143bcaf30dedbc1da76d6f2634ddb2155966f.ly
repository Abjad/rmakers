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
            \tuplet 4/3
            {
                \time 3/8
                c'16
                c'4
                c'8.
                ~
            }
            \time 4/8
            c'16
            c'4
            c'8.
            ~
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 7/6
            {
                \time 3/8
                c'16
                c'4
                c'8
                ~
            }
            \tuplet 5/4
            {
                \time 4/8
                c'8
                c'4
                c'4
            }
        }
    }
}