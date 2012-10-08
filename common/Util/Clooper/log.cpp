#ifndef LOG_HXX
#define LOG_HXX

#include <stdarg.h>
#include <stdio.h>

struct log_t
{
    FILE * _file;
    int _level;
    int _close;

    log_t(const char * logpath, int level = 0) : _file(NULL), _level(level), _close(1)
    {
        _file = fopen(logpath, "w");
        if (!_file)
        {
            fprintf(stderr, "Failed to open log file for writing: %s\n", logpath);
        }
    }
    log_t(FILE * file, int level = 0): _file(file), _level(level), _close(0)
    {
    }
    ~log_t()
    {
        if (_close && _file) fclose(_file);
    }
    void printf( const char * fmt, ... ) __attribute__(( format (printf, 2,3)))
    {
        if (!_file) return;
        va_list ap;
        va_start(ap,fmt);
        ::vfprintf(_file, fmt, ap);
        va_end(ap);
        fflush(_file);
    }
    void printf( int level, const char * fmt, ... ) __attribute__(( format (printf, 3,4)))
    {
        if (level <= _level)
        {
            if (!_file) return;
            fprintf(_file, "L%i:", level);
            va_list ap;
            va_start(ap,fmt);
            ::vfprintf(_file, fmt, ap);
            va_end(ap);
            fflush(_file);
        }
    }
};

#endif
