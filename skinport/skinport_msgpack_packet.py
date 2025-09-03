import struct
import msgpack
from socketio.msgpack_packet import MsgPackPacket

# Definim clasele lipsă dacă nu există în msgpack
try:
    from msgpack import Timestamp, ExtType
except ImportError:
    # Implementare minimală a claselor lipsă
    class ExtType:
        def __init__(self, code, data):
            self.code = code
            self.data = data

    class Timestamp:
        @staticmethod
        def from_unix(unix_time):
            return unix_time
            
        @staticmethod
        def to_unix():
            return 0

class SkinportMsgPackPacket(MsgPackPacket):

    def encode(self):
        """Encode the packet for transmission."""
        return msgpack.dumps(self._to_dict(), default=self._default)

    def decode(self, encoded_packet):
        """Decode a transmitted package."""
        decoded = msgpack.loads(encoded_packet, ext_hook=self._ext_hook)
        self.packet_type = decoded['type']
        self.data = decoded.get('data')
        self.id = decoded.get('id')
        self.namespace = decoded['nsp']

    def _ext_hook(self, code, data):
        if code == 0 and len(data) == 8:
            return self._decode_timestamp_from_ext(code, data)
        return ExtType(code, data)

    @staticmethod
    def _decode_timestamp_from_ext(code, data):
        milliseconds = struct.unpack("!Q", data)[0]
        try:
            return Timestamp.from_unix(milliseconds / 1000)
        except AttributeError:
            # Returnăm direct timestamp-ul ca float dacă clasa nu există
            return milliseconds / 1000

    def _default(self, obj):
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'Timestamp':
            return self._encode_timestamp_to_ext(obj)
        return obj

    @staticmethod
    def _encode_timestamp_to_ext(obj):
        try:
            milliseconds = int(obj.to_unix() * 1000)
        except AttributeError:
            # Presupunem că obiectul este deja un unix timestamp
            milliseconds = int(obj * 1000)
        return ExtType(0, struct.pack("!Q", milliseconds))

