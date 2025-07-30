\version "2.19.83"
\language "english"
\include "abjad.ily"
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
        \override TupletBracket.direction = #up
        \override TupletBracket.staff-padding = 5
    }
    {
        \context Voice = "Voice"
        {
            \context Voice = "RhythmMaker.Music"
            {
                \tweak text #tuplet-number::calc-fraction-text
                \tuplet 5/3
                {
                    \time 3/4
                    c'4
                    <<
                        \context Voice = "On_Beat_Grace_Container"
                        {
                            \set fontSize = #-3
                            \slash
                            \voiceOne
                            <
                                \tweak font-size 0
                                \tweak transparent ##t
                                c'
                            >8 * 10/21
                            [
                            (
                            c'8 * 10/21
                            )
                            ]
                        }
                        \context Voice = "RhythmMaker.Music"
                        {
                            \voiceTwo
                            c'4
                        }
                    >>
                    <<
                        \context Voice = "On_Beat_Grace_Container"
                        {
                            \set fontSize = #-3
                            \slash
                            \voiceOne
                            <
                                \tweak font-size 0
                                \tweak transparent ##t
                                c'
                            >8 * 10/21
                            [
                            (
                            c'8 * 10/21
                            c'8 * 10/21
                            c'8 * 10/21
                            )
                            ]
                        }
                        \context Voice = "RhythmMaker.Music"
                        {
                            \voiceTwo
                            c'4
                        }
                    >>
                    <<
                        \context Voice = "On_Beat_Grace_Container"
                        {
                            \set fontSize = #-3
                            \slash
                            \voiceOne
                            <
                                \tweak font-size 0
                                \tweak transparent ##t
                                c'
                            >8 * 10/21
                            [
                            (
                            c'8 * 10/21
                            )
                            ]
                        }
                        \context Voice = "RhythmMaker.Music"
                        {
                            \voiceTwo
                            c'4
                        }
                    >>
                    \oneVoice
                    c'4
                }
            }
        }
    }
}