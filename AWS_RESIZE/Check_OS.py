import boto3
import os
import json
import logging

log = logging.getLogger()


def lambda_handler(event, context):
    Instance_Id = event.get("Instance_ID")
    client = boto3.client('ec2')

    response = client.describe_instances(
    InstanceIds=[
        Instance_Id
        ]
    )   
    try:
        Platform = response['Reservations'][0]['Instances'][0]['Platform']
        print(Platform)
        return Platform
    except:
        Platform = 'linux'
        print(Platform)
        return Platform
