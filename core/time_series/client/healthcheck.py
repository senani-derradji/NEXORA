import influxdb_client
from influxdb_client.rest import ApiException
from influxdb_client.client.bucket_api import BucketsApi
from influxdb_client.client.organizations_api import OrganizationsApi
from influxdb_client import InfluxDBClient
from core.time_series.config.settings import TSBS_INFO

URL=TSBS_INFO.URL
ORG_NAME=TSBS_INFO.ORGANIZATION
BUCKET_NAME=TSBS_INFO.BUCKET
TOKEN=TSBS_INFO.TOKEN


def credentials_is_valid():
    try:
        print(f"[DEBUG] Attempting to connect to InfluxDB at: {URL}")
        print(f"[DEBUG] Using token: {TOKEN[:10]}..." if TOKEN else "[DEBUG] Token is None or empty!")
        print(f"[DEBUG] Looking for organization: {ORG_NAME}")
        print(f"[DEBUG] Looking for bucket: {BUCKET_NAME}")

        client = InfluxDBClient(
                                url=URL,
                                token=TOKEN,
                                org=ORG_NAME
                                )
        print(f"[DEBUG] InfluxDBClient created successfully")

        orgs_api = OrganizationsApi(client)
        buckets_api = BucketsApi(client)

        print(f"[DEBUG] Attempting to find organization: {ORG_NAME}")
        org = orgs_api.find_organizations(org=ORG_NAME)
        if org:
            org = org[0]
            print(f"[DEBUG] Found organization: {org.name} (ID: {org.id})")
        else:
            print(f"[DEBUG] Organization '{ORG_NAME}' not found!")

        bucket = buckets_api.find_bucket_by_name(BUCKET_NAME)
        if bucket is None:
            print(f"Bucket '{BUCKET_NAME}' does not exist. Creating it...")
            retention_rules = [influxdb_client.domain.BucketRetentionRules(type="expire", every_seconds=0)]
            new_bucket = influxdb_client.domain.Bucket(name=BUCKET_NAME, org_id=org.id, retention_rules=retention_rules)
            bucket = buckets_api.create_bucket(new_bucket)
            print(f"Bucket '{BUCKET_NAME}' created with ID: {bucket.id}")

        client.close()


    except ApiException as e:
        print(f"[ERROR] An API error occurred: {e}")
        print(f"[ERROR] API Exception details: status={e.status}, reason={e.reason}")
        return False
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True



def health_check():
    from .client import InfluxClient

    try:
        influx_client = InfluxClient()
        if influx_client.client is None:
            raise Exception("InfluxClient is not initialized - credentials may be invalid")

        health = influx_client.client.health()
        print(health)

        if health.status == "pass":
            print(f"Health check passed: {health.message}")
            return True
        else:
            raise Exception(f"Health check failed: {health.message}")


    except Exception as e:
        raise Exception(f"Health check failed: {e}")

    finally:
        try:
            influx_client.client.close()
        except:
            pass