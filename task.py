from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import argparse


modes_to_names = {socket.SOCK_STREAM: 'TCP', socket.SOCK_DGRAM: 'UDP'}


def is_port_free(mode, address, sock):
    ok = False
    try:
        if mode == socket.SOCK_STREAM:
            sock.connect(address)
            ok = True
        elif mode == socket.SOCK_DGRAM:
            sock.sendto(b'query', address)
            sock.recvfrom(512)
            ok = True
    except OSError:
        ok = False

    sock.close()
    return ok


def run(host, start_port, end_port):
    result = []
    for mode in modes_to_names.keys():
        result.append(run_with_mode(mode, host, start_port, end_port))
    return result


def run_with_mode(mode, host, start_port, end_port):
    result = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_port = {}
        for port in range(start_port, end_port):
            new_socket = socket.socket(socket.AF_INET, mode)
            future = executor.submit(is_port_free, mode, (host, port), new_socket)
            future_to_port[future] = port

        for future in as_completed(future_to_port):
            port = future_to_port[future]
            try:
                port_is_free = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (port, exc))
            else:
                result.append((modes_to_names[mode], port, port_is_free))
    return result


def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("host", type=str)
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)

    return parser


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    result = run(args.host, args.start, args.end)

    for ports in result:
        for port_info in sorted(ports, key=lambda x: x[1]):
            protocol, port, is_open = port_info
            print(protocol, port, is_open)
        print('---------------------------')
