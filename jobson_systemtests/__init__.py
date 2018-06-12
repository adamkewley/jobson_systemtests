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

import base64
import http
import http.client
import json
import logging
import os
import unittest
from _datetime import datetime
from itertools import repeat
from time import sleep

import yaml

__author__ = """Adam Kewley"""
__email__ = 'contact@adamkewley.com'
__version__ = '0.1.0'


def run(
    specs_dir,
    host,
    port,
    login,
    password):

    __SystemTests().run_all(specs_dir, host, port, login, password)


class __SystemTests(unittest.TestCase):
    seconds_between_polling_requests = 3
    safety_limit_on_request_polling = 2000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("jobson_systemtests")

    def run_all(self, specs_dir, host, port, login, password):
        self.test_can_request_list_of_jobs(host, port, login, password)
        self.test_can_request_list_of_specs(host, port, login, password)
        self.test_can_run_all_test_yaml_files(specs_dir, host, port, login, password)

    def test_can_request_list_of_jobs(self, host, port, username, password):
        http_conn = http.client.HTTPConnection(host, port)
        try:
            http_conn.request("GET", "/v1/jobs", None, self._generate_req_headers(username, password))
            resp = http_conn.getresponse()
            self.assertEqual(resp.status, 200)
        finally:
            http_conn.close()

    def _generate_req_headers(self, username, password):
        return {
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode((username + ":" + password).encode("utf-8")).decode("utf-8"),
        }

    def test_can_request_list_of_specs(self, host, port, username, password):
        http_conn = http.client.HTTPConnection(host, port)
        try:
            http_conn.request("GET", "/v1/specs", None, self._generate_req_headers(username, password))
            resp = http_conn.getresponse()
            self.assertEqual(resp.status, 200)
        finally:
            http_conn.close()

    def test_can_run_all_test_yaml_files(self, specs_dir, host, port, username, password):
        self.logger.info("Attempting to run tests.yml files in each spec directory")
        specs_folder = _project_file(specs_dir)

        if not os.path.exists(specs_folder):
            raise AssertionError("%s: does not exist (has the deployment been built)?" % specs_folder)

        a_test_suite_failed = False

        for spec_folder in _subdirs_in(specs_folder):
            try:
                self._try_run_test_file(spec_folder, host, port, username, password)
            except AssertionError as ex:
                a_test_suite_failed = True
                self.logger.error("A test in {} failed: {}".format(spec_folder, ex))

        if a_test_suite_failed:
            raise AssertionError("One or more test suites failed")

    def _try_run_test_file(self, spec_folder, host, port, username, password):
        spec_id = os.path.basename(spec_folder)
        maybe_tests_file = os.path.join(spec_folder, "tests.yml")

        if os.path.exists(maybe_tests_file):
            self.logger.info("%s: has a tests.yml file. Running tests" % spec_id)
            self._run_test_file(spec_id, maybe_tests_file, host, port, username, password)
        else:
            self.logger.info("%s: does not have a tests.yml file. Skipping." % spec_id)

    def _run_test_file(self, spec_id, test_file_path, host, port, username, password):
        with open(test_file_path, 'r') as f:
            tests_data = yaml.load(f)

        a_test_failed = False

        for test_name, test_details in tests_data["tests"].items():
            try:
                self._run_test_file_test(spec_id, test_name, test_details, host, port, username, password)
            except AssertionError as ex:
                a_test_failed = True
                self.logger.error("{}: {} failed: {}.".format(spec_id, test_name, ex))
                self.logger.error("Moving on to next test")

        if a_test_failed:
            raise AssertionError("One or more tests failed")

    def _run_test_file_test(self, spec_id, test_name, test_details, host, port, username, password):
        http_conn = http.client.HTTPConnection(host, port)
        try:
            body = json.dumps({
                "spec": spec_id,
                "name": "systemtest_%s_%s" % (spec_id, test_name),
                "inputs": test_details["inputs"],
            })

            self.logger.info("%s: %s: Sending job request" % (spec_id, test_name))
            http_conn.request("POST", "/v1/jobs", body, self._generate_req_headers(username, password))

            resp = http_conn.getresponse()

            if "expectations" in test_details:
                result_expectations = test_details["expectations"]
            else:
                msg = "{}: {}: Does not have an expectations key".format(spec_id, test_name)
                self.logger.error(msg)
                raise RuntimeError(msg)

            self._handle_test_expectations(spec_id, test_name, http_conn, result_expectations, resp, username, password)
        finally:
            http_conn.close()

    def _handle_test_expectations(self, spec_id, test_name, http_conn, expectations, submission_response, username,
                                  password):
        status = submission_response.status

        if expectations.get("isAccepted", True):
            self.assertEqual(status, 200, "%s: %s: Should have been accepted but was rejected with status %s" % (
            spec_id, test_name, status))
            job_id = self._read_response_body_as_json(submission_response)["id"]
            self.logger.info(
                "%s: %s: Job request was accepted (as expected) and given an ID of '%s'" % (spec_id, test_name, job_id))
            self._handle_after_submission_test_expectations(spec_id, test_name, http_conn, expectations, job_id,
                                                            username, password)
        else:
            self.assertNotEqual(status, 200,
                                "%s: %s: Should have been rejected but was accepted" % (spec_id, test_name))
            self.logger.info("%s: %s: Job request was rejected (as expected)" % (spec_id, test_name))

    def _read_response_body_as_json(self, response):
        return json.loads(response.read().decode("utf-8"))

    def _handle_after_submission_test_expectations(self, spec_id, test_name, http_conn, expectations, job_id, username,
                                                   password):
        self.logger.info("%s: %s: Polling the job for its final status" % (spec_id, test_name))
        submission_time = datetime.now()
        final_job_details = self._poll_for_final_job_details(http_conn, job_id, username, password)
        final_status = self._extract_latest_status(final_job_details)
        end_time = datetime.now()
        self.logger.info("%s: %s: Final status was '%s'" % (spec_id, test_name, final_status))

        self.assertEqual(expectations.get("finalStatus", "finished"), final_status)

        outputs_expectations = expectations.get("outputs", None)

        if outputs_expectations is not None:
            self.logger.info("%s: %s: Has output expectations. Testing that the job produced the expected outputs" % (
            spec_id, test_name))
            self._handle_outputs_expectations(spec_id, test_name, http_conn, outputs_expectations, job_id, username,
                                              password)

    def _poll_for_final_job_details(self, http_conn, job_id, username, password):
        for _ in repeat(self.safety_limit_on_request_polling):
            job_details = self._get_job_details(http_conn, job_id, username, password)
            status = self._extract_latest_status(job_details)
            if status in ["finished", "fatal-error", "aborted"]:
                return job_details
            sleep(self.seconds_between_polling_requests)

    def _get_job_details(self, http_conn, job_id, username, password):
        http_conn.request("GET", "/v1/jobs/" + job_id, None, self._generate_req_headers(username, password))
        resp = http_conn.getresponse()
        self.assertEqual(resp.status, 200)
        return json.loads(resp.read().decode("utf-8"))

    def _extract_latest_status(self, job_details):
        return job_details["timestamps"][-1]["status"]

    def _handle_outputs_expectations(self, spec_id, test_name, http_conn, outputs_expectations, job_id, username,
                                     password):
        http_conn.request("GET", "/v1/jobs/%s/outputs" % job_id, None, self._generate_req_headers(username, password))
        job_outputs_resp = http_conn.getresponse()

        self.assertEqual(job_outputs_resp.status, 200)

        job_outputs_metadata = self._read_response_body_as_json(job_outputs_resp)

        for output_expectation in outputs_expectations:
            matcher = self._get_output_id_matcher(output_expectation["id"])
            self._handle_output_expectation(spec_id, test_name, http_conn, output_expectation, job_id)

    def _get_output_id_matcher(self, expected_id):
        if expected_id.startswith("/"):
            ()
        else:
            ()

    def _handle_output_expectation(self, spec_id, test_name, http_conn, output_expectation, output_id):
        ()


def _project_file(path):
    """
    Returns the supplied path resolved relative to the project root.
    """
    return os.path.join(os.path.dirname(__file__), path)


def _subdirs_in(path):
    dir_names = next(os.walk(path))[1]
    return map(lambda dir_name: os.path.join(path, dir_name), dir_names)

