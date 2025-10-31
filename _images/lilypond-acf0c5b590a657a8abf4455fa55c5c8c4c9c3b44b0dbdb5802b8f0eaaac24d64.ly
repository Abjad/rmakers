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
            \time 3/4
            c'16
            ~
            c'4
            c'16
            ~
            c'4
            c'8
            ~
            c'8.
            [
            c'16
            ]
            ~
            c'4
            c'4
        }
    }
}