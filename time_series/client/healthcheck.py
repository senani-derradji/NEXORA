import influxdb_client
from influxdb_client.rest import ApiException
from influxdb_client.client.bucket_api import BucketsApi
from influxdb_client.client.organizations_api import OrganizationsApi
from influxdb_client import InfluxDBClient
from time_series.config.settings import TSBS_INFO

URL=TSBS_INFO.URL
ORG_NAME=TSBS_INFO.ORGANIZATION
BUCKET_NAME=TSBS_INFO.BUCKET
TOKEN=TSBS_INFO.TOKEN


def credentials_is_valid():
    try:
        client = InfluxDBClient(
                                url=URL,
                                token=TOKEN
                                )
        orgs_api = OrganizationsApi(client)
        buckets_api = BucketsApi(client)

        org = orgs_api.find_organizations(org=ORG_NAME)
        if org: org = org[0]

        bucket = buckets_api.find_bucket_by_name(BUCKET_NAME)
        if bucket is None:
            print(f"Bucket '{BUCKET_NAME}' does not exist. Creating it...")
            retention_rules = [influxdb_client.domain.BucketRetentionRules(type="expire", every_seconds=0)]
            new_bucket = influxdb_client.domain.Bucket(name=BUCKET_NAME, org_id=org.id, retention_rules=retention_rules)
            bucket = buckets_api.create_bucket(new_bucket)
            print(f"Bucket '{BUCKET_NAME}' created with ID: {bucket.id}")

        client.close()
    except ApiException as e:
        print(f"An API error occurred: {e}") ; return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}") ; return False

    return True


def health_check():
    from .client import InfluxClient

    try:
        health = InfluxClient().client.health()
        print(health)

        if health.status == "pass":
            print(f"Health check passed: {health.message}")
            return True
        else:
            raise Exception(f"Health check failed: {health.message}")


    except Exception as e:
        raise Exception(f"Health check failed: {e}")

    finally: InfluxClient().client.close()

