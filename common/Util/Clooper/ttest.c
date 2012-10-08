
#include <pthread.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <sys/time.h>

double sleeptime = 0.0;
int usleep(int);
static void * threadfn(void * _arg)
{
    double pytime(const struct timeval * tv)
    {
        return (double) tv->tv_sec + (double) tv->tv_usec / 1000000.0;
    }
    struct timeval tv0, tv1;
    double m = 0.0;

    int loops = 0;

    while (1)
    {
        gettimeofday(&tv0, 0);
        usleep( (int) (sleeptime * 1000000) );
        gettimeofday(&tv1, 0);
        double t0 = pytime(&tv0);
        double t1 = pytime(&tv1);
        if (t1 - t0 > 1.2 * sleeptime)
        {
            fprintf(stderr, "critical lagginess %lf\n", t1 - t0);
        }
        if (m < t1 - t0)
        {
            m = t1 - t0;
            fprintf(stderr, "maximum lag %lf\n", m);
        }

        if ( ( loops % 100 ) == 0 )
        {
            fprintf(stderr, "loop (%lf)\n", t0);
        }
        ++loops;
    }
    return NULL;
}
void testtimer(double st)
{
    pthread_t pth;
    sleeptime = st;

    pthread_create( &pth, NULL, &threadfn, NULL );
}

