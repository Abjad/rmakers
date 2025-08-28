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
            c'8
            c'8.
            ]
            \time 4/8
            c'2
            ~
            \time 3/8
            c'8
            c'4
            \time 4/8
            c'2
        }
    }
}