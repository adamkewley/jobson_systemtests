==================
jobson_systemtests
==================

A CLI utility for system testing a Jobson server

Install
-------

.. code-block:: bash
    pip3 install .


Usage
-----

Each spec in `specs/` *may* contain a `test.yml` file. If a `test.yml` file is found, the
tests declared within are ran.


.. code-block:: bash

    jobson_systemtests specs/ localhost 8080 username password


Example `tests.yml` (in e.g. `specs/{spec-id}/tests.yml`):

.. code-block:: yaml

    ---
    tests:

      should_work_when_given_a_name:

        inputs:
          name: J. Doe

        expectations:
          isAccepted: true
          finalStatus: finished


      shouldnt_work_if_given_wrong_input:

        inputs:
          some_non_existent_input:
          - bogus

        expectations:
          isAccepted: false


      shouldnt_work_when_given_the_name_foo:

        inputs:
          name: foo

        expectations:
          isAccepted: true
          finalStatus: fatal-error
