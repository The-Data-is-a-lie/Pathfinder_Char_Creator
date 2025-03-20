SECRET_KEY = 'ldkaf0-92ui0[9kl;jlk;jdf98ashj9f8das]l;jfads0989uyio3aw98ioph'
# prod
redis_url = "redis://red-cvakqvtrie7s7395c1m0:6379"  # Your Redis URL
# dev
# redis_url = "redis://localhost:6379"  # Your Redis URL 


import os

class Config:
    # Redis configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Example usage of the Config class
if __name__ == "__main__":
    print(f"Redis Host: {Config.REDIS_HOST}")
    print(f"Redis Port: {Config.REDIS_PORT}")