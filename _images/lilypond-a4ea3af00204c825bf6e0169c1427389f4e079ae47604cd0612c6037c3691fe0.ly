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
\with
{
    \override TupletBracket.bracket-visibility = ##t
    \override TupletBracket.padding = 2
}
{
    \context RhythmicStaff = "Staff"
    \with
    {
        \override Clef.stencil = ##f
    }
    {
        \context Voice = "Voice"
        {
            \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) { \rhythm { 2 } + \rhythm { 8 } }
            \tuplet 1/1
            {
                \time 5/8
                \once \override Beam.grow-direction = #right
                c'16 * 61/32
                [
                c'16 * 115/64
                c'16 * 49/32
                c'16 * 5/4
                c'16 * 33/32
                c'16 * 57/64
                c'16 * 13/16
                c'16 * 25/32
                ]
            }
            \revert TupletNumber.text
            \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
            \tuplet 1/1
            {
                \time 3/8
                \once \override Beam.grow-direction = #right
                c'16 * 117/64
                [
                c'16 * 99/64
                c'16 * 69/64
                c'16 * 13/16
                c'16 * 47/64
                ]
            }
            \revert TupletNumber.text
            {
                \time 1/8
                c'8
            }
        }
    }
}