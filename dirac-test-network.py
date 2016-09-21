#!/usr/bin/env python
"""Module for testing network conections."""
import re
import sys
import argparse
import socket
import logging
import ConfigParser
import collections

Address = collections.namedtuple('address', ('host', 'port', 'servicename'))
Family = {getattr(socket, i): i for i in dir(socket) if i.startswith('AF_')}
Socktype = {getattr(socket, i): i for i in dir(socket) if i.startswith('SOCK_')}
Proto = {getattr(socket, i): i for i in dir(socket) if i.startswith('IPPROTO_')}


def test_address(host, port, servicename=''):
    """
    Test the connection to a given address.

    This function will attempt to connect a streaming socket to the
    provided address (host, port). This checks both ipv4 and ipv6 if available.

    Args:
        host (str): The hostname or ip address of a host machine.
        port (int): The port number which to connect to.
        servicename (str): Optional name to display for the service we
                           are connecting to.

    Returns:
        tuple: A tuple containing the statistics of the number of connection
               attempts (passed, skipped and failed) in that order.

    Example:
        >>> passed, skipped, failed = test_address('google.com', 80, 'Web Server')
        >>> print passed, skiped, failed
        (2, 0, 0)

        if you have previously set up the python logging system then you will also see
        the following logging output:
        INFO:root:Testing address google.com:80 (Web Server)
        INFO:root:      Addr: 2a00:1450:4009:80e::200e:80, Family: AF_INET6, Socktype: SOCK_STREAM, Proto: IPPROTO_TCP ... PASSED
        INFO:root:      Addr: 216.58.213.78:80, Family: AF_INET, Socktype: SOCK_STREAM, Proto: IPPROTO_TCP ... PASSED
    """
    if servicename:
        servicename = '(%s)' % servicename
    logging.info("Testing address %s:%s %s", host, port, servicename)
    try:
        addrinfo = socket.getaddrinfo(host, port)
    except socket.error as err:
        logging.error("Exception in getaddrinfo(%s, %s): %s", host, port, str(err))
        raise

    logging.debug("Return from getaddrinfo(%s, %s): %s", host, port, addrinfo)
    if not addrinfo:
        logging.warning("No information returned from getaddrinfo(%s, %s)", host, port)
        return (0, 0, 0)

    passed = 0
    skipped = 0
    failed = 0
    for result in addrinfo:
        if result[1] != socket.SOCK_STREAM:
            continue
        log_msg = '\tAddr: {addr[0]}:{addr[1]}, Family: {family}, Socktype: {socktype}, Proto: {proto} ... '.format(addr=result[4], family=Family[result[0]], socktype=Socktype[result[1]], proto=Proto[result[2]])
        try:
            sock = socket.socket(*result[0:3])
        except socket.error as err:
            skipped += 1
            logging.warning(log_msg + "SKIPPED")
            logging.debug(log_msg + str(err))
            continue

        try:
            sock.connect(result[4])
            sock.close()
            passed += 1
            logging.info(log_msg + "PASSED")
        except socket.error as err:
            failed += 1
            logging.warning(log_msg + "FAILED")
            logging.debug(log_msg + str(err))
    return (passed, skipped, failed)

__all__ = ('test_address',)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test network connections.')
    parser.add_argument('-v', '--verbose', action='store_const', const=logging.DEBUG,
                        default=logging.INFO, dest='logginglevel',
                        help='Output debugging log messages')
    parser.add_argument('-c', '--config', action='append', metavar='configfile', dest='configfiles',
                        default=[],
                        help="Parse a config file. This allows you to store a list of addresses "
                             "in a configuration file rather than type them into the command line "
                             "each time. The format for the configuration file is similar to an "
                             "ini file. It is divided into sections by host and has key value "
                             "pairs for each. These pairs map a service name to a port e.g "
                             "[google.com] WebServer = 80. This option can be given multiple "
                             "times and config files are parsed in the order they are given with "
                             "newer values overriding older ones.")
    parser.add_argument('addresses', nargs='*', default=[], metavar='address',
                        help='A network address host name and port separated with a colon. '
                             'e.g. google.com:80. Note one can also use ip literals '
                             'e.g. 192.168.0.1:80 or [2001:db8:1f70::999:de8:7648:6e8]:100. '
                             'In the case of ipv6, because zeros are omitted with double colons '
                             '::, the host ip address is enclosed in square brackets [ ] to '
                             'distinguish it from the port number as per RFC 3986, section 3.2.2: '
                             'Host (http://www.ietf.org/rfc/rfc3986.txt).')
    args = parser.parse_args()
    logging.basicConfig(level=args.logginglevel, format="%(levelname)8s : %(message)s")
    logging.debug("Program args: %s", args)

    config_addresses = []
    if args.configfiles:
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        read_config = set(config.read(args.configfiles))
        unread_config = set(args.configfiles).difference(read_config)
        if unread_config:
            logging.warning("Failed to read the following config files: %s", list(unread_config))

        logging.debug("Requested Config:")
        logging.debug("*****************")
        for host in config.sections():
            logging.debug(host)
            for servicename, port in config.items(host):
                logging.debug("\t%s: %s", servicename, port)
                config_addresses.append(Address(host, port, servicename))
        logging.debug("*****************")

    if not args.addresses and not config_addresses:
        logging.error("Please specify an address (host:port) to test.")
        logging.error("Try %s -h for help.", parser.prog)
        sys.exit()

    passed = 0
    skipped = 0
    failed = 0
    for address in config_addresses:
        try:
            p, s, f = test_address(address.host.strip('[]'),
                                   int(address.port),
                                   address.servicename)
        except socket.error:
            # sys.exit("Program terminated due to error.")
            continue
        passed += p
        skipped += s
        failed += f

    address_regex = re.compile(r'^([0-9a-zA-Z._/]+|\[[0-9a-fA-F:]+\]):(\d+)$')
    for address in args.addresses:
        match = address_regex.match(address)
        if not match:
            logging.warning("address '%s' is not valid, skipping...", address)
            continue
        host, port = match.groups()
        try:
            p, s, f = test_address(host.strip('[]'), int(port))
        except socket.error:
            # sys.exit("Program terminated due to error.")
            continue
        passed += p
        skipped += s
        failed += f

    logging.info("Summary:")
    logging.info("--------")
    logging.info("\t#Passed : %s", passed)
    logging.info("\t#Skipped: %s", skipped)
    logging.info("\t#Failed : %s", failed)
    logging.shutdown()
