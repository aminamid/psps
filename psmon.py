# -*- coding: utf-8 -*-

from logging import getLogger

module_logger = getLogger(__name__)

STAT_INDEX=[
    'pid',         # 1
    'comm',        # 2
    'state',       # 3
    'ppid',        # 4
    'pgrp',        # 5
    'session',     # 6
    'tty_nr',      # 7
    'tpgid',       # 8
    'flags',       # 9
    'minflt',      #10
    'cminflt',     #11
    'majflt',      #12
    'cmajflt',     #13
    'utime',       #14
    'stime',       #15
    'cutime',      #16
    'cstime',      #17
    'priority',    #18
    'nice',        #19
    'num_threads', #20
    'itrealvalue', #21
    'starttime',   #22
    'vsize',       #23
    'rss',         #24
    'rsslim'       #25
#    'startcode',   #26
#    'encode',      #27
#    'startstack',  #28
#    'kstkesp',     #29
#    'kstkeip',     #30
#    'signal',      #31
#    'blocked',     #32
#    'sigignore',   #33
#    'sigcactch',   #34
#    'wchan',       #35
#    'nswap',       #36
#    'cnswap',      #37
#    'exit_signal', #38
#    'processor',   #39
#    'rt_priority', #40
#    'policy',      #41
#    'delayacct_blkio_ticks', #42
#    'guest_time',  #43
#    'cguest_time', #44
]

STAT_KEEP={
    'pid':'pid',
    'comm':'comm',
    'utime':'utime',
    'stime':'stime',
    'cutime':'cutime',
    'cstime':'cstime',
    'starttime':'start',
    'num_threads':'lwp',
}

STATUS_KEEP={
    'Uid':'uid',
    'VmSize':'vsz',
    'VmRSS':'rsz',
    'VmPeak':'vmax',
    'VmHWM':'rmax',
    'VmStk':'mstk',
    'VmData':'mdata',
    'VmExe':'mtext',
    'VmSwap':'mswap',
    'voluntary_ctxt_switches':'cs_v',
    'nonvoluntary_ctxt_switches':'cs_nv',
}


TO_SHOW={
    'pid': 'pidcom',
    'uid': 'uid',
    'comm': 'str',
    'cmdline': 'arg',
    'cpu': 'float',
    'usr': 'float',
    'sys': 'float',
    'vsz': None,
    'rsz': None,
    'vmax': None,
    'rmax': None,
    'mstk': None,
    'mdata': None,
    'mtext': None,
    'mswap': None,
    'cs_v': None,
    'cs_nv': None,
    'lwp': None,
#
    'utime': None,
    'stime': None,
    'cutime': None,
    'cstime': None,
    'delta': None,
}



from time import time
from pwd import getpwuid
from os import chdir
from os import uname
from glob import glob
import re




class ProcInfoIter(object):
    def __init__(self, cfg_to_show=TO_SHOW, cfg_stat_index=STAT_INDEX, cfg_stat_keep=STAT_KEEP, cfg_status_keep=STATUS_KEEP, proc_dir='/proc', cpustat_file = 'stat', influxprefix = None, hostname = None ):
        self.cfg_to_show = cfg_to_show
        self.cfg_stat_index=cfg_stat_index
        self.cfg_stat_keep=cfg_stat_keep
        self.cfg_status_keep=cfg_status_keep
        self.influxprefix=influxprefix
        self.pid_data_now = {}
        chdir( proc_dir )
        self.data=[{},{}]
        self.now=0
        self.old=1
        self.hostname = hostname if hostname else uname()[1]


    def __iter__(self):
        return self

    def next(self):
        self.now, self.old = self.old, self.now
        self.data[self.now]={}
        self.raw_data = {}
        self.current_time = int(time())
        pid_list = glob('[0-9]*')
        for pid in pid_list:
            self.tmp_data = {}
            try:
                with open('{0}'.format('stat' ), 'r') as f: self.tmp_data['cpustat']   =f.readline()
                with open('{0}/{1}'.format(pid,'stat'   ), 'r') as f: self.tmp_data['stat']   =f.readline()
                with open('{0}/{1}'.format(pid,'cmdline'), 'r') as f: self.tmp_data['args']=f.readline()
                with open('{0}/{1}'.format(pid,'status' ), 'r') as f: self.tmp_data['status'] =f.readlines()
                # if there are no exceptions, pass the temporary dict's pointer to raw_data
                self.raw_data[pid] = self.tmp_data
            except Exception, e:
                module_logger.debug( 'Exception: {0}'.format(e) )
        for pid in self.raw_data.keys():
            self.data[self.now][pid]={}

        self._parse_cpustat()
        self._parse_stat()
        self._parse_cmdline()
        self._parse_status()
        self._calcu_cpuusage()

            
        if self.influxprefix:
            return self._output_influx()
        else:
            return self._output_dict()

    def _output_influx(self):
        to_showkeys = self.cfg_to_show.keys()
        uniq_columns_set = []
        content = {}
        for pid in self.data[self.now].keys():
            tmpcolumns = ['time' ]
            tmppoints  = [ self.current_time ]
            for colname in to_showkeys:
                if not self.data[self.now][pid].has_key(colname): continue
                if not self.cfg_to_show[colname]:
                    tmpcolumns.append(colname)
                    tmppoints.append(int(self.data[self.now][pid][colname]))
                    continue
                if self.cfg_to_show[colname] == 'float':
                    tmpcolumns.append(colname)
                    tmppoints.append(float(self.data[self.now][pid][colname]))
                    continue
                if self.cfg_to_show[colname] == 'str':
                    tmpcolumns.append(colname)
                    tmppoints.append(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'uid':
                    try:
                        tmpcolumns.append(colname)
                        tmppoints.append(getpwuid(int(self.data[self.now][pid][colname])).pw_name)
                    except Exception, e:
                        tmpcolumns.append(colname)
                        tmppoints.append(str(self.data[self.now][pid][colname]))
                    continue
                if self.cfg_to_show[colname] == 'arg':
                    tmpcolumns.append(colname)
                    tmppoints.append(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'pidcom':
                    tmpcolumns.append(colname)
                    tmppoints.append('{0}_{1}'.format(self.data[self.now][pid]['comm'],self.data[self.now][pid][colname]))
                    continue
    
            tmpcolumns_str = ','.join(tmpcolumns)
            if not tmpcolumns_str in uniq_columns_set:
                uniq_columns_set.append(tmpcolumns_str)
                content[tmpcolumns_str]=[{ "name": '{0}.{1}'.format(self.influxprefix, self.hostname), "columns": tmpcolumns, "points": [ tmppoints ] } ]
                #content[tmpcolumns_str]=[{ "name": '{0}'.format(self.influxprefix), "columns": tmpcolumns, "points": [ tmppoints ] } ]
            else:
                content[tmpcolumns_str][0]["points"].append(tmppoints)

        return content


    def _output_list(self):
        content = []
        for pid in self.data[self.now].keys():
            tmpdict = {'time': self.current_time}
            for colname in self.cfg_to_show.keys():
                if not self.data[self.now][pid].has_key(colname): continue
                if not self.cfg_to_show[colname]:
                    tmpdict[colname]=int(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'float':
                    tmpdict[colname]=float(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'str':
                    tmpdict[colname]=self.data[self.now][pid][colname]
                    continue
                if self.cfg_to_show[colname] == 'uid':
                    try:
                        tmpdict[colname]=getpwuid(int(self.data[self.now][pid][colname])).pw_name
                    except Exception, e:
                        tmpdict[colname]=str(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'arg':
                    tmpdict[colname]=self.data[self.now][pid][colname]
                    continue
            content.append(tmpdict) 

        return content

    def _output_dict(self):
        content = {'time': self.current_time }
        for pid in self.data[self.now].keys():
            content[pid]={}
            for colname in self.cfg_to_show.keys():
                if not self.data[self.now][pid].has_key(colname): continue
                if not self.cfg_to_show[colname]:
                    content[pid][colname]=int(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'float':
                    content[pid][colname]=float(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'str':
                    content[pid][colname]=self.data[self.now][pid][colname]
                    continue
                if self.cfg_to_show[colname] == 'uid':
                    try:
                        content[pid][colname]=getpwuid(int(self.data[self.now][pid][colname])).pw_name
                    except Exception, e:
                        content[pid][colname]=str(self.data[self.now][pid][colname])
                    continue
                if self.cfg_to_show[colname] == 'arg':
                    content[pid][colname]=self.data[self.now][pid][colname]
                    continue
        return content

    def _parse_status(self):
        self.key_value_regx= re.compile( r"^([^:]+)\s*:\s*(\S+)(\s+\S+)*$" )
        for pid in self.raw_data.keys():
            for line in self.raw_data[pid]['status']:
                regx_result = self.key_value_regx.search(line)
                if regx_result and regx_result.group(1) in self.cfg_status_keep.keys():
                    self.data[self.now][pid][self.cfg_status_keep[regx_result.group(1)]]=regx_result.group(2)

    def _parse_cmdline(self):
        for pid in self.raw_data.keys():
            self.data[self.now][pid]['args']=self.raw_data[pid]['args'].replace('\0',' ')

    def _parse_stat(self):
        len_cfg_stat_index= len(self.cfg_stat_index)-1
        for pid in self.raw_data.keys():
            for i, value in enumerate(self.raw_data[pid]['stat'].split(' ',len_cfg_stat_index)) : 
                if self.cfg_stat_index[i] in self.cfg_stat_keep.keys():
                    self.data[self.now][pid][self.cfg_stat_keep[self.cfg_stat_index[i]]]=value

    def _parse_cpustat(self):
        for pid in self.raw_data.keys():
            self.data[self.now][pid]['delta'] = sum([int(s) for s in self.raw_data[pid]['cpustat'].split()[1:]])


    def _calcu_cpuusage(self):
        for pid in self.raw_data.keys():
            self.data[self.now][pid]['usrraw']=int(self.data[self.now][pid]['utime'])+int(self.data[self.now][pid]['cutime'])
            self.data[self.now][pid]['sysraw']=int(self.data[self.now][pid]['stime'])+int(self.data[self.now][pid]['cstime'])
            if self.data[self.old].has_key(pid):
                uRaw=float(self.data[self.now][pid]['usrraw'] - self.data[self.old][pid]['usrraw'])
                sRaw=float(self.data[self.now][pid]['sysraw'] - self.data[self.old][pid]['sysraw'])
                denomi = float(int(self.data[self.now][pid]['delta'])-int(self.data[self.old][pid]['delta']))
            else:
                uRaw=float(self.data[self.now][pid]['usrraw'])
                sRaw=float(self.data[self.now][pid]['sysraw'])
                denomi = float(int(self.data[self.now][pid]['delta'])-int(self.data[self.now][pid]['start']))
            totalRaw=uRaw+sRaw
            self.data[self.now][pid]['cpu']=(uRaw+sRaw)/denomi
            self.data[self.now][pid]['usr']=uRaw/denomi
            self.data[self.now][pid]['sys']=sRaw/denomi

