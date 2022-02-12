import shutil
import os


def pytest_sessionfinish(session, exitstatus):
    if os.path.exists('TEMP'):
        shutil.rmtree('TEMP')
