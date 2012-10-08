from gettext import gettext as _

class Tooltips:
    def __init__(self):
        # Edit
        self.Edit = {}
        # tools
        self.Edit["2toolPointerButton"] = _('Select tool')
        self.Edit["2toolPencilButton"] = _('Draw tool')
        self.Edit["2toolBrushButton"] = _('Paint tool')
        # create tune
        self.Edit["2generateBtn"] = _('Generate new tune')
        # page
        self.Edit["2pageGenerateButton"] = _('Generate page')
        self.Edit["2pagePropertiesButton"] = _('Page properties')
        self.Edit["2pageDeleteButton"] = _('Delete page(s)')
        self.Edit["2pageDuplicateButton"] = _('Duplicate page(s)')
        self.Edit["2pageNewButton"] = _('Add page')
        self.Edit["2pageBeatsButton"] = _('Beats per page')
        self.Edit["2saveButton"] = _('Save tune')
        self.Edit["2loadButton"] = _('Load tune')
        # track
        self.Edit["2trackGenerateButton"] = _('Generate track')
        self.Edit["2trackPropertiesButton"] = _('Track properties')
        self.Edit["2trackDeleteButton"] = _('Clear track')
        self.Edit["2trackDuplicateButton"] = _('Duplicate track')
        # note
        self.Edit["2notePropertiesButton"] = _('Note(s) properties')
        self.Edit["2noteDeleteButton"] = _('Delete note(s)')
        self.Edit["2noteDuplicateButton"] = _('Duplicate note(s)')
        self.Edit["2noteOnsetMinusButton"] = _('Move note in time')
        self.Edit["2noteOnsetPlusButton"] = _('Move note in time')
        self.Edit["2notePitchMinusButton"] = _('Lower pitch')
        self.Edit["2notePitchPlusButton"] = _('Raise pitch')
        self.Edit["2noteDurationMinusButton"] = _('Modify duration')
        self.Edit["2noteDurationPlusButton"] = _('Modify duration')
        self.Edit["2noteVolumeMinusButton"] = _('Lower volume')
        self.Edit["2noteVolumePlusButton"] = _('Raise volume')
        # transport
        self.Edit["2playButton"] = _('Play')
        self.Edit["2pauseButton"] = _('Pause')
        self.Edit["2stopButton"] = _('Stop')
        self.Edit["2keyRecordButton"] = _('Keyboard recording')
        self.Edit["2recordButton"] = _('Save as .ogg')
        self.Edit["2rewindButton"] = _('Rewind')
        self.Edit["2closeButton"] = _('Save to journal and quit')
        # volume and tempo
        self.Edit["2volumeSlider"] = _('Master volume')
        self.Edit["2tempoSlider"] = _('Tempo')
        #InstrumentBox
        self.Edit["2instrument1muteButton"] = _("Left click to mute, right click to solo")
        self.Edit["2instrument2muteButton"] = _("Left click to mute, right click to solo")
        self.Edit["2instrument3muteButton"] = _("Left click to mute, right click to solo")
        self.Edit["2instrument4muteButton"] = _("Left click to mute, right click to solo")
        self.Edit["2drumMuteButton"] = _("Left click to mute, right click to solo")

        self.ALGO = {}
        self.ALGO["XYButton1"] = _('-- Rhythm density, | Rhythm regularity' )
        self.ALGO["XYButton2"] = _('-- Pitch regularity, | Pitch maximum step' )
        self.ALGO["XYButton3"] = _('-- Average duration, | Silence probability')
        self.ALGO["drunk"] = _('Drunk')
        self.ALGO["droneJump"] = _('Drone and Jump')
        self.ALGO["repeat"] = _('Repeater')
        self.ALGO["loopSeg"] = _('Loop segments')
        # TRANS: http://en.wikipedia.org/wiki/Major_scale
        self.ALGO["majorKey"] = _('Major scale')
        # TRANS: http://en.wikipedia.org/wiki/Minor_scale#Harmonic_and_melodic_minor
        self.ALGO["minorHarmKey"] = _('Harmonic minor scale')
        # TRANS: http://en.wikipedia.org/wiki/Minor_scale#Natural_minor
        self.ALGO["minorKey"] = _('Natural minor scale')
        # TRANS: http://en.wikipedia.org/wiki/Phrygian_mode
        self.ALGO["phrygienKey"] = _('Phrygian scale')
        # TRANS: http://en.wikipedia.org/wiki/Dorian_mode
        self.ALGO["dorienKey"] = _('Dorian scale')
        # TRANS: http://en.wikipedia.org/wiki/Lydian_mode
        self.ALGO["lydienKey"] = _('Lydian scale')
        # TRANS: http://en.wikipedia.org/wiki/Mixolydian_mode
        self.ALGO["myxoKey"] = _('Mixolydian scale')
        self.ALGO["saveButton"] = _('Save preset')
        self.ALGO["loadButton"] = _('Load preset')
        self.ALGO["checkButton"] = _('Generate')
        self.ALGO["cancelButton"] = _('Close')

        self.PROP = {}
        self.PROP['pitchUp'] = _('Transpose up')
        self.PROP['pitchDown'] = _('Transpose down')
        self.PROP['volumeUp'] = _('Volume up')
        self.PROP['volumeDown'] = _('Volume down')
        self.PROP['panSlider'] = _('Panoramization')
        self.PROP['reverbSlider'] = _('Reverb')
        self.PROP['attackSlider'] = _('Attack duration')
        self.PROP['decaySlider'] = _('Decay duration')
        # TRANS: http://en.wikipedia.org/wiki/Lowpass_filter
        self.PROP['filterTypeLowButton'] = _('Lowpass filter')
        # TRANS: http://en.wikipedia.org/wiki/Highpass_filter
        self.PROP['filterTypeHighButton'] = _('Highpass filter')
        # TRANS: http://en.wikipedia.org/wiki/Bandpass_filter
        self.PROP['filterTypeBandButton'] = _('Bandpass filter')
        # TRANS: http://en.wikipedia.org/wiki/Cutoff_frequency
        self.PROP['cutoffSlider'] = _('Filter cutoff')
        self.PROP['pitchGen'] = _('Open algorithmic generator')
        self.PROP['volumeGen'] = _('Open algorithmic generator')
        self.PROP['panGen'] = _('Open algorithmic generator')
        self.PROP['reverbGen'] = _('Open algorithmic generator')
        self.PROP['attackGen'] = _('Open algorithmic generator')
        self.PROP['decayGen'] = _('Open algorithmic generator')
        self.PROP['cutoffGen'] = _('Open algorithmic generator')
        self.PROP['line'] = _('Line')
        self.PROP['drunk'] = _('Drunk')
        self.PROP['droneJump'] = _('Drone and Jump')
        self.PROP['repeater'] = _('Repeater')
        self.PROP['loopseg'] = _('Loop segments')
        self.PROP['minSlider'] = _('Minimum value')
        self.PROP['maxSlider'] = _('Maximum value')
        self.PROP['paraSlider'] = _('Specific parameter')
        self.PROP['checkButton'] = _('Apply generator')
        self.PROP['cancelButton'] = _('Cancel')

    categories = {
            # TRANS: Instrument category
            'all': _('All'),
            # TRANS: Instrument category
            'animals': _('Animals'),
            # TRANS: Instrument category
            'concret': _('Objects'),
            # TRANS: Instrument category
            # TRANS: http://en.wikipedia.org/wiki/Keyboard_instrument
            'keyboard': _('Keyboard'),
            # TRANS: Instrument category
            'people': _('People'),
            # TRANS: Instrument category
            # TRANS: http://en.wikipedia.org/wiki/Percussion_instrument
            'percussions': _('Percussions'),
            # TRANS: Instrument category
            # TRANS: http://en.wikipedia.org/wiki/String_instrument
            'strings': _('Strings'),
            # TRANS: Instrument category
            # TRANS: http://en.wikipedia.org/wiki/Wind_instrument
            'winds': _('Winds'),
            }

    #miniTamTam
    VOL = _('Volume')
    BAL = _('Balance')
    REV = _('Reverb')
    PLAY = _('Play / Stop')
    STOP = _('Stop')
    SEQ = _('Left click to record, right click to record on top')
    GEN = _('Generate')
    COMPL = _('Complexity of beat')
    BEAT = _('Beats per bar')
    TEMPO = _('Tempo')
    RECMIC = _('Record with the microphone')
    RECLAB = _('Open SynthLab to create noise')
    MT_RECORDBUTTONS = [_('Record microphone into slot 1'), _('Record microphone into slot 2'), _('Record microphone into slot 3'), _('Record microphone into slot 4')]
