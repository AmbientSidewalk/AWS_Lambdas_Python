from unittest import TestCase
import boto3
from create_docker_worker import get_docker_ami

class TestGet_docker_ami(TestCase):
    def test_get_docker_ami(self):
        get_docker_ami(ec2_client=boto3.client('ec2'), release='Prod')
        self.fail()
