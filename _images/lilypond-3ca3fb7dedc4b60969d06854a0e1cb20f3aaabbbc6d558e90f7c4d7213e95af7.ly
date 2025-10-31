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
    autoBeaming = ##f
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
            {
                \override RhythmicStaff.Stem.stemlet-length = 0.75
                \time 3/8
                c'16
                [
                c'16
                c'16
                r16
                c'16
                c'16
                ]
                \revert RhythmicStaff.Stem.stemlet-length
            }
            {
                \override RhythmicStaff.Stem.stemlet-length = 0.75
                \time 4/8
                c'16
                [
                r16
                c'16
                c'16
                c'16
                r16
                c'16
                c'16
                ]
                \revert RhythmicStaff.Stem.stemlet-length
            }
            {
                \override RhythmicStaff.Stem.stemlet-length = 0.75
                \time 3/8
                c'16
                [
                r16
                c'16
                c'16
                c'16
                r16
                ]
                \revert RhythmicStaff.Stem.stemlet-length
            }
            {
                \override RhythmicStaff.Stem.stemlet-length = 0.75
                \time 4/8
                c'16
                [
                c'16
                c'16
                r16
                c'16
                c'16
                c'16
                r16
                ]
                \revert RhythmicStaff.Stem.stemlet-length
            }
        }
    }
}