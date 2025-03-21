import os
# dev
# redis_url = os.getenv("REDIS_URL", "redis://redis:6379")


class Config:
    # Redis configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Example usage of the Config class
if __name__ == "__main__":
    print(f"Redis Host: {Config.REDIS_HOST}")
    print(f"Redis Port: {Config.REDIS_PORT}")