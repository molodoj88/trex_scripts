from typing import Callable


def count_stats(stats: dict) -> dict:
    rx_port_ipackets = stats[1]["ipackets"]
    tx_port_opackets = stats[0]["opackets"]
    packet_loss = (tx_port_opackets - rx_port_ipackets) / tx_port_opackets

    speed = stats[0]["tx_bps"] / 1000 / 1000 # Mbit/s

    return {
        "speed": speed,
        "packet_loss": packet_loss
    }


def run_test(starter_func: Callable, params: tuple, one_test_finished_callback=None) -> list:
    """
    Runs test
    Arguments:
        starter_func: function that starts one test. Should return stats dict
        params: tuple of test parameters:
            1. stl client object
            2. list of streams to be generated
            3. list of multipliers for base flow to be used for test
            4. duration of test in seconds
    Returns: list with statistics for each run (number of elements = number of multipliers)
    """
    client = params[0]
    streams = params[1]
    multipliers = params[2]
    duration = params[3]

    final_stats = []

    for m in multipliers:
        stats = starter_func(client, streams, m, duration)
        counted_stats = count_stats(stats)
        final_stats.append(counted_stats)
        if one_test_finished_callback is not None:
            try:
                one_test_finished_callback(counted_stats)
            except Exception as e:
                print("Cannot cexecute callback function: {}".format(e))
    
    return final_stats
