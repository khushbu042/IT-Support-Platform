import boto3
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
BUCKET_NAME = "fastapi-ticket-attachments-khushbu-381492289538-us-east-1-an"

Session = boto3.Session(profile_name="fastapi-dev")

s3_client = Session.client(
    "s3",
    region_name=AWS_REGION,
)


def upload_file(file: str, object_key: str):
    s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        object_key,
    )


def download_file(object_key: str, file_path: str):
    s3_client.download_file(
        BUCKET_NAME,
        object_key,
        file_path,
    )

# def get_file(object_key: str):
#     response = s3_client.get_object(
#         BUCKET_NAME,
#         object_key,
#     )

#     return response

def get_file(object_key: str):
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
        )

        return response

    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            raise FileNotFoundError("Attachment not found in S3")

        raise


def delete_file(object_key: str):
    s3_client.delete_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
    )

def generate_download_url(object_key: str, expires_in: int = 3600):
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )