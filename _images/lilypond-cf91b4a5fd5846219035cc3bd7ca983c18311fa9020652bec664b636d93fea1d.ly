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
            r8
            r8.
            \time 4/8
            r4
            r16
            r8
            r16
            \time 3/8
            r8
            r4
            \time 4/8
            r16
            r8
            r8.
            c'8
        }
    }
}