#!/usr/bin/python
#
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import base64
import urllib

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import _load_params

from ..module_utils.cert_utils import normalize_whitespace
from ..module_utils.dict_utils import (copy_dict, diff_dicts, equal_dicts,
                                       merge_dicts)
from ..module_utils.module import BlockchainModule
from ..module_utils.ordering_services import OrderingServiceNode
from ..module_utils.utils import (get_certificate_authority_by_module,
                                  get_console, get_ordering_service_by_module)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ordering_service_node
short_description: Manage a Hyperledger Fabric ordering service node
description:
    - Create, update, or delete a Hyperledger Fabric ordering service node.
    - This module works with the IBM Support for Hyperledger Fabric software or the Hyperledger Fabric
      Open Source Stack running in a Red Hat OpenShift or Kubernetes cluster.
author: Simon Stone (@sstone1)
options:
    api_endpoint:
        description:
            - The URL for the Fabric operations console.
        type: str
        required: true
    api_authtype:
        description:
            - C(basic) - Authenticate to the Fabric operations console using basic authentication.
              You must provide both a valid API key using I(api_key) and API secret using I(api_secret).
        type: str
        required: true
    api_key:
        description:
            - The API key for the Fabric operations console.
        type: str
        required: true
    api_secret:
        description:
            - The API secret for the Fabric operations console.
            - Only required when I(api_authtype) is C(basic).
        type: str
    api_timeout:
        description:
            - The timeout, in seconds, to use when interacting with the Fabric operations console.
        type: int
        default: 60
    state:
        description:
            - C(absent) - An ordering service node matching the specified name will be stopped and removed.
            - C(present) - Asserts that an ordering service node matching the specified name and configuration exists.
              If no ordering service node matches the specified name, an ordering service node will be created.
              If an ordering service node matches the specified name but the configuration does not match, then the
              ordering service node will be updated, if it can be. If it cannot be updated, it will be removed and
              re-created with the specified configuration.
        type: str
        default: present
        choices:
            - absent
            - present
    name:
        description:
            - The name for the ordering service node.
        type: str
        required: true
    ordering_service:
        description:
            - The name of the ordering service that this ordering service node belongs to.
            - You can pass a string, which is the display name of a ordering service registered
              with the Fabric operations console.
            - You can also pass a dictionary, which must match the result format of one of the
              M(ordering_service_info) or M(ordering_service) modules.
            - Only required when I(config) is not specified.
        type: str
    msp_id:
        description:
            - The MSP ID for this ordering service node.
            - Only required when I(state) is C(present).
        type: str
    orderer_type:
        description:
            - C(raft) - The ordering service node will use the Raft consensus algorithm.
        default: raft
        type: str
        choices:
            - raft
    system_channel_id:
        description:
            - The name of the system channel for this ordering service node.
        default: testchainid
        type: str
    config_block:
        description:
            - The path to where the config block for the system channel is stored.
            - You must first update the config for the system channel by adding this ordering service
              node into the consenter set of the system channel.
            - The config block will only be submitted to the ordering service node if the ordering
              service node has been pre-created and is not ready for use.
        type: str
    certificate_authority:
        description:
            - The certificate authority to use to enroll the identity for this ordering service node.
            - You can pass a string, which is the display name of a certificate authority registered
              with the Fabric operations console.
            - You can also pass a dictionary, which must match the result format of one of the
              M(certificate_authority_info) or M(certificate_authority) modules.
            - Only required when I(config) is not specified.
        type: raw
    enrollment_id:
        description:
            - The enrollment ID, or user name, of an identity registered on the certificate authority for this ordering service node.
            - Only required when I(config) is not specified.
        type: str
    enrollment_secret:
        description:
            - The enrollment secret, or password, of an identity registered on the certificate authority for this ordering service node.
            - Only required when I(config) is not specified.
        type: str
    admins:
        description:
            - The list of administrator certificates for this ordering service node.
            - Administrator certificates must be supplied as base64 encoded PEM files.
            - Only required when I(config) is not specified.
        type: list
        elements: str
    config:
        description:
            - The initial configuration for the ordering service node. This is only required if you need more advanced configuration than
              is provided by this module using I(certificate_authority) and related options.
        type: dict
    config_override:
        description:
            - The configuration overrides for the ordering service node.
            - "See the Hyperledger Fabric documentation for available options: https://github.com/hyperledger/fabric/blob/release-1.4/sampleconfig/core.yaml"
        type: dict
    crypto:
        description:
            - Component crypto configuration for connecting to a certificate authority
        type: dict
        suboptions:
            enrollment:
                description:
                    - Enrollment information for connecting to a certificate authority
                type: dict
                suboptions:
                    component:
                        description:
                            - Admin certificates for connecting to a certificate authority
                        type: dict
                        suboptions:
                            admins:
                                description:
                                    - An array that contains base 64 encoded PEM identity certificates for administrators. Also known as signing certificates of an organization administrator.
                                type: dict
                    ca:
                        description:
                            - Configuration for connecting to the certificate authority
                        type: dict
                        suboptions:
                            host:
                                description:
                                    - The CA's hostname. Do not include protocol or port. Must be a hostname from a known CA.
                                type: str
                            port:
                                description:
                                    - The CA's port.
                                type: str
                            name:
                                description:
                                    - The CA's "CAName" attribute. This name is used to distinguish this CA from the TLS CA.
                                type: str
                            tls_cert:
                                description:
                                    - The TLS certificate as base 64 encoded PEM. Certificate is used to secure/validate a TLS connection with this component.
                                type: str
                            enroll_id:
                                description:
                                    - The username of the enroll id.
                                type: str
                            enroll_secret:
                                description:
                                    - The password of the enroll id.
                                type: str
                    tlsca:
                        description:
                            - Configuration for connecting to the TLS certificate authority
                        type: dict
                        suboptions:
                            host:
                                description:
                                    - The CA's hostname. Do not include protocol or port. Must be a hostname from a known CA.
                                type: str
                            port:
                                description:
                                    - The CA's port.
                                type: str
                            name:
                                description:
                                    - The CA's "CAName" attribute. This name is used to distinguish this CA from the TLS CA.
                                type: str
                            tls_cert:
                                description:
                                    - The TLS certificate as base 64 encoded PEM. Certificate is used to secure/validate a TLS connection with this component.
                                type: str
                            enroll_id:
                                description:
                                    - The username of the enroll id.
                                type: str
                            enroll_secret:
                                description:
                                    - The password of the enroll id.
                                type: str
    resources:
        description:
            - The Kubernetes resource configuration for the ordering service node.
        type: dict
        suboptions:
            orderer:
                description:
                    - The Kubernetes resource configuration for the orderer container.
                type: dict
                suboptions:
                    requests:
                        description:
                            - The Kubernetes resource requests for the orderer container.
                        type: str
                        suboptions:
                            cpu:
                                description:
                                    - The Kubernetes CPU resource request for the orderer container.
                                type: str
                                default: 250m
                            memory:
                                description:
                                    - The Kubernetes memory resource request for the orderer container.
                                type: str
                                default: 500M
            proxy:
                description:
                    - The Kubernetes resource configuration for the proxy container.
                type: dict
                suboptions:
                    requests:
                        description:
                            - The Kubernetes resource requests for the proxy container.
                        type: str
                        suboptions:
                            cpu:
                                description:
                                    - The Kubernetes CPU resource request for the proxy container.
                                type: str
                                default: 100m
                            memory:
                                description:
                                    - The Kubernetes memory resource request for the proxy container.
                                type: str
                                default: 200M
    storage:
        description:
            - The Kubernetes storage configuration for the ordering service node.
        type: dict
        suboptions:
            orderer:
                description:
                    - The Kubernetes storage configuration for the orderer container.
                type: dict
                suboptions:
                    size:
                        description:
                            - The size of the Kubernetes persistent volume claim for the orderer container.
                        type: str
                        default: 100Gi
                    class:
                        description:
                            - The Kubernetes storage class for the the Kubernetes persistent volume claim for the orderer container.
                            - By default, the Kubernetes storage class for the Fabric operations console is used.
                        type: str
    hsm:
        description:
            - "The PKCS #11 compliant HSM configuration to use for the ordering service node."
        type: dict
        suboptions:
            pkcs11endpoint:
                description:
                    - The HSM proxy endpoint that the ordering service node should use.
                type: str
            label:
                description:
                    - The HSM label that the ordering service node should use.
                type: str
            pin:
                description:
                    - The HSM pin that the ordering service node should use.
                type: str
    zone:
        description:
            - The Kubernetes zone for this ordering service node.
            - If you do not specify a Kubernetes zone, and multiple Kubernetes zones are available, then a random Kubernetes zone will be selected for you.
            - "See the Kubernetes documentation for more information: https://kubernetes.io/docs/setup/best-practices/multiple-zones/"
        type: str
    version:
        description:
            - The version of Hyperledger Fabric to use for this ordering service node.
            - If you do not specify a version, the default Hyperledger Fabric version will be used for a new ordering service node.
            - If you do not specify a version, an existing ordering service node will not be upgraded.
            - If you specify a new version, an existing ordering service node will be automatically upgraded.
            - The version can also be specified as a version range specification, for example C(>=2.2,<3.0), which will match Hyperledger Fabric v2.2 and greater, but not Hyperledger Fabric v3.0 and greater.
            - "See the C(semantic_version) Python module documentation for more information: https://python-semanticversion.readthedocs.io/en/latest/reference.html#semantic_version.SimpleSpec"
        type: str
    wait_timeout:
        description:
            - The timeout, in seconds, to wait until the ordering service node is available.
        type: int
        default: 60
notes: []
requirements: []
'''

EXAMPLES = '''
- name: Create ordering service node
  hyperledger.fabric_ansible_collection.ordering_service_node:
    state: present
    api_endpoint: https://console.example.org:32000
    api_authtype: basic
    api_key: xxxxxxxx
    api_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    name: Ordering Service Node 2
    msp_id: OrdererOrgMSP
    certificate_authority: Orderer Org CA
    enrollment_id: orderingorgorderer
    enrollment_secret: orderingorgordererpw
    admin_certificates:
      - LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...

- name: Create ordering service node with custom resources and storage
  hyperledger.fabric_ansible_collection.ordering_service_node:
    state: present
    api_endpoint: https://console.example.org:32000
    api_authtype: basic
    api_key: xxxxxxxx
    api_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    name: Ordering Service Node 2
    msp_id: OrdererOrgMSP
    certificate_authority: Orderer Org CA
    enrollment_id: orderingorgorderer
    enrollment_secret: orderingorgordererpw
    admin_certificates:
      - LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
    resources:
      orderer:
        requests:
          cpu: 500m
          memory: 1000M
    storage:
      orderer:
        size: 200Gi
        class: ibmc-file-gold

- name: Create ordering service node that uses an HSM
  hyperledger.fabric_ansible_collection.ordering_service_node:
    state: present
    api_endpoint: https://console.example.org:32000
    api_authtype: basic
    api_key: xxxxxxxx
    api_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    name: Ordering Service Node 2
    msp_id: OrdererOrgMSP
    nodes: 5
    certificate_authority: Orderer Org CA
    enrollment_id: orderingorgorderer
    enrollment_secret: orderingorgordererpw
    admin_certificates:
      - LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
    hsm:
      pkcs11endpoint: tcp://pkcs11-proxy.example.org:2345
      label: Org1 CA label
      pin: 12345678

- name: Destroy ordering service node
  hyperledger.fabric_ansible_collection.ordering_service_node:
    state: absent
    api_endpoint: https://console.example.org:32000
    api_authtype: basic
    api_key: xxxxxxxx
    api_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    name: Ordering Service Node 2
'''

RETURN = '''
---
ordering_service_node:
    description:
        - The ordering service node.
    type: dict
    returned: when I(state) is C(present)
    contains:
        name:
            description:
                - The name of the ordering service node.
            type: str
            sample: Ordering Service_1
        api_url:
            description:
                - The URL for the API of the ordering service node.
            type: str
            sample: grpcs://orderingservice1-api.example.org:32000
        operations_url:
            description:
                - The URL for the operations service of the ordering service node.
            type: str
            sample: https://orderingservice1-operations.example.org:32000
        grpcwp_url:
            description:
                - The URL for the gRPC web proxy of the ordering service node.
            type: str
            sample: https://orderingservice1-grpcwebproxy.example.org:32000
        msp_id:
            description:
                - The MSP ID of the ordering service node.
            type: str
            sample: OrdererOrgMSP
        pem:
            description:
                - The TLS certificate chain for the ordering service node.
                - The TLS certificate chain is returned as a base64 encoded PEM.
            type: str
            sample: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
        tls_ca_root_cert:
            description:
                - The TLS certificate chain for the ordering service node.
                - The TLS certificate chain is returned as a base64 encoded PEM.
            type: str
            sample: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
        tls_cert:
            description:
                - The TLS certificate for the ordering service node.
                - The TLS certificate is returned as a base64 encoded PEM.
            type: str
            sample: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
        location:
            description:
                - The location of the ordering service node.
            type: str
            sample: ibmcloud
        system_channel_id:
            description:
                - The name of the system channel for the ordering service node.
            type: str
            sample: testchainid
        client_tls_cert:
            description:
                - The client TLS certificate for the ordering service node.
                - The client TLS certificate is returned as a base64 encoded PEM.
            type: str
            sample: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
        server_tls_cert:
            description:
                - The server TLS certificate for the ordering service node.
                - The server TLS certificate is returned as a base64 encoded PEM.
            type: str
            sample: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
        cluster_id:
            description:
                - The unique ID of the ordering service cluster.
            type: str
            sample: abcdefgh
        cluster_name:
            description:
                - The name of the ordering service cluster.
            type: str
            sample: Ordering Service
        consenter_proposal_fin:
            description:
                - True if the ordering service node has been added to the consenter
                  set of the system channel, false otherwise. Ordering service nodes
                  that have not been added to the consenter set of the system channel
                  are not ready for use.
            type: boolean
            sample: true
'''


def get_crypto(console, module):

    # Get the crypto configuration.
    return {"enrollment": get_crypto_enrollment_config(console, module)}


def get_crypto_enrollment_config(console, module):

    # Get the crypto configuration.
    return {
        "component": get_crypto_enrollment_component_config(console, module),
        "ca": get_crypto_enrollment_ca_config(console, module),
        "tlsca": get_crypto_enrollment_tlsca_config(console, module),
    }


def get_crypto_enrollment_component_config(console, module):
    admins = module.params["admins"]
    return {"admincerts": admins}


def get_crypto_enrollment_ca_config(console, module):

    # Get the enrollment configuration for the ordering services MSP.
    certificate_authority = get_certificate_authority_by_module(console, module)
    certificate_authority_url = urllib.parse.urlsplit(certificate_authority.api_url)
    enrollment_id = module.params["enrollment_id"]
    enrollment_secret = module.params["enrollment_secret"]
    return {
        "host": certificate_authority_url.hostname,
        "port": str(certificate_authority_url.port),
        "name": certificate_authority.ca_name,
        "tls_cert": certificate_authority.pem,
        "enroll_id": enrollment_id,
        "enroll_secret": enrollment_secret,
    }


def get_crypto_enrollment_tlsca_config(console, module):

    # Get the enrollment configuration for the ordering services TLS.
    certificate_authority = get_certificate_authority_by_module(console, module)
    certificate_authority_url = urllib.parse.urlsplit(certificate_authority.api_url)
    enrollment_id = module.params["enrollment_id"]
    enrollment_secret = module.params["enrollment_secret"]
    return {
        "host": certificate_authority_url.hostname,
        "port": str(certificate_authority_url.port),
        "name": certificate_authority.tlsca_name,
        "tls_cert": certificate_authority.pem,
        "enroll_id": enrollment_id,
        "enroll_secret": enrollment_secret,
    }


def main():

    # Create the module.
    argument_spec = dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        api_endpoint=dict(type='str', required=True),
        api_authtype=dict(type='str', required=True, choices=['ibmcloud', 'basic']),
        api_key=dict(type='str', required=True, no_log=True),
        api_secret=dict(type='str', no_log=True),
        api_timeout=dict(type='int', default=60),
        api_token_endpoint=dict(type='str', default='https://iam.cloud.ibm.com/identity/token'),
        name=dict(type='str', required=True),
        ordering_service=dict(type='raw'),
        msp_id=dict(type='str'),
        orderer_type=dict(type='str', default='raft', choices=['raft']),
        system_channel_id=dict(type='str', default='testchainid'),
        config_block=dict(type='str'),
        certificate_authority=dict(type='raw'),
        enrollment_id=dict(type='str'),
        enrollment_secret=dict(type='str', no_log=True),
        admins=dict(type='list', elements='str', aliases=['admin_certificates']),
        crypto=dict(type='dict'),
        config_override=dict(type='dict', default=dict()),
        resources=dict(type='dict'),
        storage=dict(type='dict', default=dict(), options=dict(
            orderer=dict(type='dict', default=dict(), options={
                'size': dict(type='str', default='100Gi'),
                'class': dict(type='str')
            })
        )),
        hsm=dict(type='dict', options=dict(
            pkcs11endpoint=dict(type='str'),
            label=dict(type='str', required=True, no_log=True),
            pin=dict(type='str', required=True, no_log=True)
        )),
        zone=dict(type='str'),
        version=dict(type='str'),
        wait_timeout=dict(type='int', default=60)
    )
    required_if = [
        ('api_authtype', 'basic', ['api_secret']),
        ('state', 'present', ['name'])
    ]
    # Ansible doesn't allow us to say "require one of X and Y only if condition A is true",
    # so we need to handle this ourselves by seeing what was passed in.
    actual_params = _load_params()
    if actual_params.get('state', 'present') == 'present':
        required_one_of = [
            ['certificate_authority', 'crypto']
        ]
    else:
        required_one_of = []
    required_together = [
        ['certificate_authority', 'enrollment_id'],
        ['certificate_authority', 'enrollment_secret'],
        ['certificate_authority', 'admins']
    ]
    mutually_exclusive = [
        ['certificate_authority', 'crypto']
    ]
    module = BlockchainModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if)

    # Ensure all exceptions are caught.
    try:

        # Log in to the console.
        console = get_console(module)

        # Determine if the ordering service node exists.
        name = module.params['name']
        ordering_service_node = console.get_component_by_display_name('fabric-orderer', name, deployment_attrs='included')
        ordering_service_node_exists = ordering_service_node is not None
        ordering_service_node_corrupt = ordering_service_node is not None and 'deployment_attrs_missing' in ordering_service_node
        module.json_log({
            'msg': 'got ordering service node',
            'ordering_service_node': ordering_service_node,
            'ordering_service_node_exists': ordering_service_node_exists,
            'ordering_service_node_corrupt': ordering_service_node_corrupt
        })

        # define a default set of resources
        default_resources = dict(type='dict', default=dict(), options=dict(
            orderer=dict(type='dict', default=dict(), options=dict(
                requests=dict(type='dict', default=dict(), options=dict(
                    cpu=dict(type='str', default='250m'),
                    memory=dict(type='str', default='500M')
                ))
            )),
            proxy=dict(type='dict', default=dict(), options=dict(
                requests=dict(type='dict', default=dict(), options=dict(
                    cpu=dict(type='str', default='100m'),
                    memory=dict(type='str', default='200M')
                ))
            ))
        ))

        # If this is a free cluster, we cannot accept resource/storage configuration,
        # as these are ignored for free clusters. We must also delete the defaults,
        # otherwise they cause a mismatch with the values that actually get set.
        if console.is_free_cluster():
            actual_params = _load_params()
            if 'resources' in actual_params or 'storage' in actual_params:
                raise Exception('Cannot specify resources or storage for a free IBM Kubernetes Service cluster')
            if ordering_service_node_exists:
                module.params['resources'] = dict()
                module.params['storage'] = dict()

        # If the ordering service node should not exist, handle that now.
        state = module.params['state']
        if state == 'absent' and ordering_service_node_exists:

            # The ordering service node should not exist, so delete it.
            console.delete_ordering_service_node(ordering_service_node['id'])
            return module.exit_json(changed=True)

        elif state == 'absent':

            # The ordering service node should not exist and doesn't.
            return module.exit_json(changed=False)

        # If the ordering service node is corrupt, delete it first. This may happen if somebody imported an external
        # ordering service node with the same name, or if somebody deleted the Kubernetes resources directly.
        changed = False
        if ordering_service_node_corrupt:
            module.warn('Ordering service node exists in console but not in Kubernetes, deleting it before continuing')
            console.delete_ext_ordering_service_node(ordering_service_node['id'])
            ordering_service_node_exists = ordering_service_node_corrupt = False
            changed = True

        # Either create or update the ordering service.
        changed = False
        if state == 'present' and not ordering_service_node_exists:

            # Get the ordering service that this ordering service node should belong to.
            ordering_service = get_ordering_service_by_module(console, module)
            cluster_id = ordering_service.nodes[0].cluster_id
            cluster_name = ordering_service.nodes[0].cluster_name

            required_if = [
                ('api_authtype', 'basic', ['api_secret']),
                ('state', 'present', ['msp_id', 'ordering_service'])
            ]

            module = BlockchainModule(
                argument_spec=argument_spec,
                supports_check_mode=True,
                required_if=required_if,
                required_one_of=required_one_of,
                required_together=required_together,
                mutually_exclusive=mutually_exclusive)

            # HACK: strip out the storage class if it is not specified. Can't pass null as the API barfs.
            storage = module.params['storage']
            for storage_type in storage:
                if 'class' not in storage[storage_type]:
                    continue
                storage_class = storage[storage_type]['class']
                if storage_class is None:
                    del storage[storage_type]['class']

            resources = copy_dict(default_resources)
            merge_dicts(resources, module.params['resources'])

            # Extract the expected ordering service node configuration.
            expected_ordering_service_node = dict(
                display_name=name,
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                msp_id=module.params['msp_id'],
                orderer_type=module.params['orderer_type'],
                system_channel_id=module.params['system_channel_id'],
                config_override=module.params['config_override'],
                resources=resources,
                storage=storage
            )

            # Delete the resources and storage configuration for a new ordering
            # service being deployed to a free cluster.
            if console.is_free_cluster():
                del expected_ordering_service_node['resources']
                del expected_ordering_service_node['storage']

            # Add the HSM configuration if it is specified.
            hsm = module.params['hsm']
            if hsm is not None:
                pkcs11endpoint = hsm['pkcs11endpoint']
                if pkcs11endpoint:
                    expected_ordering_service_node['hsm'] = dict(pkcs11endpoint=pkcs11endpoint)
                hsm_config_override = dict(
                    General=dict(
                        BCCSP=dict(
                            Default='PKCS11',
                            PKCS11=dict(
                                Label=hsm['label'],
                                Pin=hsm['pin']
                            )
                        )
                    )
                )
                merge_dicts(expected_ordering_service_node['config_override'], hsm_config_override)

            # Add the zone if it is specified.
            zone = module.params['zone']
            if zone is not None:
                expected_ordering_service_node['zone'] = zone

            # Add the version if it is specified.
            version = module.params['version']
            if version is not None:
                resolved_version = console.resolve_ordering_service_node_version(version)
                expected_ordering_service_node['version'] = resolved_version

            # There is no "create an ordering service node" API, so we need to create/append to
            # an existing ordering service. This means we have to convert various parameters to
            # lists to make it look like a request to create a one node ordering service.
            expected_ordering_service_node['config_override'] = [expected_ordering_service_node['config_override']]
            if zone is not None:
                expected_ordering_service_node['zone'] = [zone]

            # Get the config.
            expected_ordering_service_node['crypto'] = [
                get_crypto(console, module)
            ]

            # Create the ordering service.
            ordering_service = console.create_ordering_service(expected_ordering_service_node)
            if isinstance(ordering_service, list):
                ordering_service_node = ordering_service[0]
            else:
                ordering_service_node = ordering_service
            changed = True

        elif state == 'present' and ordering_service_node_exists:

            # HACK: never send the limits back, as they are rejected.
            for thing in ['orderer', 'proxy']:
                if thing in ordering_service_node['resources']:
                    if 'limits' in ordering_service_node['resources'][thing]:
                        del ordering_service_node['resources'][thing]['limits']

            # HACK: never send the init resources back, as they are rejected.
            ordering_service_node['resources'].pop('init', None)

            # Extract the expected ordering service node configuration.
            expected_ordering_service_node = dict(
                config_override=module.params['config_override'],
                resources=module.params['resources'],
                crypto=module.params['crypto'],
                version=module.params['version']
            )

            if expected_ordering_service_node['config_override'] is None:
                del expected_ordering_service_node['config_override']

            if expected_ordering_service_node['resources'] is None:
                del expected_ordering_service_node['resources']

            if expected_ordering_service_node['crypto'] is None:
                del expected_ordering_service_node['crypto']

            if expected_ordering_service_node['version'] is None:
                del expected_ordering_service_node['version']

            # Add the version if it is specified.
            version = module.params['version']
            if version is not None:
                resolved_version = console.resolve_peer_version(version)
                expected_ordering_service_node['version'] = resolved_version

            # Update the ordering service node configuration.
            new_ordering_service_node = copy_dict(ordering_service_node)
            merge_dicts(new_ordering_service_node, expected_ordering_service_node)

            # Check to see if any banned changes have been made.
            # HACK: zone is documented as a permitted change, but it has no effect.
            permitted_changes = ['resources', 'config_override', 'version', 'crypto']
            diff = diff_dicts(ordering_service_node, new_ordering_service_node)
            for change in diff:
                if change not in permitted_changes:
                    raise Exception(f'{change} cannot be changed from {ordering_service_node[change]} to {new_ordering_service_node[change]} for existing ordering service node')

            # If a change was supplied to resources, apply the change to the entire resources
            if module.params['resources'] is not None:
                diff['resources'] = new_ordering_service_node['resources']

            # If the ordering service node has changed, apply the changes.
            ordering_service_node_changed = not equal_dicts(ordering_service_node, new_ordering_service_node)
            if ordering_service_node_changed:

                # Log the differences.
                module.json_log({
                    'msg': 'differences detected, updating ordering service node',
                    'ordering_service_node': ordering_service_node,
                    'new_ordering_service_node': new_ordering_service_node,
                    'diff': diff
                })

                # Remove anything that hasn't changed from the updates.
                things = list(new_ordering_service_node.keys())
                for thing in things:
                    if thing not in diff:
                        del new_ordering_service_node[thing]

                # Apply the updates.
                ordering_service_node = console.update_ordering_service_node(ordering_service_node['id'], diff)
                changed = True

            # Now need to compare the list of admin certs. The admin certs may be passed in via
            # three different parameters (admins, config.enrollment.component.admincerts, and
            # config.msp.component.admincerts) so we need to find them.
            # HACK: if the admin certs did not get returned, we're running on IBP v2.1.3
            # and it does not support this feature.
            expected_admins = module.params['admins']
            if not expected_admins:
                crypto = module.params['crypto']
                if crypto:
                    for config_type in ['enrollment', 'msp']:
                        expected_admins = crypto.get(config_type, dict()).get('component', dict()).get('admincerts', None)
                        if expected_admins:
                            break
            if expected_admins:
                expected_admins_set = set(map(normalize_whitespace, expected_admins))
                actual_admins = ordering_service_node.get('admin_certs', None)
                if actual_admins is not None:
                    actual_admins_set = set(map(normalize_whitespace, actual_admins))
                    append_admin_certs = list(expected_admins_set.difference(actual_admins_set))
                    remove_admin_certs = list(actual_admins_set.difference(expected_admins_set))
                    if append_admin_certs or remove_admin_certs:
                        console.edit_admin_certs(ordering_service_node['id'], append_admin_certs, remove_admin_certs)
                        changed = True

            # If the ordering service node has not been added to the system channel, we may need to
            # send the ordering service node a config block.
            if not ordering_service_node['consenter_proposal_fin']:

                # Check to see if a config block has been specified.
                config_block_file = module.params['config_block']
                if config_block_file:

                    # Read the config block and base64 encode it.
                    with open(config_block_file, 'rb') as file:
                        config_block = file.read()
                    config_block = base64.b64encode(config_block).decode('utf-8')

                    # Submit the config block to the ordering service.
                    console.submit_config_block(ordering_service_node['id'], config_block)

                    # Edit the ordering service node.
                    ordering_service_node = console.edit_ordering_service_node(ordering_service_node['id'], dict(consenter_proposal_fin=True))
                    changed = True

        # Wait for the ordering service node to start, but only if it has been added to the system channel.
        ordering_service_node = OrderingServiceNode.from_json(console.extract_ordering_service_node_info(ordering_service_node))
        if ordering_service_node.consenter_proposal_fin:
            timeout = module.params['wait_timeout']
            ordering_service_node.wait_for(timeout)

        # Return the ordering service node.
        module.exit_json(changed=changed, ordering_service_node=ordering_service_node.to_json())

    # Notify Ansible of the exception.
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
