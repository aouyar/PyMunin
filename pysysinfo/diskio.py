"""Implements DiskIOinfo Class for gathering I/O stats of Block Devices.

"""

import re
import os
from filesystem import FilesystemInfo
from system import SystemInfo

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
        self._mapDevType = None
        self._mapFSpathDev = None
        self._dmMajorNum = None
        self._devClassTree = None
        self._partitionTree = None
        self._vgTree = None
        self._partList = None
        self._swapList = None

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
            raise IOError('Failed reading interface stats from file: %s'
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
        """Check files in /dev/mapper to initialize data structures for 
        mappings between device-mapper devices, minor device numbers, VGs 
        and LVs.
        
        """
        self._mapMinorDmName = {}
        self._mapMinorLV = {}
        self._mapLVminor = {}
        self._vgTree = {}
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
                if not self._vgTree.has_key(vg):
                    self._vgTree[vg] = []
                self._vgTree[vg].append(lv)
                
    def _initFilesystemInfo(self):
        """Initialize filesystem to device mappings."""
        self._mapFSpathDev = {}
        fsinfo = FilesystemInfo()
        if self._diskStats is None:
            self._initDiskStats()
        for fs in fsinfo.getFSlist():
            devpath = fsinfo.getFSdev(fs)
            if re.match('\/dev\/', devpath):
                mobj = re.match('\/dev\/(.*)$', os.path.realpath(devpath))
                if mobj:
                    self._mapFSpathDev[fs] = mobj.group(1)
    
    def _initSwapInfo(self):
        """Initialize swap partition to device mappings."""
        self._swapList = []
        sysinfo = SystemInfo()
        for (swap,attrs) in sysinfo.getSwapStats().iteritems():
            if attrs['type'] == 'partition':
                mobj = re.match('\/dev\/(.*)$', os.path.realpath(swap))
                if mobj:
                    self._swapList.append(mobj.group(1))
    
    def _initDiskStats(self):
        """Parse and initialize block device I/O stats in /proc/diskstats."""
        self._diskStats = {}
        try:
            fp = open(diskStatsFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise IOError('Failed reading interface stats from file: %s'
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
        self._devClassTree = {}
        self._partitionTree = {}
        self._mapDevType = {}
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
                    if not self._devClassTree.has_key(devclass):
                        self._devClassTree[devclass] = []
                    self._devClassTree[devclass].append(dev)
                    self._mapDevType[dev] = devclass
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
                    if not self._partitionTree.has_key(dev):
                        self._partitionTree[dev] = []
                    self._partitionTree[dev].append(partdev)
                    self._mapDevType[partdev] = 'part'
                    
    def getDevType(self, dev):
        """Returns type of device dev.
        
        @return: Device type as string.
        
        """
        if self._devClassTree is None:
            self._initDevClasses()
        return self._mapDevType.get(dev)
        
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
        if self._devClassTree is None:
            self._initDevClasses()
        return self._devClassTree.get('sd')
    
    def getMDlist(self):
        """Returns list of MD devices.
        
        @return: List of device names.
        
        """
        if self._devClassTree is None:
            self._initDevClasses()
        return self._devClassTree.get('md')
    
    def getDMlist(self):
        """Returns list of DM devices.
        
        @return: List of device names.
        
        """
        if self._devClassTree is None:
            self._initDevClasses()
        return self._devClassTree.get('device-mapper')
    
    def getPartitionDict(self):
        """Returns dict of disks and partitions.
        
        @return: Dict of disks and partitions.
        
        """
        if self._partitionTree is None:
            self._initDevClasses()
        return self._partitionTree
    
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
    
    def getVGdict(self):
        """Returns dict of VGs.
        
        @return: Dict of VGs.
        
        """
        if self._vgTree is None:
            self._initDMinfo()
        return self._vgTree
    
    def getVGlist(self):
        """Returns list of VGs.
        
        @return: List of VGs.
        
        """
        return self.getVGdict().keys()
        
    def getLVlist(self):
        """Returns list of LV Devices.
        
        @return: List of (vg,lv) pairs.
        
        """
        if self._vgTree is None:
            self._initDMinfo()
        return self._mapMinorLV.values()

    def getFilesystemDict(self):
        """Returns map of filesystems to disk devices.
        
        @return: Dict of filesystem to disk device mappings.
        
        """
        if self._mapFSpathDev is None:
            self._initFilesystemInfo()
        return self._mapFSpathDev
    
    def getFilesystemList(self):
        """Returns list of filesystems mapped to disk devices.
        
        @return: List of filesystem paths.
        
        """
        return self.getFilesystemDict().keys()

    def getSwapList(self):
        """Returns list of disk devices used for paging.
        
        @return: List of disk devices.
        
        """
        if self._swapList is None:
            self._initSwapInfo()
        return self._swapList
    
    def getDevStats(self, dev, devtype = None):
        """Returns I/O stats for block device.
        
        @param dev:     Device name
        @param devtype: Device type. (Ignored if None.)
        @return:        Dict of stats.
        
        """
        if self._diskStats is None:
            self._initDiskStats()
        if devtype is not None:
            if self._devClassTree is None:
                self._initDevClasses()
            if devtype <> self._mapDevType.get(dev):
                return None
        return self._diskStats.get(dev) 

    def getDiskStats(self, dev):
        """Returns I/O stats for hard disk device.
        
        @param dev: Device name for hard disk.
        @return: Dict of stats.
        
        """
        return self.getDevStats(dev, 'sd')
    
    def getPartitionStats(self, dev):
        """Returns I/O stats for partition device.
        
        @param dev: Device name for partition.
        @return: Dict of stats.
        
        """
        return self.getDevStats(dev, 'part')
        
    def getMDstats(self, dev):
        """Returns I/O stats for MD (Software RAID) device.
        
        @param dev: Name for MD device.
        @return: Dict of stats.
        
        """
        return self.getDevStats(dev, 'md')
    
    def getDMstats(self, dev):
        """Returns I/O stats for DM (Device Mapper) device.
        
        @param dev: Device name for DM.
        @return: Dict of stats.
        
        """
        return self.getDevStats(dev, 'device-mapper')
    
    def getSwapStats(self, dev):
        """Returns I/O stats for swap partition.
        
        @param dev: Device name for swap partition.
        @return: Dict of stats.
        
        """
        if self._swapList is None:
            self._initSwapInfo()
        if dev in self._swapList:
            return self.getDevStats(dev)
        else:
            return None
    
    def getLVstats(self, *args):
        """Returns I/O stats for LV.
        
        @param args: Two calling conventions are implemented:
                     - Passing two parameters vg and lv.
                     - Passing only one parameter in vg-lv format.  
        @return:     Dict of stats.
        
        """
        if len(args) == 1:
            lvdev = args[0]
        elif len(args) == 2:
            lvdev = '-'.join(args)
        else:
            raise AttributeError("The getLVstats must be called with either "
                                 "one or two arguments.")
        if self._mapLVminor is None:
            self._initDMinfo()
        minor = self._mapLVminor.get(lvdev)
        if minor is not None:
            return self.getDevStats("dm-%d" % minor)
        else:
            return None
    
    def getFilesystemStats(self, fs):
        """Returns I/O stats for filesystem.
        
        @param fs: Filesystem path.
        @return: Dict of stats.
        
        """
        if self._diskStats is None:
            self._initDiskStats()
        if self._mapFSpathDev is None:
            self._initFilesystemInfo()
        return self._diskStats.get(self._mapFSpathDev.get(fs))
    