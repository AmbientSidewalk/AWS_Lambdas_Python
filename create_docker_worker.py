import sys, getopt, boto3


# def main(argv):
#     release = 'prod'
#     try:
#         opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
#     except getopt.GetoptError:
#         print 'test.py -i <inputfile> -o <outputfile>'
#         sys.exit(2)
#     for opt, arg in opts:
#         if opt == '-h':
#             print 'test.py -i <inputfile> -o <outputfile>'
#             sys.exit()
#         elif opt in ("-i", "--ifile"):
#             inputfile = arg
#         elif opt in ("-o", "--ofile"):
#             outputfile = arg

EC2_CLIENT = boto3.client('ec2')
DEFAULT_AMI_TAG_TYPE = 'Docker Base'
DEFAULT_AMI_TAG_RELEASE = 'Prod'
RELEASE_TAG_VALUES = ['Prod', 'UAT', 'Test']


def get_docker_ami(**kwargs):
    """get the ami_id of the latest image tagged with 'Type:type_image_tag' and
    'Release:release_image_tag'  where release is one of the following values:
        (Prod, UAT, Test)

    Throws exception on missing kwarg ec2_client, invalid value for argument release_image_tag,
    or no images found

    Keyword arguments:
    ec2_client (required) -- an amazon BOTO3 EC2 client
    type_image_tag -- default 'Docker Base'
    release_image_tag -- default 'Prod'
    """

    ec2_client = kwargs.get('ec2_client', EC2_CLIENT)
    image_type = kwargs.get('type_image_tag', DEFAULT_AMI_TAG_TYPE)
    release = kwargs.get('release_image_tag', DEFAULT_AMI_TAG_RELEASE)

    if release not in RELEASE_TAG_VALUES:
        raise Exception("Invalid AMI Tag 'Release' Value '"+release+"'")

    response = ec2_client.describe_images(
        Filters=[
            {
                'Name': 'tag:Release',
                'Values': [release]
            },
            {
                'Name': 'tag:Type',
                'Values': [image_type]
            }
        ]
    )

    creation_date = ''
    ami = ''
    for image in response['Images']:
        if image['CreationDate'] > creation_date:
            creation_date = image['CreationDate']
            ami = image['ImageId']

    if ami == '':
        raise Exception("No Images found matching tags 'Type:"+image_type+"' 'Release:"+release+"' ")

    return ami

NETWORK_SEGMENT_TAG_VALUES = ('MW', 'DMZ', 'PUB', 'INT', 'DB', 'ADMIN')


def get_best_subnet_id(**kwargs):
    ec2_client = kwargs.get('ec2_client', EC2_CLIENT)
    environment_name = kwargs.get('environment_name')
    network_segment = kwargs.get('network_segment')

    subnets = get_subnet_ids(
        ec2_client=ec2_client,
        environment_name=environment_name,
        network_segment=network_segment
    )

    available_ips=0
    subnet_id=''
    for subnet in subnets:
        if subnet.get('AvailableIpAddressCount') > available_ips:
            available_ips=subnet.get('AvailableIpAddressCount')
            subnet_id=subnet.get('SubnetId')

    return subnet_id


def get_subnet_ids(**kwargs):
    """get the subnets with 'Environment_Name:environment_name_subnet_tag' and
    'Network_Segnment:network_segment_subnet_tag'  where release is one of the following values:
        (MW,DMZ,PUB,INT,DB,ADMIN)

    Throws exception on missing kwarg ec2_client, invalid value for argument network_segment_subnet_tag,
    or no images found

    Keyword arguments:
    ec2_client (required) -- an amazon BOTO3 EC2 client
    environment_name (required) -- environment name
    network_segment -- default 'MW'
    availability_zone -- if specified filter to this AZ only

    Returns:
        List of
         {'AvailabilityZone': str,
           'AvailableIpAddressCount': int,
           'SubnetId': str
         }
    """

    ec2_client = kwargs.get('ec2_client', EC2_CLIENT)
    if 'environment_name' not in kwargs:
        raise Exception('Missing required parameter environment_name')
    environment_name = kwargs.get('environment_name')

    network_segment = kwargs.get('network_segment', 'MW')
    az = kwargs.get('availability_zone', '')

    if network_segment not in NETWORK_SEGMENT_TAG_VALUES:
        raise Exception("Invalid Subnet Tag 'Network_Segment' Value '" + network_segment + "'")

    filters = [
        {
            'Name': 'tag:Environment_Name',
            'Values': [environment_name]
        },
        {
            'Name': 'tag:Network_Segment',
            'Values': [network_segment]
        }
    ]

    az_error = ''
    if az != '':
        filters.append({
            'Name': 'availabilityZone',
            'Values': [az]
        })
        az_error = " 'avaliabilityZone: "+az+"'"

    response = ec2_client.describe_subnets(Filters=filters)

    if len(response.get('Subnets')) == 0:
        raise Exception("No Subnets Found for 'Environment_Name:" + environment_name +
                        "' 'Network_Segment:" + network_segment + "' " + az_error)

    subnets = []
    for subnet in response.get('Subnets'):
        subnets.append(
            {'AvailabilityZone': subnet['AvailabilityZone'],
             'AvailableIpAddressCount': subnet['AvailableIpAddressCount'],
             'SubnetId': subnet['SubnetId']
             }
        )
    return subnets


def get_next_available_name(**kwargs):
    """get the next available instance name matching format
        <base_instance_name>0a0#

    Keyword arguments:
    ec2_client (required) -- an amazon BOTO3 EC2 client
    environment_name (required) -- environment name
    network_segment (required) -- network_segment
    """

    ec2_client = kwargs.get('ec2_client', EC2_CLIENT)
    if 'environment_name' not in kwargs:
        raise Exception('Missing required parameter environment_name')
    env_name = kwargs.get('environment_name')

    if 'network_segment' not in kwargs:
        raise Exception('Missing required parameter base_instance_name')
    network_segment = kwargs.get('network_segment')

    base_name = env_name.lower()+'-'+network_segment.lower()+'-docker'

    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [base_name+'*']
            },
        ]
    )

    names = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            names += [tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'Name']

    count = 1
    while base_name+format(count, '02d') in names:
        count += 1
    new_name = base_name+format(count, '02d')

    return new_name


def create_docker_instance(**kwargs):
    ec2_client = kwargs.get('ec2_client', EC2_CLIENT)
    if 'environment_name' not in kwargs:
        raise Exception('Missing required parameter environment_name')
    env_name = kwargs.get('environment_name')

    if 'network_segment' not in kwargs:
        raise Exception('Missing required parameter network_segment')
    network_segment = kwargs.get('network_segment')

    release = kwargs.get('release', 'PROD')
    key_name = kwargs.get('key_name', 'stratos-rootish')
    security_group_ids = [
        'sg-fc846784',  #default
        'sg-bd21d7c6',  #phonehome
        'sg-650d831d'   #nat
    ]
    instance_type = kwargs.get('instance_type', 't2.medium')
    project = kwargs.get('project', 'Unassigned')
    team = kwargs.get('team', 'Unassigned')

    ami_id = get_docker_ami(
        ec2_client=boto3.client('ec2'),
        release=release)

    instance_name = get_next_available_name(
        ec2_client=ec2_client,
        environment_name=env_name,
        network_segment=network_segment)

    subnet_id = get_best_subnet_id(
        ec2_client=ec2_client,
        environment_name=env_name,
        network_segment=network_segment
    )
    response = ec2_client.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        KeyName=key_name,
        SecurityGroupIds=security_group_ids,
        SubnetId=subnet_id,
        TagSpecifications=[
            {
                'ResourceType': 'volume',
                'Tags': [
                    {
                        'Key': 'Environment_Name',
                        'Value': env_name
                    },
                    {
                        'Key': 'Project',
                        'Value': project
                    },
                    {
                        'Key': 'Team',
                        'Value': team
                    },
                    {
                        'Key': 'Name',
                        'Value': instance_name
                    }
                ]
            },
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Environment_Name',
                        'Value': env_name
                    },
                    {
                        'Key': 'Project',
                        'Value': project
                    },
                    {
                        'Key': 'Team',
                        'Value': team
                    },
                    {
                        'Key': 'Name',
                        'Value': instance_name
                    }
                ]
            }
        ]
    )
    result = {
        'imageId': response['Instances'][0]['imageId'],
        'ip': response['Instances'][0]['PublicIpAddress']}
    return result
