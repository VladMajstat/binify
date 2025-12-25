#!/usr/bin/env python3
import sys
import importlib
import os

def print_diagnostics():
    try:
        print('PYTHONPATH:', sys.path)
        print('FIND_SPEC:', importlib.util.find_spec('hash_generator'))
        for p in ('/app', '/app/hash_generator', '/app/hash_generator/hash_generator'):
            try:
                print(p + ':', os.listdir(p))
            except Exception as e:
                print(p + ': cannot list ->', e)
    except Exception as e:
        print('diagnostics failed:', e)

if __name__ == '__main__':
    print_diagnostics()
    # Replace current process with uvicorn (preserves signals)
    os.execvp('uvicorn', ['uvicorn', 'hash_generator.hash_service:app', '--host', '0.0.0.0', '--port', '8081'])
