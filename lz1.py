import os.path
import sys
import struct
import pdb

VERSION = "0.1"

#ratio vs. speed constant
#the larger this constant, the better the compression
MAXCOMPARES=75

#unused entry flag
NIL=0xFFFF

#bits per symbol- normally 8 for general purpose compression
CHARBITS=8

#minimum match length & maximum match length
THRESHOLD = 2
MATCHBITS = 4
MAXMATCH = ((1 << MATCHBITS) + THRESHOLD - 1)

#sliding dictionary size and hash table's size
#some combinations of HASHBITS and THRESHOLD values will not work
#correctly because of the way this program hashes strings
DICTBITS  = 13
HASHBITS  = 10
DICTSIZE  = (1 << DICTBITS)
HASHSIZE  = (1 << HASHBITS)

# bits to shift after each XOR hash
# this constant must be high enough so that only THRESHOLD + 1
# characters are in the hash accumulator at one time */
SHIFTBITS = ((HASHBITS + THRESHOLD) // (THRESHOLD + 1))

# sector size constants
SECTORBIT = 10
SECTORLEN = (1 << SECTORBIT)

HASHFLAG1 = 0x8000
HASHFLAG2 = 0x7FFF

ldict = [0]*(DICTSIZE+MAXMATCH)
lhash = [0]*(HASHSIZE+1)
nextlink = [0]*(DICTSIZE+1)
lastlink = [0]*(DICTSIZE+1)

matchlength=0
matchpos=0
bitbuf=0
bitsin=0
masks = [0,1,3,7,15,31,63,127,255,511,1023,2047,4095,8191,16383,32767,65535]

infile = None
outfile = None
inFileSize = 0

def SendBits(bits, numbits):
	"""writes multiple bit codes to the output stream"""
	global bitbuf, bitsin, outfile

	bitbuf |= (bits<<bitsin)
	bitsin += numbits

	if (bitsin>16):
		outfile.write(struct.pack("=B",bitbuf & 0xFF))
		bitbuf = bits >> (8-(bitsin-numbits))
		bitsin -= 8

	while (bitsin >= 8):
		outfile.write(struct.pack("=B",bitbuf & 0xFF))
		bitbuf >>=8
		bitsin -= 8

def ReadBits(numbits):
	"""reads multiple bit codes from the input stream"""
	global bitbuf, bitsin, outfile

	i = bitbuf >> (8 - bitsin)

	while (numbits > bitsin):
		bitbuf = infile.read(1)[0]
		i |= (bitbuf << bitsin)
		bitsin += 8

	bitsin -= numbits

	return (i & masks[numbits])


def SendMatch(matchlen, matchdistance):
	"""sends a match to the output stream"""

	SendBits(1, 1)

	SendBits(matchlen - (THRESHOLD + 1), MATCHBITS)

	SendBits(matchdistance, DICTBITS)


def SendChar(character):
	"""sends one character (or literal) to the output stream"""
	SendBits(0, 1)

	SendBits(character, CHARBITS)


def InitEncode():
	"""initializes the search structures needed for compression"""
	for i in range(HASHSIZE):
		lhash[i] = NIL

	nextlink[DICTSIZE] = NIL


def LoadDict(dictpos):
	"""loads dictionary with characters from the input stream"""

	inbytes = infile.read(SECTORLEN)

	for i in range(len(inbytes)):
		ldict[dictpos+i] = inbytes[i]

	#since the dictionary is a ring buffer, copy the characters at
	#the very start of the dictionary to the end
	if (dictpos == 0):
		for j in range(MAXMATCH):
			ldict[j + DICTSIZE] = ldict[j]

	return len(inbytes)

#deletes data from the dictionary search structures
#this is only done when the number of bytes to be   
#compressed exceeds the dictionary's size         
def DeleteData(dictpos):

	#delete all references to the sector being deleted

	k = dictpos + SECTORLEN

	for i in range(dictpos, k):
		j = lastlink[i]
		if (j & HASHFLAG1):
			if (j != NIL):
				lhash[j & HASHFLAG2] = NIL
		else:
			nextlink[j] = NIL

#hash data just entered into dictionary
#XOR hashing is used here, but practically any hash function will work
def HashData(dictpos, bytestodo):

	if (bytestodo <= THRESHOLD):   #not enough bytes in sector for match?
		for i in range(bytestodo):
			nextlink[dictpos + i] = NIL
			lastlink[dictpos + i] = NIL
	else:
		#matches can't cross sector boundries
		for i in range(bytestodo - THRESHOLD, bytestodo):
			nextlink[dictpos + i] = NIL
			lastlink[dictpos + i] = NIL

		j = (ldict[dictpos] << SHIFTBITS) ^ ldict[dictpos + 1]

		k = dictpos + bytestodo - THRESHOLD #calculate end of sector

		for i in range(dictpos,k):
			j = ((j << SHIFTBITS) & (HASHSIZE - 1)) ^ ldict[i + THRESHOLD]
			lastlink[i] = j | HASHFLAG1
			nextlink[i] = lhash[j]
			if (nextlink[i] != NIL):
				lastlink[nextlink[i]] = i
			lhash[j] = i

#finds match for string at position dictpos
#this search code finds the longest AND closest
#match for the string at dictpos               
def FindMatch(dictpos, startlen):
	global matchlength, matchpos

	i = dictpos
	matchlength = startlen
	k = MAXCOMPARES
	l = ldict[dictpos + matchlength]

	while True:
		i = nextlink[i]
		if (i == NIL):
			return   #get next string in list

		if ldict[i + matchlength] == l:        #possible larger match?
			j=0
			while j<MAXMATCH:
				if ldict[dictpos + j] != ldict[i + j]:
					break
				j+=1

			if j > matchlength:  #found larger match?
				matchlength = j
				matchpos = i
				if matchlength == MAXMATCH:
					return #exit if largest possible match
				l = ldict[dictpos + matchlength]
	
		k -= 1 #keep on trying until we run out of chances
		if k==0:
			break

def DictSearch(dictpos, bytestodo):
	"""finds dictionary matches for characters in current sector"""
	global matchlength, matchpos

	i = dictpos
	j = bytestodo

	while (j!=0): #loop while there are still characters left to be compressed
		FindMatch(i, THRESHOLD)

		if (matchlength > j):
			matchlength = j     #clamp matchlength

		if (matchlength > THRESHOLD):  #valid match?
			SendMatch(matchlength, (i - matchpos) & (DICTSIZE - 1))
			i += matchlength
			j -= matchlength
		else:
			SendChar(ldict[i])
			i+=1
			j-=1


def Encode():
	"""main encoder"""
	global bitsin

	InitEncode()

	dictpos = 0
	deleteflag = 0
	bytescompressed = 0;

	#pdb.set_trace()

	while True:
		#delete old data from dictionary
		if deleteflag: 
			DeleteData(dictpos)

		#grab more data to compress
		sectorlen = LoadDict(dictpos)
		if sectorlen == 0:
			break

		#hash the data
		HashData(dictpos, sectorlen)

		#find dictionary matches
		DictSearch(dictpos, sectorlen)

		bytescompressed += sectorlen

		print('{0}/{1}\r'.format(bytescompressed, inFileSize), end='')

		dictpos += SECTORLEN

		#wrap back to beginning of dictionary when its full
		if dictpos == DICTSIZE:
			dictpos = 0
			deleteflag = 1	#ok to delete now

	#Send EOF flag
	SendMatch(MAXMATCH + 1, 0)

	#Flush bit buffer
	if bitsin!=0:
		SendBits(0, 8 - bitsin)

def Decode():
	"""main decoder"""
	i = 0
	bitsdecompressed = 0

	while True:
		bitsdecompressed += 1

		if (ReadBits(1) == 0):   #character or match?
			bitsdecompressed += CHARBITS
			ldict[i] = ReadBits(CHARBITS)
			i += 1
			if i == DICTSIZE:
				for jj in range(DICTSIZE):
					outfile.write(struct.pack("=B",ldict[jj]))
			
				i = 0
				print('{0}/{1}\r'.format(bitsdecompressed//8, inFileSize), end='')
		else:
			#get match length from input stream
			bitsdecompressed += MATCHBITS
			k = (THRESHOLD + 1) + ReadBits(MATCHBITS)
			if k == (MAXMATCH + 1):      #Check for EOF flag
				for jj in range(i):
					outfile.write(struct.pack("=B",ldict[jj]))
				
				break
			  
			# get match position from input stream 
			bitsdecompressed += DICTBITS
			j = ((i - ReadBits(DICTBITS)) & (DICTSIZE - 1))

			if (i + k) >= DICTSIZE:
				while True:
					ldict[i] = ldict[j]
					i+=1
					j+=1
					j &= (DICTSIZE - 1)
					if i == DICTSIZE:
						for jj in range(DICTSIZE):
							outfile.write(struct.pack("=B",ldict[jj]))
						i = 0
						print('{0}/{1}\r'.format(bitsdecompressed//8, inFileSize), end='')
					k-=1
					if k==0:
						break
			else:
				if (j + k) >= DICTSIZE:
					while True:
						ldict[i] = ldict[j]
						i+=1
						j+=1
						j &= (DICTSIZE - 1)
						k-=1
						if k==0:
							break
				else:
					while True:
						ldict[i] = ldict[j]
						i+=1
						j+=1
						k-=1
						if k==0:
							break
	print('{0}/{1}\r'.format(inFileSize, inFileSize), end='')

def usage():
	print("lz1 e <file> : encode <file> into <file>.lz1")
	print("lz1 d <file>.lz1 : decodes <file>.lz1 t <file>")

if __name__ == "__main__":

	print("LZ77 encoder/decoder V"+VERSION)
	print("By Rich Geldreich (Python port by Epsilon)")

	argc = len(sys.argv)

	if argc != 3:
		usage()
		exit(1)

	action = sys.argv[1].upper()
	if (action != "D") and (action != "E"):
		usage()
		exit(1)

	inFilename = sys.argv[2]
	if not os.path.isfile(inFilename): 
		usage()
		exit(1)

	inFileSize = os.path.getsize(inFilename)

	if action == 'E':
		infile = open(inFilename, 'rb')
		outfile = open(inFilename+".lz1", 'wb')
		Encode()
		infile.close()
		outfile.close()
	else:
		if not inFilename.endswith(".lz1"):
			usage
			exit(1)

		infile = open(inFilename, 'rb')
		outfile = open(os.path.splitext(inFilename)[0], 'wb')
		Decode()
		infile.close()
		outfile.close()