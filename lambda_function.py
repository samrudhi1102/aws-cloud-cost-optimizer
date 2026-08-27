import json
import boto3
from datetime import datetime, timedelta, timezone


# ========================================
# CONFIGURATION
# ========================================

REPORT_BUCKET = "aws-cloud-cost-optimizer-reports-568521408843"


# ========================================
# LAMBDA HANDLER
# ========================================

def lambda_handler(event, context):

    print("=" * 60)
    print("AWS CLOUD COST OPTIMIZER - LAMBDA")
    print("=" * 60)

    ec2 = boto3.client("ec2")
    cloudwatch = boto3.client("cloudwatch")
    s3 = boto3.client("s3")

    recommendations = []

    # ========================================
    # EC2 ANALYSIS
    # ========================================

    print("\nEC2 ANALYSIS")
    print("-" * 60)

    response = ec2.describe_instances()

    for reservation in response["Reservations"]:

        for instance in reservation["Instances"]:

            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            state = instance["State"]["Name"]

            print(
                f"Instance: {instance_id} | "
                f"Type: {instance_type} | "
                f"State: {state}"
            )

            if state != "running":
                continue

            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=7)

            metrics = cloudwatch.get_metric_statistics(
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

            datapoints = metrics.get("Datapoints", [])

            if not datapoints:

                print("  CPU: No CloudWatch data")

                continue

            average_cpu = sum(
                point["Average"]
                for point in datapoints
            ) / len(datapoints)

            average_cpu = round(average_cpu, 2)

            print(
                f"  Average CPU (7 days): "
                f"{average_cpu}%"
            )

            if average_cpu < 10:

                print("  Status: HIGHLY UNDERUTILIZED")

                recommendations.append({
                    "service": "EC2",
                    "resource": instance_id,
                    "priority": "HIGH",
                    "issue":
                        f"Very low CPU utilization "
                        f"({average_cpu}%)",
                    "recommendation":
                        "Review whether the instance "
                        "needs to run continuously."
                })

            elif average_cpu < 30:

                print("  Status: UNDERUTILIZED")

                recommendations.append({
                    "service": "EC2",
                    "resource": instance_id,
                    "priority": "MEDIUM",
                    "issue":
                        f"Low CPU utilization "
                        f"({average_cpu}%)",
                    "recommendation":
                        "Review instance sizing and "
                        "workload requirements."
                })

    # ========================================
    # EBS ANALYSIS
    # ========================================

    print("\nEBS ANALYSIS")
    print("-" * 60)

    volumes = ec2.describe_volumes()

    for volume in volumes["Volumes"]:

        volume_id = volume["VolumeId"]
        size = volume["Size"]
        volume_type = volume["VolumeType"]

        attachments = volume.get(
            "Attachments",
            []
        )

        if not attachments:

            print(
                f"Volume: {volume_id} | "
                f"Size: {size} GB | "
                f"Status: UNATTACHED"
            )

            recommendations.append({
                "service": "EBS",
                "resource": volume_id,
                "priority": "HIGH",
                "issue": "Unattached EBS volume",
                "recommendation":
                    "Review the volume and delete it "
                    "if the data is no longer required."
            })

        else:

            print(
                f"Volume: {volume_id} | "
                f"Size: {size} GB | "
                f"Type: {volume_type} | "
                f"Status: ATTACHED"
            )

    # ========================================
    # S3 ANALYSIS
    # ========================================

    print("\nS3 ANALYSIS")
    print("-" * 60)

    buckets = s3.list_buckets()

    for bucket in buckets["Buckets"]:

        bucket_name = bucket["Name"]

        # Do not analyze our own report bucket
        if bucket_name == REPORT_BUCKET:
            continue

        print(
            f"Bucket: {bucket_name}"
        )

        try:

            paginator = s3.get_paginator(
                "list_objects_v2"
            )

            total_size = 0
            object_count = 0

            for page in paginator.paginate(
                Bucket=bucket_name
            ):

                for obj in page.get(
                    "Contents",
                    []
                ):

                    total_size += obj["Size"]
                    object_count += 1

            size_gb = total_size / (1024 ** 3)

            print(
                f"  Storage: "
                f"{round(size_gb, 4)} GB"
            )

            print(
                f"  Objects: "
                f"{object_count}"
            )

            if object_count == 0:

                recommendations.append({
                    "service": "S3",
                    "resource": bucket_name,
                    "priority": "LOW",
                    "issue": "Empty S3 bucket",
                    "recommendation":
                        "Review whether the bucket is still required."
                })

            elif size_gb < 0.01:

                print(
                    "  Status: Storage usage appears low."
                )

        except Exception as error:

            print(
                f"  Error: {error}"
            )

    # ========================================
    # SUMMARY
    # ========================================

    print("\nOPTIMIZATION SUMMARY")
    print("-" * 60)

    print(
        f"Recommendations: "
        f"{len(recommendations)}"
    )

    for recommendation in recommendations:

        print(
            f"[{recommendation['priority']}] "
            f"{recommendation['service']} - "
            f"{recommendation['resource']}"
        )

    # ========================================
    # GENERATE REPORT
    # ========================================

    generated_at = datetime.now(
        timezone.utc
    ).isoformat()

    report = {
        "project": "AWS Cloud Cost Optimizer",
        "generated_at": generated_at,
        "region": "ap-south-1",
        "recommendation_count": len(recommendations),
        "recommendations": recommendations
    }

    # ========================================
    # SAVE REPORT TO S3
    # ========================================

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d-%H-%M-%S")

    report_key = (
        f"reports/aws-cost-report-{timestamp}.json"
    )

    s3.put_object(
        Bucket=REPORT_BUCKET,
        Key=report_key,
        Body=json.dumps(
            report,
            indent=4
        ),
        ContentType="application/json"
    )

    print("\nREPORT SAVED TO S3")
    print("-" * 60)
    print(
        f"s3://{REPORT_BUCKET}/{report_key}"
    )

    print("\n" + "=" * 60)
    print("Lambda scan completed.")
    print("=" * 60)

    # ========================================
    # RESPONSE
    # ========================================

    return {
        "statusCode": 200,
        "body": json.dumps(report)
    }