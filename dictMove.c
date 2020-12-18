void dictMove(long long *top, long long *fromp, long long *maskp, long long *nump, char *dict)
{
	long long i = *top;
	long long j = *fromp;
	long long mask = *maskp;
	long long k = *nump;

	dict += sizeof(long long);

	do
	{
		dict[i++] = dict[j++];
		j &= mask;
	}
	while (--k);

	*top = i;
	*fromp = j;
}
