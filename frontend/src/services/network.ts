import api from "./api";

export interface NetworkDevice {
  ip: string;
  mac: string;
  hostname?: string;
  switch_ip?: string;
  switch_port?: string;
  lldp_chassis_id?: string;
  cdp_device_id?: string;
  interface?: string;
  state?: string;
  source?: string;
}

export interface NetworkTopologyResponse {
  available: boolean;
  discovered_at: string;
  devices: NetworkDevice[];
  local_interfaces: Array<{
    name: string;
    ip: string;
    prefix_length: number;
  }>;
  switch_topology: Array<{
    switch_ip: string;
    topology: Array<{
      mac: string;
      port_name: string;
      lldp_chassis_id?: string;
      cdp_device_id?: string;
    }>;
  }>;
}

export const DEMO_TOPOLOGY: NetworkTopologyResponse = {
  available: true,
  discovered_at: new Date().toISOString(),
  devices: [
    {
      ip: "192.168.10.1",
      mac: "aa:bb:cc:00:01:01",
      hostname: "core-sw01",
      switch_ip: "192.168.10.1",
      switch_port: "GigabitEthernet1/0/1",
      lldp_chassis_id: "core-sw01",
      cdp_device_id: "core-sw01",
      interface: "Ethernet0",
      state: "Reachable",
      source: "snmp",
    },
    {
      ip: "192.168.10.2",
      mac: "aa:bb:cc:00:02:01",
      hostname: "dist-sw01",
      switch_ip: "192.168.10.1",
      switch_port: "GigabitEthernet1/0/2",
      lldp_chassis_id: "dist-sw01",
      cdp_device_id: "dist-sw01",
      interface: "Ethernet1",
      state: "Reachable",
      source: "snmp",
    },
    {
      ip: "192.168.10.10",
      mac: "aa:bb:cc:00:10:01",
      hostname: "veeam-server",
      switch_ip: "192.168.10.2",
      switch_port: "GigabitEthernet1/0/12",
      lldp_chassis_id: "",
      cdp_device_id: "veeam-server",
      interface: "Ethernet2",
      state: "Reachable",
      source: "arp",
    },
    {
      ip: "192.168.10.20",
      mac: "aa:bb:cc:00:20:01",
      hostname: "hyperv-host01",
      switch_ip: "192.168.10.2",
      switch_port: "GigabitEthernet1/0/24",
      lldp_chassis_id: "",
      cdp_device_id: "hyperv-host01",
      interface: "Ethernet3",
      state: "Reachable",
      source: "arp",
    },
    {
      ip: "192.168.10.30",
      mac: "aa:bb:cc:00:30:01",
      hostname: "nas-storage01",
      switch_ip: "192.168.10.2",
      switch_port: "GigabitEthernet1/0/36",
      lldp_chassis_id: "",
      cdp_device_id: "nas-storage01",
      interface: "Ethernet4",
      state: "Reachable",
      source: "arp",
    },
    {
      ip: "192.168.10.40",
      mac: "aa:bb:cc:00:40:01",
      hostname: "corhqrobertb",
      switch_ip: "192.168.10.2",
      switch_port: "GigabitEthernet1/0/48",
      lldp_chassis_id: "",
      cdp_device_id: "CORHQROBERTB",
      interface: "Ethernet5",
      state: "Reachable",
      source: "arp",
    },
  ],
  local_interfaces: [
    { name: "Ethernet0", ip: "192.168.10.1", prefix_length: 24 },
    { name: "Ethernet1", ip: "192.168.10.2", prefix_length: 24 },
  ],
  switch_topology: [
    {
      switch_ip: "192.168.10.1",
      topology: [
        {
          mac: "aa:bb:cc:00:02:01",
          port_name: "GigabitEthernet1/0/2",
          lldp_chassis_id: "dist-sw01",
          cdp_device_id: "dist-sw01",
        },
      ],
    },
    {
      switch_ip: "192.168.10.2",
      topology: [
        {
          mac: "aa:bb:cc:00:10:01",
          port_name: "GigabitEthernet1/0/12",
          lldp_chassis_id: "",
          cdp_device_id: "veeam-server",
        },
        {
          mac: "aa:bb:cc:00:20:01",
          port_name: "GigabitEthernet1/0/24",
          lldp_chassis_id: "",
          cdp_device_id: "hyperv-host01",
        },
        {
          mac: "aa:bb:cc:00:30:01",
          port_name: "GigabitEthernet1/0/36",
          lldp_chassis_id: "",
          cdp_device_id: "nas-storage01",
        },
        {
          mac: "aa:bb:cc:00:40:01",
          port_name: "GigabitEthernet1/0/48",
          lldp_chassis_id: "",
          cdp_device_id: "CORHQROBERTB",
        },
      ],
    },
  ],
};

export const networkApi = {
  getTopology(agentId: number) {
    return Promise.resolve({ data: DEMO_TOPOLOGY });
  },
};
