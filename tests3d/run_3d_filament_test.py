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

from boutdata.data import BoutOutputs, BoutOptionsFile
from boututils.datafile import DataFile
from boututils.run_wrapper import launch
from boutdata import restart
import numpy
import os
import glob
import time
from datetime import datetime, timedelta

tolerance = 1.e-11
abs_tolerance = tolerance

testname = os.path.basename(os.getcwd())
runOutputDir = "data"
runOutput = os.path.join(runOutputDir,"BOUT.dmp.*")
runExpectedOutput = os.path.join(runOutputDir,"expectedResults","BOUT.dmp.nc")
executable = "../../storm3d/storm"

def test(numProcs,retestOutput=False):

    start_time = time.monotonic()

    print("***************************************")
    print(testname)
    print("testing at "+str(datetime.now()))
    print("***************************************")

    if not retestOutput:
        s = run_test(numProcs)
        if s is not 0:
            print("Error: simulation run failed")
            return 1,1

    numFailures,numTests = check_test()

    end_time = time.monotonic()
    print ("Test took "+str(timedelta(seconds=end_time-start_time)))

    return numFailures,numTests

def run_test(numProcs):
    # Run the simulation

    # Remove existing output files
    for filename in glob.glob(runOutput):
        os.remove(filename)

    print("Running simulation on "+str(numProcs)+" processors")

    # Read nxpe (number of processors in x direction) to pass to restart.redistribute, if present in BOUT.inp
    options = BoutOptionsFile(os.path.join(runOutputDir,"BOUT.inp"))
    try:
        nxpe = options["nxpe"]
    except KeyError:
        nxpe = None

    # prepare restart files
    restart.redistribute(numProcs,nxpe=nxpe,path=os.path.join(runOutputDir,"restart"),output=runOutputDir)
    
    # run simulation
    print("running: "+executable)
    s,out = launch(executable,nproc=numProcs,output="test_run.log")

    return s

def check_test():

    print("Checking output")

    numFailures = 0
    numTests = 0
    try:
        run = BoutOutputs(runOutputDir, info=False, yguards=True)
    except TypeError:
        # Option not implemented in boutdata.data
        run = BoutOutputs(runOutputDir, yguards=True)
    runExpected = DataFile(runExpectedOutput)

    # Get number of guard cells
    m_guards = (run["MXG"], run["MYG"])
    m_guards_expected = (runExpected["MXG"], runExpected["MYG"])

    # Get names of evolving variables, which we will test
    try:
        evolvingVariables = run.evolvingVariables()
    except AttributeError:
        # This part should be deleted once BOUT++ repo is updated so that the above works everywhere
        print("Warning: Updated boutdata.data not found")
        from get_evolving_fields import get_evolving_fields
        evolvingVariables = get_evolving_fields(run)

    # Test output
    for name in evolvingVariables:
        if len(run[name].shape) == 1:
            # scalars are diagnostic outputs like wall-time, so not useful to test
            continue
        # exclude second x guard cells as they are not used and may not always be set consistently
        data = testfield_slice(run[name], m_guards)
        expectedData = testfield_slice(runExpected.read(name), m_guards_expected)
        diff_max,norm_max = testfield_max(data,expectedData)
        numTests = numTests+1
        if diff_max/norm_max>tolerance and diff_max>abs_tolerance:
            numFailures = numFailures+1
            print("FAILURE: Test of max error "+str(numTests)+" ("+name+") failed, with diff_max/norm_max="+str(diff_max/norm_max)+" and diff_max="+str(diff_max))
        else:
            print("Test of max error "+str(numTests)+" ("+name+") passed, with diff_max/norm_max="+str(diff_max/norm_max)+" and diff_max="+str(diff_max))
        diff_mean,norm_mean = testfield_mean(data,expectedData)
        print("Test of mean error "+str(numTests)+" ("+name+") diff_mean/norm_mean="+str(diff_mean/norm_mean)+" and diff_mean="+str(diff_mean))

    print(str(numTests-numFailures)+"/"+str(numTests)+" tests passed in "+testname)

    return numFailures,numTests

def testfield_slice(data, m_guards):
    # Restrict data to valid, consistently set indices

    # Zero corner guard cells
    mxg, myg = m_guards
    data[:,:mxg,:myg,:] = 0.
    data[:,:mxg,-myg:,:] = 0.
    data[:,-mxg:,:myg,:] = 0.
    data[:,-mxg:,-myg:,:] = 0.

    # Only test first x-guard cells
    # (because phi only has the first guard cells set)
    xstart = mxg-1 if mxg-1>0 else None
    data = data[:,xstart:-xstart,:,:]

    return data

def testfield_max(data,expectedData):
    norm = numpy.sqrt(expectedData**2).mean()
    if norm==0.:
        norm==1.
    diff = numpy.sqrt(((data-expectedData)**2).max())
    return diff,norm

def testfield_mean(data,expectedData):
    norm = numpy.sqrt(expectedData**2).mean()
    if norm==0.:
        norm==1.
    diff = numpy.sqrt(((data-expectedData)**2).mean())
    return diff,norm

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

    numFailures,numTests = test(args.np,retestOutput=args.retest)
    exit(numFailures)
