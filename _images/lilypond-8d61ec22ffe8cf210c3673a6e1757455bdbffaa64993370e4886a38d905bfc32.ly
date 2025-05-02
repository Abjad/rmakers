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
            \time 1/4
            s1 * 1/4
            \time 3/16
            s1 * 3/16
            \time 5/8
            s1 * 5/8
            #(ly:expect-warning "strange time signature found")
            \time 1/3
            s1 * 1/3
        }
    }
}