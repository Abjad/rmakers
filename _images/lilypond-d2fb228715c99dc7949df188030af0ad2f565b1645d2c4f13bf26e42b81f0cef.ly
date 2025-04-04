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
                [
                c'8
                ]
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 4/7
            {
                \time 7/16
                c'8
                [
                c'8
                ]
            }
        }
    }
}