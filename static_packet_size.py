import stl_path
from trex.stl.api import *
from pprint import pprint
from runner import run_test

duration = 20
pkt_payload = 64
multipliers = list(range(40000, 134001, 13428))
def create_stream(payload, dst_ip, src_ip_min, src_ip_max):
    scapy_pkt = Ether()/IP(dst=dst_ip)/UDP(sport=54321, dport=12345)/(payload*'\x55')

    vm = [
        STLVmFlowVar(name="src_ipv4", min_value=src_ip_min,
                     max_value=src_ip_max, size=4, op="inc"),
        STLVmWrFlowVar(fv_name="src_ipv4", pkt_offset="IP.src"),
        STLVmFixIpv4(offset="IP")
    ]

    burst = STLStream(packet=STLPktBuilder(pkt=scapy_pkt, vm=vm),
                      mode=STLTXCont())

    return burst

def create_streams(payload):
    stream_0 = create_stream(pkt_payload, "10.10.10.100", "192.168.88.2", "192.168.88.254")
    stream_1 = create_stream(pkt_payload, "192.168.88.100", "10.10.10.2", "10.10.10.254")

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
        streams = create_streams(pkt_payload)
        params = (
            c,
            streams,
            multipliers,
            duration
        )
        print_stats = lambda stats: print("Speed: %s Mbit/s, loss: %s" % (stats["speed"], "{:.6f}".format(stats["packet_loss"]).replace(".", ",")))
        final_stats = run_test(start_test, params, print_stats)
        pprint(final_stats)
    except STLError as e:
        print(e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()