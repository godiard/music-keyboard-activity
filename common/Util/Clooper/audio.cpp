#ifndef AUDIO_HXX
#define AUDIO_HXX

/*
 *  Latency test program
 *
 *     Author: Jaroslav Kysela <perex@suse.cz>
 *
 *  This small demo program can be used for measuring latency between
 *  capture and playback. This latency is measured from driver (diff when
 *  playback and capture was started). Scheduler is set to SCHED_RR.
 *
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the Free Software
 *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sched.h>
#include <errno.h>
#include <getopt.h>
#include <sys/time.h>
#include <math.h>

#include <string>
#include <alsa/asoundlib.h>

#define ERROR_HERE ll->printf("ERROR_HERE: %s %i\n", __FILE__, __LINE__)

struct SystemStuff
{
    log_t * ll;

    snd_pcm_t *phandle;
    snd_pcm_uframes_t period_size;
    unsigned int      rate;
    const snd_pcm_format_t sample_format;
    SystemStuff(log_t * ll) : ll(ll), phandle(NULL), period_size(0), rate(0), sample_format(SND_PCM_FORMAT_S16)
    {
    }
    ~SystemStuff()
    {
        if (phandle) close(0);
    }

    void setscheduler(void)
    {
        struct sched_param sched_param;

        if (sched_getparam(0, &sched_param) < 0) {
                ll->printf( "Scheduler getparam failed...\n");
                return;
        }
        sched_param.sched_priority = sched_get_priority_max(SCHED_RR);
        if (!sched_setscheduler(0, SCHED_RR, &sched_param)) {
            ll->printf( "Scheduler set to Round Robin with priority %i...\n", sched_param.sched_priority);
            return;
        }
        ll->printf( "!!!Scheduler set to Round Robin with priority %i FAILED!!!\n", sched_param.sched_priority);
    }

    int open(unsigned int rate0, int upsample_max, snd_pcm_uframes_t period0, unsigned int p_per_buff)
    {
        snd_pcm_hw_params_t *hw;

        if (phandle)
        {
            ll->printf( "ERROR: open called twice! First close the sound device\n");
            return -1;
        }

        if ( 0 > snd_pcm_open(&phandle, "default", SND_PCM_STREAM_PLAYBACK, 0)) { ERROR_HERE; return -1; }
        if ( 0 > snd_pcm_hw_params_malloc(&hw))                                 { ERROR_HERE; snd_pcm_close(phandle); phandle = NULL; return -1; }

        //now we can be a bit flexible with the buffer size and the sample-rate...

        int upsample;
        for (upsample = 1; upsample < upsample_max; ++upsample)
        {
            rate = rate0 * upsample;

            if ( 0 > snd_pcm_hw_params_any(phandle, hw))                               { ERROR_HERE; goto open_error;}

            //first do the compulsory steps... interleaved float, 2 channel
            if ( 0 > snd_pcm_hw_params_set_rate_resample(phandle, hw, 0))              { ERROR_HERE; goto open_error;}
            if ( 0 > snd_pcm_hw_params_test_access(phandle, hw, SND_PCM_ACCESS_RW_INTERLEAVED)){ ERROR_HERE; goto open_error;}
            if ( 0 > snd_pcm_hw_params_set_access(phandle, hw, SND_PCM_ACCESS_RW_INTERLEAVED)){ ERROR_HERE; goto open_error;}
            if ( 0 > snd_pcm_hw_params_test_format(phandle, hw, sample_format)) { ERROR_HERE; goto open_error;}
            if ( 0 > snd_pcm_hw_params_set_format(phandle, hw, sample_format))  { ERROR_HERE; goto open_error;}
            if ( 0 > snd_pcm_hw_params_set_channels(phandle, hw, 2))                   { ERROR_HERE; goto open_error;}

            if ( snd_pcm_hw_params_set_rate_near(phandle, hw, &rate, 0)) 
            {
                ll->printf("test_rate failed( %i\n", rate);
                continue;
            }
            else
            {
                ll->printf(1, "success! setting rate :  %i\n", rate);

                snd_pcm_uframes_t minb=0, maxb= 0;
                int mind=0, maxd=0;
                snd_pcm_hw_params_get_period_size_min(hw, &minb,&mind);
                snd_pcm_hw_params_get_period_size_max(hw, &maxb,&maxd);
                ll->printf(2, "FYI: period size range is [%li/%i,%li/%i]\n", minb,mind, maxb, maxd);

                if ((mind != 0) || (maxd == 0))
		{
                    ll->printf(2, "watch out, mind and maxd non-zero... you didn't set rate_resample to 0 did you...\n");
		}

                if (period0 < minb) 
                {
                    ll->printf(1, "requested period size (%li) < min (%li), adjusting to min\n", period_size, minb);
                    period_size = minb;
                }
                else if (period0 > maxb) 
                {
                    ll->printf(2, "requested period size (%li) < max (%li), adjusting to min\n", period_size, maxb);
                    period_size = maxb;
                }
                else
                {
                    period_size = period0;
                }

                ll->printf(1, "testing period size :  %li\n", period_size);
                if ( 0 > snd_pcm_hw_params_test_period_size(phandle, hw, period_size, 0)){ ERROR_HERE; goto open_error;}


                ll->printf(1, "setting period size :  %li\n", period_size);
                if ( 0 > snd_pcm_hw_params_set_period_size_near(phandle, hw, &period_size, 0)){ ERROR_HERE; goto open_error;}
                
                ll->printf(1, "setting buffer size :  %i * %li = %li\n", p_per_buff, period_size, p_per_buff * period_size);
                snd_pcm_uframes_t buff_size = p_per_buff * period_size;
                if ( 0 > snd_pcm_hw_params_set_buffer_size_near(phandle, hw, &buff_size)) { ERROR_HERE; goto open_error;}

                break;
            }
        }

        if (upsample_max == upsample) { ERROR_HERE; goto open_error; }

        if (0 > snd_pcm_hw_params(phandle, hw)) { ERROR_HERE; goto open_error; }

        snd_pcm_hw_params_free (hw);
        return 0;

open_error:
        snd_pcm_hw_params_free (hw);
        snd_pcm_close(phandle);
        phandle = NULL;
        return -1;
    }
    void close(int drain = 0)
    {
        if (!phandle) 
        {
            ll->printf(0, "WARNING: attempt to close already-closed pcm\n");
            return;
        }
        ll->printf(1, "INFO: closing phandle device\n");
        if (drain) snd_pcm_drain(phandle);
        snd_pcm_close(phandle);
        phandle = NULL;
    }
    void prepare()
    {
        if (!phandle)
        {
            ll->printf(0, "ERROR: attempt to prepare a closed pcm\n");
            return;
        }
        if (0 > snd_pcm_prepare(phandle)) { ERROR_HERE; }
    }
    int writebuf(snd_pcm_uframes_t frame_count, short int * frame_data)
    {
        if (!phandle)
        {
            ll->printf(0, "ERROR: attempt to write a closed phandle\n");
            return -1;
        }
        int err = 0;
        while (frame_count > 0) {
            err = snd_pcm_writei (phandle, frame_data, frame_count );
            if (err == (signed)frame_count) return 0; //success
            if (err == -EAGAIN)
                continue;
            if (err < 0)
                break;
            frame_data += err * 4;
            frame_count -= err;
        }

	if (err >= 0)
	{
	    ll->printf(0, "madness on line %s:%i\n", __FILE__, __LINE__);
		return -1;
	}

        const char * msg = NULL;
        snd_pcm_state_t state = snd_pcm_state(phandle);
        switch (state)
        {
            case SND_PCM_STATE_OPEN:    msg = "open"; break;
            case SND_PCM_STATE_SETUP:   msg = "setup"; break;
            case SND_PCM_STATE_PREPARED:msg = "prepared"; break;
            case SND_PCM_STATE_RUNNING: msg = "running"; break;
            case SND_PCM_STATE_XRUN:    msg = "xrun"; break;
            case SND_PCM_STATE_DRAINING: msg = "draining"; break;
            case SND_PCM_STATE_PAUSED:  msg = "paused"; break;
            case SND_PCM_STATE_SUSPENDED: msg = "suspended"; break;
            case SND_PCM_STATE_DISCONNECTED: msg = "disconnected"; break;
        }
        ll->printf(1,  "WARNING: write failed (%s)\tstate = %s\ttime=%lf\n", snd_strerror (err), msg, pytime(NULL));
        if (0 > snd_pcm_recover(phandle, err, 0)) { ERROR_HERE; return err;}
        if (0 > snd_pcm_prepare(phandle))         { ERROR_HERE; return err;}
        return 1; //warning
    }
};
#undef ERROR_HERE

#endif
