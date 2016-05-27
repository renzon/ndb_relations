#!/usr/bin/env python
# coding: utf-8

import sys
import unittest

import os

PROJECT_PATH = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-2])
ROOT_PATH = os.path.dirname(__file__)


def main():
    fix_path()
    tests = unittest.TestLoader().discover(ROOT_PATH, "*.py")
    result = unittest.TextTestRunner().run(tests)
    if not result.wasSuccessful():
        sys.exit(1)


def fix_path():
    if 'GAE_SDK' in os.environ:
        SDK_PATH = os.environ['GAE_SDK']

        sys.path.insert(0, SDK_PATH)

        import dev_appserver
        dev_appserver.fix_sys_path()
    sys.path.append(os.path.join(PROJECT_PATH, '..'))


if __name__ == '__main__':
    main()
