Installation
============

Requirements
------------

* Python 3.12 or higher
* No runtime dependencies (by design)

Installing from Source
----------------------

Clone the repository and install in development mode:

.. code-block:: bash

    git clone https://github.com/aa-parky/pipeworks_name_generation.git
    cd pipeworks_name_generation
    pip install -e .

For development with testing tools:

.. code-block:: bash

    pip install -e ".[dev]"

Installing from PyPI
--------------------

.. note::
    Package not yet published to PyPI. Currently in Phase 1 (proof of concept).

Once published, you'll be able to install with:

.. code-block:: bash

    pip install pipeworks-name-generation

Verifying Installation
-----------------------

Verify the installation by running the proof of concept example:

.. code-block:: bash

    python examples/minimal_proof_of_concept.py

You should see output confirming deterministic name generation works correctly.

Next Steps
----------

* Read the :doc:`quickstart` guide to get started
* Explore the :doc:`user_guide` for detailed usage information
* Check out the :doc:`api_reference` for complete API documentation
