#!/usr/bin/env python3

# Copyright L. Easy, F. Militello, T. Nicholas, J. Omotani, F. Riva, N.
# Walkden, UKAEA, 2017, 2018
# email: fulvio.militello@ukaea.uk
#
# This file is part of the STORM module of BOUT++.
#
# STORM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# STORM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with STORM.  If not, see <https://www.gnu.org/licenses/>.

from boututils.run_wrapper import shell
import os
import time
from datetime import timedelta

tests = ["test-3d"]
testcommand = "./runtest.py"
retestOption = " --retest t"

def test_filament_3d(numProcs,retest=False):
    global tests,testcommand,retestOption

    start_time = time.monotonic()

    numTests = 0
    numFailures = 0
    failedTests = []
    currentDir = os.getcwd()
    testcommand = testcommand + " " + str(numProcs)
    if retest:
        print("Rechecking results - NOT running test examples")
        testcommand = testcommand+retestOption

    for testdir in tests:
        os.chdir(currentDir)
        os.chdir(testdir)
        s,out = shell(testcommand,pipe=False)
        numTests = numTests+1
        if s is not 0:
            numFailures = numFailures+1
            failedTests.append(testdir)
        print("")

    if numFailures is 0:
        print("All "+str(numTests)+" tests passed")
    else:
        print(str(numFailures)+"/"+str(numTests)+" failed.")
        print("Failed tests:")
        for name in failedTests:
            print("    "+name)

    end_time = time.monotonic()
    print ("Tests took "+str(timedelta(seconds=end_time-start_time)))

if __name__=="__main__":

    import argparse
    from sys import exit

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    def str_to_bool(string):
        return string=="True" or string=="true" or string=="T" or string=="t"
    parser.add_argument("np",type=int)
    parser.add_argument("--retest",default=False)
    args = parser.parse_args()

    test_filament_3d(args.np,args.retest)

    exit(0)
