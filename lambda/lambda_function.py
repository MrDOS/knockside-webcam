import boto3
import io
import json
import PIL.Image

INPUT_PREFIX = "webcam/masters/"
OUTPUT_PREFIX = "webcam/compressed/"
LATEST_FILENAME = "knockside.jpg"
MANIFEST_FILENAME = "manifest.json"

OUTPUT_SIZE = (1920, 1080)
OUTPUT_QUALITY = 85

s3 = boto3.client("s3")


def compress_capture(bucket_name: str, input_key: str, output_key: str) -> None:
    input_object = s3.get_object(Bucket=bucket_name, Key=input_key)
    input_data = input_object["Body"].read()
    input_image = PIL.Image.open(io.BytesIO(input_data))

    scale_size = (
        OUTPUT_SIZE[0],
        int(input_image.size[1] / (input_image.size[0] / OUTPUT_SIZE[0])),
    )
    print(f"Resizing to {scale_size[0]} x {scale_size[1]}.")
    output_image = input_image.resize(scale_size)

    if output_image.size[1] > OUTPUT_SIZE[1]:
        y_offset = (output_image.size[1] - OUTPUT_SIZE[1]) // 2
        print(f"Cropping {y_offset} px off the top.")
        output_image = output_image.crop(
            (0, y_offset, OUTPUT_SIZE[0], y_offset + OUTPUT_SIZE[1])
        )

    output_data = io.BytesIO()
    output_image.save(output_data, "JPEG", quality=OUTPUT_QUALITY)
    size = output_data.tell()
    output_data.seek(0)

    print(f"Uploading {size} B to s3://{bucket_name}/{output_key}.")
    s3.upload_fileobj(
        output_data,
        bucket_name,
        output_key,
        {
            "ContentType": "image/jpeg",
        },
    )


def update_manifest(bucket_name: str, manifest_key: str, timestamp: str) -> None:
    manifest_object = s3.get_object(Bucket=bucket_name, Key=manifest_key)
    manifest_data = manifest_object["Body"].read()
    manifest = json.loads(manifest_data)

    manifest.append(timestamp)
    # Eliminate duplicates.
    manifest = sorted(list(set(manifest)))

    manifest_data = json.dumps(manifest)

    print(f"Uploading {len(manifest_data)} B to s3://{bucket_name}/{manifest_key}.")
    s3.put_object(
        Body=manifest_data,
        Bucket=bucket_name,
        Key=manifest_key,
        CacheControl="max-age=60",
        ContentType="application/json",
    )


def update_latest(bucket_name: str, compressed_key: str, latest_key: str) -> None:
    s3.copy_object(
        Bucket=bucket_name,
        CopySource={
            "Bucket": bucket_name,
            "Key": compressed_key,
        },
        Key=latest_key,
        MetadataDirective="REPLACE",
        CacheControl="max-age=60",
        ContentType="image/jpeg",
    )


def read_s3_event(event):
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    input_key = event["Records"][0]["s3"]["object"]["key"]

    return (bucket_name, input_key)


def read_eventbridge_event(event):
    bucket_name = event["detail"]["bucket"]["name"]
    input_key = event["detail"]["object"]["key"]

    return (bucket_name, input_key)


def lambda_handler(event, context):
    found = False

    for event_reader in [read_s3_event, read_eventbridge_event]:
        try:
            bucket_name, input_key = event_reader(event)
            print(f"{event_reader.__name__} read from the event.")
            found = True
            break
        except IndexError, KeyError:
            print(f"{event_reader.__name__} could not read from the event.")
            pass

    if not found:
        return {
            "statusCode": 400,
            "message": "Event does not contain an S3 bucket name and object key",
        }

    if not input_key.startswith(INPUT_PREFIX):
        return {"statusCode": 400, "message": "Unexpected input object prefix"}
    output_key = OUTPUT_PREFIX + input_key[len(INPUT_PREFIX) :]

    compress_capture(bucket_name, input_key, output_key)

    latest_key = OUTPUT_PREFIX + LATEST_FILENAME
    update_latest(bucket_name, output_key, latest_key)

    basename = output_key[output_key.rfind("/") + 1 :]
    timestamp = basename[basename.find("-") + 1 : basename.rfind(".")]
    manifest_key = OUTPUT_PREFIX + MANIFEST_FILENAME
    update_manifest(bucket_name, manifest_key, timestamp)

    return {"statusCode": 200}
