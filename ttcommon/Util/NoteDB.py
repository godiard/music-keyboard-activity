import common.Util.InstrumentDB as InstrumentDB
import common.Config as Config

class PARAMETER:
    PAGE_BEATS, \
    PAGE_COLOR, \
    ONSET, \
    PITCH, \
    AMPLITUDE, \
    DURATION, \
    INSTRUMENT, \
    PAN, \
    REVERB, \
    ATTACK, \
    DECAY, \
    FILTERTYPE, \
    FILTERCUTOFF, \
    INSTRUMENT2 \
    = range(14)    #python-stye enum

class Note:
    def __init__( self, page, track, id, cs ):
        self.page = page
        self.track = track
        self.id = id
        self.cs = cs

        self.csStack = []

    def pushState( self ):
        self.csStack.append( self.cs.clone() )

    def popState( self ):
        self.cs = self.csStack.pop()

class Page:
    def __init__( self, beats, color = 0, instruments = False, local = True ): # , tempo, insruments, color = 0 ):
        self.instrumentDB = InstrumentDB.getRef()
        self.beats = beats
        self.ticks = beats*Config.TICKS_PER_BEAT

        self.color = color

        if not instruments:
            self.instruments = [ self.instrumentDB.instNamed["kalimba"].instrumentId for i in range(Config.NUMBER_OF_TRACKS-1) ] + [ self.instrumentDB.instNamed["drum1kit"].instrumentId ]
        else:
            self.instruments = instruments[:]

        self.local = local # page local/global?

        self.nextNoteId = 0 # first note will be 1

    def genId( self ):
        self.nextNoteId += 1
        if self.nextNoteId == 65536: # short
            print "note id overflow!"
            # TODO think of how to handle this!?
        return self.nextNoteId

    def setLocal( self, local ):
        self.local = local

class PageListener:
    def notifyPageAdd( self, id, at ):
        pass

    def notifyPageDelete( self, which, safe ):
        pass

    def notifyPageDuplicate( self, new, at ):
        pass

    def notifyPageMove( self, which, low, high ):
        pass

    def notifyPageUpdate( self, which, parameter, value ):
        pass

class NoteListener:
    def notifyNoteAdd( self, page, track, id ):
        pass
    def notifyNoteDelete( self, page, track, id ):
        pass
    def notifyNoteUpdate( self, page, track, id, parameter, value ):
        pass

class NoteDB:
    def __init__( self ):
        self.instrumentDB = InstrumentDB.getRef()
        self.noteD = {}     # bins containing all the notes by page, track, and id
                            # structure self.noteD[pageId][trackIndex][noteId]

        self.noteS = {}     # bins containing all the notes by page and track
                            # first sorted by onset then by pitch (for drum hits)
                            # structure self.noteS[pageId][trackIndex][noteIndex]

        self.pages = {}     # dict of Pages indexed by pageId

        self.tune = []      # list of pageIds ordered by tune

        #self.beatsBefore = {}     # count of beats on previous pages indexed by page id

        self.listeners = []       # complete list of listeners
        self.pageListeners = []   # list of listeners who want page notifications
        self.noteListeners = []   # list of listeners who want note notifications
        self.parasiteList = {}    # dict of parasites indexed by listener

        self.parasiteD = {}       # bin of parasites indexed by listener
        self.parasiteS = {}       # parasites sorted as in self.noteS,

        self.nextId = 0     # base id, first page will be 1

        self.clipboard = [] # stores copied cs notes
        self.clipboardArea = [] # stores the limits and tracks for each page in the clipboard

    def dumpToStream( self, ostream, localOnly = False ):
        for pid in self.tune:
            if not localOnly or self.pages[pid].local:
                ostream.page_add(pid, self.pages[pid])
                for note in self.getNotesByPage( pid ):
                    ostream.note_add( note )

    #-- private --------------------------------------------
    def _genId( self ):
        self.nextId += 1
        if self.nextId == 65536: # short
            print "page id overflow!"
            # TODO think of how to handle this!?
        return self.nextId

    #=======================================================
    # Page Functions

    def addPage( self, pid, page, after = False ):
        pid = self._newPage( pid, page )
        at = self._insertPage( pid, after )

        #self._updateBeatsBefore( at )

        for l in self.pageListeners:
            l.notifyPageAdd( pid, at )

        return pid

    def deletePages( self, which, instruments = False ):
        beats = self.pages[self.tune[0]].beats

        low = 999999
        ind = -1
        for id in which:
            ind = self.tune.index(id)
            if ind < low: low = ind

            for t in range(Config.NUMBER_OF_TRACKS):
                for n in self.noteD[id][t].keys():
                    self.deleteNote( id, t, n )

            #del self.beatsBefore[id]

            del self.noteD[id]
            del self.noteS[id]
            del self.parasiteD[id]
            del self.parasiteS[id]
            del self.pages[id]

            at = self.tune.index( id )
            self.tune.pop(at)

        if not len(self.tune):
            self.addPage( -1, Page(beats, instruments = instruments) ) # always have at least one page
            safe = self.tune[0]
            #self._updateBeatsBefore(0)
        else:
            safe = self.tune[max(ind-1,0)]
            #self._updateBeatsBefore(low)

        for l in self.pageListeners:
            l.notifyPageDelete( which, safe )

    def duplicatePages( self, which, after = False ):
        sorted = []
        if after: first = self.tune.index(after)+1
        else: first = 0

        i = j = 0
        while i < len(self.tune) and j < len(which):
            if self.tune[i] in which:
                sorted.append(self.tune[i])
                j += 1
            i += 1

        new = {}
        for cp in sorted:
            id = self._newPage( -1, Page(self.pages[cp].beats,self.pages[cp].color,self.pages[cp].instruments) )
            self._insertPage( id, after )
            after = id
            new[cp] = id

        #self._updateBeatsBefore( first )

        for l in self.pageListeners:
            l.notifyPageDuplicate( new, first )

        for cp in sorted:
            for t in range(Config.NUMBER_OF_TRACKS):
                for n in self.noteD[cp][t].keys():
                    self.duplicateNote( cp, t, n, new[cp], t, 0 )

        return new

    def movePages( self, which, after = False ):
        sorted = []
        if after: at = self.tune.index(after)+1
        else: at = 0
        low = high = at

        i = j = 0
        while i < len(self.tune):
            if self.tune[i] in which:
                sorted.append(self.tune[i])
                self.tune.pop(i)
                if i < low: low = i
                if i > high: high = i
                if i < at: at -= 1
                j += 1
            else:
                i += 1

        self.tune = self.tune[:at] + sorted + self.tune[at:]

        #self._updateBeatsBefore( low )

        for l in self.pageListeners:
            l.notifyPageMove( sorted, low, high )

    def updatePage( self, page, parameter, value ):
        if parameter == PARAMETER.PAGE_BEATS:
            ticks = value*Config.TICKS_PER_BEAT
            if self.pages[page].beats > value: # crop some notes
                dstream = []
                ustream = []
                for track in range(Config.NUMBER_OF_TRACKS):
                    dsub = []
                    usub = []
                    for note in self.getNotesByTrack(page, track):
                        if ticks <= note.cs.onset:
                            dsub.append( note.id )
                        elif ticks < note.cs.onset + note.cs.duration:
                            usub.append( note.id )
                            usub.append( ticks - note.cs.onset )
                    if len(dsub):
                        dstream += [ page, track, len(dsub) ] + dsub
                    if len(usub):
                        ustream += [ page, track, PARAMETER.DURATION, len(usub)//2 ] + usub
                if len(dstream):
                    self.deleteNotes( dstream + [-1] )
                if len(ustream):
                    self.updateNotes( ustream + [-1] )

            self.pages[page].beats = value
            self.pages[page].ticks = ticks
            #self._updateBeatsBefore(self.tune.index(page))
        elif parameter == PARAMETER.PAGE_COLOR:
            self.pages[page].color = value

        for l in self.pageListeners:
            l.notifyPageUpdate( page, parameter, value )

    # stream format:
    # parameter id
    # number of following pages (N)
    # page id
    # value
    def updatePages( self, stream ):
        i = [-1]
        parameter = self._readstream(stream,i)
        N = self._readstream(stream,i)
        for j in range(N):
            page = self._readstream(stream,i)
            val = self._readstream(stream,i)
            self.updatePage( page, parameter, val )

    def getInstruments(self, pages):
        dict = {}
        for page in pages:
            list = []
            for track in range(Config.NUMBER_OF_TRACKS):
                list.append(self.instrumentDB.instId[self.pages[page].instruments[track]].name)
            dict[page] = list[:]
        return dict

   #-- private --------------------------------------------
    def _newPage( self, pid, page ):
        if pid == -1 : pid = self._genId()
        self.pages[pid] = page
        self.noteD[pid] = [ {}  for i in range(Config.NUMBER_OF_TRACKS) ]
        self.noteS[pid] = [ [] for i in range(Config.NUMBER_OF_TRACKS) ]
        self.parasiteD[pid] = [ {} for i in range(Config.NUMBER_OF_TRACKS) ]
        self.parasiteS[pid] = [ {} for i in range(Config.NUMBER_OF_TRACKS) ]
        for i in range(Config.NUMBER_OF_TRACKS):
            for par in self.parasiteList.keys():
                self.parasiteD[pid][i][par] = {}
                self.parasiteS[pid][i][par] = []
        return pid

    def _insertPage( self, pid, after ):
        if not after: at = 0
        else: at = self.tune.index(after)+1
        self.tune.insert( at, pid )

        return at

    #def _updateBeatsBefore( self, ind ):
    #    if ind == 0: beats = 0
    #    else: beats = self.beatsBefore[self.tune[ind-1]] + self.pages[self.tune[ind-1]].beats
    #    for i in range(ind, len(self.tune)):
    #        self.beatsBefore[self.tune[ind]] = beats
    #        beats += self.pages[self.tune[ind]].beats



    #=======================================================
    # Track Functions

    def setInstrument( self, pages, track, instrumentId ):
        stream = []
        for page in pages:
            self.pages[page].instruments[track] = instrumentId
            notes = self.getNotesByTrack( page, track )
            sub = []
            for note in notes:
                sub.append( note.id )
                sub.append( instrumentId )
            if len(sub):
                stream += [ page, track, PARAMETER.INSTRUMENT, len(sub)//2 ] + sub
        if len(stream):
            self.updateNotes( stream + [-1] )

    def setInstrument2( self, pages, track, instrumentId ):
        stream = []
        for page in pages:
            #self.pages[page].instruments[track] = instrumentId
            notes = self.getNotesByTrack( page, track )
            sub = []
            for note in notes:
                sub.append( note.id )
                sub.append( instrumentId )
            if len(sub):
                stream += [ page, track, PARAMETER.INSTRUMENT2, len(sub)//2 ] + sub
        if len(stream):
            self.updateNotes( stream + [-1] )

    #=======================================================
    # Note Functions

    def addNote( self, nid, page, track, cs, hint = False ):
        if nid == -1: nid = self.pages[page].genId()
        n = self.noteD[page][track][nid] = Note( page, track, nid, cs )

        if not hint: at = 0
        else: at = hint[0]
        while at > 0:
            onset = self.noteS[page][track][at-1].cs.onset
            if onset <= cs.onset:
                if onset <= cs.onset: break
                elif self.noteS[page][track][at-1].cs.pitch <= cs.pitch: break
            at -= 1
        last = len(self.noteS[page][track])
        while at < last:
            onset = self.noteS[page][track][at].cs.onset
            if onset >= cs.onset:
                if onset > cs.onset: break
                elif self.noteS[page][track][at].cs.pitch > cs.pitch: break
            at += 1

        self.noteS[page][track].insert( at, n )

        for par in self.parasiteList.keys():
            parasite = self.parasiteList[par]( self, par, n )
            self.parasiteD[page][track][par][nid] = parasite.attach() # give parasites the option of return something other than themselves
            self.parasiteS[page][track][par].insert( at, parasite.attach() )

        if hint: hint[0] = at + 1 # assume the next note will fall after this one

        for l in self.noteListeners:
            l.notifyNoteAdd( page, track, nid )

        return nid

    # stream format:
    # page id
    # track index
    # number of following notes (N)
    # cs pointer
    # ... up to N
    # page id or -1 to exit
    def addNotes( self, stream ):
        new = {}
        i = [-1]
        p = self._readstream(stream,i)
        while p != -1:
            if p not in new:
                new[p] = [ [] for x in range(Config.NUMBER_OF_TRACKS) ]
            t = self._readstream(stream,i)
            N = self._readstream(stream,i)
            hint = [0]
            for j in range(N):
                new[p][t].append( self.addNote( -1, p, t, self._readstream(stream,i), hint ) )
            p = self._readstream(stream,i)

        return new

    def deleteNote( self, page, track, id ):
        ind = self.noteS[page][track].index( self.noteD[page][track][id] )

        for par in self.parasiteList.keys():
            self.parasiteD[page][track][par][id].destroy()
            self.parasiteS[page][track][par].pop(ind)
            del self.parasiteD[page][track][par][id]

        self.noteS[page][track].pop(ind)
        del self.noteD[page][track][id]

        for l in self.noteListeners:
            l.notifyNoteDelete( page, track, id )

    # stream format:
    # page id
    # track index
    # number of following notes (N)
    # note id
    # ... up to N
    # page id or -1 to exit
    def deleteNotes( self, stream ):
        i = [-1]
        p = self._readstream(stream,i)
        while p != -1:
            t = self._readstream(stream,i)
            N = self._readstream(stream,i)
            for j in range(N):
                self.deleteNote( p, t, self._readstream(stream,i) )
            p = self._readstream(stream,i)

    def deleteNotesByTrack( self, pages, tracks ):
        for p in pages:
            for t in tracks:
                notes = self.noteS[p][t][:]
                for n in notes:
                    self.deleteNote( p, t, n.id )

    def duplicateNote( self, page, track, id, toPage, toTrack, offset ):
        cs = self.noteD[page][track][id].cs.clone()
        cs.trackId = toTrack
        cs.pageId = toPage
        cs.onset += offset
        ticks = self.pages[toPage].ticks
        if cs.onset >= ticks: return False # off the end of the page
        if cs.onset + cs.duration > ticks:
            cs.duration = ticks - cs.onset

        return self.addNote( -1, toPage, toTrack, cs )

    # stream format:
    # page id
    # track index
    # toPage id
    # toTrack index
    # offset
    # number of following notes (N)
    # note id
    # ... up to N
    # page id or -1 to exit
    def duplicateNotes( self, stream ):
        i = [-1]
        p = self._readstream(stream,i)
        while p != -1:
            t = self._readstream(stream,i)
            toP = self._readstream(stream,i)
            toT = self._readstream(stream,i)
            offset = self._readstream(stream,i)
            N = self._readstream(stream,i)
            for j in range(N):
                self.duplicateNote( p, t, self._readstream(stream,i), toP, toT, offset )
            p = self._readstream(stream,i)


    def updateNote( self, page, track, id, parameter, value ):
        if parameter == PARAMETER.ONSET:
            self.noteD[page][track][id].cs.onset = value
            self._resortNote( page, track, id )
        elif parameter == PARAMETER.PITCH:
            self.noteD[page][track][id].cs.pitch= value
            self._resortNote( page, track, id )
        elif parameter == PARAMETER.AMPLITUDE:
            self.noteD[page][track][id].cs.amplitude = value
        elif parameter == PARAMETER.DURATION:
            self.noteD[page][track][id].cs.duration = value
        elif parameter == PARAMETER.INSTRUMENT:
            self.noteD[page][track][id].cs.instrumentId = value
        elif parameter == PARAMETER.PAN:
            self.noteD[page][track][id].cs.pan = value
        elif parameter == PARAMETER.REVERB:
            self.noteD[page][track][id].cs.reverbSend = value
        elif parameter == PARAMETER.ATTACK:
            self.noteD[page][track][id].cs.attack = value
        elif parameter == PARAMETER.DECAY:
            self.noteD[page][track][id].cs.decay = value
        elif parameter == PARAMETER.FILTERTYPE:
            self.noteD[page][track][id].cs.filterType = value
        elif parameter == PARAMETER.FILTERCUTOFF:
            self.noteD[page][track][id].cs.filterCutoff = value
        elif parameter == PARAMETER.INSTRUMENT2:
            self.noteD[page][track][id].cs.instrumentId2 = value

        for par in self.parasiteList.keys():
            self.parasiteD[page][track][par][id].updateParameter( parameter, value )

        for l in self.noteListeners:
            l.notifyNoteUpdate( page, track, id, parameter, value )

    # stream format:
    # page id
    # track index
    # parameter id
    # number of following notes (N)
    # note id
    # value
    # ... up to N
    # page id or -1 to exit
    def updateNotes( self, stream ):
        i = [-1]
        p = self._readstream(stream,i)
        while p != -1:
            t = self._readstream(stream,i)
            param = self._readstream(stream,i)
            N = self._readstream(stream,i)
            for j in range(N):
                self.updateNote( p, t, self._readstream(stream,i), param, self._readstream(stream,i) )
            p = self._readstream(stream,i)

    #-- private --------------------------------------------
    def _readstream( self, stream, i ):
        i[0] += 1
        return stream[i[0]]

    def _resortNote( self, page, track, id ):
        ins = out = self.noteS[page][track].index(self.noteD[page][track][id])
        cs = self.noteD[page][track][id].cs
        while ins > 0: # check backward
            onset = self.noteS[page][track][ins-1].cs.onset
            if onset <= cs.onset:
                if onset <= cs.onset: break
                elif self.noteS[page][track][ins-1].cs.pitch <= cs.pitch: break
            ins -= 1
        if ins == out: # check forward
            ins += 1
            last = len(self.noteS[page][track])
            while ins < last:
                onset = self.noteS[page][track][ins].cs.onset
                if onset >= cs.onset:
                    if onset > cs.onset: break
                    elif self.noteS[page][track][ins].cs.pitch > cs.pitch: break
                ins += 1

        if ins != out: # resort
            if ins > out: ins -= 1
            n = self.noteS[page][track].pop( out )
            self.noteS[page][track].insert( ins, n )
            for par in self.parasiteList.keys():
                p = self.parasiteS[page][track][par].pop( out )
                self.parasiteS[page][track][par].insert( ins, p )


    #=======================================================
    # Clipboard Functions

    # stream format:
    # page id
    # track index
    # number of following notes (N)
    # note id
    # ... up to N
    # page id or -1 to exit
    def notesToClipboard( self, stream ):
        self.clipboard = []
        self.clipboardArea = []
        i = [-1]
        pages = []
        p = self._readstream(stream,i)
        while p != -1:
            if p not in pages:
                page = [ [] for x in range(Config.NUMBER_OF_TRACKS) ]
                pageArea = { "limit": [ 99999, 0 ],
                             "tracks": [ 0 for x in range(Config.NUMBER_OF_TRACKS) ] }
                pages.append(p)
                self.clipboard.append(page)
                self.clipboardArea.append(pageArea)
            else:
                ind = pages.index(p)
                page = self.clipboard[ind]
                pageArea = self.clipboardArea[ind]
            t = self._readstream(stream,i)
            pageArea["tracks"][t] = 1
            N = self._readstream(stream,i)
            for j in range(N):
                cs = self.noteD[p][t][self._readstream(stream,i)].cs.clone()
                if cs.onset < pageArea["limit"][0]: pageArea["limit"][0] = cs.onset
                if cs.onset + cs.duration > pageArea["limit"][1]: pageArea["limit"][1] = cs.onset + cs.duration
                page[t].append( cs )
            p = self._readstream(stream,i)

        return self.clipboardArea

    def tracksToClipboard( self, pages, tracks ):
        self.clipboard = []
        self.clipboardOrigin = [ 0, 0 ]
        self.clipboardArea = []
        for p in pages:
            page = [ [] for x in range(Config.NUMBER_OF_TRACKS) ]
            pageArea = { "limit": [ 0, 99999 ],
                         "tracks": [ 0 for x in range(Config.NUMBER_OF_TRACKS) ] }
            self.clipboard.append(page)
            self.clipboardArea.append(pageArea)
            for t in tracks:
                pageArea["tracks"][t] = 1
                for id in self.noteD[p][t]:
                    cs = self.noteD[p][t][id].cs.clone()
                    page[t].append( cs )

        return self.clipboardArea

    # trackMap = { X: Y, W: Z, ... }; X,W are track indices, Y,Z are clipboard indices
    # instrumentMap = { X: Y, W: Z, ... }; X,W are track indices, Y,Z are instrument ids
    def pasteClipboard( self, pages, offset, trackMap, instrumentMap = {} ):
        if not len(self.clipboard): return

        deleteStream = []
        updateStream = []
        addStream = []

        pp = 0
        ppMax = len(self.clipboard)
        for p in pages:
            ticks = self.pages[p].ticks
            area = self.clipboardArea[pp]
            area["limit"][0] += offset
            area["limit"][1] += offset
            for t in trackMap.keys():
                if not area["tracks"][trackMap[t]]: continue
                if instrumentMap.has_key(t):
                    updateInstrument = True
                    instrumentId = instrumentMap[t]
                else:
                    updateInstrument = False
                tdeleteStream = []
                tupdateOStream = []
                tupdateDStream = []
                taddStream = []
                # clear area
                for n in self.noteS[p][t]:
                    start = n.cs.onset
                    end = start + n.cs.duration
                    if area["limit"][0] <= start < area["limit"][1]: start = area["limit"][1]
                    if area["limit"][0] < end <= area["limit"][1]: end = area["limit"][0]
                    if start < area["limit"][0] and end > area["limit"][1]: end = area["limit"][0]
                    if end <= start:
                        tdeleteStream.append( n.id )
                    elif start != n.cs.onset:
                        tupdateDStream += [ n.id, end - start ]
                        tupdateOStream += [ n.id, start ]
                    elif end != start + n.cs.duration:
                        tupdateDStream += [ n.id, end - start ]
                if len(tdeleteStream):
                    deleteStream += [ p, t, len(tdeleteStream) ] + tdeleteStream
                if len(tupdateOStream):
                    updateStream += [ p, t, PARAMETER.ONSET, len(tupdateOStream)//2 ] + tupdateOStream
                if len(tupdateDStream):
                    updateStream += [ p, t, PARAMETER.DURATION, len(tupdateDStream)//2 ] + tupdateDStream
                # paste notes
                for cs in self.clipboard[pp][trackMap[t]]:
                    newcs = cs.clone()
                    newcs.onset += offset
                    if newcs.onset >= ticks: continue
                    if newcs.onset + newcs.duration > ticks:
                        newcs.duration = ticks - newcs.onset
                    newcs.pageId = p
                    newcs.trackId = t
                    if updateInstrument:
                        newcs.instrumentId = instrumentId
                    # TODO update any other parameters?
                    taddStream.append( newcs )
                if len(taddStream):
                    addStream += [ p, t, len(taddStream) ] + taddStream

            pp += 1
            if pp == ppMax: pp -= ppMax



        if len(deleteStream):
            self.deleteNotes( deleteStream + [-1] )
        if len(updateStream):
            self.updateNotes( updateStream + [-1] )
        if len(addStream):
            return self.addNotes( addStream + [-1] )

        return None

    def getClipboardArea( self, ind ):
        N = len(self.clipboardArea)
        while ind >= N: ind -= N
        return self.clipboardArea[ind]

    #=======================================================
    # Listener Functions

    def addListener( self, listener, parasite = None, page = False, note = False ):
        if listener in self.listeners:
            return # only one listener per object

        if parasite:
            self.parasiteList[listener] = parasite
            self._addParasite( listener, parasite )

        if page: self.pageListeners.append( listener )
        if note: self.noteListeners.append( listener )
        self.listeners.append( listener )

    def deleteListener( self, listener ):
        self.listeners.remove( listener )
        if listener in self.pageListeners:
            self.pageListeners.remove( listener )
        if listener in self.noteListeners:
            self.noteListeners.remove( listener )
        if self.parasites.has_key( listener ):
            self._deleteParasite( listener )
            del self.parasiteList[listener]

    #-- private --------------------------------------------
    def _addParasite( self, listener, parasite ):
        for p in self.tune:
            for t in range(Config.NUMBER_OF_TRACKS):
                self.parasiteD[p][t][listener] = {}
                self.parasiteS[p][t][listener] = []
                for n in self.noteD[p][t].keys():
                    parasite( self, listener, self.noteD[p][t][n] )
                    self.parasiteD[p][t][listener][n] = parasite.attach() # give parasites the option of returning something other than themselves
                    self.parasiteS[p][t][listener].insert( self.noteS[p][t].index( self.noteD[p][t][n]), parasite.attach() )

    def _deleteParasite( self, listener ):
        for p in self.tune:
            for t in range(Config.NUMBER_OF_TRACKS):
                for n in self.notes[p][t].keys():
                    self.parasiteD[p][t][listener][n].destroy()
                del self.parasiteD[p][t][listener]
                del self.parasiteS[p][t][listener]

    #=======================================================
    # Get Functions

    def getPageCount( self ):
        return len(self.pages)

    def getTune( self ):
        return self.tune

    def getPage( self, page ):
        return self.pages[page]

    def getPageByIndex( self, ind ):
        return self.tune[ind]

    def getPageIndex( self, page ):
        return self.tune.index(page)

    # Not sure if this is useful!
    #def getBeatsBeforePage( self, page ):
    #    return self.beatsBefore[page]

    def getNote( self, page, track, id, listener = None ):
        if listener:
            return self.parasiteD[page][track][listener][id]
        return self.noteD[page][track][id]

    def getNotesByPage( self, page, listener = None ):
        notes = []
        if listener:
            for i in range(Config.NUMBER_OF_TRACKS):
                notes.extend( self.parasiteS[page][i][listener] )
        else:
            for i in range(Config.NUMBER_OF_TRACKS):
                notes.extend( self.noteS[page][i] )
        return notes


    def getNotesByTrack( self, page, track, listener = None ):
        if listener:
            return self.parasiteS[page][track][listener]
        else:
            return self.noteS[page][track]

    def getNotes(self, listener = None ):
        notes = []
        for p in self.pages:
            notes.extend( self.getNotesByPage(p, listener ) )
        return notes


    def getCSNotesByPage( self, page ):
        return map( lambda n: n.cs, self.getNotesByPage( page ) )

    def getCSNotesByTrack( self, page, track ):
        return map( lambda n: n.cs, self.getNotesByTrack( page, track ) )
