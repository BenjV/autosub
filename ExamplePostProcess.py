#------------------------------------------------------------------------------------------------------------------
# This Script is an example of what is possible with the
# PostProcess feature of Auto-Sub
# It will expect the following arguments from autosub:
# argv[1]: Path + filename of the subtitle file
# argv[2]: Path + filename of the video file
# argv[3]: Language of the subtile
# argv[4]: Name of the Serie
# argv[5]: Season number of the serie 
# argv[6]: Episode number of the serie
#
# This example moves the videofile and the subfile to a different location.
#------------------------------------------------------------------------------------------------------------------

import os, shutil, errno

#---------------------------------------#
# This is the Start of the main program #
#---------------------------------------#

# First we move the parameters we got from autosub to some easy reading names.
SubSpecs     = sys.argv[1]
VideoSpecs   = sys.argv[2]
Language     = sys.argv[3]
SerieName    = sys.argv[4]
SeasonNum    = sys.argv[5]
EpisodeNum   = sys.argv[6]

#-----------------------------------------------------------------------------------------------------------------#
# Put her the part of the foldername(SrtRoot) you want to be replaced with another folder(DstRooT.                #
# Beware, Linux systems are case sensitive!!!                                                                     #
# If you use a '\' character in a string you have to escape it with another '\' and use '\\' insted.              #
#-----------------------------------------------------------------------------------------------------------------#
#SrtRoot = '/volume1/video/series'
#DstRoot = '/volume1/video/tv/shows'
SrtRoot = 'D:\sync\Tv Series'
DstRoot = 'D:\sync\TV\Series'

# here we normalise the path for the current OS
DstRoot      = os.path.normpath(DstRoot)
SrtRoot      = os.path.normpath(SrtRoot)
#-----------------------------------------------------------------------------------------------------------------#
# Here we create the destination folder.
# We catch the error and if it already exitst its fine otherwise we leave
#-----------------------------------------------------------------------------------------------------------------#

try:
    os.makedirs(DstRoot)
except OSError as exception:
    if exception.errno != errno.EEXIST:
        sys.stdout.write('- Could not create destination folder')
        sys.exit(0)
#-----------------------------------------------------------------------------------------------------------------#
# Here we create the destination files specs bij replacing the first part of the spec with a new part
#-----------------------------------------------------------------------------------------------------------------#
DstSubSpecs = SubSpecs.replace(SrtRoot,DstRoot)

# Now we move the subtilefile, if we fail we leave with a error message
try:
    shutil.move(SubSpecs,DstSubSpecs)
except Exception as error:
    sys.stdout.write(error)
    sys.exit(0)

#-----------------------------------------------------------------------------------------------------------------#
# Here we create the destination files specs bij replacing the first part of the spec with a new part
#-----------------------------------------------------------------------------------------------------------------#
DstVideoSpecs = VideoSpecs.replace(SrtRoot,DstRoot)
#-----------------------------------------------------------------------------------------------------------------#
# Now we move the subtilefile, if we fail we leave with a error message
#-----------------------------------------------------------------------------------------------------------------#
try:
    shutil.move(VideoSpecs,DstVideoSpecs)
except Exception as error:
    sys.stdout.write(error)
    sys.exit(0)
sys.stdout.write(" - Postprocess routine finished succesfull")
sys.exit(0)