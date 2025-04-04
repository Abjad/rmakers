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
            \set stemLeftBeamCount = 0
            \set stemRightBeamCount = 1
            \time 5/32
            c'8
            [
            ~
            \set stemLeftBeamCount = 3
            \set stemRightBeamCount = 1
            c'32
            \set stemLeftBeamCount = 1
            \set stemRightBeamCount = 1
            c'8
            ~
            \set stemLeftBeamCount = 3
            \set stemRightBeamCount = 0
            c'32
            ]
        }
    }
}