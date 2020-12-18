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

/* finds match for string at position dictpos     */
/* this search code finds the longest AND closest */
/* match for the string at dictpos                */
void FindMatch(long long *matchlengthp, long long *matchposp, char *dict, long long *nextlink, long long *dictposp)
{
  long long i, j, k, matchlength;
  long long dictpos = *dictposp;
  long long matchpos = *matchposp;
  char l;

  dict += sizeof(long long);

  i = dictpos; matchlength = THRESHOLD; k = MAXCOMPARES;
  l = dict[dictpos + matchlength];

  do
  {
    if ((i = nextlink[i]) == NIL) break;   /* get next string in list */

    if (dict[i + matchlength] == l)        /* possible larger match? */
    {
      for (j = 0; j < MAXMATCH; j++)          /* compare strings */
        if (dict[dictpos + j] != dict[i + j]) break;

      if (j > matchlength)  /* found larger match? */
      {
        matchlength = j;
        matchpos = i;
        if (matchlength == MAXMATCH) break;  /* exit if largest possible match */
        l = dict[dictpos + matchlength];
      }
    }
  }
  while (--k);  /* keep on trying until we run out of chances */

  *matchlengthp = matchlength;
  *matchposp = matchpos;
}
