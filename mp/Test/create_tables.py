import sys
sys.path.insert(0, '/home/efcastillo/ryu/ryu/app/ipro/mp')
import ConnectionBD_v2

#we create table to store port statistics
#ConnectionBD_v2.createTablePort()
ConnectionBD_v2.createTableFlow()