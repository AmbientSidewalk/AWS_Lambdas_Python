from unittest import TestCase
from create_docker_worker import *


class TestGet_docker_ami(TestCase):

    def test_get_docker_ami(self):
        get_subnet_ids(ec2_client=boto3.client('ec2'),
                       environment_name_subnet_tag='PRQA1',
                       network_segment_subnet_tag='MW',
                       availability_zone='us-east-1e')

    def test_get_next_available_name(self):
        get_next_available_name(ec2_client=boto3.client('ec2'),
                                base_instance_name='prqa1-dmz-docker')

    def test_get_docker_ami(self):
        ami_id = get_docker_ami(ec2_client=boto3.client('ec2'), release='Prod')
        self.assertEquals(ami_id,'')

