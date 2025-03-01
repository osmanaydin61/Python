import boto3
from datetime import datetime, timedelta, UTC

def get_cpu_utilization(instance_id):
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(minutes=10)

    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Average']
    )
    return response['Datapoints']

if __name__ == "__main__":
    instance_id = "i-0d355e17b8947e5cc"  # EC2 örneğinizin ID'si
    cpu_data = get_cpu_utilization(instance_id)
    print("CloudWatch'tan alınan veri:", cpu_data)