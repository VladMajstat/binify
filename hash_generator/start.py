#!/usr/bin/env python3
import sys
import importlib
import importlib.util
import os

def print_diagnostics():
    try:
        print('PYTHONPATH:', sys.path)
        try:
            spec = importlib.util.find_spec('hash_generator')
        except Exception as e:
            spec = f'find_spec failed: {e}'
        print('FIND_SPEC:', spec)
        for p in ('/app', '/app/hash_generator', '/app/hash_generator/hash_generator'):
            try:
                print(p + ':', os.listdir(p))
            except Exception as e:
                print(p + ': cannot list ->', e)
        # print some env vars useful for debugging
        for k in ('UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'REDIS_HOST'):
            print(f'{k}={os.getenv(k)}')
    except Exception as e:
        print('diagnostics failed:', e)

if __name__ == '__main__':
    print_diagnostics()
    # Replace current process with uvicorn (preserves signals)
    os.execvp('uvicorn', ['uvicorn', 'hash_generator.hash_service:app', '--host', '0.0.0.0', '--port', '8081'])
