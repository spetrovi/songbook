\version "2.24.1"
% automatically converted by musicxml2ly from uztababaumrela.mxl
\pointAndClickOff

\include "articulate.ly"

\header {
    title =  "Untitled score"
    composer =  "Composer / arranger"
    encodingsoftware =  "MuseScore 4.2.1"
    encodingdate =  "2024-02-23"
    subtitle =  Subtitle
    }

\layout {
    \context { \Score
        skipBars = ##t
        }
    }
PartPOneVoiceOne =  \relative e'' {
    \clef "treble" \time 2/4 \key c \major \transposition bes | % 1
    e2 ~ | % 2
    c8 g8 c8 g8 ~ | % 3
    c4 d4 | % 4
    e4 d4 | % 5
    c2 | % 6
    e4 e4 | % 7
    e4 ~ g4 | % 8
    f8 e8 d4 | % 9
    f4 e4 | \barNumberCheck #10
    d4 \afterGrace { c4 ( } { f8 ) } | % 11
    e8 d8 c4 | % 12
    c8 c8 c8 d8 | % 13
    e4 d4 | % 14
    c2 | % 15
    R2*22 | % 37
    f'2 | % 38
    R2*27 \bar "|."
    }

PartPOneVoiceTwo =  \relative c'' {
    \clef "treble" \time 2/4 \key c \major \transposition bes | % 1
    c2 ~ | % 2
    e2 | % 3
    g,2 | % 4
    c8 g8 ~ g4 ~ | % 5
    g2 | % 6
    c4 ~ c8 g8 | % 7
    c8 c8 c8 g8 | % 8
    g2 | % 9
    c8 g8 c4 | \barNumberCheck #10
    g2 | % 11
    g2 ~ | % 12
    g2 ~ | % 13
    g2 ~ | % 14
    g2 s1*4 s1*6 s1*6 s1*6 s1*3 \bar "|."
    }


% The score definition
\score {
    <<

        \new Staff
        <<
            \set Staff.instrumentName = "Bagpipe"
            \set Staff.shortInstrumentName = "Bagp."
            \set Staff.midiInstrument = "bagpipe"

            \context Staff <<
                \mergeDifferentlyDottedOn\mergeDifferentlyHeadedOn
                \context Voice = "PartPOneVoiceOne" {  \voiceOne \PartPOneVoiceOne }
                \context Voice = "PartPOneVoiceTwo" {  \voiceTwo \PartPOneVoiceTwo }
                >>
            >>

        >>
    \layout {}
    }
\score {
    \unfoldRepeats \articulate {

        \new Staff
        <<
            \set Staff.instrumentName = "Bagpipe"
            \set Staff.shortInstrumentName = "Bagp."
            \set Staff.midiInstrument = "bagpipe"

            \context Staff <<
                \mergeDifferentlyDottedOn\mergeDifferentlyHeadedOn
                \context Voice = "PartPOneVoiceOne" {  \voiceOne \PartPOneVoiceOne }
                \context Voice = "PartPOneVoiceTwo" {  \voiceTwo \PartPOneVoiceTwo }
                >>
            >>

        }
    \midi {\tempo 4 = 100 }
    }
