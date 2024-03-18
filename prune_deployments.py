import boto3
import argparse
import os
from datetime import datetime, timedelta, timezone
from botocore.exceptions import NoCredentialsError

# Parse command line arguments
parser = argparse.ArgumentParser(description='Prune S3 deployments.')
parser.add_argument('--bucket_name', type=str, required=True, help='The name of the S3 bucket.')
parser.add_argument('--num_deployments', type=int, required=False, help='The most recent number of deployments to keep.')
parser.add_argument('--prune_older_than_days', type=int, required=False, help='Prune all deployments older than this number of days.')
parser.add_argument('--keep_min_deployments', type=int, required=False, help='Minimum number of deploys to keep if --prune_older_than_days is specified.')
parser.add_argument('--access_key', default=os.getenv('AWS_ACCESS_KEY_ID'), type=str, required=False, help='Your AWS access key.')
parser.add_argument('--secret_key', default=os.getenv('AWS_SECRET_ACCESS_KEY'), type=str, required=False, help='Your AWS secret key.')

args = parser.parse_args()

# If --prune_older_than_days is specified, --min_deployments must also be specified.
if ('prune_older_than_days' in vars(args) and args.prune_older_than_days is not None) and ('keep_min_deployments' in vars(args) and args.keep_min_deployments is None):
    parser.error('You must specify --prune_older_than_days with the argument --keep_min_deployments.')

def auth_to_bucket(bucket_name, access_key=None, secret_key=None):
    # Use the AWS credentials if provided, otherwise use the default credentials
    if access_key and secret_key:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    else:
        try:
            session = boto3.Session()

        except NoCredentialsError:
            raise NoCredentialsError("No AWS credentials found")

    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    return bucket

def get_sorted_deployment_timestamps(bucket):
    directories = {}

    # Get the last modified date for each directory
    for obj in bucket.objects.all():
        directory = obj.key.split('/')[0]
        if directory not in directories or obj.last_modified > directories[directory]:
            directories[directory] = obj.last_modified

    # Sort the directories by LIFO
    sorted_directories = sorted(directories.items(), key=lambda x: x[1], reverse=True)
    
    # Return a list of dictionaries containing the directory name and last modified date
    directory_list = [{'name': k, 'last_modified': v} for k, v in sorted_directories]
    return directory_list

def save_deployments(directory_list, num_deployments):
    print(f'-----------SAVING----------------')

    for deployments in directory_list[:num_deployments]:
        print(f'Object: {deployments["name"]}, Last modified: {deployments["last_modified"]}')

def prune_num_deployments(bucket, directory_list, num_deployments):
    save_deployments(directory_list, args.num_deployments)
    print(f'-----------PRUNING---------------')
    # prune objects that are beyond the num_deployments limit
    for deployments in directory_list[num_deployments:]:
        print(f'Pruning object: {deployments["name"]}, Last modified: {deployments["last_modified"]}')
        bucket.objects.filter(Prefix=deployments["name"]).delete()

def prune_days_older_than_deployments(bucket, directory_list, prune_older_than_days, keep_min_deployments):

    # Get timestamp for the cutoff date
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=prune_older_than_days)

    # Get a list of deployments beyond the minimum number of deployments to keep constraint
    for deployments in directory_list[keep_min_deployments:]:
        time_left = int((deployments["last_modified"]-cutoff_date).days)

        # Prune objects that are older than the cutoff time
        if time_left < 0:
            print(f'-----------PRUNING OLDER THAN {prune_older_than_days} DAYS---------------')
            print(f'Pruning object: {deployments["name"]}, Last modified: {deployments["last_modified"]}')
            bucket.objects.filter(Prefix=deployments["name"]).delete()

def prune_deployments(bucket, directory_list, num_deployments=None, prune_older_than_days=None, keep_min_deployments=None):

    # Validate the input
    if num_deployments is not None and prune_older_than_days is not None:
        raise ValueError("Cannot specify both num_deployments and prune_older_than_days")
    elif num_deployments is None and prune_older_than_days is None:
        raise ValueError("Must specify either num_deployments or prune_older_than_days/keep_min_deployments")
    
    # Prune the deployments based on the input
    if num_deployments:
        prune_num_deployments(bucket, directory_list, num_deployments)
    elif prune_older_than_days:
        prune_days_older_than_deployments(bucket, directory_list, prune_older_than_days, keep_min_deployments)

# Use the functions to get the sorted deployment timestamps, save the deployments, and prune the deployments
directory_list = get_sorted_deployment_timestamps(auth_to_bucket(args.bucket_name, args.access_key, args.secret_key))
prune_deployments(auth_to_bucket(args.bucket_name, args.access_key, args.secret_key), directory_list, args.num_deployments, args.prune_older_than_days, args.keep_min_deployments)
