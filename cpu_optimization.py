import boto3
from datetime import datetime, timedelta, UTC
import subprocess
import matplotlib.pyplot as plt

# CloudWatch'tan CPU kullanımını çekme (son 10 veri)
def get_cpu_utilization(instance_id):
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(minutes=15)  # Zaman aralığını daralttık

    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'cpu_usage',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instance_id
                            },
                        ]
                    },
                    'Period': 30,  # 30 saniyelik veri çek
                    'Stat': 'Average'
                },
                'ReturnData': True
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        ScanBy='TimestampDescending',  # En yeni verileri önce getir
        MaxDatapoints=20  # Daha fazla veri al, çünkü eski veri gelmiş olabilir
    )

    if 'MetricDataResults' in response and response['MetricDataResults']:
        cpu_usage = response['MetricDataResults'][0].get('Values', [])
        print(f"📊 CloudWatch'tan Güncellenmiş CPU Verileri: {cpu_usage}")
        return cpu_usage
    else:
        print("❌ CloudWatch'tan CPU verisi alınamadı!")
        return []


    #return response['MetricDataResults'][0]['Values']

# Yüksek CPU kullanan işlemleri bulma

def find_high_cpu_processes():
    result = subprocess.run(['top', '-b', '-n', '1'], stdout=subprocess.PIPE, text=True)
    output = result.stdout.split("\n")

    processes = []
    for line in output:
        parts = line.split()

        # 🔹 İlk sütun PID olmalı ve sayısal olmalı
        if len(parts) < 9 or not parts[0].isdigit():
            continue  # Geçersiz satırları atla

        try:
            pid = int(parts[0])  # PID sayıya çevrildi
            cpu_usage = float(parts[8])  # CPU % değeri alındı

            if cpu_usage > 50.0:  # %50'den fazla CPU kullanan işlemleri ekleyelim
                processes.append((pid, cpu_usage))
        
        except ValueError:
            continue  # Eğer hata olursa satırı atla

    return processes


# Rapor oluşturma
def create_cpu_report(cpu_usage):
    plt.figure()
    plt.plot(cpu_usage, label="CPU Kullanımı (%)")
    plt.xlabel("Zaman")
    plt.ylabel("Kullanım Oranı (%)")
    plt.legend()
    plt.grid()
    plt.savefig("cpu_report.png")

# Ana fonksiyon
def main():
    instance_id = "i-0d355e17b8947e5cc"  # EC2 örneğinizin ID'si
    cpu_usage = get_cpu_utilization(instance_id)

    if not cpu_usage:  # Eğer veri yoksa
        print("CloudWatch'tan CPU kullanım verisi alınamadı.")
        return
    # Tüm değerleri float'a çevir ve yazdır
    cpu_usage = [float(x) for x in cpu_usage]
    print(f"CPU Kullanım Değerleri: {cpu_usage}")

    if max(cpu_usage) > 80.0:
        print("Yüksek CPU kullanımı tespit edildi!")
        high_cpu_processes = find_high_cpu_processes()
        for pid, usage in high_cpu_processes:
            print(f"PID: {pid}, CPU Kullanımı: {usage}%")
        
        create_cpu_report(cpu_usage)
        print("Rapor oluşturuldu: cpu_report.png")
    else:
        print("CPU kullanımı normal.")

if __name__ == "__main__":
    main()