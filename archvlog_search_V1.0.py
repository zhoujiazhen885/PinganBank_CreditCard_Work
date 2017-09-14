#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

2017-9-15 V1.0 Creating the function of seraching logs on 10.1.183.83.
               Jiazhen Zhou , Pudong Shanghai.
"""

import subprocess
import sys
import time
import threading


# get the user's input ,including system's name ,componentName ,date and keyword.
def getInputWords():
    systemName = raw_input("Please input the system's name:").lower().replace('-', '_')
    componentName = raw_input("Please input the componentName or the host IP, if you want to search all the hosts please input 'ALL':").upper()
    d = raw_input("Please input the logs producing date,and it should be 'mmdd' format like '0706': ")
    keyWord = raw_input("Please input the key word:")
    return componentName, keyWord, systemName, d


# 根据用户输入，读取配置文件，输出IP和日志文件路径
def exportConf(componentName, systemName):
    # checking if the system's config has been existed!
    systemName = systemName + '.conf'
    confName = '/wls/bankdplyop/tools/getlog/conf/' + systemName
    checkConfFile = subprocess.Popen("cat %s" % confName, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    f = checkConfFile.stdout.read()
    # 判断配置文件是否存在
    if f:
        pass
    else:
        print "The conf file is not existed, please check!"
        sys.exit(0)
    # componentName
    # 查找所有服务器
    if componentName == 'ALL':
        # 将ip和logFile匹配成字段
        dict1 = {}
        lines = open(confName)
        for line in lines:
            f = line.split(':')[1]
            f = f.split(',')
            for value in f:
                ip = value.split('|')[0]
                logFile = value.split('|')[1]
                dict1[ip] = logFile
        lines.close()
        return dict1

        # 查找单台服务器
    elif componentName[0:3] == '10.':
        # 将ip和logFile匹配成字段
        dict1 = {}
        lines = open(confName)
        for line in lines:
            f = line.split(':')[1]
            f = f.split(',')
            for value in f:
                ip = value.split('|')[0]
                logFile = value.split('|')[1]
                dict1[ip] = logFile
        lines.close()
        if componentName in dict1:
            item = [(componentName, dict1[componentName])]
            dict1 = dict(item)
            return dict1
        else:
            print "The inputing host IP is not belonged the system, please check!"
            sys.exit(0)

    # 按组件查找
    else:
        dict1 = {}
        ssh1 = subprocess.Popen("grep %s %s" % (componentName, confName), shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        f = ssh1.stdout.read()
        f = f.split(':')[1]
        f = f.split(',')
        for value in f:
            ip = value.split('|')[0]
            logFile = value.split('|')[1]
            dict1[ip] = logFile
        return dict1


# the function of searching log
def searchLog(ip, searchLogFile, keyWord, systemName, i):
    # replace the /n problem
    searchLogFile = searchLogFile.replace('\n', '')
    start = time.time()
    print (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), "begin")
    #    print 'The children process %s is searching  the log %s on the %s .' % (os.getpid(), searchLogFile, ip)
    print  'The %s thread is searching  the log %s on the %s .' % (i, searchLogFile, ip)
    # the temp log name is "systemName-ip.temp"
    templog = tempLogDir + systemName + '-' + ip + '.temp'
    ssh3 = subprocess.Popen("touch %s" % templog, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    templogWrite = open(templog, 'w')

    values1 = (systemName, ip, keyWord, searchLogFile)
    ssh2 = subprocess.Popen(
        "export DEPLOY_PASSWORD=deploy;deploytool dremotecmd -s %s -i %s 'grep -n %s %s '" % values1, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    f = ssh2.stdout.read()
    fError = ssh2.stderr.read()
    templogWrite.write(f)

    for n in range(1, 200):
        searchLogFile1 = searchLogFile + '.' + str(n)
        print searchLogFile1
        ssh4 = subprocess.Popen("export DEPLOY_PASSWORD=deploy;deploytool dremotecmd -s %s -i %s 'head  %s' " % (
        systemName, ip, searchLogFile1), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        f2 = ssh4.stdout.read()
        # checking if the log.* is exsited
        if "�޷���" not in f2:
            #            print f2
            #            print 'The children process %s is searching  the log %s on the %s .' % (os.getpid(), searchLogFile1, ip)
            print 'Thread %s is searching  the log %s on the %s .' % (i, searchLogFile1, ip)
            values2 = (systemName, ip, keyWord, searchLogFile1)
            ssh5 = subprocess.Popen(
                "export DEPLOY_PASSWORD=deploy;deploytool dremotecmd -s %s -i %s 'grep -n %s %s '" % values2,
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            f = ssh5.stdout.read()
            templogWrite.write(f)
        # searchLogFile1 = searchLogFile
        else:
            #            print "The child process %s can't find the %s!" % (os.getpid(), searchLogFile1)
            print "Thread %s can't find the %s!" % (i, searchLogFile1)
            # exit the for loop
            break

    templogWrite.close()
    end = time.time()
    #    print 'Process %s runs %0.2f seconds, and the templog is %s.' % (os.getpid(), (end - start), templog)
    print 'Thread %s runs %0.2f seconds, and the templog is %s.' % (i, (end - start), templog)


# 清理临时日志，并整合成一个整体日志
def collectLog():
    # 整合后的日志文件名
    logFile = '/wls/bankdplyop/tools/getlog/log/' + systemName + '.log'
    ssh1 = subprocess.Popen("cat %s" % logFile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    f1 = ssh1.stdout.read()
    if f1:
        ssh2 = subprocess.Popen("rm %s" % logFile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        pass
    # 找到临时目录的临时文件，即以temp结尾的文件
    ssh3 = subprocess.Popen("ls -l %s" % tempLogDir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    f = ssh3.stdout.read().split(' ')
    for x in f:
        n = x.find('temp')
        # 判断取出来的文件名中是否包含"temp"
        if n != -1:
            # x为取出来的临时日志文件名
            x = x[0:n + 4]
            # 临时日志文件绝对路径
            tempLogFile = tempLogDir + x
            # 将临时日志的文件内容整合到一个日志文件中
            ssh4 = subprocess.Popen("cat %s >> %s; rm %s" % (tempLogFile, logFile, tempLogFile), shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # ssh5 = subprocess.Popen("rm %s" % tempLogFile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            pass
    print "All logs have been written to the file %s !" % logFile


if __name__ == '__main__':
    # 日志文件名目录
    tempLogDir = '/wls/bankdplyop/tools/getlog/log/temp/'
    # 获取用户输入
    componentName, keyWord, systemName = getInputWords()
    print systemName, componentName, keyWord

    # 配置文件目录
    #    conf = '/wls/bankdplyop/tools/getlog/conf/icss_cccs_csi.conf'


    # 输出要查找的IP和日志文件目录
    dictIpLogfile = exportConf(componentName, systemName)

    n = len(dictIpLogfile)
    print 'Total number is %s' % n
    # 利用多进程查找日志
    #    print 'Parent process %s.' % os.getpid()
    #    p = Pool(12)
    threadpros = []
    listIpLogfile = dictIpLogfile.items()
    for i in range(n):
        l = listIpLogfile[i]
        #            results = p.apply_async(searchLog, args=(l[0], l[1], keyWord, systemName))
        t = threading.Thread(target=searchLog, args=(l[0], l[1], keyWord, systemName, i))
        threadpros.append(t)
    for i in range(n):
        threadpros[i].start()
    for i in range(n):
        threadpros[i].join()
    # except KeyboardInterrupt:
    #        t.terminate()
    #        print "You cancelled the program!"
    #        sys.exit(1)
    #    print 'Waiting for all subprocesses done...'
    #    p.close()
    #    p.join()
    print 'All threads has done.'
    # 清理临时日志，并整合成一个完整的日志
    collectLog()

