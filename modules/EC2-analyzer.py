import boto3
from datetime import datetime, timedelta, timezone


def get_ec2_instances():

    ec2 = boto3.client("ec2")

    response = ec2.describe_instances()

    instances = []

    for reservation in response["Reservations"]:

        for instance in reservation["Instances"]:

            instances.append({
                "id": instance["InstanceId"],
                "type": instance["InstanceType"],
                "state": instance["State"]["Name"],
                "az": instance["Placement"]["AvailabilityZone"]
            })

    return instances


def get_cpu_utilization(instance_id):

    cloudwatch = boto3.client("cloudwatch")

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=["Average"]
    )

    datapoints = response.get("Datapoints", [])

    if not datapoints:
        return None

    total = sum(
        datapoint["Average"]
        for datapoint in datapoints
    )

    average = total / len(datapoints)

    return round(average, 2)


def analyze_cpu(instance_id, cpu_usage):

    if cpu_usage is None:

        return {
            "status": "NO DATA",
            "recommendation": (
                "CloudWatch has no CPU data "
                "for this instance."
            )
        }

    if cpu_usage < 10:

        return {
            "status": "HIGHLY UNDERUTILIZED",
            "recommendation": (
                "Consider downsizing or stopping "
                "the instance if it is not required."
            )
        }

    elif cpu_usage < 30:

        return {
            "status": "UNDERUTILIZED",
            "recommendation": (
                "Review instance size and workload."
            )
        }

    elif cpu_usage > 80:

        return {
            "status": "HIGH UTILIZATION",
            "recommendation": (
                "Consider monitoring performance "
                "or scaling resources."
            )
        }

    else:

        return {
            "status": "HEALTHY",
            "recommendation": (
                "CPU utilization appears reasonable."
            )
        }