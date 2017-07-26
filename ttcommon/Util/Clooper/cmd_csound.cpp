
#include <stdio.h>
#include <csound/csound.hpp>

#include "SoundClient.h"

int main( int argc, char ** argv)
{
    int userInput = 200;
    int rval = sc_initialize(argv[1]);
    sc_setMasterVolume(30.0);

    while ((userInput != 0) && (rval == 0))
    {
        fprintf(stderr, "Enter a pitch\n");
        scanf("%i", &userInput);
        //sc_instrumentLoad(5083, "/home/olpc/tamtam/Resources/Sounds/sitar");
        scanf("%i", &userInput);
    }

    return 0;
}
