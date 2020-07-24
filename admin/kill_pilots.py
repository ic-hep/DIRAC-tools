#!/usr/bin/env python
"""at the moment only one value per option is supported"""

from __future__ import print_function

import sys
import DIRAC
from DIRAC import gLogger, S_OK
from DIRAC.Core.Base import Script
from DIRAC.WorkloadManagementSystem.Client.PilotManagerClient import PilotManagerClient

#from DIRAC.Interfaces.API.DiracAdmin import DiracAdmin


class Params(object):
  """
  handles input options for kill_pilots
  """

  def __init__(self):
    """
    creates a Params class with default values
    For 'status' the only allowed options are: Submitted, Scheduled, Unknown, Waiting
    """
    # I'll go back to lists if I allow more than one value for each selector
    # status is special, as the default is a list
    self.status = []
    self.ce = ''
    self.site = ''
    self.vo = ''
    self.dryrun = False

  def addVO(self, voname):
    """
    only pilot jobs from the VO will be deleted
    """
    # self.vo.append(voname)
    self.vo = voname
    return S_OK()
  def addCE(self, cename):
    """
    only pilot jobs submitted to this CE will be deleted
    """
    # self.ce.append(cename)
    self.ce = cename
    return S_OK()

  def addStatus(self, status):
    """
    only pilot jobs in the selected status will be deleted
    """
    self.status.append(status)
    # self.status = status
    return S_OK()

  def addSite(self, site):
    """
    only pilot jobs from the selected site will be deleted
    """
    # self.site.append(site)
    self.site = site
    return S_OK()

  def set_dryrun(self, _):
    """
    allow to check which pilots will be deleted
    """
    self.dryrun = True


  # note the magic : and =
  def registerCLISwitches(self):
    """
    add options to dirac option parser
    """
    Script.setUsageMessage("Script to kill pilot jobs."
                           "Pilots in Running, Done or Failed states will be ignored."
                           "You must choose at least one (or two if you specify 'status') option.")
    # apparently short switch 'c' and 's' already defined, maybe just not use short switches at all ?
    # ':' means only one parameter allowed, but I want more ?
    Script.registerSwitch("v:", "vo=", "delete pilots jobs for this VO only", self.addVO)
    Script.registerSwitch("C:", "ce=", "delete pilots jobs for this CE only", self.addCE)
    Script.registerSwitch("S:", "site=", "delete pilots jobs for this Site only", self.addSite)
    Script.registerSwitch("T", "status=", "delete pilots jobs in this Status only", self.addStatus)
    Script.registerSwitch("D", "dryrun", "lists pilots to be deleted, but does not delete them", self.set_dryrun)

def main():
  """reads in the options and deletes the matching pilots"""
  options = Params()
  options.registerCLISwitches()
  Script.parseCommandLine(ignoreErrors=True)
  # make sure *something* is set
  if not options.site and not options.ce and  not options.vo and not options.status:
    print("You must chose at least one of the following options: --vo, --ce --site")


  # occasionally the same job might appear twice, but that shouldn't matter
  conditions = {}
  if options.status:
    conditions["Status"] = options.status[0]
  else:
    conditions["Status"] = ["Submitted", "Scheduled", "Waiting", "Unknown"]

  if options.site:
    conditions["GridSite"] = options.site

  if options.ce:
    conditions["DestinationSite"] = options.ce

  if options.vo:
    pilotstring = options.vo + "_pilot"
    conditions["OwnerGroup"] = pilotstring

  # conditions = {"Status":"Submitted", "GridSite":"LCG.UKI-LT2-IC-HEP.uk",
  #               "OwnerGroup":["lz_pilot", "gridpp_pilot"], "DestinationSite":"ceprod00.grid.hep.ph.ic.ac.uk"}
  print("Selecting pilots fulfulling the following conditions: %s" %conditions)

  pilotmanager = PilotManagerClient()
  result = pilotmanager.selectPilots(conditions)

  if not result['Value']:
    print("No pilots matching these criteria were found.")
    sys.exit(0)

  print("Found the following matching pilots:")
  for pilotRef in result['Value']:
    print(pilotRef)

  if options.dryrun:
    print("Dry run only. No pilots will be deleted")
    sys.exit(0)


  # now get the pilot references and delete them

  from DIRAC.Interfaces.API.DiracAdmin import DiracAdmin
  diracAdmin = DiracAdmin()

  for pilotRef in result['Value']:
    result = diracAdmin.killPilot(pilotRef)
    if not result['OK']:
      print("Error encountered when deleting pilot %s" %pilotRef)
      print(result)


if __name__ == "__main__":
  main()
