class Packet:
    def __init__(self, src_ip, dst_ip, src_port, dst_port):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port

    def __repr__(self):
        return f'Packet({self.src_ip}, {self.dst_ip}, {self.src_port}, {self.dst_port})'

class Action:
    def __init__(self, action_type, action_value=None):
        # action_type: 'forward' or 'drop'
        self.action_type = action_type
        # for 'forward', action_value is the next router
        self.action_value = action_value


class SDNRouter:
    def __init__(self, ip_address, rules):
        self.ip_address = ip_address
        # rules is a list of (Match functions, Action) tuples
        self.rules = rules

    def forward(self, packet):
        for match_func, action in self.rules:
            if match_func(packet):
                if action.action_type == 'forward':
                    return action.action_value
                elif action.action_type == 'drop':
                    return 'drop'

        # if no rule matches, return 'drop'
        return 'drop'

def get_packet_route(packet, network_map, max_hops=8):
    hops = [packet.src_ip]
    for i in range(max_hops):
        current_hop = hops[-1]

        # if we have too many hops, we have a loop (drop packet)
        if i == max_hops - 1:
            hops.append('x (dropped)')
            break

        # if current_hop is dst, return hops
        elif current_hop == packet.dst_ip:
            break

        # else, find the next hop using the router forwarding table
        else:   
            next_hop = network_map[current_hop].forward(packet)
            if next_hop == 'drop': # SDNRouter dropped the packet
                hops.append('x (dropped)')
                break
            hops.append(next_hop)
    
    # print the route
    print(f'{packet}: ', end='')
    for hop in hops[:-1]:
        print(f'{hop} -> ', end='')
    print(hops[-1])

    return hops

# match functions (add some more!)
def match_dst_port_22(packet):
    return packet.dst_port == '22'

def match_dst_port_80(packet):
    return packet.dst_port == '80'

def match_dst_ip_0000(packet):
    return packet.dst_ip == '0000'

def match_dst_ip_0001(packet):
    return packet.dst_ip == '0001'

def match_dst_ip_0011(packet):
    return packet.dst_ip == '0011'

def match_dst_ip_0000_and_dst_port_22(packet):
    return packet.dst_ip == '0000' and packet.dst_port == '22'

def match_dst_ip_0001_and_dst_port_22(packet):
    return packet.dst_ip == '0001' and packet.dst_port == '22'

if __name__=='__main__':
    # network map for first network example
    network_map = {
        '0000': SDNRouter('0000',
            [
                (match_dst_port_22, Action('forward', '0010')), 
                (match_dst_ip_0001, Action('forward', '0011')),
            ]),
        '0001': SDNRouter('0001', 
            [
                (match_dst_port_22, Action('forward', '0010')), 
                (match_dst_ip_0000, Action('forward', '0011')),
            ]),
        '0010': SDNRouter('0010', 
            [
                (lambda p: p.dst_ip == '0000' and p.dst_port == '22', Action('forward', '0000')),
                (lambda p: p.dst_ip == '0001' and p.dst_port == '22', Action('forward', '0001')),
            ]),
        '0011': SDNRouter('0011', 
            [
                (match_dst_port_80, Action('drop')), 
                (match_dst_ip_0000, Action('forward', '0000')), 
                (match_dst_ip_0001, Action('forward', '0001')),
            ]),
    }

    # HTTPS request packet (should succeed)
    p1 = Packet('0000', '0001', '34213', '8080')

    # HTTPS response packet (should succeed)
    p2 = Packet('0001', '0000', '8080', '34213')

    # HTTP packets (should be dropped by 0011 router)
    p3 = Packet('0000', '0011', '32123', '80')
    p4 = Packet('0011', '0000', '80', '32123')

    # SSH packets get special treatment
    p5 = Packet('0000', '0010', '12314', '22')
    p6 = Packet('0010', '0000', '22', '12314')

    packets = [p1, p2, p3, p4, p5, p6]
    for packet in packets:
        get_packet_route(packet, network_map)
