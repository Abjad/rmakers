\version "2.19.83"
\language "english"
\score
{
    \new Score
    \with
    {
        autoBeaming = ##f
    }
    <<
        \new Staff
        {
            c'8
            d'8
            e'8
            f'8
            g'8
            [
            a'8
            ]
        }
    >>
}