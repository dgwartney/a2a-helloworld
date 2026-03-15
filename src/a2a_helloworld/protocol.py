"""A2A protocol constants shared by agent and client modules."""

from a2a.types import TransportProtocol

KNOWN_A2A_PROTOCOL_VERSIONS = {'0.1', '0.2', '0.3', '1.0'}

TRANSPORT_HTTP_JSON = TransportProtocol.http_json  # 'HTTP+JSON'
TRANSPORT_GRPC = TransportProtocol.grpc            # 'GRPC'
TRANSPORT_JSONRPC = TransportProtocol.jsonrpc       # 'JSONRPC'

SUPPORTED_TRANSPORTS = [TRANSPORT_HTTP_JSON, TRANSPORT_GRPC, TRANSPORT_JSONRPC]
