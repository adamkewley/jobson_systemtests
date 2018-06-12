#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import argparse
import sys

import jobson_systemtests


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Run jobson system tests')

    parser.add_argument(
        'specs_dir',
        type=str,
        help='Path to directory containing jobson specs (and tests)')
    parser.add_argument(
        'host',
        type=str,
        help='The host running the server (e.g. localhost)')
    parser.add_argument(
        'port',
        type=int,
        help='The port the Jobson API is listening on (e.g. 8080)')
    parser.add_argument(
        'login',
        type=str,
        help='The login to use to access the API')
    parser.add_argument(
        'password',
        type=str,
        help='The password to use the access the API')

    args = parser.parse_args(argv[1:])

    jobson_systemtests.run(
        specs_dir=args.specs_dir,
        host=args.host,
        port=args.port,
        login=args.login,
        password=args.password)

    return 0


if __name__ == "__main__":
    sys.exit(main())
