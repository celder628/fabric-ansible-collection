..
.. SPDX-License-Identifier: Apache-2.0
..

Hyperledger Fabric Ansible Collection
=====================================

This Ansible collection, enables you to automate the building of Hyperledger Fabric networks.

It supports creating these networks within:
- The IBM Hyperledger Fabric Support Offering
- The Hyperledger Fabric Open Source Stack (Hyperledger Labs `Fabric Operator <https://github.com/hyperledger-labs/fabric-operator>`_  and `Fabric Operations Console <https://github.com/hyperledger-labs/fabric-operations-console>`_)

Roles are provided to install the operations console and operator; additional roles and modules can then create the Fabric Network.

License
=======

Apache-2.0

Author Information
==================

..
   TODO: Confirm if this is still the case?

This Ansible collection is maintained by the IBM Blockchain development team.

..
.. Fabric Operator:

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   installation
   migrating-v12-v2.rst

.. toctree::
   :maxdepth: 2
   :caption: Tutorials
   :hidden:

   tutorials/oss-installing
   tutorials/hlfsupport-installing
   tutorials/building
   tutorials/joining
   tutorials/certificate-management
   tutorials/deploying

.. toctree::
   :maxdepth: 2
   :caption: Tasks
   :hidden:
   :glob:

   tasks/*

.. toctree::
   :maxdepth: 3
   :caption: Reference
   :hidden:

   modules
   roles

.. toctree::
   :maxdepth: 2
   :caption: Support
   :hidden:

   support

