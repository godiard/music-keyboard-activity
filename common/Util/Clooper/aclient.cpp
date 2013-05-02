#include <Python.h>

#include <pthread.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <sys/time.h>
#include <sched.h>

#include <vector>
#include <map>
#include <cmath>

#include <csound/csound.h>

#include "log.cpp"


int VERBOSE = 3;
FILE * _debug = NULL;
struct TamTamSound;
struct Music;
TamTamSound * g_tt = NULL;
Music * g_music = NULL;
static log_t * g_log = NULL;
const int STEP_eventMax = 16;  //this is the most events that will be queued by a loop per step()

/**
 * Event is the type of event that Clooper puts in the loop buffer.
 * It corresponds to a line of csound that starts with an 'i'
 */
struct Event
{
    char type;  ///< if this event were listed in a csound file, the line would begin with this letter
    int onset;  ///< the onset time of this event (its temporal position)
    bool time_in_ticks; ///< if true, then some parameters will be updated according to the tempo
    bool active; ///< if true, then event() will actually do something
    MYFLT prev_secs_per_tick; ///< normally used for ____, sometimes set to -1 to force recalculation of param[] entries
    MYFLT duration, attack, decay;///< canonical values of some tempo-dependent parameters
    std::vector<MYFLT> param;     ///< parameter buffer for csound

    Event(char type, MYFLT * p, int param_count, bool in_ticks, bool active)
        : type(type), onset(0), time_in_ticks(in_ticks), active(active), param(param_count)
    {
        assert(param_count >= 4);
        onset = (int) p[1];
        duration = p[2];
        attack = param_count > 8 ? p[8]: 0.0; //attack
        decay = param_count > 9 ? p[9]: 0.0; //decay
        prev_secs_per_tick = -1.0;
        for (int i = 0; i < param_count; ++i) param[i] = p[i];

        param[1] = 0.0; //onset
    }
    /*
    bool operator<(const Event &e) const
    {
        return onset < e.onset;
    }
    */
    void ev_print(FILE *f)
    {
        fprintf(f, "INFO: scoreEvent %c ", type);
        for (size_t i = 0; i < param.size(); ++i) fprintf(f, "%lf ", param[i]);
        fprintf(f, "[%s]\n", active ? "active": "inactive");
    }
    /**
     *  Update the idx'th param value to have a certain value.
     *
     * Certain of the parameters are linked in strange hack-y ways, as defined by
     * the constructor, and update()  (which should be consistent with one another!)
     *
     * These events are for use with the file: TamTam/Resources/univorc.csd.
     * So that file defines how the parameters will be interpreted by csound.
     */
    void update(int idx, MYFLT val)
    {
        if ( (unsigned)idx >= param.size())
        {
            if (_debug && (VERBOSE > 0)) fprintf(_debug, "ERROR: updateEvent request for too-high parameter %i\n", idx);
            return;
        }
        if (time_in_ticks)
        {
            switch(idx)
            {
                case 1: onset = (int) val; break;
                case 2: duration =    val; break;
                case 8: attack =      val; break;
                case 9: decay  =      val; break;
                default: param[idx] = val; break;
            }
            prev_secs_per_tick = -1.0; //force recalculation
        }
        else
        {
            param[idx] = val;
        }
    }
    /**
     * An Event instance can be in an active or inactive state.  If an Event instance
     * is active, then event() will call a corresponding csoundScoreEvent().  If an
     * Event instance is inactive, then event() is a noop.
     */
    void activate_cmd(int cmd)
    {
        switch(cmd)
        {
            case 0: active = false; break;
            case 1: active = true; break;
            case 2: active = !active; break;
        }
    }

    /**
     * Iff this instance is active, this call generates a csound event.
     * Parameters are passed directly as a buffer of floats.  If secs_per_tick
     * != prev_secs_per_tick (possibly because prev_secs_per_tick was set to -1
     * by update() ) then this call will do some floating point ops to
     * recalculate the parameter buffer.
     */
    void event(CSOUND * csound, MYFLT secs_per_tick)
    {
        if (!active) return;

        if (time_in_ticks && (secs_per_tick != prev_secs_per_tick))
        {
            param[2] = duration * secs_per_tick;
            if (param.size() > 8) param[8] = std::max(0.002f, attack * param[2]);
            if (param.size() > 9) param[9] = std::max(0.002f, decay * param[2]);
            prev_secs_per_tick = secs_per_tick;
            if (_debug && (VERBOSE > 2)) fprintf(_debug, "setting duration to %f\n", param[5]);
        }
        csoundScoreEvent(csound, type, &param[0], param.size());
    }
};

/** 
 *
 * Loop is a repeat-able loop of Event instances.
 * */
struct Loop
{
    typedef int onset_t;
    typedef int id_t;
    typedef std::pair<onset_t, Event *> pair_t;
    typedef std::multimap<onset_t, Event *>::iterator iter_t;
    typedef std::map<id_t, iter_t>::iterator idmap_t;        

    int tick_prev;
    int tickMax;
    MYFLT rtick;

    // a container of all events, sorted by onset time
    // used for efficient playback
    std::multimap<onset_t, Event *> ev;
    // the playback head
    std::multimap<onset_t, Event *>::iterator ev_pos;
    // a container of pointers into ev, indexed by note id
    // used for deleting, updating notes
    std::map<id_t, iter_t> idmap;
    int steps;
    int playing; //true means that step() works, else step() is no-op

    Loop() : tick_prev(0), tickMax(1), rtick(0.0), ev(), ev_pos(ev.end()), steps(0), playing(0)
    {
    }
    ~Loop()
    {
        //TODO: send these events to a recycling queue, don't erase them
        for (iter_t i = ev.begin(); i != ev.end(); ++i)
        {
            delete i->second;
        }
    }
    void deactivateAll()
    {
        for (iter_t i = ev.begin(); i != ev.end(); ++i)
        {
            i->second->activate_cmd(0);
        }
    }
    MYFLT getTickf()
    {
        return fmod(rtick, (MYFLT)tickMax);
    }
    void setNumTicks(int nticks)
    {
        tickMax = nticks;
        MYFLT fnticks = nticks;
        if (rtick > fnticks)
        {
            rtick = fmodf(rtick, fnticks);
        }
    }
    void setTickf(float t)
    {
        rtick = fmodf(t, (MYFLT) tickMax);
        ev_pos = ev.lower_bound( (int) rtick );
    }
    /**  advance in play loop by rtick_inc ticks, possibly generate some
     * csoundScoreEvent calls.
     */
    void step(MYFLT rtick_inc, MYFLT secs_per_tick , CSOUND * csound)
    {
        if (!playing) return;
        rtick += rtick_inc;
        int tick = (int)rtick % tickMax;
        if (tick == tick_prev) return;

        int events = 0;
        int loop0 = 0;
        int loop1 = 0;
        if (!ev.empty()) 
        {
            if (steps && (tick < tick_prev)) // should be true only after the loop wraps (not after insert)
            {
                while (ev_pos != ev.end())
                {
                    if (_debug && (VERBOSE > 3)) ev_pos->second->ev_print(_debug);
                    if (events < STEP_eventMax) ev_pos->second->event(csound, secs_per_tick);
                    ++ev_pos;
                    ++events;
                    ++loop0;
                }
                ev_pos = ev.begin();
            }
            while ((ev_pos != ev.end()) && (tick >= ev_pos->first))
            {
                if (_debug && (VERBOSE > 3)) ev_pos->second->ev_print(_debug);
                if (events < STEP_eventMax) ev_pos->second->event(csound, secs_per_tick);
                ++ev_pos;
                ++events;
                ++loop1;
            }
        }
        tick_prev = tick;
        if (_debug && (VERBOSE>1) && (events >= STEP_eventMax)) fprintf(_debug, "WARNING: %i/%i events at once (%i, %i)\n", events, (int)ev.size(),loop0,loop1);
        ++steps;
    }
    void addEvent(int id, char type, MYFLT * p, int np, bool in_ticks, bool active)
    {
        Event * e = new Event(type, p, np, in_ticks, active);

        idmap_t id_iter = idmap.find(id);
        if (id_iter == idmap.end())
        {
            //this is a new id
            iter_t e_iter = ev.insert(pair_t(e->onset, e));

            //TODO: optimize by thinking about whether to do ev_pos = e_iter
            ev_pos = ev.upper_bound( tick_prev );
            idmap[id] = e_iter;
        }
        else
        {
            g_log->printf(1, "%s duplicate note %i\n", __FUNCTION__, id);
        }
    }
    void delEvent(int id)
    {
        idmap_t id_iter = idmap.find(id);
        if (id_iter != idmap.end())
        {
            iter_t e_iter = id_iter->second;//idmap[id];
            if (e_iter == ev_pos) ++ev_pos;

            delete e_iter->second;
            ev.erase(e_iter);
            idmap.erase(id_iter);
        }
        else
        {
            g_log->printf( 1, "%s unknown note %i\n", __FUNCTION__, id);
        }
    }
    void updateEvent(int id, int idx, float val, int activate_cmd)
    {
        idmap_t id_iter = idmap.find(id);
        if (id_iter != idmap.end())
        {
            //this is a new id
            iter_t e_iter = id_iter->second;
            Event * e = e_iter->second;
            int onset = e->onset;
            e->update(idx, val);
            e->activate_cmd(activate_cmd);
            if (onset != e->onset)
            {
                ev.erase(e_iter);

                e_iter = ev.insert(pair_t(e->onset, e));

                //TODO: optimize by thinking about whether to do ev_pos = e_iter
                ev_pos = ev.upper_bound( tick_prev );
                idmap[id] = e_iter;
            }
        }
        else
        {
            g_log->printf(1, "%s unknown note %i\n", __FUNCTION__, id);
        }
    }
    void reset()
    {
        steps = 0;
    }
    void setPlaying(int tf)
    {
        playing = tf;
    }
};

/** management of loops */
struct Music
{
    typedef int loopIdx_t;
    typedef std::map<int, Loop * > eventMap_t;

    eventMap_t loop;
    int loop_nextIdx;
    void * mutex; //modification and playing of loops cannot be interwoven

    Music() : 
        loop(), 
        loop_nextIdx(0), 
        mutex(csoundCreateMutex(0))
    {
    }
    ~Music()
    {
        for (eventMap_t::iterator i = loop.begin(); i != loop.end(); ++i)
        {
            delete i->second;
        }
        csoundDestroyMutex(mutex);
    }

    void step(MYFLT amt, MYFLT secs_per_tick, CSOUND * csound)
    {
        csoundLockMutex(mutex);
        for (eventMap_t::iterator i = loop.begin(); i != loop.end(); ++i)
        {
            i->second->step(amt, secs_per_tick, csound);
        }
        csoundUnlockMutex(mutex);
    }

    /** allocate a new loop, and return its index */
    loopIdx_t alloc()
    {
        csoundLockMutex(mutex);
        //find a loop_nextIdx that isn't in loop map already
        while ( loop.find( loop_nextIdx) != loop.end()) ++loop_nextIdx; 
        loop[loop_nextIdx] = new Loop();
        csoundUnlockMutex(mutex);
        return loop_nextIdx;
    }
    /** de-allocate a loop */
    void destroy(loopIdx_t loopIdx)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            csoundLockMutex(mutex);
            //TODO: save the note events to a cache for recycling
            delete loop[loopIdx];
            loop.erase(loopIdx);
            csoundUnlockMutex(mutex);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    /** set the playing flag of the given loop */
    void playing(loopIdx_t loopIdx, int tf)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            csoundLockMutex(mutex);
            loop[loopIdx]->setPlaying(tf);
            csoundUnlockMutex(mutex);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    /** set the playing flag of the given loop */
    void addEvent(loopIdx_t loopIdx, int eventId, char type, MYFLT * p, int np, bool in_ticks, bool active)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            csoundLockMutex(mutex);
            loop[loopIdx]->addEvent(eventId, type, p, np, in_ticks, active);
            csoundUnlockMutex(mutex);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    void delEvent(loopIdx_t loopIdx, int eventId)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            csoundLockMutex(mutex);
            loop[loopIdx]->delEvent(eventId);
            csoundUnlockMutex(mutex);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    void updateEvent(loopIdx_t loopIdx, int eventId, int pIdx, float pVal, int activate_cmd)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            csoundLockMutex(mutex);
            loop[loopIdx]->updateEvent(eventId, pIdx, pVal, activate_cmd);
            csoundUnlockMutex(mutex);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    MYFLT getTickf(loopIdx_t loopIdx)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            return loop[loopIdx]->getTickf();
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
            return 0.0;
        }
    }
    void setTickf(loopIdx_t loopIdx, MYFLT tickf)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            loop[loopIdx]->setTickf(tickf);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    void setNumTicks(loopIdx_t loopIdx, int numTicks)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            loop[loopIdx]->setNumTicks(numTicks);
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }
    void deactivateAll(loopIdx_t loopIdx)
    {
        if (loop.find(loopIdx) != loop.end())
        {
            loop[loopIdx]->deactivateAll();
        }
        else
        {
            g_log->printf(1, "%s() called on non-existant loop %i\n", __FUNCTION__ , loopIdx);
        }
    }

};

/**
 * The main object of control in the Clooper plugin.
 *
 * This guy controls the sound rendering thread, loads and unloads ALSA, 
 * maintains a csound instance, and maintains a subset of notes from the
 * currently-loaded TamTam.
 */
struct TamTamSound
{
    /** the id of an running sound-rendering thread, or NULL */
    void * ThreadID;
    /** a flag to tell the thread to continue, or break */
    enum {CONTINUE, STOP} PERF_STATUS;
    /** our csound object, NULL iff there was a problem creating it */
    CSOUND * csound;
    /** our note sources */
    Music music;

    MYFLT secs_per_tick;
    MYFLT ticks_per_period;
    MYFLT tick_adjustment; //the default time increment in thread_fn
    MYFLT tick_total;

    /** the upsampling ratio from csound */
    int csound_frame_rate;
    long csound_period_size;

    log_t * ll;

    TamTamSound(log_t * ll, char * orc, int framerate )
        : ThreadID(NULL), PERF_STATUS(STOP), csound(NULL),
        music(),
        ticks_per_period(0.0),
        tick_adjustment(0.0), 
        tick_total(0.0),
        csound_frame_rate(framerate),           //must agree with the orchestra file
        ll( ll )
    {
        csound = csoundCreate(NULL);
        int argc=4;
        const char  **argv = (const char**)malloc(argc*sizeof(char*));
        argv[0] = "csound";
        argv[1] = "-m0";
        argv[2] = "-+rtaudio=alsa";
        argv[3] = orc;

        ll->printf(1,  "loading csound orchestra file %s\n", orc);
        //csoundInitialize(&argc, &argv, 0);
        csoundPreCompile(csound);
        int result = csoundCompile(csound, argc, (char**)argv);
        if (result)
        {
            csound = NULL;
            ll->printf( "ERROR: csoundCompile of orchestra %s failed with code %i\n", orc, result);
        }
        free(argv);
        csound_period_size = csoundGetOutputBufferSize(csound);
        csound_period_size /= 2; /* channels */
        setTickDuration(0.05);
    }
    ~TamTamSound()
    {
        if (csound)
        {
            stop();
            ll->printf(2, "Going for csoundDestroy\n");
            csoundDestroy(csound);
        }
        ll->printf(2, "TamTamSound destroyed\n");
        delete ll;
    }
    bool good()
    {
        return csound != NULL;
    }

    uintptr_t thread_fn()
    {
        assert(csound);

        tick_total = 0.0f;
        while (PERF_STATUS == CONTINUE)
        {
            if (csoundPerformBuffer(csound)) break;
            if (tick_adjustment > - ticks_per_period)
            {
                MYFLT tick_inc = ticks_per_period + tick_adjustment;
                music.step( tick_inc, secs_per_tick, csound);
                tick_adjustment = 0.0;
                tick_total += tick_inc;
            }
            else
            {
                tick_adjustment += ticks_per_period;
            }
        }

        ll->printf(2, "INFO: performance thread returning 0\n");
        return 0;
    }
    static uintptr_t csThread(void *clientData)
    {
        return ((TamTamSound*)clientData)->thread_fn();
    }
    int start(int )
    {
        if (!csound) {
            ll->printf(1, "skipping %s, csound==NULL\n", __FUNCTION__);
            return 1;
        }
        if (!ThreadID)
        {
            PERF_STATUS = CONTINUE;
            ThreadID = csoundCreateThread(csThread, (void*)this);
            ll->printf( "INFO(%s:%i) aclient launching performance thread (%p)\n", __FILE__, __LINE__, ThreadID );
            return 0;
        }
        ll->printf( "INFO(%s:%i) skipping duplicate request to launch a thread\n", __FILE__, __LINE__ );
        return 1;
    }
    int stop()
    {
        if (!csound) {
            ll->printf(1, "skipping %s, csound==NULL\n", __FUNCTION__);
            return 1;
        }
        if (ThreadID)
        {
            PERF_STATUS = STOP;
            ll->printf( "INFO(%s:%i) aclient joining performance thread\n", __FILE__, __LINE__ );
            uintptr_t rval = csoundJoinThread(ThreadID);
            ll->printf( "INFO(%s:%i) ... joined\n", __FILE__, __LINE__ );
            if (rval)  ll->printf( "WARNING: thread returned %zu\n", rval);
            ThreadID = NULL;
            return 0;
        }
        return 1;
    }

    /** pass an array event straight through to csound.  only works if perf. thread is running */
    void scoreEvent(char type, MYFLT * p, int np)
    {
        if (!csound) {
            ll->printf(1, "skipping %s, csound==NULL\n", __FUNCTION__);
            return;
        }
        if (!ThreadID)
        {
            if (_debug && (VERBOSE > 1)) fprintf(_debug, "skipping %s, ThreadID==NULL\n", __FUNCTION__);
            return ;
        }
        if (_debug && (VERBOSE > 2))
        {
            fprintf(_debug, "INFO: scoreEvent %c ", type);
            for (int i = 0; i < np; ++i) fprintf(_debug, "%lf ", p[i]);
            fprintf(_debug, "\n");
        }
        csoundScoreEvent(csound, type, p, np);
    }
    /** pass a string event straight through to csound.  only works if perf. thread is running */
    void inputMessage(const char * msg)
    {
        if (!csound) {
            ll->printf(1, "skipping %s, csound==NULL\n", __FUNCTION__);
            return;
        }
        if (!ThreadID)
        {
            if (_debug && (VERBOSE > 1)) fprintf(_debug, "skipping %s, ThreadID==NULL\n", __FUNCTION__);
            return ;
        }
        if (_debug &&(VERBOSE > 3)) fprintf(_debug, "%s\n", msg);
        csoundInputMessage(csound, msg);
    }
    /** pass a setChannel command through to csound. only works if perf. thread is running */
    void setChannel(const char * name, MYFLT vol)
    {
        if (!csound) {
            ll->printf(1, "skipping %s, csound==NULL\n", __FUNCTION__);
            return;
        }
        if (!ThreadID)
        {
            if (_debug && (VERBOSE > 1)) fprintf(_debug, "skipping %s, ThreadID==NULL\n", __FUNCTION__);
            return ;
        }
        MYFLT *p;
        if (!(csoundGetChannelPtr(csound, &p, name, CSOUND_CONTROL_CHANNEL | CSOUND_INPUT_CHANNEL)))
            *p = (MYFLT) vol;
        else
        {
            if (_debug && (VERBOSE >0)) fprintf(_debug, "ERROR: failed to set channel: %s\n", name);
        }
    }

    /** adjust the global tick value by this much */
    void adjustTick(MYFLT dtick)
    {
        tick_adjustment += dtick;
    }
    void setTickDuration(MYFLT d )
    {
        secs_per_tick = d;
        ticks_per_period = csound_period_size / ( secs_per_tick  * csound_frame_rate);
        ll->printf( 3, "INFO: duration %lf := ticks_per_period %lf\n", secs_per_tick , ticks_per_period);
    }
    MYFLT getTickf()
    {
        return tick_total + tick_adjustment;
    }
};


static void cleanup(void)
{
    if (g_tt)
    {
        delete g_tt;
        g_tt = NULL;
    }
}

#define DECL(s) static PyObject * s(PyObject * self, PyObject *args)
#define RetNone Py_INCREF(Py_None); return Py_None;

//call once at end
DECL(sc_destroy)
{
    if (!PyArg_ParseTuple(args, ""))
    {
        return NULL;
    }
    if (g_tt)
    {
        delete g_tt;
        g_tt = NULL;
        if (_debug) fclose(_debug);
    }
    RetNone;
}
//call once at startup, should return 0
DECL(sc_initialize) //(char * csd)
{
    char * str;
    char * log_file;
    int framerate;
    if (!PyArg_ParseTuple(args, "ssii", &str, &log_file, &VERBOSE, &framerate ))
    {
        return NULL;
    }
    if ( log_file[0] )
    {
        _debug = fopen(log_file,"w"); 
        if (_debug==NULL) 
        {
            fprintf(stderr, "WARNING: fopen(%s) failed, logging to stderr\n", log_file);
            _debug = stderr;
        }
    }
    else
    {
        _debug = NULL;
        fprintf(stderr, "Logging disabled on purpose\n");
    }
    g_log = new log_t(_debug, VERBOSE);
    g_tt = new TamTamSound(g_log, str, framerate);
    g_music = & g_tt->music;
    atexit(&cleanup);
    if (g_tt->good()) 
        return Py_BuildValue("i", 0);
    else
        return Py_BuildValue("i", -1);
}
//compile the score, connect to device, start a sound rendering thread
DECL(sc_start)
{
    int ppb;
    if (!PyArg_ParseTuple(args, "i", &ppb ))
    {
        return NULL;
    }
    return Py_BuildValue("i", g_tt->start(ppb));
}
//stop csound rendering thread, disconnect from sound device, clear tables.
DECL(sc_stop) 
{
    if (!PyArg_ParseTuple(args, "" ))
    {
        return NULL;
    }
    return Py_BuildValue("i", g_tt->stop());
}
DECL(sc_scoreEvent) //(char type, farray param)
{
    char ev_type;
    PyObject *o;
    if (!PyArg_ParseTuple(args, "cO", &ev_type, &o ))
    {
        return NULL;
    }
    if (o->ob_type
            &&  o->ob_type->tp_as_buffer
            &&  (1 == o->ob_type->tp_as_buffer->bf_getsegcount(o, NULL)))
    {
        if (o->ob_type->tp_as_buffer->bf_getreadbuffer)
        {
            void * ptr;
            size_t len;
            len = o->ob_type->tp_as_buffer->bf_getreadbuffer(o, 0, &ptr);
            float * fptr = (float*)ptr;
            size_t flen = len / sizeof(float);
            g_tt->scoreEvent(ev_type, fptr, flen);

            Py_INCREF(Py_None);
            return Py_None;
        }
        else
        {
            assert(!"asdf");
        }
    }
    assert(!"not reached");
    return NULL;
}
DECL (sc_inputMessage) //(const char *msg)
{
    char * msg;
    if (!PyArg_ParseTuple(args, "s", &msg ))
    {
        return NULL;
    }
    g_tt->inputMessage(msg);
    RetNone;
}
DECL(sc_setChannel) //(string name, float value)
{
    const char * str;
    float v;
    if (!PyArg_ParseTuple(args, "sf", &str,&v))
    {
        return NULL;
    }
    g_tt->setChannel(str,v);
    Py_INCREF(Py_None);
    return Py_None;
}
DECL(sc_getTickf) // () -> float
{
    if (!PyArg_ParseTuple(args, ""))
    {
        return NULL;
    }
    return Py_BuildValue("f", g_tt->getTickf());
}
DECL(sc_adjustTick) // (MYFLT ntick)
{
    float spt;
    if (!PyArg_ParseTuple(args, "f", &spt ))
    {
        return NULL;
    }
    g_tt->adjustTick(spt);
    RetNone;
}
DECL(sc_setTickDuration) // (MYFLT secs_per_tick)
{
    float spt;
    if (!PyArg_ParseTuple(args, "f", &spt ))
    {
        return NULL;
    }
    g_tt->setTickDuration(spt);
    RetNone;
}
DECL(sc_loop_new) // () -> int
{
    if (!PyArg_ParseTuple(args, "" )) return NULL;
    return Py_BuildValue("i", g_music->alloc());
}
DECL(sc_loop_delete) // (int loopIdx)
{
    int loopIdx;
    if (!PyArg_ParseTuple(args, "i", &loopIdx )) return NULL;
    g_music->destroy(loopIdx);
    RetNone;
}
DECL(sc_loop_getTickf) // (int loopIdx) -> float
{
    int idx;
    if (!PyArg_ParseTuple(args, "i", &idx ))
    {
        return NULL;
    }
    return Py_BuildValue("f", g_music->getTickf(idx));
}
DECL(sc_loop_setNumTicks) //(int loopIdx, int nticks)
{
    int loopIdx;
    int nticks;
    if (!PyArg_ParseTuple(args, "ii", &loopIdx, &nticks )) return NULL;
    g_music->setNumTicks(loopIdx, nticks);
    RetNone;
}
DECL(sc_loop_setTickf) // (int loopIdx, float pos)
{
    int loopIdx;
    MYFLT pos;
    if (!PyArg_ParseTuple(args, "if", &loopIdx, &pos )) return NULL;
    g_music->setTickf(loopIdx, pos);
    RetNone;
}
DECL(sc_loop_addScoreEvent) // (int loopIdx, int id, int duration_in_ticks, char type, farray param)
{
    int loopIdx, qid, inticks, active;
    char ev_type;
    PyObject *o;
    if (!PyArg_ParseTuple(args, "iiiicO", &loopIdx, &qid, &inticks, &active, &ev_type, &o )) return NULL;

    if (o->ob_type
            &&  o->ob_type->tp_as_buffer
            &&  (1 == o->ob_type->tp_as_buffer->bf_getsegcount(o, NULL)))
    {
        if (o->ob_type->tp_as_buffer->bf_getreadbuffer)
        {
            void * ptr;
            size_t len;
            len = o->ob_type->tp_as_buffer->bf_getreadbuffer(o, 0, &ptr);
            float * fptr = (float*)ptr;
            size_t flen = len / sizeof(float);

            g_music->addEvent(loopIdx, qid, ev_type, fptr, flen, inticks, active);

            RetNone;
        }
        else
        {
            assert(!"asdf");
        }
    }
    assert(!"not reached");
    return NULL;
}
DECL(sc_loop_delScoreEvent) // (int loopIdx, int id)
{
    int loopIdx, id;
    if (!PyArg_ParseTuple(args, "ii", &loopIdx, &id ))
    {
        return NULL;
    }
    g_music->delEvent(loopIdx, id);
    RetNone;
}
DECL(sc_loop_updateEvent) // (int loopIdx, int id, int paramIdx, float paramVal, int activate_cmd))
{
    int loopIdx, eventId;
    int idx;
    float val;
    int cmd;
    if (!PyArg_ParseTuple(args, "iiifi", &loopIdx, &eventId, &idx, &val, &cmd)) return NULL;
    g_music->updateEvent(loopIdx, eventId, idx, val, cmd);
    RetNone;
}
DECL(sc_loop_deactivate_all) // (int id)
{
    int loopIdx;
    if (!PyArg_ParseTuple(args, "i", &loopIdx)) return NULL;
    g_music->deactivateAll(loopIdx);
    RetNone;
}
DECL(sc_loop_playing) // (int loopIdx, int tf)
{
    int loopIdx, tf;
    if (!PyArg_ParseTuple(args, "ii", &loopIdx, &tf )) return NULL;
    g_music->playing(loopIdx, tf);
    RetNone;
}

#define MDECL(s) {""#s, s, METH_VARARGS, "documentation of "#s"... nothing!"}
static PyMethodDef SpamMethods[] = {
    MDECL(sc_destroy),
    MDECL(sc_initialize),
    MDECL(sc_start),
    MDECL(sc_stop),

    MDECL(sc_setChannel),
    MDECL(sc_inputMessage),
    MDECL(sc_scoreEvent),

    MDECL(sc_getTickf),
    MDECL(sc_adjustTick),
    MDECL(sc_setTickDuration),

    MDECL(sc_loop_new),
    MDECL(sc_loop_delete),
    MDECL(sc_loop_getTickf),
    MDECL(sc_loop_setTickf),
    MDECL(sc_loop_setNumTicks),
    MDECL(sc_loop_delScoreEvent),
    MDECL(sc_loop_addScoreEvent),
    MDECL(sc_loop_updateEvent),
    MDECL(sc_loop_deactivate_all),
    MDECL(sc_loop_playing),
    {NULL, NULL, 0, NULL} /*end of list */
};

PyMODINIT_FUNC
initaclient(void)
{
    (void) Py_InitModule("aclient", SpamMethods);
}


