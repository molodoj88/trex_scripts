import stl_path
from trex.stl.api import *
from pprint import pprint
from runner import run_test

duration = 20
max_packet_payload = 1400
multipliers = list(range(6000, 20001, 2000))


def create_stream(max_packet_payload, dst_ip, src_ip_min, src_ip_max):
    p_l2 = Ether()
    p_l3 = IP(dst=dst_ip)
    p_l4 = UDP(sport=54321, dport=12345)

    payload_size = max(0, max_packet_payload - len(p_l3/p_l4))
    base_pkt = p_l2/p_l3/p_l4/('\x55'*(payload_size))

    l3_len_fix =-(len(p_l2))
    l4_len_fix =-(len(p_l2/p_l3))

    vm = [
        STLVmFlowVar(name="fv_rand", min_value=64, max_value=len(base_pkt), size=2, op="random"),
        STLVmFlowVar(name="src_ipv4", min_value=src_ip_min, max_value=src_ip_max, size=4, op="inc"),
        STLVmWrFlowVar(fv_name="src_ipv4", pkt_offset="IP.src"),
        STLVmTrimPktSize("fv_rand"), # total packet size
        STLVmWrFlowVar(fv_name="fv_rand", pkt_offset="IP.len", add_val=l3_len_fix), # fix ip len
        STLVmFixIpv4(offset="IP"),
        STLVmWrFlowVar(fv_name="fv_rand", pkt_offset= "UDP.len", add_val=l4_len_fix) # fix udp len
    ]

    packet = STLPktBuilder(pkt=base_pkt, vm=vm)
    burst = STLStream(packet=packet, random_seed=0x1234, mode=STLTXCont())
    return burst


def create_streams(max_packet_payload):
    stream_0 = create_stream(max_packet_payload, "10.10.10.100", "192.168.88.2", "192.168.88.254")
    stream_1 = create_stream(max_packet_payload, "192.168.88.100", "10.10.10.2", "10.10.10.254")

    return [stream_0, stream_1]


def start_test(client, streams, multiplier, duration):
    client.reset(ports=[0, 1])
    client.add_streams(ports=[0, 1], streams=streams)
    client.start(ports=[0, 1], mult="%dpps" % multiplier, duration=duration)
    client.wait_on_traffic(ports=[0, 1])

    stats = client.get_stats()

    return stats


def main():
    c = STLClient(server='127.0.0.1')
    try:
        c.connect()
        streams = create_streams(max_packet_payload)
        params = (
            c,
            streams,
            multipliers,
            duration
        )
        print_stats = lambda stats: print("Speed: %s Mbit/s, loss: %f" % (stats["speed"], stats["packet_loss"]))
        final_stats = run_test(start_test, params, print_stats)
        pprint(final_stats)
    except STLError as e:
        print(e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()