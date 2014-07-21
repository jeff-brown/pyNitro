#!/usr/bin/python

#
# Copyright (c) 2008-2015 Citrix Systems, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License")
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http:#www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#


import sys
from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nsconfig import nsconfig
from nssrc.com.citrix.netscaler.nitro.util.filtervalue import filtervalue
from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver import lbvserver
from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_service_binding import lbvserver_service_binding
from nssrc.com.citrix.netscaler.nitro.resource.config.cs.csvserver import csvserver
from nssrc.com.citrix.netscaler.nitro.service.nitro_service import nitro_service
from nssrc.com.citrix.netscaler.nitro.resource.stat.lb.lbvserver_stats import lbvserver_stats
from nssrc.com.citrix.netscaler.nitro.resource.stat.cs.csvserver_stats import csvserver_stats
from nssrc.com.citrix.netscaler.nitro.resource.stat.lb.lbvserver_stats import lbvserver_stats
from nssrc.com.citrix.netscaler.nitro.resource.stat.basic.service_stats import service_stats
from nssrc.com.citrix.netscaler.nitro.resource.stat.basic.servicegroup_stats import servicegroup_stats
from nssrc.com.citrix.netscaler.nitro.resource.stat.basic.servicegroupmember_stats import servicegroupmember_stats
from nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup import servicegroup
from nssrc.com.citrix.netscaler.nitro.resource.config.basic.service import service
from nssrc.com.citrix.netscaler.nitro.resource.config.basic.server import server
from nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_servicegroupmember_binding import servicegroup_servicegroupmember_binding
from nssrc.com.citrix.netscaler.nitro.resource.config.basic.service import service
from nssrc.com.citrix.netscaler.nitro.resource.config.network.route import route
from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nsip import nsip
from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nsfeature import nsfeature
from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nsmode import nsmode

# This sample code demonstrates basic usage of the NITRO APIs
class nitro_demo : 
	def __init__(self):
		_ip=""
		_username=""
		_password=""

	@staticmethod
	def main(cls, args_):
		if(len(args_) < 3):
			print("Usage: run.bat <ip> <username> <password>")
			return

		config = nitro_demo()
		config.ip = args_[1]
		config.username = args_[2]
		config.password = args_[3] 

		try :
			client = nitro_service(config.ip,"http")
			client.set_credential(config.username,config.password)
			client.timeout = 500
			config.run_demo(client)
			client.logout()
		except nitro_exception as  e:
			print("Exception::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:         
			print("Exception::message="+str(e.args))
			return

	#0.1) clear config - full
	def clearconfig(self, client) :
		try :
			var = nsconfig()
			var.level = nsconfig.Level.extended
			nsconfig.clear(client, var)
			print("clearconfig - Done")
		except nitro_exception as e :
			print("Exception::clearconfig::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::clearconfig::message="+str(e.args))

	#0.2) save config
	def saveconfig(self, client) :
		try :
			obj = nsconfig()
			nsconfig.save(client,obj)
			print("saveconfig - Done")
		except nitro_exception as e :
			print("Exception::saveconfig::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::saveconfig::message="+str(e.args))

	#0.3) Perform basic configurations - routes, enable features, etc
	def base_config(self, client) : 
		try : 
			#enable basic features
			feature = [nsfeature.Feature.LB, nsfeature.Feature.CS, nsfeature.Feature.SSL]
			client.enable_features(feature)

			#enable MBF
			mode = [nsmode.Mode.MBF]
			client.enable_modes(mode)

			#configure snip in data plane
			nsip_obj = nsip()
			nsip_obj.ipaddress = "192.168.5.70"
			nsip_obj.netmask = "255.255.255.0"
			nsip.add(client, nsip_obj) 

			#change default gw to data plance
			route_obj = route()
			route_obj.network = "0.0.0.0"
			route_obj.netmask = "0.0.0.0"
			route_obj.gateway = "192.168.5.254"

			#remove old default gw from control plane
			route.add(client, route_obj) 
			route_obj.gateway = "10.217.242.1"
			route.delete(client, route_obj) 

			print("base_config - Done")
		except nitro_exception as e :
			print("Exception::base_config::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::base_config::message="+str(e.args))

	#1) Stat a vserver/servicegroup
	def stats(self, client, lbv_name, svc_name) : 
		try : 
			obj = lbvserver_stats.get(client, lbv_name)         
			print("statlbvserver_byname result::name="+lbvserver.get(client, lbv_name).ipv46+", servicetype="+obj.type +",totalrequests="+obj.totalrequests)

			obj_svc = service_stats.get(client, svc_name)         
			print("statservice_byname result::name="+obj_svc.name+", servicetype="+obj_svc.servicetype +",totalrequests="+obj_svc.totalrequests)

			#obj_svcgms = servicegroupmember_stats()
			#obj_svcgms.servicegroupname = svcg_name
			#obj_svcgms.ip = "192.168.2.10"
			#obj_svcgms.port = 80
			#obj1_svcgms = servicegroupmember_stats.get(client, obj_svcgms)
			#print("statservicegrpmem result::req="+obj1_svcgms.servicegroupname+", curClintConnctions="+obj1_svcgms.curclntconnections)
			print("stats - Done")
		except nitro_exception as e :
			print("Exception::stats::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::stats::message="+str(e.args))

	#2) disable/enable server/vserver/servicegroup
	def change_state(self, client, lbv_name, svc_name) : 
		try : 
			if lbvserver_stats.get(client, lbv_name).state == "ENABLED":
				lbvserver.disable(client, lbv_name)
			else:
				lbvserver.enable(client, lbv_name)

			print("service result::state="+service.get(client, svc_name).svrstate)

			if service.get(client, svc_name).svrstate == "UP":
				service.disable(client, svc_name)
			else:
				service.enable(client, svc_name)

			print("change_state - Done")
		except nitro_exception as e :
			print("Exception::change_state::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::change_state::message="+str(e.args))


	#add/modify service
	def add_service(self, client, svc_name):        
		try:            
			port=80            
			service1 = service()            
			service1.name = svc_name           
			service1.ip ="192.168.2.10"            
			service1.port = port           
			service1.servicetype ="http"            
			service.add(client, service1)                            
			print("add_service - Done")        
		except nitro_exception as e :            
			print("Exception::add_service::errorcode="+str(e.errorcode)+",message="+ e.message)        
		except Exception as e:            
			print("Exception::add_service::message="+str(e.args))

	#add/modify/remove basic vip
	def basic_lbv(self, client, lbv_name, svc_name) : 
		try : 
			#Create an instance of the virtual server class
			new_lbvserver_obj = lbvserver()

			#Create a new virtual server
			new_lbvserver_obj.name = lbv_name
			new_lbvserver_obj.ipv46 = "10.217.242.76"
			new_lbvserver_obj.servicetype = "HTTP"
			new_lbvserver_obj.port = 80
			new_lbvserver_obj.lbmethod = "ROUNDROBIN"

			#get all lbvservers and shove them into a list 
			#FIXME this is not working as expected it.  it sets all list members to the same lbv object
			resources = lbvserver.get(client)
			for resource in resources:
				if resource.name == lbv_name:
					print("lbvserver resource::name="+resource.name+" exists.")
					lbvserver.delete(client, new_lbvserver_obj)
					break
			lbvserver.add(client, new_lbvserver_obj)

			#bind service to lbv
			bindObj = lbvserver_service_binding()
			bindObj.name = lbv_name
			bindObj.servicename = svc_name
			bindObj.weight = 20
			lbvserver_service_binding.add(client, bindObj)

			print("basic_lbv - Done")
		except nitro_exception as e :
			print("Exception::basic_lbv::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::basic_lbv::message="+str(e.args))

	#don't use - infinite loop bug in SDK 10.5-50.10
	def bind_servicegroup_server(self, client, svcg_name) : 
		try :
			grp = servicegroup()
			grp.servicegroupname = svcg_name
			grp.servicetype = servicegroup.Servicetype.HTTP
			servicegroup.add(client, grp)
			obj = servicegroup_servicegroupmember_binding()
			obj.servicegroupname = svcg_name
			obj.ip = "192.168.2.10"
			obj.port = 80
			servicegroup_servicegroupmember_binding.add(client, obj)
			print("bind_servicegroup_server - Done")
		except nitro_exception as e :
			print("Exception::bind_servicegroup_server::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::bind_servicegroup_server::message="+str(e.args))

	#retrieve config/status (up/down only) for vserver/servicegroup/cs vserver 
	def check_status(self, client, lbv_name, svc_name) : 
		try : 

			#Retrieve state of a lbvserver
			obj_lbv = lbvserver_stats.get(client, lbv_name)
			print("statlbvserver_byname result::name="+obj_lbv.name+", servicetype="+obj_lbv.type +",state="+obj_lbv.state)

			#Retrieve state of a servicegroup
			obj_svc = service.get(client, svc_name)
			print("statsvcg_byname result::name="+obj_svc.name+", servicetype="+obj_svc.servicetype +",state="+obj_svc.svrstate)

			#filtered list of lbvservers
			filter_params = []
			filter_params = [filtervalue() for _ in range(1)]
			filter_params[0] = filtervalue("effectivestate","DOWN")       
			result_list = lbvserver.get_filtered(client, filter_params)
			if result_list :
				print("getlbvserver_svc_bindings result::length="+str(len(result_list)))
				for x in range(0, len(result_list)): 
					print("x="+str(x)+",lbvserver_byfilter result::name="+result_list[x].name+", servicetype="+result_list[x].servicetype +",state="+result_list[x].effectivestate)
			else:
				print("getlbvserver_svc_bindings :: Done")  

			print("check_status - Done")
		except nitro_exception as e :
			print("Exception::check_status::errorcode="+str(e.errorcode)+",message="+ e.message)
		except Exception as e:
			print("Exception::check_status::message="+str(e.args))

	#Gosub!
	def run_demo(self, client) :
		self.clearconfig(client) 
		self.base_config(client) 
		self.add_service(client, "nitro_svc")
		self.basic_lbv(client, "nitro_lbv", "nitro_svc") 
		#self.bind_servicegroup_server(client, "nitro_svc") #don't use this - infinite loop bug
		self.stats(client, "nitro_lbv", "nitro_svc") 
		self.change_state(client, "nitro_lbv", "nitro_svc")
		self.check_status(client, "nitro_lbv", "nitro_svc") 
		self.saveconfig(client)  

#
# Main thread of execution
#

if __name__ == '__main__':
	try:
		if len(sys.argv) != 4:
			sys.exit()
		else:
			ipaddress=sys.argv[1]
			username=sys.argv[2]
			password=sys.argv[3]
			nitro_demo().main(nitro_demo(),sys.argv)
	except SystemExit:
		print("Exception::Usage: Sample.py <directory path of Nitro.py> <nsip> <username> <password>")

