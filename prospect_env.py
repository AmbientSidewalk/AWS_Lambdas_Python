import boto3

SNS_TOPIC_NAMES = ['prospect-list-uploaded', 'prospect-lead-generated', 'prospect-person-identified',
                   'prospect-person-identification-internal-failed', 'prospect-lead-orderable',
                   'prospect-lead-completed', 'prospect-lead-accepted', 'prospect-order-readyToSend',
                   'prospect-order-completed']

SQS_QUEUE_NAMES = ['prospect-list-parse', 'prospect-person-identify-internal', 'prospect-person-identify-external',
                   'prospect-lead-orderability-check', 'prospect-lead-pend', 'prospect-data-export',
                   'prospect-workflow-decline', 'prospect-order-send', 'prospect-order-createAccount',
                   'ext-person-id-hold']

SNS_TOPIC_SUBS = [{'topic':'prospect-list-uploaded', 'queue':'prospect-list-parse'},
                  {'topic':'prospect-lead-generated', 'queue':'prospect-person-identify-internal'},
                  {'topic':'prospect-person-identified', 'queue':'prospect-person-identify-external'},
                  {'topic':'prospect-person-identification-internal-failed', 'queue':'prospect-lead-orderability-check'},
                  {'topic':'prospect-lead-orderable', 'queue':'prospect-lead-pend'},
                  {'topic':'prospect-lead-completed', 'queue':'prospect-data-export'},
                  {'topic':'prospect-lead-accepted', 'queue':'prospect-workflow-decline'},
                  {'topic':'prospect-order-readyToSend', 'queue':'prospect-order-send'},
                  {'topic':'prospect-order-completed', 'queue':'prospect-order-createAccount'} ]

SNS_CLIENT = boto3.client("sns")
SQS_CLIENT = boto3.client("sqs")

def lambda_handler(event, context):


def delete_env(**kwargs):
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    delete_sns_topics(env_name=env_name)
    delete_sqs_queues(env_name=env_name)


def delete_sns_topics(**kwargs):
    sns_client = kwargs.get('sns_client', SNS_CLIENT)
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    for topic_base_name in SNS_TOPIC_NAMES:
        topic_name = env_name+'-'+topic_base_name
        print ("Deleting SNS topic '"+topic_name+"'")
        topic_arn = sns_client.create_topic(Name=topic_name).get('TopicArn')
        sns_client.delete_topic(TopicArn=topic_arn)


def delete_sqs_queues(**kwargs):
    sqs_client = kwargs.get('sqs_client', SQS_CLIENT)
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    for base_queue_name in SQS_QUEUE_NAMES:
        queue_name = env_name+'-'+base_queue_name
        print ("Deleting SQS queue '"+queue_name+"'")
        queue_url = sqs_client.create_queue(QueueName=queue_name).get('QueueUrl')
        sqs_client.delete_queue(QueueUrl=queue_url)


def create_env(**kwargs):
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    sns_arns = create_sns_topics(env_name=env_name)
    sqs_urls = create_sqs_queues(env_name=env_name)
    subscribe_queues_to_topics(
        env_name=env_name,
        sns_arns=sns_arns,
        sqs_urls=sqs_urls
    )


def create_sns_topics(**kwargs):
    sns_client = kwargs.get('sns_client', SNS_CLIENT)
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    sns_arns = {}
    for topic_base_name in SNS_TOPIC_NAMES:
        topic_name = env_name+'-'+topic_base_name
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response.get('TopicArn')
        print("SNS Topic "+topic_name+" created '"+topic_arn+"'")
        sns_arns.update({topic_name: topic_arn})

    return sns_arns


def create_sqs_queues(**kwargs):
    sqs_client = kwargs.get('sqs_client', SQS_CLIENT)
    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    sqs_arns = {}
    for base_queue_name in SQS_QUEUE_NAMES:
        queue_name = env_name+'-'+base_queue_name
        response = sqs_client.create_queue(QueueName=queue_name)
        queue_url = response.get('QueueUrl')

        queue_arn =sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        ).get('Attributes').get('QueueArn')
        print("SQS Queue '"+queue_name+"' created '"+queue_arn+"'")
        sqs_arns.update({queue_name: queue_arn})

    return sqs_arns


def subscribe_queues_to_topics(**kwargs):
    sns_client = kwargs.get('sns_client', SNS_CLIENT)
    if 'sns_arns' not in kwargs:
        raise Exception("Missing required arg sns_arns")
    sns_arns = kwargs.get('sns_arns')

    if 'sqs_urls' not in kwargs:
        raise Exception("Missing required arg sqs_urls")
    sqs_urls = kwargs.get('sqs_urls')

    if 'env_name' not in kwargs:
        raise Exception("Missing required arg env_name")
    env_name = kwargs.get('env_name')

    for my_dict in SNS_TOPIC_SUBS:
        topic = env_name+'-'+my_dict.get('topic')
        queue = env_name+'-'+my_dict.get('queue')
        topic_arn = sns_arns.get(topic, '')
        queue_arn = sqs_urls.get(queue, '')

        if topic_arn and queue_arn:
            response = sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )
            sub_arn = response['SubscriptionArn']
            print("SQS Queue '"+queue+"' subscribed to SNS Topic '"+topic+"'")
            print("  Subscription ARN '"+sub_arn+"'")

