#!/usr/bin/python

import sys
import os
import time
import subprocess
import ConfigParser

VERBOSE=True


Config = ConfigParser.SafeConfigParser()

Config.read('run-backup.conf')

try:
    backup_sources = dict(Config.items('sources'))
    backup_targets = dict(Config.items('targets'))
    backup_actions = dict(Config.items('actions'))
except ConfigParser.Error:
    print "Config file is incomplete!"


# Get a list of all mounted images
def get_mounted_images():

    # Use hdiutil to find out mounted images
    output = subprocess.check_output("hdiutil info", shell=True)

    # Check each one against our own image filenames
    # TODO: Probably don't need to check here, just list..
    mounted_images = []
    for line in output.splitlines():
        if line.startswith("image-path"):
            for name in backup_sources:
                if line.endswith(backup_sources[name]):
                    mounted_images.append(name)
    
    return mounted_images


# Check if image is mounted
def image_mounted(name):

    # Check if this image name appears in Mounted Images
    if name in get_mounted_images():
        return True
    else:
        return False

def backup_running(_remove=False):
    if _remove is True:
        # Remove the file
        os.remove('/tmp/sparse-backup.lock')
        return False

    # Check that the lockfile does not exist
    if os.path.isfile('/tmp/sparse-backup.lock'):
        return True
    else:
        open('/tmp/sparse-backup.lock', 'w').close()


    return False

# Main routine, to perform the backups
def main():
    for source in backup_actions:

        destinations = backup_actions[source].split(',')

        for dest in destinations:
            print "\033[1;37m" + source + " -> " + dest + "\033[0m"

            if image_mounted(source):
                print "\033[91m    [FAIL]\n\n    Image is currently mounted\033[0m\n"
                continue

            # Check the source is not mounted
            try:
                cmd = backup_sources[source] + ' ' + backup_targets[dest]
            except KeyError:
                print "Backup source or destination does not exist"
                continue;

            _start_time = time.time()

            _p = subprocess.Popen(('rsync', '-avz', '--delete', backup_sources[source], backup_targets[dest]), stdout=subprocess.PIPE,stderr=subprocess.PIPE)

            (stdout, stderr) = _p.communicate()

            _end_time = time.time()
            _runtime = _end_time-_start_time


            if _p.returncode is not 0:
                # An error occurred
                print "\033[1;31m    [FAIL]\n"
                
                #lines = stderr.splitlines()
                
                for line in stderr.splitlines():
                    print "    " + line
            else:
                if _p.returncode is 0 and len(stderr) > 0:
                    # A warning occurred
                    #print "    \033[93m[Warning]\n"

                    lines = stderr.splitlines()
                    
                    for line in lines:
                        print "\033[1;33m    Warning: " + line


                print "    \033[1;32m[Done]\033[0;32m in " + str(round(_runtime, 2)) + " seconds"


            

            if VERBOSE is True:
                print "\033[0;33m"
                for line in stdout.splitlines():
                    print "    Output: " + line

            print "\033[0m"


if __name__ == "__main__":

    if backup_running():
        print "Backup already running (lockfile exists), exiting.."
        sys.exit(10)

    main()

    backup_running(_remove=True)
