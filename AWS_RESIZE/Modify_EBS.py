import boto3
import botocore
import os
import decimal
import logging

log = logging.getLogger()


def lambda_handler(event, context):
    print(event)
    VolumeId = event.get("EbsVolumeId")
    client = boto3.client("ec2")
    # doo % of size and return  this sand trigger emaol if reach 100
    Size = volume_size(client, VolumeId)

    increase_percentage = os.environ["INCREASE_PERCENTAGE"]
    increase_percentage_d = decimal.Decimal(increase_percentage)
    increase = int(Size + (Size * increase_percentage_d))
    print(increase)

    snapshot_response = create_snapshot(client, VolumeId)
    SnapshotId = snapshot_response["SnapshotId"]
    modify_volume(client, VolumeId, increase)

    return {"SnapshotId": SnapshotId, "NewSize": increase}


def volume_size(client, VolumeId):
    response = client.describe_volumes(VolumeIds=[VolumeId])
    Size = response["Volumes"][0]["Size"]
    return Size


def create_snapshot(client, VolumeId):
    response = client.create_snapshot(
        Description="Create snap for resize", VolumeId=VolumeId,
    )
    SnapshotId = response["SnapshotId"]
    client.waiter_names
    waiter = client.get_waiter("snapshot_completed")

    # Increase the max number of tries as appropriate
    # waiter.config.max_attempts = 120

    # Add a 60 second delay between attempts
    waiter.config.delay = 60
    print("waiter delay: " + str(waiter.config.delay))
    try:
        waiter.wait(SnapshotIds=[SnapshotId])

    except botocore.exceptions.WaiterError as e:
        if "Max attempts exceed" in e.messeage:
            print("Snapshot did not complete in 600 sec")
        else:
            print(e.messege)

    return response


def modify_volume(client, VolumeId, increase):
    client.modify_volume(VolumeId=VolumeId, Size=increase)
    log.info("Modifed Volume")