#!/usr/bin/env python

import os
import sys,time
import subprocess
from clrpr import clrprt

#patch_src="/extend/disk1G1/work/ti-am334x/ti-linux-kernel/"
#patch_dst="/extend/disk1G1/work/ti-am334x/kernel-3.14.x/"
#global patch_src
#global patch_dst

def runcmd(cmd, cmdshow=0):
    if cmdshow:
        print(cmd)
    return os.popen(cmd).read()

def context_cut_filt(contex,d_arg,f_arg, cmdshow=0):
    "run the command echo $contex | cut -d d_arg -f f_arg"
    cmd="echo \""+contex+"\" | cut -d "+d_arg+" -f "+f_arg
    if cmdshow:
        print(cmd)
    return os.popen(cmd).read()

def path_modefy_files(filename):
    "print the modefy files in one patch"
    if not os.path.exists(filename):
        return
    cmd="cat "+filename+" | grep \"+++ \""+" | cut -b 7-"
    cmdout=os.popen(cmd).read()
    print(cmdout)

def cmp_file(filename,src,dst):
    "cmp the file,if the same, return 0"
    src_file=src+filename
    dst_file=dst+filename
    if os.path.exists(src_file) and os.path.exists(dst_file):
        cmd="diff -q "+src_file+" "+dst_file
        print("           "+cmd)
        cmdout=os.popen(cmd).read()
        if not cmdout =="":
            return 1
        else:
            return 0
    return 1

def get_linuxmail_patch(patchname,maildir,  curdir="", cmp_upstream="\[ Upstream commit "):
    "throught the patchname, then get the same patch \
    through kernle mailline. \
    argments: \
        patchname: the patch name \
        maildir: the mailline dir \
        curdir: the format patch out"

    #get the commit id in upstream
    if curdir=="":
        cmd="pwd"
        curdir=os.popen(cmd).read()
    
    retstr=""
    upstream_commit_num=0
    commitid=""
    cmd="cat "+patchname+" | grep \""+cmp_upstream+"\""
    cmdout=os.popen(cmd)
    for line in cmdout.readlines():

        if line == "":
            if upstream_commit_num==0:
                return "";
            else:
                if upstream_commit_num>1:
                    clrprt.printc("patch: "+patchname+" need your check")
                    return ""
                else:
                    return retstr
        else:
            commitid=line[18:-3]
            #clrprt.printc(commitid)
            cmd="cd "+maildir+"; "+"git show "+commitid
            cmdout1=os.popen(cmd).read()
            upstream_commit_num += 1
            cmd="cd "+maildir+"; "+"git format-patch -1 "+commitid+" -o "+curdir
            #print(cmd)
            retstr=os.popen(cmd).read()

    return retstr


def format_sdk_patch(patchname, context, checkcontext):
    "add sdk patch context \
     context: sdk commit \
     checkcontext: if has the checkcontxt, just return"

    out=runcmd("cat "+patchname+" | grep -n \""+checkcontext+"\"",1)
    if not out=="":
        return
    out=runcmd("cat "+patchname+" | grep -n \" upstream$\"")
    if not out=="":
        return
    linecnt=""
    cmd="cat "+patchname+" | grep -n \"^---$\" | cut -d : -f 1"
    cmdout=os.popen(cmd).read()
    if cmdout == "":
        return
    else:
        linecnt=cmdout[:-1]
        cmd="sed -i '"+linecnt+" i"+context+"' "+patchname
        print(patchname)
        if os.system(cmd):
            clrprt.printc(cmd+" is failed")


def replace_mailine_patch(patchname, mailine_path="/home/wrsadmin/github/linux-stable"):
    "replace the patchname by using the mailine"
    inter_num=5
    cmdout=runcmd("cat "+patchname+" | grep -n \"upstream$\"")
    if not cmdout == "":
        clrprt.printc(patchname+" has upstream commit")
        return

    cmdout=runcmd("cat "+patchname+" | grep -n \"Subject:\" | cut -d ] -f 2")
    commit_context=cmdout[:-1]
    cmd="sed -n '5p' "+patchname
    cmdout2=os.popen(cmd).read()
    if len(cmdout2)<2:
        pass
    else:
        commit_context = commit_context + cmdout2[:-1]
        inter_num += 1

    shortlog=mailine_path+"/shortlog "
    cmdout2=runcmd("cat "+shortlog+" | grep -n "+"\""+commit_context+"\"")
    if len(cmdout2) > 10:
        clrprt.printc(patchname+" find upstream")
        number=runcmd("echo \""+cmdout2[:-1]+"\" | cut -d : -f 1")
        number=str((int(number[:-1])-3))
        out=runcmd("sed -n '"+number+"p' "+shortlog)
        commitid=out[7:-1]
        out=runcmd("git -C "+mailine_path+" format-patch -1 "+commitid+" -o "+runcmd("pwd"))
        runcmd("cp "+out[:-1]+" "+patchname, 1)

        f=open(patchname, 'r')
        number=0
        for line in f.readlines():
            number += 1
            #print(line[:-1]+"number: "+str(number)+"len: "+str(len(line)))
            if len(line) == 1:
                cmd="sed -i '"+str(number)+" acommit "+commitid+" upstream\\n'"+" "+patchname
                if os.system(cmd):
                    clrprt.printc(cmd+" is failed")
                break

            
        #runcmd("sed -i '"+str(inter_num)+" acommit "+commitid+" upstream\\n'"+" "+patchname

def format_linuxmail_patch(patchname):
    "add  commit $commit upstream \
     to mailpatch"
    commitid=""

#判断是否已经有了upstream commit
    inter_num=5
    cmd="cat "+patchname+" | grep -n \"upstream$\""
    cmdout=os.popen(cmd).read()
    if not cmdout == "":
        clrprt.printc(patchname+" has upstream commit")
        return
    cmd="cat "+patchname+" | grep -n \"Subject:\" | cut -d ] -f 2"
    cmdout=os.popen(cmd).read()
    commit_context=cmdout[:-1]
    #print(commit_context)
    cmd="sed -n '5p' "+patchname
    cmdout2=os.popen(cmd).read()
    #print(cmdout2)
    if len(cmdout2)<2:
        pass
    else:
        commit_context = commit_context + cmdout2[:-1]
        inter_num += 1
    #print(commit_context)

    cmd="cat /home/wrsadmin/github/linux-stable/shortlog "+" | grep -n "+"\""+commit_context+"\""
    cmdout2=os.popen(cmd).read()
    if len(cmdout2) > 10:
        #print(cmdout2)
        clrprt.printc(patchname+" find upstream")
        number=runcmd("echo \""+cmdout2[:-1]+"\" | cut -d : -f 1")
        #print(number)
        number=str((int(number[:-1])-3))
        out=runcmd("sed -n '"+number+"p' "+"/home/wrsadmin/github/linux-stable/shortlog")
        commitid=out[7:-1]
        cmd="sed -i '"+str(inter_num)+" acommit "+commitid+" upstream\\n'"+" "+patchname
        if os.system(cmd):
            clrprt.printc(cmd+" is failed")

def git_apply(patchname,src,dst):
    "git apply the patchname, if success, return 0"

    if not os.path.exists(patchname):
        print(patchname+" isn't exist")
        return 1

    patch_src=src
    patch_dst=dst

    cmd="cat "+patchname+" | grep \"+++ \""+" | cut -b 7-"
    cmdout=os.popen(cmd)
    files_num=0
    samefile_num=0
    for line in cmdout.readlines():
        filename=line[:-1]
        #file is deferent
        if not cmp_file(filename,patch_src,patch_dst):
            samefile_num += 1
        files_num += 1

    #the patch no need, because the src and dst is the same
    if files_num == samefile_num:
        print(patchname+" no need, the file is the same")
        return 2

    cmd="git apply "+patchname
    p=subprocess.Popen(cmd, stdin = subprocess.PIPE, \
        stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    p.wait()
    #git apply fail
    if p.returncode:
        errout=p.stderr.read()
        print(errout)
        return 1
    else:
        print(patchname+" apply successfully")
        return 0

def cmp_shortlog(sdklog, dstlog):
    "find the log patch in dstlog from sdklog"
    cmd="cat "+sdklog
    cmdout=os.popen(cmd)
    flag_commit = 0
    flag_number = -1 
    commit_id ="";
    for line in cmdout.readlines():
        if line[:6] == "commit":
            commit_id = line[6:-1]
            #print("find commit :"+line[10:-1])
            flag_commit = 1
            flag_number = 0 
        if flag_number >= 0:
            flag_number += 1;
        if flag_number >= 4:
            if line[0] == 'M':
                pass
            else:
                flag_number = -1;
                #print(line[:-1])
                #commit_id = line[10:-1]
                cmd1="cat "+dstlog + " | grep " + "\""+line[:-1]+"\""
                cmd1out = os.popen(cmd1).read();
                if cmd1out != "":
                    pass
                    #print(line[:-1])
                else:
                    print(line[:-1]+ " commitid: "+commit_id)
def format_patch(mode,git_dir,out_dir,arg1,arg2):
    "git format patch"
    "mode: author: generat log file to record the patch of author"
        "arg1: author name"
    "mode: frm: format list patches from log file"
        "arg1: log name"
        "arg2: patch out dir"
    #generate git log
    if mode == "author":
        runcmd("git -C "+git_dir+"  --author="+arg1+" > git_author_log")
    else if mode == "frm"
        pass


           
if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("argments is less")
        exit()

    patchname=sys.argv[1]
    git_apply(patchname,src, dst)
