import boto3


def get_ebs_volumes():

    ec2 = boto3.client("ec2")

    response = ec2.describe_volumes()

    volumes = []

    for volume in response["Volumes"]:

        attachments = volume.get("Attachments", [])

        volumes.append({
            "id": volume["VolumeId"],
            "size": volume["Size"],
            "type": volume["VolumeType"],
            "state": volume["State"],
            "attached": len(attachments) > 0
        })

    return volumes