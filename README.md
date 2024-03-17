# Prune Deployments

### Requirements
- python3
- pip
- AWS role or credentials with permission to list/read/remove objects in bucket

### Usage

```
pip install -r requirements.txt (once)

python prune_deployments.py --bucket_name $BUCKET_NAME --num_deployments $NUM_DEPLOYMENTS
python prune_deployments.py --bucket_name $BUCKET_NAME --access_key $AWS_ACCESS_KEY_ID --secret_key $AWS_SECRET_ACCESS_KEY --prune_older_than_days $PRUNE_OLDER_THAN_DAYS --keep_min_deployments $KEEP_MIN_DEPLOYMENTS
```

### Input Variables

- Bucket Name (string) - `BUCKET_NAME`
- AWS_ACCESS_KEY_ID if not using a default role (string) - `AWS_ACCESS_KEY_ID`
- AWS_SECRET_ACCESS_KEY if not using a default role (string) - `AWS_SECRET_ACCESS_KEY`
- Number Deployments to keep (integer) - `NUM_DEPLOYMENTS`
- Number of days of deployments to keep (integer) - `PRUNE_OLDER_THAN_DAYS`
- Minimum number of deployments to keep if days is specified (integer) - `KEEP_MIN_DEPLOYMENTS`

### Assumptions
- Once a deployment is created, it is immutable.
- All top-level directories are assumed to be deployments.
- Deployments are uploaded into S3 at different times.
- Empty directories are not deployments and therefore can be purged.