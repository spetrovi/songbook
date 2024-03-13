\version "2.24.1"
% automatically converted by musicxml2ly from co_si_janycko.mxl
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
PartPOneVoiceOne =  \relative e' {
    \clef "treble" \time 8/4 \key c \none \transposition bes | % 1
    e8 fis8 gis4 fis4 e4 gis8 a8 b4 a4 gis4 | % 2
    gis8 a8 b4 b8 cis8 b4 b8 b8 gis4 fis4 e4 | % 3
    R1*28 \bar "|."
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
                \context Voice = "PartPOneVoiceOne" {  \PartPOneVoiceOne }
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
                \context Voice = "PartPOneVoiceOne" {  \PartPOneVoiceOne }
                >>
            >>

        }
    \midi {\tempo 4 = 100 }
    }
