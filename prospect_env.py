import boto3

SQS_QUEUE_NAMES = ['prospect-list-parse', 'prospect-person-identify-internal', 'prospect-person-identify-external',
                   'prospect-lead-orderability-check', 'prospect-lead-pend', 'prospect-data-export',
                   'prospect-workflow-decline', 'prospect-order-send', 'prospect-order-createAccount',
                   'ext-person-id-hold']

SNS_TOPIC_NAMES = ['prospect-list-uploaded', 'prospect-lead-generated', 'prospect-person-identified',
                   'prospect-person-identification-internal-failed', 'prospect-lead-orderable',
                   'prospect-lead-completed', 'prospect-lead-accepted', 'prospect-order-readyToSend',
                   'prospect-order-completed']

SNS_TOPIC_SUBS = [{'prospect-list-uploaded', 'prospect-list-parse'},
                  {'prospect-lead-generated', 'prospect-person-identify-internal'},
                  {'prospect-person-identified', 'prospect-person-identify-external'},
                  {'prospect-person-identification-internal-failed', 'prospect-lead-orderability-check'},
                  {'prospect-lead-orderable', 'prospect-lead-pend'},
                  {'prospect-lead-completed', 'prospect-data-export'},
                  {'prospect-lead-accepted', 'prospect-workflow-decline'},
                  {'prospect-order-readyToSend', 'prospect-order-send'},
                  {'prospect-order-completed', 'prospect-order-createAccount'} ]

SNS_CLIENT = boto3.client("sns")
SQS_CLIENT = boto3.client("sqs")


def create_sns_topics(**kwargs):
    sns_client = kwargs.get('sns_client', SNS_CLIENT)
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    sns_arns = {}
    for topic_base_name in SNS_TOPIC_NAMES:
        topic_name = env_name+'-'+topic_base_name
        response = sns_client.create_topic(Name=topic_name)
        sns_arns.update({topic_name: response.get('TopicArn')})

    return sns_arns


def create_sqs_queues(**kwargs):
    sqs_client = kwargs.get('sqs_client', SQS_CLIENT)
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    sqs_urls = {}
    for base_queue_name in SQS_QUEUE_NAMES:
        queue_name = env_name+'-'+base_queue_name
        response = sqs_client.create_queue(QueueName=queue_name)

    return sqs_urls
