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
\with
{
    \override TupletBracket.bracket-visibility = ##t
    \override TupletBracket.staff-padding = 4.5
    tupletFullLength = ##t
}
{
    \context RhythmicStaff = "Staff"
    \with
    {
        \override Clef.stencil = ##f
    }
    {
        \context Voice = "Voice"
        {
            {
                \time 1/4
                c'16
                [
                c'16
                c'16
                c'16
                ]
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 3/4
            {
                c'16
                [
                c'16
                c'16
                ]
            }
            {
                c'16
                [
                c'16
                c'16
                c'16
                ]
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 3/4
            {
                c'16
                [
                c'16
                c'16
                ]
            }
        }
    }
}