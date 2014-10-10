#!/usr/bin/python

import os
import sys
import shutil
import socket
import string
import random
import getpass
from subprocess import Popen, PIPE

# Some things that won't change often.
DIRAC_BRANCH="rel-v6r12"
DIRACWEB_BRANCH="v1r3p7"
DIRACGRIDPP_BRANCH="master"

# We keep a dictionary of all our parameters for this install
# This gets more parameters added as the install progresses.
PARAMETERS={ "DIRAC_BRANCH": DIRAC_BRANCH,
             "DIRACWEB_BRANCH": DIRACWEB_BRANCH,
             "DIRACGRIDPP_BRANCH": DIRACGRIDPP_BRANCH,
             "USERNAME": getpass.getuser(),
             "HOSTNAME": socket.gethostname(),
             "CADIR": "/etc/grid-security/certificates",
             "VOMSDIR": "/etc/grid-security/vomsdir",
             "HOSTCERT": os.path.expanduser("~/.globus/hostcert.pem"),
             "HOSTKEY": os.path.expanduser("~/.globus/hostkey.pem"),
             "USERCERT": os.path.expanduser("~/.globus/usercert.pem"),
             "USERKEY": os.path.expanduser("~/.globus/userkey.pem"),
           }

def prompt_user(prompt="Continue?"):
  """ Prompt the user to continue, return true if they say to continue,
      false otherwise.
  """
  while True:
    s = raw_input("%s [Y/n] " % prompt).lower()
    if not len(s):
      return True # Default response
    if s[0] == "y":
      return True
    elif s[0] == "n":
      return False
    # All other answers are bad... Try again...

def simple_run(cmd, warn_run=False, shell=False):
  """ Runs a command and exits on error.
      Command output gets sent to the console.
  """
  proc = Popen(cmd, shell=shell)
  proc.wait()
  if proc.returncode:
    print "ERROR: %s failed. Check output above." % cmd[0]
    if warn_run:
      print "NOTE: Processes may have been left running at this point."
    print "Full Cmd: %s" % str(cmd)
    sys.exit(0)


# Check input parameters
if len(sys.argv) != 3:
  print ""
  print "Usage: dirac_in_a_box.py <install_dir> <git_url>"
  print "  <install_dir> is the target root directory for dirac."
  print "  <git_url> is the top URL to check the code from."
  print " i.e. install_diracdev.py ~/dirac https://github.com/DIRACGrid"
  print " (Note DIRAC.git and DIRACWeb.git will be appended to git_url)."
  print ""
  sys.exit(0)
tmp_path = os.path.expanduser(sys.argv[1])
install_path = os.path.realpath(tmp_path)
PARAMETERS["TARGET_DIR"] = install_path
PARAMETERS["DIRAC_URL"] = "%s/%s" % (sys.argv[2], "DIRAC.git")
PARAMETERS["DIRACWEB_URL"] = "%s/%s" % (sys.argv[2], "DIRACWeb.git")
PARAMETERS["DIRACGRIDPP_URL"] = "%s/%s" % (sys.argv[2], "GridPPDIRAC.git")
PARAMETERS["INSTALL_CONF"] = os.path.join(install_path, "etc/dinstall.cfg")

print "\n\n[0/7] Checking Prerequisites..."
## Check git is installed
if not os.path.exists("/usr/bin/git"):
  print "ERROR: git is required, but not found"
  sys.exit(0)
## Check install path is real and final dir doesn't exist.
base_path, _ = os.path.split(PARAMETERS["TARGET_DIR"])
if not os.path.isdir(base_path):
  print "ERROR: TARGET_DIR parent does not exist."
  sys.exit(0)
if os.path.exists(PARAMETERS["TARGET_DIR"]):
  if len(os.listdir(PARAMETERS["TARGET_DIR"])):
    print "ERROR: TARGET_DIR (%s) isn't empty?" % PARAMETERS["TARGET_DIR"]
    print " You should remove this so we can start from scratch."
    sys.exit(0)
## Now we can check key accessibility
for key_name in ("HOSTCERT", "HOSTKEY", "USERCERT", "USERKEY"):
  key_path = PARAMETERS[key_name]
  if not os.access(key_path, os.R_OK):
    print "ERROR: Can't access the %s at %s." % (key_name, key_path)
    print "This should be accessible by the current user."
    sys.exit(0)
## Get the DNs from the certificates...
for cert_name in ("HOSTCERT", "USERCERT"):
  cert_path = PARAMETERS[cert_name]
  ssl_cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-subject" ]
  proc = Popen(ssl_cmd, stdout=PIPE, stderr=PIPE)
  subject_tmp, subject_err = proc.communicate()
  if proc.returncode:
    print "Failed to get %s DN from %s?" % (cert_name, cert_path)
    print "Possible error string: %s" % subject_err.strip()
    sys.exit(0)
  # subject_tmp has the DN in "subject= /some/dn" form, we just want the DN
  subject = " ".join(subject_tmp.split(" ")[1:])
  PARAMETERS["%s_DN" % cert_name] = subject.strip()
## Check the certificates and vomses dirs contain things
for dir_name in ("CADIR", "VOMSDIR"):
  dir_path = PARAMETERS[dir_name]
  if len(os.listdir(dir_path)) < 10:
    print "WARNING: %s (%s) contains less than 10 entries." % \
            (dir_name, dir_path)
    print " This is probably an error."
    if not prompt_user("Continue anyway?"):
      sys.exit(0)
## Extra safety checks
if os.path.exists("/etc/my.cnf"):
  print "ERROR: /etc/my.cnf exists. This will break DIRAC's built-in mysql."
  sys.exit(0)
if not os.path.exists("/usr/bin/voms-proxy-init") or \
   not os.path.exists("/etc/emi-release"):
  print "ERROR: This machine doesn't seem to have an EMI UI installed."
  sys.exit(0)
if "DIRAC" in os.environ:
  print "ERROR: Your environment already contains 'DIRAC'."
  print " You should start with a clean environment."
  sys.exit(0)
## Here's a good one that just wasted a few hours of my life:
## If the user dirac is running as can read /etc/grid-security/hostkey.pem
## Then globus-url-copy uses that, and you can't get the PilotOutput
## This is probably a bug in the globus-url-copy tool for ignoring the user.
if os.access("/etc/grid-security/hostkey.pem", os.R_OK):
  print "ERROR: /etc/grid-security/hostkey.pem is readable by this user."
  print " This breaks the fetching of job outputs."
  print " (See the comments by this error in script for full details.)"
  sys.exit(0)
## Check there is enough space...
target_base, _ = os.path.split(PARAMETERS["TARGET_DIR"])
fs_stat = os.statvfs(target_base)
MIN_SPACE = 2147483648 # 2GiB
if fs_stat.f_bavail * fs_stat.f_bsize < MIN_SPACE:
  print "WARNING: Target directory has less than 2G of space."
  print "         This probably isn't enough to run DIRAC successfully."
  if not prompt_user():
    sys.exit(0)


# Print a summary of what we're going to do
print """
*** Install Summary ***
 Target Dir: %(TARGET_DIR)s
 CA Dir: %(CADIR)s
 VOMS Dir: %(VOMSDIR)s
 Username: %(USERNAME)s
 Hostname: %(HOSTNAME)s
 Your DN: %(USERCERT_DN)s
 Host DN: %(HOSTCERT_DN)s
 DIRAC code URL: %(DIRAC_URL)s
 DIRAC Branch: %(DIRAC_BRANCH)s
 DIRACWeb code URL: %(DIRACWEB_URL)s
 DIRACWeb Branch: %(DIRACWEB_BRANCH)s
 DIRACGridPP code URL: %(DIRACGRIDPP_URL)s
 DIRACGridPP Branch: %(DIRACGRIDPP_BRANCH)s
""" % PARAMETERS
if not prompt_user():
  sys.exit(0)

print "\n\n[1/7] Checking Out Code..."
# Make our directory and chdir into it
if not os.path.exists(PARAMETERS["TARGET_DIR"]):
  os.mkdir(PARAMETERS["TARGET_DIR"])
os.chdir(PARAMETERS["TARGET_DIR"])
# Check out the code
for code_name, code_target in (("DIRAC", "DIRAC"), \
                               ("DIRACWEB", "Web"), \
                               ("DIRACGRIDPP", "GridPPDIRAC")):
  code_url = PARAMETERS["%s_URL" % code_name]
  code_branch = PARAMETERS["%s_BRANCH" % code_name]
  code_path = os.path.join(PARAMETERS["TARGET_DIR"], code_target)
  git_cmd = [ "git", "clone", code_url, code_path ]
  simple_run(git_cmd)
  # Switch to the correct branch
  git_cmd = [ "git", "--git-dir=%s" % os.path.join(code_path, ".git"), \
              "--work-tree=%s" % code_path, \
              "checkout", code_branch ]
  simple_run(git_cmd)
# Now we can create the scripts directory and source bashrc in this session
simple_run(["DIRAC/Core/scripts/dirac-deploy-scripts.py"])


print "\n\n[2/7] Creating DIRAC config..."
# Create the etc dir
target_dir = PARAMETERS["TARGET_DIR"]
etc_dir = os.path.join(target_dir, "etc")
gridsec_dir = os.path.join(etc_dir, "grid-security")
os.mkdir(etc_dir)
os.mkdir(gridsec_dir)
# Host cert/key
shutil.copy(PARAMETERS["HOSTCERT"], os.path.join(gridsec_dir, "hostcert.pem"))
shutil.copy(PARAMETERS["HOSTKEY"], os.path.join(gridsec_dir, "hostkey.pem"))
os.symlink(PARAMETERS["CADIR"], os.path.join(gridsec_dir, "certificates"))
os.symlink(PARAMETERS["VOMSDIR"], os.path.join(gridsec_dir, "vomsdir"))
# Generate some database passwords
for pass_name in ("MYSQL_USER_PASS", "MYSQL_ROOT_PASS"):
  charset = string.ascii_letters + string.digits
  PARAMETERS[pass_name] = ''.join(random.choice(charset) for _ in range(12))
# Now create an installation config
dirac_cfg = """
LocalInstallation
{
  Release = integration
  PythonVersion = 26
  InstallType = server
  UseVersionsDir = no
  TargetPath = %(TARGET_DIR)s
  ExtraModules = Web, GridPP
  SiteName = DEV.DIRAC
  Setup = Development
  InstanceName = Devel
  SkipCADownload = yes
  UseServerCertificate = yes
  ConfigurationName = DevelConfig
  AdminUserName = dirac_host
  AdminUserDN = %(HOSTCERT_DN)s
  AdminUserEmail = %(USERNAME)s@%(HOSTNAME)s
  AdminGroupName = dirac_admin
  HostDN = %(HOSTCERT_DN)s
  ConfigurationMaster = yes
  Host = %(HOSTNAME)s
  Services  = Configuration/Server
  Services += Framework/SystemAdministrator
  Services += DataManagement/StorageElement
  Services += DataManagement/FileCatalog
  Services += Framework/SystemLoggingReport
  Services += Framework/Monitoring
  Services += Framework/Notification
  Services += Framework/SecurityLogging
  Services += Framework/UserProfileManager
  Services += Framework/ProxyManager
  Services += Framework/SystemLogging
  Services += Framework/Plotting
  Services += Framework/BundleDelivery
  Services += WorkloadManagement/SandboxStore
  Services += WorkloadManagement/Matcher
  Services += WorkloadManagement/JobMonitoring
  Services += WorkloadManagement/JobManager
  Services += WorkloadManagement/JobStateUpdate
  Services += WorkloadManagement/WMSAdministrator
  Services += WorkloadManagement/OptimizationMind
  Services += RequestManagement/ReqManager
  Services += Accounting/DataStore
  Services += Accounting/ReportGenerator
  Agents  = Framework/SystemLoggingDBCleaner
  Agents += Framework/TopErrorMessagesReporter
  Agents += WorkloadManagement/PilotStatusAgent
  Agents += WorkloadManagement/JobHistoryAgent
  Agents += WorkloadManagement/SiteDirector
  Agents += WorkloadManagement/InputDataAgent
  Agents += WorkloadManagement/TaskQueueDirector
  Agents += WorkloadManagement/JobCleaningAgent
  Agents += WorkloadManagement/StalledJobAgent
  Agents += RequestManagement/RequestExecutingAgent
  Agents += RequestManagement/CleanReqDBAgent
  Agents += WorkloadManagement/StatesAccountingAgent
  Agents += WorkloadManagement/PilotMonitorAgent
  Databases  = AccountingDB
  Databases += SandboxMetadataDB
  Databases += JobDB
  Databases += FileCatalogDB
  Databases += JobLoggingDB
  Databases += UserProfileDB
  Databases += TaskQueueDB
  Databases += NotificationDB
  Databases += ReqDB
  Databases += FTSDB
  Databases += ComponentMonitoringDB
  Databases += ProxyDB
  Databases += PilotAgentsDB
  Databases += SystemLoggingDB
  Executors = WorkloadManagement/Optimizers
  WebPortal = yes
  Database
  {
    User = Dirac 
    Password = %(MYSQL_USER_PASS)s
    RootPwd = %(MYSQL_ROOT_PASS)s
    Host = localhost
    MySQLLargeMem = no
  }
}
""" % PARAMETERS
install_file = PARAMETERS["INSTALL_CONF"]
fd = open(install_file, "w")
fd.write(dirac_cfg)
fd.close()


print "\n\n[3/7] Installing Pre-built Prerequisites..."
simple_run([ "scripts/dirac-install", "-X", PARAMETERS["INSTALL_CONF"] ])
# We have to "source" the bashrc now.
# This is a bit of a hassle to do as we're in python not bash.
# There are some pickle tricks to do this, but python changes on source bashrc.
# We'll do it the slightly more tedious way:
source_cmd = [ "/bin/bash", "-c", "source bashrc && env" ]
proc = Popen(source_cmd, stdout=PIPE)
vars_out, _ = proc.communicate()
if proc.returncode:
  print "ERROR: Failed to source bashrc. Check output above."
  sys.exit(0)
# Get the vars from the output
for var in vars_out.split("\n"):
  var_name, _, var_value = var.partition("=")
  os.environ[var_name] = var_value

# DIRACWeb also has prerequisites, but the install script is broken.
# It uses a URL that's no longer valid. We'll download the tarball for it,
# using a working mirror...
os.mkdir("Web/tarballs/down")
wget_cmd = ["wget", "-O", "Web/tarballs/down/ext-4.0.2a-gpl.zip", \
            "http://distcache.freebsd.org/ports-distfiles/ext-4.0.2a-gpl.zip"]
simple_run(wget_cmd)
simple_run(["Web/dirac-postInstall.py"])
simple_run(["Web/givePerm.sh"])


print "\n\n[4/7] Configuring DIRAC install & Database..."
# Do the base dirac install config
simple_run([ "scripts/dirac-configure", "-F", PARAMETERS["INSTALL_CONF"] ])
# Install the DB
simple_run(["scripts/dirac-install-mysql"], True)


print "\n\n[5/7] Installing DIRAC..."
# DIRAC setup site has a habit of getting stuck
# We have to patch this... We'll probably merge this as one of our fixes.
fd = open("DIRAC/Core/scripts/dirac-setup-site.py", "a")
fd.write("\n\nimport os\nos._exit( 0 )\n")
fd.close()
simple_run(["scripts/dirac-setup-site"], True)
# Undo our patch so the git repo is clean
code_path = os.path.join(PARAMETERS["TARGET_DIR"], "DIRAC")
git_cmd = [ "git", "--git-dir=%s" % os.path.join(code_path, ".git"), \
            "--work-tree=%s" % code_path, \
            "reset", "--hard" ]
simple_run(git_cmd, True)


print "\n\n[6/7] Loading DIRAC Config..."
# First we need to write out config template
# We'll do a generic "Imperial & CERN Set-up"
main_cfg = """
DIRAC
{
  Extensions = GridPP
}
Registry
{
  DefaultGroup = dteam_user, user
  Users
  {
    dirac
    {
      DN = %(USERCERT_DN)s
      Email = %(USERNAME)s@%(HOSTNAME)s
    }
  }
  Groups
  {
    user
    {
      Users = dirac_host
      Users += dirac
    }
    dirac_admin
    {
      Users = dirac_host
      Users += dirac
    }
    dteam_user
    {
      Users = dirac
      Properties = NormalUser
      VOMSRole = /dteam
      VOMSVO = dteam
      VO = dteam
      SubmitPool = Pool_dteam
      AutoAddVOMS = True
      AutoUploadProxy = True
      AutoUploadPilotProxy = True
    }
    dteam_pilot
    {
      Users = dirac
      Properties = LimitedDelegation
      Properties += GenericPilot
      Properties += Pilot
      VOMSVO = dteam
      VOMSRole = /dteam
      VO = dteam
    }
  }
  VO
  {
    dteam
    {
      SubmitPools = Pool_dteam
      VOAdmin = dirac
      VOMSName = dteam
      VOMSServers
      {
        voms.hellasgrid.gr
        {
          DN = /C=GR/O=HellasGrid/OU=hellasgrid.gr/CN=voms.hellasgrid.gr
          CA = /C=GR/O=HellasGrid/OU=Certification Authorities/CN=HellasGrid CA 2006
          Port = 15004
        }
        voms2.hellasgrid.gr
        {
          DN = /C=GR/O=HellasGrid/OU=hellasgrid.gr/CN=voms2.hellasgrid.gr
          CA = /C=GR/O=HellasGrid/OU=Certification Authorities/CN=HellasGrid CA 2006
          Port = 15004
        }
      }
    }
  } 
  VOMS
  {
    Mapping
    {
      dteam_user = /dteam
    }
    Servers
    {
      dteam
      {
        voms.hellasgrid.gr
        {
          DN = /C=GR/O=HellasGrid/OU=hellasgrid.gr/CN=voms.hellasgrid.gr
          CA = /C=GR/O=HellasGrid/OU=Certification Authorities/CN=HellasGrid CA 2006
          Port = 15004
        }
        voms2.hellasgrid.gr
        {
          DN = /C=GR/O=HellasGrid/OU=hellasgrid.gr/CN=voms2.hellasgrid.gr
          CA = /C=GR/O=HellasGrid/OU=Certification Authorities/CN=HellasGrid CA 2006
          Port = 15004
        }
      }
    }
    URLs
    {
      VOMSAdmin = https://voms.hellasgrid.gr:8443/voms/dteam/services/VOMSAdmin
      VOMSAttributes = https://voms.hellasgrid.gr:8443/voms/dteam/services/VOMSAttributes
    }
  }
}
Systems
{
  WorkloadManagement
  {
    Devel
    {
      Services
      {
        SandboxStore
        {
          BasePath = %(TARGET_DIR)s/storage/sandboxes
        }
      }
      Agents
      {
        PilotStatusAgent
        {
          GridEnv = /etc/profile.d/grid-env
        }
        SiteDirector
        {
          ExtraPilotOptions = -u http://homes.hep.ph.ic.ac.uk/~sf105/dirac/installSource -t https://github.com/ic-hep/DIRAC.git -t https://github.com/ic-hep/GridPPDIRAC.git
        }
        SiteDirectorDteam
        {
          Community = dteam
          Module = SiteDirector
          LogLevel = DEBUG
        }
      }
    }
  }
}
Operations
{
  Development
  {
    Pilot
    {
      Version = v6r12-pre18
    }
  }
  dteam
  {
    Development
    {
      Pilot
      {
        GenericPilotGroup = dteam_pilot
        GenericPilotDN = %(USERCERT_DN)s
      }
      Shifter
      {
        SAMManager
        {
          User = dirac
          Group = dteam_user
        }
        ProductionManager
        {
          User = dirac
          Group = dteam_user
        }
        DataManager
        {
          User = dirac
          Group = dteam_user
        }
      }
      Services
      {
        Catalogs
        {
          FileCatalog
          {
            AccessType = ReadWrite
            Status = Active
          }
        }
      }
    }
  }
  Defaults
  {
    Shifter
    {
      TestManager
      {
        User = dirac
        Group = dteam_user
      }
    }
  }

  JobDescription
  {
    AllowedJobTypes = User
    AllowedJobTypes += Test
    SubmitPools = Pool_dteam
  }
}
Resources
{
  FileCatalogs
  {
    FileCatalog
    {
      AccessType = ReadWrite
      Status = Active
    }
    IMPERIAL-lfc
    {
      MasterHost = lfc00.grid.hep.ph.ic.ac.uk
      CatalogType = LcgFileCatalog
      AccessType = Read-Write
      LcgGfalInfosys = topbdii.grid.hep.ph.ic.ac.uk
      Status = InActive
    }
  }
  StorageElements
  {
    DefaultProtocols = file
    DefaultProtocols += xroot
    DefaultProtocols += root
    DefaultProtocols += dcap
    DefaultProtocols += gsidcap
    DefaultProtocols += rfio
    ProductionSandboxSE
    {
      BackendType = DISET
      ReadAccess = Active
      WriteAccess = Active
      AccessProtocol.1
      {
        Host = %(HOSTNAME)s
        Port = 9196
        ProtocolName = DIP
        Protocol = dips
        Path = /WorkloadManagement/SandboxStore
        Access = remote
      }
    }
    IMPERIAL-disk
    {
      BackendType = dcache
      DiskCacheTB = 20
      DiskCacheTBSave = 20
      AccessProtocol.1
      {
        Host = gfe02.grid.hep.ph.ic.ac.uk
        Port = 8443
        ProtocolName = SRM2
        Protocol = srm
        Path = /pnfs/hep.ph.ic.ac.uk/data/dteam
        Access = remote
        WSUrl = /srm/managerv2?SFN=
      }
    }
    OXFORD-disk
    {
      BackendType = dpm
      DiskCacheTB = 20
      DiskCacheTBSave = 20
      AccessProtocol.1
      {
        Host = t2se01.physics.ox.ac.uk
        Port = 8446
        ProtocolName = SRM2
        Protocol = srm
        Path = /dpm/physics.ox.ac.uk/home/dteam
        Access = remote
        WSUrl = /srm/managerv2?SFN=
      }
    }
    CERN-disk
    {
      BackendType = castor
      DiskCacheTB = 20
      DiskCacheTBSave = 20
      AccessProtocol.1
      {
        Host = srm-public.cern.ch
        Port =  8443
        ProtocolName = SRM2
        Protocol = srm
        Path = /castor/cern.ch/grid/dteam/
        Access = remote
        WSUrl = /srm/managerv2?SFN=
      }
    }
  }
  StorageElementGroups
  {
    SE-USER = IMPERIAL-disk
  }
  Sites
  {
    LCG
    {
      LCG.UKI-LT2-IC-HEP.uk
      {
        CE = ceprod05.grid.hep.ph.ic.ac.uk
        CE += cetest02.grid.hep.ph.ic.ac.uk
        SE = IMPERIAL-disk
        Name = UKI-LT2-IC-HEP
        CEs
        {
          cetest02.grid.hep.ph.ic.ac.uk
          {
            wnTmpDir = /tmp
            architecture = x86_64
            OS = CentOS_0_0
            SI00 = 2075
            Pilot = True
            CEType = ARC
            SubmissionMode = Direct
            JobListFile = cetest02.grid.hep.ph.ic.ac.uk-jobs.xml
            Queues
            {
              nordugrid-Condor-condor
              {
                maxCPUTime = 0
                SI00 = 2160
                MaxTotalJobs = 4000
                WaitingToRunningRatio = 10
                VO = dteam
                VO += vo.londongrid.ac.uk
              }
            }
          }
          ceprod05.grid.hep.ph.ic.ac.uk
          {
            wnTmpDir = /tmp
            architecture = x86_64
            OS = CentOS_Final_6.5
            SI00 = 2250
            Pilot = True
            CEType = CREAM
            SubmissionMode = Direct
            Queues
            {
              cream-sge-grid.q
              {
                maxCPUTime = 2880
                SI00 = 2250
                MaxTotalJobs = 4000
                WaitingToRunningRatio = 10
                VO = dteam
                VO += vo.londongrid.ac.uk
              }
            }
          }
        }
        Coordinates = -0.17897:51.49945
        Mail = lcg-site-admin@imperial.ac.uk
      }
      LCG.UKI-SOUTHGRID-OX-HEP.uk
      {
        CE = t2arc00.physics.ox.ac.uk
        SE = OXFORD-disk
        Name = UKI-SOUTHGRID-OX-HEP
        CEs
        {
          t2arc00.physics.ox.ac.uk
          {
            wnTmpDir = /tmp
            architecture = x86_64
            OS = ScientificSL_Carbon_6.5
            SI00 = 2370
            Pilot = True
            CEType = ARC
            SubmissionMode = Direct
            JobListFile = t2arc00.physics.ox.ac.uk-jobs.xml
            Queues
            {
              nordugrid-Condor-condorDEV
              {
                maxCPUTime = 0
                SI00 = 2370
                MaxTotalJobs = 4000
                WaitingToRunningRatio = 10
                VO = dteam
              }
            }
          }
        }
        Coordinates = -1.304756:51.818076
        Mail = lcg_manager@physics.ox.ac.uk
      }
      LCG.CERN-TEST.ch
      {
        CE = ce403.cern.ch
        CE += ce404.cern.ch
        SE = CERN-disk
        Name = CERN-PROD
        CEs
        {
          ce403.cern.ch
          {
             wnTmpDir = /tmp
             architecture = x86_64
             OS = CentOS_Final_6.4
             SI00 = 2125
             Pilot = True
             CEType = CREAM
             SubmissionMode = Direct
             Queues
            {
              cream-lsf-grid_dteam
              {
                maxCPUTime = 2880
                SI00 = 2125
                MaxTotalJobs = 4000
                WaitingToRunningRatio = 10
                VO = dteam
              }
            }
         }
         ce404.cern.ch
          {
            wnTmpDir = /tmp
            architecture = x86_64
            OS = CentOS_Final_6.4
            SI00 = 2125
            Pilot = True
            CEType = CREAM
            SubmissionMode = Direct
            Queues
            {
              cream-lsf-grid_dteam
              {
                maxCPUTime = 2880
                SI00 = 2125
                MaxTotalJobs = 4000
                WaitingToRunningRatio = 10
                VO = dteam
              }
            }
          }
         }
        }
    }
  }
  Computing
  {
    OSCompatibility
    {
      x86_64-slc6-gcc46-opt = x86_64-slc6-gcc46-opt
      x86_64-slc6-gcc46-opt += x86_64-slc5-gcc43-opt
      x86_64-slc6-gcc46-opt += i686-slc5-gcc43-opt
      x86_64-slc6-gcc46-opt += x86_64-slc5-gcc46-opt
      x86_64-slc6-gcc46-opt += x86_64-slc6-gcc44-opt
      x86_64-slc6-gcc46-opt += x86_64_Scientific Linux_SL_5.4
      x86_64-slc6-gcc46-opt += x86_64_ScientificSL_Boron_5.3
      x86_64-slc6-gcc46-opt += x86_64_ScientificSL_Boron_5.4
      x86_64-slc6-gcc46-opt += x86_64_ScientificSL_Boron_5.5
      x86_64-slc6-gcc46-opt += x86_64_ScientificSL_Boron_5.7
      x86_64-slc6-gcc46-opt += x86_64_ScientificSL_Carbon_6.4
      x86_64-slc6-gcc46-opt += x86_64_ScientificSL_Carbon_6.5
      x86_64-slc6-gcc46-opt += x86_64_CentOS_Final_5.8
      x86_64-slc6-gcc46-opt += x86_64_CentOS_Final_6.4
      x86_64-slc6-gcc46-opt += x86_64_CentOS_Final_6.5
      x86_64-slc6-gcc46-opt += x86_64_ScientificCERNSLC_Boron_5.5
      x86_64-slc6-gcc46-opt += x86_64_ScientificCERNSLC_Boron_5.4
      x86_64-slc6-gcc46-opt += x86_64_ScientificCERNSLC_Boron_5.8
      x86_64-slc6-gcc46-opt += x86_64_ScientificCERNSLC_Carbon_6.4
      x86_64-slc6-gcc46-opt += x86_64_ScientificCERNSLC_Carbon_6.5
    }
    InProcess
    {
      TotalCPUs = 1
      MaxRunningJobs = 1
      MaxTotalJobs = 1
    }
    glexec
    {
      TotalCPUs = 1
      CPUTime = 345600
      MaxRunningJobs = 1
      MaxTotalJobs = 1
    }
    CEDefaults
    {
      OutputURL = gsiftp://localhost
      MaxTotalJobs = 100
      MaxWaitingJobs = 10
      WaitingToRunningRatio = 1.0
    }
  }
}
""" % PARAMETERS
# Write the config
conf_path = os.path.join(PARAMETERS["TARGET_DIR"], "etc/dconf.cfg")
fd = open(conf_path, "w")
fd.write(main_cfg)
fd.close()
# Now get an admin proxy
proxy_cmd = ["dirac-proxy-init", "-g", "dirac_admin", \
             "-C", "etc/grid-security/hostcert.pem", \
             "-K", "etc/grid-security/hostkey.pem"]
simple_run(proxy_cmd, True)
# Merge the config
conf_script = """
mergeFromFile %s
writeToServer
y
exit
""" % conf_path
proc = Popen("dirac-configuration-cli", stdin=PIPE)
proc.communicate(conf_script)
if proc.returncode:
  print "ERROR: dirac-configuation-cli failed. Check output above."
  print "NOTE: Processes may have been left running at this point."
  sys.exit(0)
print "" # The cli doesn't terminate cleanly
# The above config sets up a sandbox dir, create it.
os.mkdir(os.path.join(PARAMETERS["TARGET_DIR"], "storage"))
os.mkdir(os.path.join(PARAMETERS["TARGET_DIR"], "storage/sandboxes"))
# Install the DteamSiteDirector
install_cmd = [ "dirac-install-agent", "-m", "SiteDirector", \
                "WorkloadManagement", "SiteDirectorDteam" ]
simple_run(install_cmd, True)
# Mark CERN as enabled, this is the only one that works everywhere
enable_cmd = [ "dirac-admin-allow-site", "LCG.CERN-TEST.ch", "Go" ]
simple_run(enable_cmd, True)


print "\n\n[7/7] Restarting Components..."
startup_dirs = os.path.join(PARAMETERS["TARGET_DIR"], "startup/*")
# We need a shell here to expand the *
simple_run("sv restart %s" % startup_dirs, True, True)

print "\n\nAll Done."
print "You'll probably need to upload a pilot proxy."
print " dirac-proxy-init -P"
print " (Although wait a minute while everything restarts...)"
bashrc_path = os.path.join(PARAMETERS["TARGET_DIR"], "bashrc")
print "Remember to source %s first!" % bashrc_path

