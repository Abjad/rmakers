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
            \tweak text #tuplet-number::calc-fraction-text
            \tweak edge-height #'(0.7 . 0)
            \tuplet 7/8
            {
                #(ly:expect-warning "strange time signature found")
                \time 5/14
                c'4
                ~
                c'16
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tweak edge-height #'(0.7 . 0)
            \tuplet 7/8
            {
                #(ly:expect-warning "strange time signature found")
                \time 3/7
                c'4.
            }
        }
    }
}