#!/usr/bin/env python
#
# cesar dot fazan at gmail dot com
#

import sys, os, zlib
from struct import pack, unpack

if (len(sys.argv) > 1):
	kernel  = sys.argv[1]
	extract = 0
	if (len(sys.argv) > 2):
		if sys.argv[2] == "extract":
			extract = 1
else:
	print "Use: hvfs.py kernelFile [extract]"
	sys.exit(0)

# Function to read a null terminated string
def read_ntstr(f):
	bytes = 1
	str = ""
	chr = f.read(1)
	while ord(chr):
		str += chr
		bytes += 1
		chr = f.read(1)
	return (str, bytes)

# Open file and seach for start of HvFs
f = open(kernel, "rb")
data = bytearray(f.read())
hvfsstart = data.find("HvFs")
print "Skiping to the start of HvFs at %d " % hvfsstart
f.seek(hvfsstart+4)

# Read HvFs header (no. of files, files total size, files start, header crc)
(num_files, total_len, namebase, crc) = unpack("<IIII", f.read(16))

inodes = []
for i in range(num_files):
	inodes.append(unpack("<IIII", f.read(16)))

curpos = 16 + 16 * num_files

# Filesystem ID string
f.seek(namebase - curpos, 1)
(str, bytes) = read_ntstr(f)
curpos += bytes


# Filenames and sizes, null terminated strings
print "%10s %10s %10s Filename" % ("Start", "End", "Filesize")
filenames = []
for (name_off, data_off, file_len, file_flags) in inodes:
	f.seek(name_off - curpos, 1)
	(str, bytes) = read_ntstr(f)
	curpos = name_off + bytes
	filenames.append(str)
	print "%10d %10d %10d %s" % (hvfsstart + data_off + 4, hvfsstart + data_off + file_len + 4, file_len, str)

# Files are not terminated in any way, but extra zeroes are  added to make every file start on a word boundary.

# Get filesystem CRC
# End = hvfsstart + 4 bytes (HvFs Magic num) + Total fs size
fs_end = hvfsstart+total_len+4
f.seek(fs_end)
fs_crc = unpack("<I", f.read(4))

print "Total Files: %d, Total Length: %d,  Total Length inc. header: %d" % (num_files, total_len, total_len + 40)
print "Header CRC: %X" % crc
print "Filesystem CRC: %X" % fs_crc

# Calculated HvFs header CRC
f.seek(hvfsstart)
hvfs_hdrcrc = f.read(16)
hvfs_hdrcrc = zlib.crc32(hvfs_hdrcrc) & 0xffffffff
print "Calc. Header CRC: %X" % hvfs_hdrcrc

# Calculated HvFs filesystem CRC
# crc = total fs size - 4 bytes (hvfs magic num) - 16 HvFs header size
f.seek(hvfsstart+20)
hvfs_fscrc = f.read(fs_end-hvfsstart-20)
hvfs_fscrc = zlib.crc32(hvfs_fscrc) & 0xffffffff
print "Calc. Filesystem CRC: %X" % hvfs_fscrc

f.seek(hvfsstart)
tocopy = total_len + 40

f2 = open("teste",'wb')
while tocopy:
	chunk = min(1024,tocopy)
	data = f.read(chunk)
	f2.write(data)
	tocopy -= chunk
f2.close()

#f.seek(hvfsstart+total_len)
#test = f.read(32)
#print ':'.join(x.encode('hex') for x in test)

# TODO: Extract files
if extract == 1:
	print "\nFile extract not yet implemented ...\n"

# TODO: Inject new kernel, fix HvFs file info, elf

f.close()
