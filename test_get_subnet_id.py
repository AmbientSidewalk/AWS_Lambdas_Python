from unittest import TestCase
from create_docker_worker import *


class TestGet_docker_ami(TestCase):

    def test_get_docker_ami(self):
        get_subnet_ids(ec2_client=boto3.client('ec2'),
                       environment_name='PRQA1',
                       network_segment='MW',
                       availability_zone='us-east-1e')

    def test_get_next_available_name(self):
        name = get_next_available_name(ec2_client=boto3.client('ec2'),
                                       environment_name='PRQA1',
                                       network_segment='DMZ')
        self.assertEqual(name, 'prqa1-dmz-docker05')

    def test_get_best_subnet_id(self):
        subnet_id = get_best_subnet_id(
            ec2_client=ec2_client,
            environment_name='PRQA1',
            network_segment='DMZ'
        )
        self.assertEqual(subnet_id, '')

    def test_get_docker_ami(self):
        ami_id = get_docker_ami(ec2_client=boto3.client('ec2'),
                                release='Prod')
        self.assertEqual(ami_id, 'ami-3483be22')

    def test_create_docker_instance(self):
        result = create_docker_instance(
            ec2_client=boto3.client('ec2'),
            environment_name='PRQA1',
            network_segment='DMZ',
            project='Prospect',
            team='Twix')

