\version "2.19.83"
\language "english"
\context Score = "Score"
<<
    \new Staff
    {
        \new Voice
        {
            \override Staff.Stem.stemlet-length = 1
            \once \override Beam.grow-direction = #left
            c'16
            [
            d'16
            r16
            f'16
            g'8
            ]
            \revert Staff.Stem.stemlet-length
        }
    }
>>