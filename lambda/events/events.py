import boto3
import json
import logging

# Inspired by https://github.com/awslabs/ecs-cid-sample/tree/master/code

# Set up a basic logger.
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Establish boto3 session.
session = boto3.session.Session()

# Instantiate the service clients
ec2 = session.client(service_name='ec2')
ecs = session.client(service_name='ecs')
asg = session.client('autoscaling')
sns = session.client('sns')

"""The Lambda handler.
    :param event: The data passed to the Lambda function.
    :param contex: Context sent to the Lambda function.
"""
def handler(event, context):
    action = 'abort'

    # Parse the SNS message from the event.
    # TODO Validate the payload?
    line = event['Records'][0]['Sns']['Message']
    message = json.loads(line)

    # Abort on anything other than "autoscaling:EC2_INSTANCE_TERMINATING"
    if 'LifecycleTransition' not in message:
        logger.info('Only autoscaling:EC2_INSTANCE_TERMINATING supported, abort')
    elif message['LifecycleTransition'] != 'autoscaling:EC2_INSTANCE_TERMINATING':
        logger.info('Only autoscaling:EC2_INSTANCE_TERMINATING supported, abort')
    else:

        # Get the cluster name and cluster instance info from the EC2 instance.
        cluster_name = cluster_name_from_instance_id(message['EC2InstanceId'])
        instance = container_instance_info(cluster_name, message['EC2InstanceId'])

        # Set to DRAINING if instance is ACTIVE, otherwise check if there are
        # tasks that are still running. If there are no tasks left, complete
        # the lifecycle action.
        if instance['status'] == 'ACTIVE':
            action = 'drain'
            subject="Draining tasks from instance " + message['EC2InstanceId']
            logger.info(subject)

            # Set instance state to DRAINING, re-publish a message to trigger
            # this function and check whether any tasks are running.
            ecs.update_container_instances_state(cluster=cluster_name,containerInstances=[instance['containerInstanceArn']],status='DRAINING')
            sns.publish(
                TopicArn=event['Records'][0]['Sns']['TopicArn'],
                Message=json.dumps(message),
                Subject=subject
            )

        else:
            if instance['runningTasksCount'] > 0:
                action = 'wait'
                subject="Waiting for " + str(instance['runningTasksCount']) + " tasks to drain from instance " + message['EC2InstanceId']
                logger.info(subject)

                # Re-publish this message to check whether tasks have drained.
                sns.publish(
                    TopicArn=event['Records'][0]['Sns']['TopicArn'],
                    Message=json.dumps(message),
                    Subject=subject
                )

            else:
                action = 'continue'
                logger.info("Tasks drained from instance %s", message['EC2InstanceId'])

                # Complete the lifecycle action for this instance.
                asg.complete_lifecycle_action(
                    LifecycleHookName=message['LifecycleHookName'],
                    AutoScalingGroupName=message['AutoScalingGroupName'],
                    LifecycleActionResult='CONTINUE',
                    InstanceId=message['EC2InstanceId']
                )

                logger.info("Lifecycle completed, sent CONTINUE for instance %s", message['EC2InstanceId'])

    return {
        "action": action,
    }


"""Returns the ECS cluster name that the passed EC2 instance is attached to.
    :param instance_id: The EC2 instance ID
"""
def cluster_name_from_instance_id(instance_id):
    response = ec2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instance_id]
            },
            {
                'Name': 'key',
                'Values': ['ecs:cluster:name']
            },
        ]
    )

    # TODO Handle when response['Tags'][0] doesn't exist
    return response['Tags'][0]['Value']


"""Returns the EC2 instance's container instance.
    :param cluster_name: The EC2 cluster name that the instance is attached to.
    :param instance_id: The EC2 instance ID.
"""
def container_instance_info(cluster_name, instance_id):
    instance_list = ecs.list_container_instances(cluster=cluster_name)
    instances = ecs.describe_container_instances(cluster=cluster_name, containerInstances=instance_list['containerInstanceArns'])

    for instance in instances['containerInstances']:
        if instance['ec2InstanceId'] == instance_id:
            return instance

    raise Exception('instance does not belong to an ECS cluster')
