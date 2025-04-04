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
                \time 5/16
                r16
                c'4
                r16
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 6/5
            {
                r16
                c'4
                r16
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 6/5
            {
                r16
                c'4
                r16
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 6/5
            {
                r16
                c'4
                r16
            }
        }
    }
}