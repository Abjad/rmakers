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
            \time 5/16
            c'8
            [
            ~
            c'32
            c'8
            ~
            c'32
            ]
            c'8
            [
            ~
            c'32
            c'8
            ~
            c'32
            ]
            c'8
            [
            ~
            c'32
            c'8
            ~
            c'32
            ]
            c'8
            [
            ~
            c'32
            c'8
            ~
            c'32
            ]
        }
    }
}