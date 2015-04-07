#!/usr/bin/env python

''' ns_ha_upgrade.py / jeff.brown@citrix.com

!!! Upgrade an HA pair of NetScaler appliances using current Citrix
best practices.  This script is provided as-is and is not
intended for proudction use !!!

PEXPECT LICENSE
    This license is approved by the OSI and FSF as GPL-compatible.
        http://opensource.org/licenses/isc-license.txt

    Copyright (c) 2012, Noah Spurrier <noah@noah.org>
    PERMISSION TO USE, COPY, MODIFY, AND/OR DISTRIBUTE THIS SOFTWARE FOR ANY
    PURPOSE WITH OR WITHOUT FEE IS HEREBY GRANTED, PROVIDED THAT THE ABOVE
    COPYRIGHT NOTICE AND THIS PERMISSION NOTICE APPEAR IN ALL COPIES.
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
    
'''

from __future__ import print_function
from __future__ import absolute_import

import pexpect
import os, sys, re, getopt, getpass, logging, argparse
from nssrc.com.citrix.netscaler.nitro.service.nitro_service import nitro_service
from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nsconfig import nsconfig
from nssrc.com.citrix.netscaler.nitro.resource.config.ha.hanode import hanode
from nssrc.com.citrix.netscaler.nitro.resource.config.ha.hafailover import hafailover

try:
    raw_input
except NameError:
    raw_input = input
    
COMMAND_PROMPT = '[$#>]'
TERMINAL_PROMPT = r'Terminal type\?'
TERMINAL_TYPE = 'vt100'
SSH_NEWKEY = r'Are you sure you want to continue connecting \(yes/no\)\?'
SSH_TIMEOUT = 'Operation timed out'
SSH_CLOSE = 'Connection closed by'
SSH_RESET = 'Connection reset by'
CLI_REBOOT = r'Are you sure you want to restart NetScaler \(Y/N\)\?'
DEBUG = 1

def login_ssh(child, host, user, password):

    logging.debug('login_ssh')
    i = 0
    while (i < 4):
        child.sendline('ssh %s@%s'%(user, host))
        i = child.expect([pexpect.TIMEOUT, SSH_RESET, SSH_TIMEOUT, SSH_CLOSE, SSH_NEWKEY, '[Pp]assword: '])
        if (i < 4): # Remote host offline. Try again.
            logging.debug('ERROR!')
            logging.debug('SSH could not login. Here is what SSH said: %s', child.after)
            #logging.debug(child.before, child.after)
    if i == 4: # SSH does not have the public key. Just accept it.
        child.sendline ('yes')
        child.expect ('[Pp]assword: ')
    child.sendline(password)
    # Now we are either at the command prompt or
    # the login process is asking for our terminal type.
    i = child.expect (['Permission denied', TERMINAL_PROMPT, COMMAND_PROMPT])
    if i == 0:
        logging.debug('Permission denied on host: %s', host)
        sys.exit (1)
    if i == 1:
        child.sendline (TERMINAL_TYPE)
        child.expect (COMMAND_PROMPT)

def mkdir_remote(child, license_path, build_path) :
    logging.debug("mkdir remote")
    child.sendline ('shell mkdir -p ' + license_path)
    i = child.expect(COMMAND_PROMPT)
    child.sendline ('shell mkdir -p ' + build_path)
    i = child.expect(COMMAND_PROMPT)

def scp_remote(user, password, host, local_path, local_file, remote_path) :
    logging.debug("scp: %s", host)
    try :
        #var_command = "scp pathdir/file.ext username@hostname:pathdir"
        #make sure in the above command that username and hostname are according to your server
        child = pexpect.spawn("scp " + local_path + "/" + local_file + " " + user + "@" + host + ":" + remote_path, timeout=300)
        i = child.expect(["Password:", pexpect.EOF])
        if i==0: # send password                
                child.sendline(password)
                child.expect(pexpect.EOF)
        elif i==1: 
                logging.debug("Got the key or connection timeout")
                pass

    except Exception as e:
         loggin.error("Exception::message="+str(e.args))

def upgrade(child, remote_path, build_file) :
    logging.debug('upgrade')
    try :
        child.sendline ('shell')
        i = child.expect(COMMAND_PROMPT)
        child.sendline ('cd ' + remote_path)
        i = child.expect(COMMAND_PROMPT)
        child.sendline ('tar -xzvf ' + build_file)
        i = child.expect(COMMAND_PROMPT)
        logging.debug('installns')
        child.sendline ('./installns -yY')
        i = child.expect('closed by remote host')
        logging.debug('Rebooting ...')
    except Exception as e:
         logging.error("Exception::message="+str(e.args))

def login_nitro(host, user, password):

    try :
        client = nitro_service(host,"http")
        client.set_credential(user,password)
        client.timeout = 500
        logging.debug("nitro login complete")
    except nitro_exception as  e:
        logging.error("Exception::login_nitro::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:         
        logging.error("Exception::loing_nitro::message="+str(e.args))

    return client

def saveconfig(client) :
	try :
		obj = nsconfig()
		nsconfig.save(client,obj)
		logging.debug("saveconfig - Done")
	except nitro_exception as e :
		logging.error("Exception::saveconfig::errorcode="+str(e.errorcode)+",message="+ e.message)
	except Exception as e:
		logging.error("Exception::saveconfig::message="+str(e.args))

def disablesync(nitro) :
    obj = hanode()
    try : 
        obj.hasync = "DISABLED"
        obj.haprop = "DISABLED"
        hanode.update(nitro,obj)
        logging.debug("disablesync - Done")
    except nitro_exception as e :
        logging.error("Exception::disablesync::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:
        logging.error("Exception::disablesync::message="+str(e.args))
        
def enablesync(nitro) :
    obj = hanode()
    try : 
        obj.hasync = "ENABLED"
        obj.haprop = "ENABLED"
        hanode.update(nitro,obj)
        logging.debug("enablesync - Done")
    except nitro_exception as e :
        logging.error("Exception::enablesync::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:
        logging.error("Exception::enablesync::message="+str(e.args))
        
def staysecondary(nitro) :
    obj = hanode()
    try : 
        obj.hastatus = "STAYSECONDARY"
        hanode.update(nitro,obj)
        logging.debug("staysecondary - Done")
    except nitro_exception as e :
        logging.error("Exception::staysecondary::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:
        logging.error("Exception::staysecondary::message="+str(e.args))
        
def stayprimary(nitro) :
    obj = hanode()
    try : 
        obj.hastatus = "STAYPRIMARY"
        hanode.update(nitro,obj)
        logging.debug("stayprimary - Done")
    except nitro_exception as e :
        logging.error("Exception::stayprimary::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:
        logging.error("Exception::stayprimary::message="+str(e.args))
        
def enableha(nitro) :
    obj = hanode()
    try : 
        obj.hastatus = "ENABLED"
        hanode.update(nitro,obj)
        logging.debug("enableha - Done")
    except nitro_exception as e :
        logging.error("Exception::enableha::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:
        logging.error("Exception::enableha::message="+str(e.args))
        
def forcefailover(nitro) :
    try : 
        nitro.forcehafailover(True)
        logging.debug("forcefailover - Done")
    except nitro_exception as e :
        logging.error("Exception::forcefailover::errorcode="+str(e.errorcode)+",message="+ e.message)
    except Exception as e:
        logging.error("Exception::forcefailover::message="+str(e.args))
    
def main(args):
    
    if args.debug:
        logging.basicConfig(filename='ns-upgrade.log', filemode='w', level=logging.DEBUG)
    else:
        logging.basicConfig(filename='ns-upgrade.log', filemode='w', level=logging.ERROR) 
    
    #logging.debug('This message should go to the log file')
    #logging.info('So should this')
    #logging.warning('And this, too')

    host1 = args.primary
    host2 = args.secondary
    user = args.user
    password = args.password
    
    local_path = args.local_path
    docs_file = args.docs_file
    build_file = args.build_file
    build_num = re.search('([0-9][0-9]\.[0-9]\-[0-9][0-9]\.[0-9])', build_file).group(1) #extract build num from build file
    
    logging.debug('Build Num: %s', build_num)
    remote_path1 = "/nsconfig/license"
    remote_path2 = "/var/nsinstall/ccnsinstall/" + build_num
    logging.debug('Path: %s', remote_path2)
    
    #spawn shell and create SSH session to secondary appliance
    child2 = pexpect.spawn('/bin/bash', timeout=None)
    if args.debug:
        fout = file('ns-child2.log','w')
        child2.logfile = fout
    login_ssh(child2, host2, user, password)
    
    #create nitro session and prepare secondary appliance for upgrade
    nitro2 = login_nitro(host2, user, password)
    disablesync(nitro2)
    staysecondary(nitro2)
    saveconfig(nitro2)
    mkdir_remote(child2, remote_path1, remote_path2)
    scp_remote(user, password, host2, local_path, build_file, remote_path2)
    
    #create nitro session to primary and tell it to stay primary
    nitro1 = login_nitro(host1, user, password)
    stayprimary(nitro1)
    saveconfig(nitro1)

    #upgrade secondary appliance and try to relogin in until it finishes rebooting
    upgrade(child2, remote_path2, build_file)
    logging.debug('returned from upgrade: %s', host2)
    login_ssh(child2, host2, user, password)   
    logging.debug('returned from relogin: %s', host2)
    nitro2 = login_nitro(host2, user, password)
    
    #re-enable ha on primary/secondary 
    enableha(nitro2) 
    saveconfig(nitro2)
    enableha(nitro1)
    saveconfig(nitro1)
    
    #spawn shell and create SSH session to secondary appliance
    child1 = pexpect.spawn('/bin/bash', timeout=None)
    if args.debug:
        fout = file('ns-child1.log','w')
        child1.logfile = fout
    login_ssh(child1, host1, user, password)
    
    #prepare primary appliance for upgrade
    mkdir_remote(child1, remote_path1, remote_path2)  
    scp_remote(user, password, host1, local_path, build_file, remote_path2)
    
    #upgrade secondary appliance and try to relogin in until it finishes rebooting
    upgrade(child1, remote_path2, build_file)
    logging.debug('returned from upgrade: %s', host1)
    login_ssh(child1, host1, user, password)   
    logging.debug('returned from relogin: %s', host1)
    nitro1 = login_nitro(host1, user, password)
    
    #re-enable ha sync/prop on second appliance and force it back to secondary
    enablesync(nitro2)
    enableha(nitro2) 
    saveconfig(nitro2)
    forcefailover(nitro2)
    
    #need to properly clean-up nitro and ssh sessions here.
    child1.sendline('exit')
    logging.debug(child1.after)
    child2.sendline('exit')
    logging.debug(child2.after)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upgrade a NetScaler High Availability Pair for fun and profit!')
    parser.add_argument("-d", "--debug", help="log level", action="store_true")
    parser.add_argument("-1", "--primary", required=True, help="ip address of primary NS")
    parser.add_argument("-2", "--secondary", required=True, help="ip address of secondary NS")
    parser.add_argument("-u", "--user", required=True, help="user name")
    parser.add_argument("-p", "--password", required=True, help="password")
    parser.add_argument("-l", "--local_path", required=True, help="local path to build file, for example: /Users/jeffbr/Documents]")
    parser.add_argument("-r", "--docs_file", help="docs bundle")
    parser.add_argument("-b", "--build_file", required=True, help="build file, for example: build-10.5-55.8_nc.tgz")
    
    args = parser.parse_args()
    main(args)
