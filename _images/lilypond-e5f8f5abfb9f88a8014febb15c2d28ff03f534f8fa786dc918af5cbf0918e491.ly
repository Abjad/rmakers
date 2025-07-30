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
    }
    {
        \context Voice = "Voice"
        {
            \context Voice = "RhythmMaker.Music"
            {
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
                        >8 * 2/7
                        [
                        (
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        )
                        ]
                    }
                    \context Voice = "RhythmMaker.Music"
                    {
                        \time 3/4
                        \voiceTwo
                        c'4
                        ~
                        c'16
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
                        >8 * 2/7
                        [
                        (
                        c'8 * 2/7
                        )
                        ]
                    }
                    \context Voice = "RhythmMaker.Music"
                    {
                        \voiceTwo
                        c'4
                        ~
                        c'16
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
                        >8 * 2/7
                        [
                        (
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        )
                        ]
                    }
                    \context Voice = "RhythmMaker.Music"
                    {
                        \voiceTwo
                        c'8
                        ~
                        c'8.
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
                        >8 * 2/7
                        [
                        (
                        c'8 * 2/7
                        )
                        ]
                    }
                    \context Voice = "RhythmMaker.Music"
                    {
                        \voiceTwo
                        c'4
                        ~
                        c'16
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
                        >8 * 2/7
                        [
                        (
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        c'8 * 2/7
                        )
                        ]
                    }
                    \context Voice = "RhythmMaker.Music"
                    {
                        \voiceTwo
                        c'4
                    }
                >>
            }
        }
    }
}