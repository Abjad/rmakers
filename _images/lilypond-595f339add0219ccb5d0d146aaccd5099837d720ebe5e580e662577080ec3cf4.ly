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
            \tweak edge-height #'(0.7 . 0)
            \tuplet 5/4
            {
                #(ly:expect-warning "strange time signature found")
                \time 1/5
                c'4
            }
            \tweak text #tuplet-number::calc-fraction-text
            \tuplet 1/1
            {
                \time 1/4
                c'4
            }
            \tweak edge-height #'(0.7 . 0)
            \tuplet 3/2
            {
                #(ly:expect-warning "strange time signature found")
                \time 1/6
                c'4
            }
            \tweak edge-height #'(0.7 . 0)
            \tuplet 9/8
            {
                #(ly:expect-warning "strange time signature found")
                \time 7/9
                c'2..
            }
        }
    }
}