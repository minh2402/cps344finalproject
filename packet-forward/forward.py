class Router:
    def __init__(self, ip_address, forward_table):
        self.ip_address = ip_address
        self.forward_table = forward_table

    def forward(self, ip_addr):
        neighbor = self.forward_table.get(ip_addr)
        if neighbor is None:
            neighbor = self.forward_table.get('*')
        if neighbor is None:
            raise KeyError(f"No route from {self.ip_address} to {ip_addr}")
        return neighbor

def get_packet_route(src_ip, dst_ip, network_map, max_hops=8):
    hops = [src_ip]
    for i in range(max_hops):
        current_hop = hops[-1]

        # if we have too many hops, we have a loop (drop packet)
        if i == max_hops - 1:
            hops.append('x (dropped)')
            break

        # if current_hop is dst, return hops
        elif current_hop == dst_ip:
            break

        # else, find the next hop using the router forwarding table
        else:   
            next_hop = network_map[current_hop].forward(dst_ip)
            hops.append(next_hop)
    
    # print the route
    print('Route: ', end='')
    for hop in hops[:-1]:
        print(f'{hop} -> ', end='')
    print(hops[-1])

    return hops


if __name__=='__main__':
    # network map for first network example
    network_map = {
        '0000': Router('0000', {'*': '0011'}),
        '0001': Router('0001', {'*': '0011'}),
        '0010': Router('0010', {'*': '0100'}),
        '0011': Router('0011', {'0000': '0000', '0001': '0001', '*': '0100'}),
        '0100': Router('0100', {'0010': '0010', '*': '0011'}),
    }

    # Here are some get_packet_route examples
    # These currently drop since the Router.forward() method is not implemented
    # TODO: implement Router.forward()
    get_packet_route('0000', '0001', network_map)
    get_packet_route('0010', '0000', network_map)

    # after that is working, implement the second network_map and uncomment the following lines
    # network_map = {} # TODO: implement network_map

    # get_packet_route('0000', '0111', network_map)
    # get_packet_route('0100', '0101', network_map)
