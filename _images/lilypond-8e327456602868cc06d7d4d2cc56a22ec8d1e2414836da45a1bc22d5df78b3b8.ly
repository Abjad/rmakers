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
            \repeat tremolo 4
            {
                \time 4/4
                c'32
                (
                c'32
                )
            }
            c'4
            c'4
            \repeat tremolo 4
            {
                c'32
                (
                c'32
                )
            }
            \repeat tremolo 4
            {
                \time 3/4
                c'32
                (
                c'32
                )
            }
            c'4
            \repeat tremolo 4
            {
                c'32
                (
                c'32
                )
            }
        }
    }
}