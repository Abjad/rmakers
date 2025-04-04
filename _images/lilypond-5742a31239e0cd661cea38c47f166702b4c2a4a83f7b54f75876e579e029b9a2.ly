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
            \tuplet 5/4
            {
                \time 3/8
                c'4.
                c'16.
            }
            \time 4/8
            r2
            \tuplet 5/4
            {
                \time 3/8
                c'4.
                c'16.
            }
            \time 4/8
            r2
        }
    }
}