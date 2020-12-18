#include "ARMCFunctions.h"

/* ratio vs. speed constant */
/* the larger this constant, the better the compression */
#define MAXCOMPARES 75

/* unused entry flag */
#define NIL       0xFFFF

/* bits per symbol- normally 8 for general purpose compression */
#define CHARBITS  8

/* minimum match length & maximum match length */
#define THRESHOLD 2
#define MATCHBITS 4
#define MAXMATCH  ((1 << MATCHBITS) + THRESHOLD - 1)

/* sliding dictionary size and hash table's size */
/* some combinations of HASHBITS and THRESHOLD values will not work
   correctly because of the way this program hashes strings */
#define DICTBITS  13
#define HASHBITS  10
#define DICTSIZE  (1 << DICTBITS)
#define HASHSIZE  (1 << HASHBITS)

/* # bits to shift after each XOR hash */
/* this constant must be high enough so that only THRESHOLD + 1
   characters are in the hash accumulator at one time */
#define SHIFTBITS ((HASHBITS + THRESHOLD) / (THRESHOLD + 1))

/* sector size constants */
#define SECTORBIT 10
#define SECTORLEN (1 << SECTORBIT)

#define HASHFLAG1 0x8000
#define HASHFLAG2 0x7FFF

/* hash data just entered into dictionary */
/* XOR hashing is used here, but practically any hash function will work */
void HashData(long long *dictposp, long long *bytestodop, long long *nextlink, long long *lastlink, long long *hash, char* dict)
{
  long long i, j, k;
  long long dictpos = *dictposp;
  long long bytestodo = *bytestodop;
  
  dict += sizeof(long long);

  if (bytestodo <= THRESHOLD)   /* not enough bytes in sector for match? */
    for (i = 0; i < bytestodo; i++)
      nextlink[dictpos + i] = lastlink[dictpos + i] = NIL;
  else
  {
    /* matches can't cross sector boundries */
    for (i = bytestodo - THRESHOLD; i < bytestodo; i++)
      nextlink[dictpos + i] = lastlink[dictpos + i] = NIL;

    j = (((long long)dict[dictpos]) << SHIFTBITS) ^ dict[dictpos + 1];

    k = dictpos + bytestodo - THRESHOLD;  /* calculate end of sector */

    for (i = dictpos; i < k; i++)
    {
      lastlink[i] = (j = (((j << SHIFTBITS) & (HASHSIZE - 1)) ^ dict[i + THRESHOLD])) | HASHFLAG1;
      if ((nextlink[i] = hash[j]) != NIL) lastlink[nextlink[i]] = i;
      hash[j] = i;
    }
  }
}
