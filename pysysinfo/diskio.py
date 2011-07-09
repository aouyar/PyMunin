"""Implements DiskIOinfo Class for gathering I/O stats of Block Devices.

"""

import re
import os
from filesystem import FilesystemInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


# Defaults
sectorSize = 512
diskStatsFile = '/proc/diskstats'
devicesFile = '/proc/devices'
devmapperDir = '/dev/mapper'
sysfsBlockdevDir = '/sys/block'


class DiskIOinfo:
    """Class to retrieve I/O stats for Block Devices."""
    
    def __init__(self):
        """Initialization
        
        @param autoInit: If True parse stats on initization.
        
        """
        self._diskStats = None
        self._mapMajorDevclass = None
        self._mapMinorLV = None
        self._mapLVminor = None
        self._mapMinorDmName = None
        self._dmMajorNum = None
        self._devClassDict = None
        self._partDict = None
        self._partList = None
        self._vgDict = None
        self._fsDict = None

    def _initBlockMajorMap(self):
        """Parses /proc/devices to initialize device class - major number map
        for block devices.
        
        """
        self._mapMajorDevclass = {}
        try:
            fp = open(devicesFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise Exception('Failed reading interface stats from file: %s'
                    % devicesFile)
        skip = True
        for line in data.splitlines():
            if skip:
                if re.match('block.*:', line, re.IGNORECASE):
                    skip = False
            else:
                mobj = re.match('\s*(\d+)\s+([\w\-]+)$', line)
                if mobj:
                    major = int(mobj.group(1))
                    devtype = mobj.group(2)
                    self._mapMajorDevclass[major] = devtype
                    if devtype == 'device-mapper':
                        self._dmMajorNum = major
    
    def _initDMinfo(self):
        """Check files in /dev/mapper to initialize data sctructures for 
        mappings between device-mapper devices, minor device numbers, VGs 
        and LVs.
        
        """
        self._mapMinorDmName = {}
        self._mapMinorLV = {}
        self._mapLVminor = {}
        self._vgDict = {}
        if self._dmMajorNum is None:
            self._initBlockMajorMap()
        for file in os.listdir(devmapperDir):
            path = os.path.join(devmapperDir, file)
            fstat = os.stat(path)
            major = os.major(fstat.st_rdev)
            minor = os.minor(fstat.st_rdev)
            if major == self._dmMajorNum:
                self._mapMinorDmName[minor] = file
            mobj = re.match('(.*[^!])-([^!].*)$', file)
            if mobj:
                vg = mobj.group(1)
                lv = mobj.group(2)
                self._mapMinorLV[minor] = (vg,lv)
                self._mapLVminor["-".join((vg,lv))] = minor
                if not self._vgDict.has_key(vg):
                    self._vgDict[vg] = []
                self._vgDict[vg].append(lv)
                
    def _initFSinfo(self):
        """Initialize filesystem to device mappings."""
        self._fsDict = {}
        fsinfo = FilesystemInfo()
        if self._diskStats is None:
            self._initDiskStats()
        for fs in fsinfo.getFSlist():
            devpath = fsinfo.getFSdev(fs)
            if re.match('\/dev\/', devpath):
                mobj = re.match('\/dev\/(.*)$', os.path.realpath(devpath))
                if mobj:
                    self._fsDict[fs] = mobj.group(1)
    
    def _initDiskStats(self):
        """Parse and initialize block device I/O stats in /proc/diskstats."""
        self._diskStats = {}
        try:
            fp = open(diskStatsFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise Exception('Failed reading interface stats from file: %s'
                    % diskStatsFile)
        for line in data.splitlines():
            cols = line.split()
            dev = cols.pop(2)
            if len(cols) == 13:
                self._diskStats[dev] = dict(zip(
                    ('major', 'minor',
                     'rios', 'rmerges', 'rsect', 'rticks',
                     'wios', 'wmerges', 'wsect', 'wticks',
                     'ios_active', 'totticks', 'rqticks'),
                    [int(x) for x in cols]))
            elif len(cols) == 6:
                self._diskStats[dev] = dict(zip(
                    ('major', 'minor',
                     'rios', 'rsect',
                     'wios', 'wsect'),
                    [int(x) for x in cols]))
            else:
                continue
            self._diskStats[dev]['rbytes'] = (
                self._diskStats[dev]['rsect'] * sectorSize)
            self._diskStats[dev]['wbytes'] = (
                self._diskStats[dev]['wsect'] * sectorSize) 
                    
    def _initDevClasses(self):
        """Sort block devices into lists depending on device class and 
        initialize device type map and partition map."""
        self._devClassDict = {}
        self._partDict = {}
        basedevs = []
        otherdevs = []
        if self._mapMajorDevclass is None:
            self._initBlockMajorMap()
        if self._diskStats is None:
            self._initDiskStats()
        for dev in self._diskStats:
            stats = self._diskStats[dev]
            devclass = self._mapMajorDevclass.get(stats['major'])
            if devclass is not None:
                devdir = os.path.join(sysfsBlockdevDir, dev)
                if os.path.isdir(devdir):
                    if not self._devClassDict.has_key(devclass):
                        self._devClassDict[devclass] = []
                    self._devClassDict[devclass].append(dev)
                    basedevs.append(dev)
                else:
                    otherdevs.append(dev)
        basedevs.sort(key=len, reverse=True)
        otherdevs.sort(key=len, reverse=True)
        idx = 0
        for partdev in otherdevs:
            while len(basedevs[idx]) > partdev:
                idx += 1 
            for dev in basedevs[idx:]:
                if re.match("%s(\d+|p\d+)$" % dev, partdev):
                    if not self._partDict.has_key(dev):
                        self._partDict[dev] = []
                    self._partDict[dev].append(partdev)
    
    def getDevList(self):
        """Returns list of block devices.
        
        @return: List of device names.
        
        """
        if self._diskStats is None:
            self._initDiskStats()
        return self._diskStats.keys()
    
    def getDiskList(self):
        """Returns list of disk devices.
        
        @return: List of device names.
        
        """
        if self._devClassDict is None:
            self._initDevClasses()
        return self._devClassDict.get('sd')
    
    def getMDlist(self):
        """Returns list of MD devices.
        
        @return: List of device names.
        
        """
        if self._devClassDict is None:
            self._initDevClasses()
        return self._devClassDict.get('md')
    
    def getDMlist(self):
        """Returns list of DM devices.
        
        @return: List of device names.
        
        """
        if self._devClassDict is None:
            self._initDevClasses()
        return self._devClassDict.get('device-mapper')
    
    def getPartitionDict(self):
        """Returns dict of disks and partitions.
        
        @return: Dict of disks and partitions.
        
        """
        if self._partDict is None:
            self._initDevClasses()
        return self._partDict
    
    def getPartitionList(self):
        """Returns list of partitions.
        
        @return: List of (disk,partition) pairs.
        
        """
        if self._partList is None:
            self._partList = []
            for (disk,parts) in self.getPartitionDict().iteritems():
                for part in parts:
                    self._partList.append((disk,part))
        return self._partList
    
    def getFilesystemList(self):
        """Returns list of filesystems mapped to block devices on disks.
        
        @return: List of filesystem paths.
        
        """
        pass
    
    def getVGdict(self):
        """Returns dict of VGs.
        
        @return: Dict of VGs.
        
        """
        if self._vgDict is None:
            self._initDMinfo()
        return self._vgDict
    
    def getVGlist(self):
        """Returns list of VGs.
        
        @return: List of VGs.
        
        """
        return self.getVGdict().keys()
        
    def getLVlist(self):
        """Returns list of LV Devices.
        
        @return: List of (vg,lv) pairs.
        
        """
        if self._vgDict is None:
            self._initDMinfo()
        return self._mapMinorLV.values()

    def getFSdict(self):
        """Returns map of filesystems to disk devices.
        
        @return: Dict of filesystem to disk device mappings.
        
        """
        if self._fsDict is None:
            self._initFSinfo()
        return self._fsDict
    
    def getFSlist(self):
        """Returns list of filesystems mapped to disk devices.
        
        @return: List of filesystem paths.
        
        """
        return self.getFSdict().keys()
    
    def getDevStats(self, dev):
        """Returns I/O stats for block device.
        
        @param dev: Device name
        @return: Dict of stats.
        
        """
        if self._diskStats is None:
            self._initDiskStats()
        return self._diskStats.get(dev)

    getDiskStats = getDevStats
    getPartitionStats = getDevStats
    getMDstats = getDevStats
    getDMstats = getDevStats
    
    def getLVstats(self, vg, lv):
        """Returns I/O stats for LV.
        
        @param vg: VG name.
        @param lv: LV name. 
        @return: Dict of stats.
        
        """
        if self._mapLVminor is None:
            self._initDMinfo()
        minor = self._mapLVminor.get("-".join((vg,lv)))
        if minor:
            return self.getDevStats("dm-%d" % minor)
        else:
            return None
    
    def getFSstats(self, fs):
        """Returns I/O stats for filesystem.
        
        @param fs: Filesystem path.
        @return: Dict of stats.
        
        """
        if self._diskStats is None:
            self._initDiskStats()
        if self._fsDict is None:
            self._initFSinfo()
        return self._diskStats.get(self._fsDict.get(fs))
    