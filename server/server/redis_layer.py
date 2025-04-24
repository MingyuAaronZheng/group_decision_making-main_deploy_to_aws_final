# myproject/redis_layer.py

from channels_redis.core import RedisChannelLayer

class TaggedRedisChannelLayer(RedisChannelLayer):
    """
    Subclass RedisChannelLayer to force all keys into the same Redis Cluster slot
    by prepending a fixed hash-tag in braces.
    """

    def make_key(self, key: str, key_type: str) -> str:
        # Let the parent build the standard key:
        base = super().make_key(key, key_type)
        # Prepend a constant tag in {braces} so ALL keys land in the same slot
        return f"{{chat-hash}}:{base}"
