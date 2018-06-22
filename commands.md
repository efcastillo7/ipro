 https://github.com/gwacter-zz/sdn-workshop/blob/master/exercises/03-simple-switch.md

 Wireshark
 	sudo wireshark &>/dev/null &

 Command from mininet console	
	 mn> py h2.IP()
	 mn> h1 ping -c 3 h2

Start mininet with 3 hosts connected to 1 switch
 	mn --topo=tree,1,3 --mac --controller=remote --switch ovsk,protocols=OpenFlow13



 sudo mn --topo single,3 --mac --controller remote --switch ovsk

 Clear all mininet components
 	# mn -c

 Ensure that no other controller is present	
 	# killall controller

 Start the Ryu simple switch application	 	
 	# export RYU_APP=/usr/local/lib/python2.7/dist-packages/ryu/app/

 	# cd ~/ryu/ && ./bin/ryu-manager --verbose ryu/app/ipro/intelligent_probing.py

Ensure that the bridge is using OpenFlow13
	mininet> sh ovs-vsctl set bridge s1 protocols=OpenFlow13

Dump flows on switch s1
	"A flow is the most fine-grained work unit of a switch. In Mininet, dpctl is a command that allows visibility and control over a single switch's flow table. It is especially useful for debugging, by viewing flow state and flow counters."

	mininet> dpctl dump-flows -O OpenFlow13