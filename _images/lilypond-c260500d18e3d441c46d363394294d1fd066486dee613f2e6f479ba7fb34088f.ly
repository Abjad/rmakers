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
            {
                \set stemLeftBeamCount = 0
                \set stemRightBeamCount = 2
                \time 3/8
                c'16
                [
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 1
                c'16
            }
            {
                \set stemLeftBeamCount = 1
                \set stemRightBeamCount = 2
                \time 4/8
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 1
                c'16
            }
            {
                \set stemLeftBeamCount = 1
                \set stemRightBeamCount = 2
                \time 3/8
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 1
                c'16
            }
            {
                \set stemLeftBeamCount = 1
                \set stemRightBeamCount = 2
                \time 4/8
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 2
                c'16
                \set stemLeftBeamCount = 2
                \set stemRightBeamCount = 0
                c'16
                ]
            }
        }
    }
}