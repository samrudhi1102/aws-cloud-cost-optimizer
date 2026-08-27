import boto3


def get_s3_buckets():

    s3 = boto3.client("s3")

    response = s3.list_buckets()

    buckets = []

    for bucket in response["Buckets"]:

        buckets.append({
            "name": bucket["Name"],
            "created": bucket["CreationDate"]
        })

    return buckets


def get_bucket_storage(bucket_name):

    s3 = boto3.client("s3")

    total_size = 0
    object_count = 0

    paginator = s3.get_paginator("list_objects_v2")

    try:

        for page in paginator.paginate(
            Bucket=bucket_name
        ):

            objects = page.get("Contents", [])

            for obj in objects:

                total_size += obj["Size"]
                object_count += 1

    except Exception as error:

        return {
            "size_gb": None,
            "object_count": None,
            "error": str(error)
        }

    size_gb = total_size / (1024 ** 3)

    return {
        "size_gb": round(size_gb, 4),
        "object_count": object_count,
        "error": None
    }