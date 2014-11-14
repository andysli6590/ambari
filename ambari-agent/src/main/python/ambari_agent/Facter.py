#!/usr/bin/env ambari-python-wrap

'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import logging
import os
import getpass
import platform
import re
import shlex
import socket
import multiprocessing
import subprocess
from shell import shellRunner
import time
import uuid
from ambari_commons import OSCheck

log = logging.getLogger()


def run_os_command(cmd):
  if type(cmd) == str:
    cmd = shlex.split(cmd)
  process = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE
  )
  (stdoutdata, stderrdata) = process.communicate()
  return process.returncode, stdoutdata, stderrdata


class FacterBase():
  def __init__(self):
    pass

  # Returns the currently running user id
  def getId(self):
    return getpass.getuser()

  # Returns the OS name
  def getKernel(self):
    return platform.system()

  # Returns the FQDN of the host
  def getFqdn(self):
    return socket.getfqdn().lower()

  # Returns the host's primary DNS domain name
  def getDomain(self):
    fqdn = self.getFqdn()
    hostname = self.getHostname()
    domain = fqdn.replace(hostname, "", 1)
    domain = domain.replace(".", "", 1)
    return domain

  # Returns the short hostname
  def getHostname(self):
    return self.getFqdn().split('.', 1)[0]

  # Returns the CPU hardware architecture
  def getArchitecture(self):
    result = platform.processor()
    if result == '':
      return 'OS NOT SUPPORTED'
    else:
      return result

  # Returns the full name of the OS
  def getOperatingSystem(self):
    return OSCheck.get_os_type()

  # Returns the OS version
  def getOperatingSystemRelease(self):
    return OSCheck.get_os_version()

  # Returns the OS TimeZone
  def getTimeZone(self):
    return time.tzname[time.daylight - 1]


  # Returns the CPU count
  def getProcessorcount(self):
    return multiprocessing.cpu_count()

  # Returns the Kernel release
  def getKernelRelease(self):
    return platform.release()


  # Returns the Kernel release version
  def getKernelVersion(self):
    kernel_release = platform.release()
    return kernel_release.split('-', 1)[0]

  # Returns the major kernel release version
  def getKernelMajVersion(self):
    return '.'.join(self.getKernelVersion().split('.', 2)[0:2])

  def getMacAddress(self):
    mac = uuid.getnode()
    if uuid.getnode() == mac:
      mac = ':'.join('%02X' % ((mac >> 8 * i) & 0xff) for i in reversed(xrange(6)))
    else:
      mac = 'UNKNOWN'
    return mac

  # Returns the operating system family

  def getOsFamily(self):
    return OSCheck.get_os_family()

  # Return uptime hours
  def getUptimeHours(self):
    return self.getUptimeSeconds() / (60 * 60)

  # Return uptime days
  def getUptimeDays(self):
    return self.getUptimeSeconds() / (60 * 60 * 24)

  def facterInfo(self):
    facterInfo = {}
    facterInfo['id'] = self.getId()
    facterInfo['kernel'] = self.getKernel()
    facterInfo['domain'] = self.getDomain()
    facterInfo['fqdn'] = self.getFqdn()
    facterInfo['hostname'] = self.getHostname()
    facterInfo['macaddress'] = self.getMacAddress()
    facterInfo['architecture'] = self.getArchitecture()
    facterInfo['operatingsystem'] = self.getOperatingSystem()
    facterInfo['operatingsystemrelease'] = self.getOperatingSystemRelease()
    facterInfo['physicalprocessorcount'] = self.getProcessorcount()
    facterInfo['processorcount'] = self.getProcessorcount()
    facterInfo['timezone'] = self.getTimeZone()
    facterInfo['hardwareisa'] = self.getArchitecture()
    facterInfo['hardwaremodel'] = self.getArchitecture()
    facterInfo['kernelrelease'] = self.getKernelRelease()
    facterInfo['kernelversion'] = self.getKernelVersion()
    facterInfo['osfamily'] = self.getOsFamily()
    facterInfo['kernelmajversion'] = self.getKernelMajVersion()

    facterInfo['ipaddress'] = self.getIpAddress()
    facterInfo['netmask'] = self.getNetmask()
    facterInfo['interfaces'] = self.getInterfaces()

    facterInfo['uptime_seconds'] = str(self.getUptimeSeconds())
    facterInfo['uptime_hours'] = str(self.getUptimeHours())
    facterInfo['uptime_days'] = str(self.getUptimeDays())

    facterInfo['memorysize'] = self.getMemorySize()
    facterInfo['memoryfree'] = self.getMemoryFree()
    facterInfo['memorytotal'] = self.getMemoryTotal()

    return facterInfo

  #Convert kB to GB
  @staticmethod
  def convertSizeKbToGb(size):
    return "%0.2f GB" % round(float(size) / (1024.0 * 1024.0), 2)

  #Convert MB to GB
  @staticmethod
  def convertSizeMbToGb(size):
    return "%0.2f GB" % round(float(size) / (1024.0), 2)


class FacterWindows(FacterBase):
  GET_SYSTEM_INFO_CMD = "systeminfo"
  GET_MEMORY_CMD = '$mem =(Get-WMIObject Win32_OperatingSystem -ComputerName "LocalHost" ); echo "$($mem.FreePhysicalMemory) $($mem.TotalVisibleMemorySize)"'
  GET_PAGE_FILE_INFO = '$pgo=(Get-WmiObject Win32_PageFileUsage); echo "$($pgo.AllocatedBaseSize) $($pgo.AllocatedBaseSize-$pgo.CurrentUsage)"'
  GET_UPTIME_CMD = 'echo $([int]((get-date)-[system.management.managementdatetimeconverter]::todatetime((get-wmiobject -class win32_operatingsystem).Lastbootuptime)).TotalSeconds)'

  # Return first ip adress
  def getIpAddress(self):
    #TODO check if we need ipconfig
    return socket.gethostbyname(socket.gethostname().lower())

  # Return  netmask
  def getNetmask(self):
    #TODO return correct netmask
    return 'OS NOT SUPPORTED'

  # Return interfaces
  def getInterfaces(self):
    #TODO return correct interfaces
    return 'OS NOT SUPPORTED'

  # Return uptime seconds
  def getUptimeSeconds(self):
    try:
      runner = shellRunner()
      result = runner.runPowershell(script_block=FacterWindows.GET_UPTIME_CMD).output.replace('\n', '').replace('\r',
                                                                                                                '')
      return int(result)
    except:
      log.warn("Can not get SwapFree")
    return 0

  # Return memoryfree
  def getMemoryFree(self):
    try:
      runner = shellRunner()
      result = runner.runPowershell(script_block=FacterWindows.GET_MEMORY_CMD).output.split(" ")[0].replace('\n',
                                                                                                            '').replace(
        '\r', '')
      return result
    except:
      log.warn("Can not get MemoryFree")
    return 0

  # Return memorytotal
  def getMemoryTotal(self):
    try:
      runner = shellRunner()
      result = runner.runPowershell(script_block=FacterWindows.GET_MEMORY_CMD).output.split(" ")[-1].replace('\n',
                                                                                                             '').replace(
        '\r', '')
      return result
    except:
      log.warn("Can not get MemoryTotal")
    return 0

  # Return swapfree
  def getSwapFree(self):
    try:
      runner = shellRunner()
      result = runner.runPowershell(script_block=FacterWindows.GET_PAGE_FILE_INFO).output.split(" ")[-1].replace('\n',
                                                                                                                 '').replace(
        '\r', '')
      return result
    except:
      log.warn("Can not get SwapFree")
    return 0

  # Return swapsize
  def getSwapSize(self):
    try:
      runner = shellRunner()
      result = runner.runPowershell(script_block=FacterWindows.GET_PAGE_FILE_INFO).output.split(" ")[0].replace('\n',
                                                                                                                '').replace(
        '\r', '')
      return result
    except:
      log.warn("Can not get SwapFree")
    return 0

  # Return memorysize
  def getMemorySize(self):
    try:
      runner = shellRunner()
      result = runner.runPowershell(script_block=FacterWindows.GET_MEMORY_CMD).output.split(" ")[-1].replace('\n',
                                                                                                             '').replace(
        '\r', '')
      return result
    except:
      log.warn("Can not get MemorySize")
    return 0

  def facterInfo(self):
    facterInfo = FacterBase.facterInfo(self)
    facterInfo['swapsize'] = FacterBase.convertSizeMbToGb(self.getSwapSize())
    facterInfo['swapfree'] = FacterBase.convertSizeMbToGb(self.getSwapFree())
    return facterInfo


class FacterLinux(FacterBase):
  # selinux command
  GET_SE_LINUX_ST_CMD = "/usr/sbin/sestatus"
  GET_IFCONFIG_CMD = "ifconfig"
  GET_UPTIME_CMD = "cat /proc/uptime"
  GET_MEMINFO_CMD = "cat /proc/meminfo"

  def __init__(self):

    self.DATA_IFCONFIG_OUTPUT = Facter.setDataIfConfigOutput()
    self.DATA_UPTIME_OUTPUT = Facter.setDataUpTimeOutput()
    self.DATA_MEMINFO_OUTPUT = Facter.setMemInfoOutput()

  @staticmethod
  def setDataIfConfigOutput():

    try:
      result = os.popen(FacterLinux.GET_IFCONFIG_CMD).read()
      return result
    except OSError:
      log.warn("Can't execute {0}".format(FacterLinux.GET_IFCONFIG_CMD))
    return ""

  @staticmethod
  def setDataUpTimeOutput():

    try:
      result = os.popen(FacterLinux.GET_UPTIME_CMD).read()
      return result
    except OSError:
      log.warn("Can't execute {0}".format(FacterLinux.GET_UPTIME_CMD))
    return ""

  @staticmethod
  def setMemInfoOutput():

    try:
      result = os.popen(FacterLinux.GET_MEMINFO_CMD).read()
      return result
    except OSError:
      log.warn("Can't execute {0}".format(FacterLinux.GET_MEMINFO_CMD))
    return ""

  def isSeLinux(self):

    try:
      retcode, out, err = run_os_command(FacterLinux.GET_SE_LINUX_ST_CMD)
      se_status = re.search('(enforcing|permissive|enabled)', out)
      if se_status:
        return True
    except OSError:
      log.warn("Could not run {0}: OK".format(FacterLinux.GET_SE_LINUX_ST_CMD))
    return False

  # Function that returns list of values that matches
  # Return empty str if no matches
  def data_return_list(self, patern, data):
    full_list = re.findall(patern, data)
    result = ""
    for i in full_list:
      result = result + i + ","

    result = re.sub(r',$', "", result)
    return result

  def data_return_first(self, patern, data):
    full_list = re.findall(patern, data)
    result = ""
    if full_list:
      result = full_list[0]

    return result

  # Return first ip adress
  def getIpAddress(self):
    ip_pattern="(?: inet addr:)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    if OSCheck.is_redhat7():
      ip_pattern="(?: inet )(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    result = self.data_return_first(ip_pattern,self.DATA_IFCONFIG_OUTPUT)
    if result == '':
      log.warn("Can't get an ip address from {0}".format(self.DATA_IFCONFIG_OUTPUT))
      return socket.gethostbyname(socket.gethostname().lower())
    else:
      return result

  # Return  netmask
  def getNetmask(self):
    mask_pattern="(?: Mask:)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    if OSCheck.is_redhat7():
      mask_pattern="(?: netmask )(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    result = self.data_return_first(mask_pattern,self.DATA_IFCONFIG_OUTPUT)
    if result == '':
      log.warn("Can't get a netmask from {0}".format(self.DATA_IFCONFIG_OUTPUT))
      return 'OS NOT SUPPORTED'
    else:
      return result

  # Return interfaces
  def getInterfaces(self):
    interface_pattern="(\w+)(?:.*Link encap:)"
    if OSCheck.is_redhat7():
      interface_pattern="(\w+)(?:.*flags=)"
    result = self.data_return_list(interface_pattern, self.DATA_IFCONFIG_OUTPUT)
    if result == '':
      log.warn("Can't get a network interfaces list from {0}".format(self.DATA_IFCONFIG_OUTPUT))
      return 'OS NOT SUPPORTED'
    else:
      return result

  # Return uptime seconds
  def getUptimeSeconds(self):
    try:
      return int(self.data_return_first("\d+", self.DATA_UPTIME_OUTPUT))
    except ValueError:
      log.warn("Can't get an uptime value from {0}".format(self.DATA_UPTIME_OUTPUT))
      return 0

  # Return memoryfree
  def getMemoryFree(self):
    #:memoryfree_mb => "MemFree",
    try:
      return int(self.data_return_first("MemFree:.*?(\d+) .*", self.DATA_MEMINFO_OUTPUT))
    except ValueError:
      log.warn("Can't get free memory size from {0}".format(self.DATA_MEMINFO_OUTPUT))
      return 0

  # Return memorytotal
  def getMemoryTotal(self):
    try:
      return int(self.data_return_first("MemTotal:.*?(\d+) .*", self.DATA_MEMINFO_OUTPUT))
    except ValueError:
      log.warn("Can't get total memory size from {0}".format(self.DATA_MEMINFO_OUTPUT))
      return 0

  # Return swapfree
  def getSwapFree(self):
    #:swapfree_mb   => "SwapFree"
    try:
      return int(self.data_return_first("SwapFree:.*?(\d+) .*", self.DATA_MEMINFO_OUTPUT))
    except ValueError:
      log.warn("Can't get free swap memory size from {0}".format(self.DATA_MEMINFO_OUTPUT))
      return 0

  # Return swapsize
  def getSwapSize(self):
    #:swapsize_mb   => "SwapTotal",
    try:
      return int(self.data_return_first("SwapTotal:.*?(\d+) .*", self.DATA_MEMINFO_OUTPUT))
    except ValueError:
      log.warn("Can't get total swap memory size from {0}".format(self.DATA_MEMINFO_OUTPUT))
      return 0

  # Return memorysize
  def getMemorySize(self):
    #:memorysize_mb => "MemTotal"
    try:
      return int(self.data_return_first("MemTotal:.*?(\d+) .*", self.DATA_MEMINFO_OUTPUT))
    except ValueError:
      log.warn("Can't get memory size from {0}".format(self.DATA_MEMINFO_OUTPUT))
      return 0

  def facterInfo(self):
    facterInfo = FacterBase.facterInfo(self)
    facterInfo['selinux'] = self.isSeLinux()
    facterInfo['swapsize'] = FacterBase.convertSizeKbToGb(self.getSwapSize())
    facterInfo['swapfree'] = FacterBase.convertSizeKbToGb(self.getSwapFree())
    return facterInfo


if platform.system() == "Windows":
  Facter = FacterWindows
else:
  Facter = FacterLinux


def main(argv=None):
  print Facter().facterInfo()


if __name__ == '__main__':
  main()
