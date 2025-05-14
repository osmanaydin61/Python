import boto3
from datetime import datetime, timedelta, UTC
import subprocess
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# E-Posta gönderme fonksiyonu
def send_email_alert(cpu_value):
    sender_email = "losmanaydin61@gmail.com"
    receiver_email = "losmanaydin61@gmail.com"
    app_password = "vhyp hhrz ujuf indw"

    subject = "🚨 Yüksek CPU Kullanımı Uyarısı!"
    body = f"""
    Sunucuda CPU kullanımı çok yüksek! ⚠️

    Şu anki CPU kullanım oranı: {cpu_value}%
    Lütfen kontrol et!

    Bu mesaj otomatik olarak sistem izleyici tarafından gönderildi.
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("📧 Uyarı e-postası gönderildi.")
    except Exception as e:
        print(f"❌ E-posta gönderimi başarısız: {e}")

# CloudWatch'tan CPU verisi alma
def get_cpu_utilization(instance_id):
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(minutes=60)

    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'cpu_usage',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [{'Name': 'InstanceId', 'Value': instance_id}]
                    },
                    'Period': 60,
                    'Stat': 'Average'
                },
                'ReturnData': True
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        ScanBy='TimestampDescending',
        MaxDatapoints=10
    )
    return response['MetricDataResults'][0]['Values']

# Yüksek CPU kullanan işlemler
def find_high_cpu_processes():
    result = subprocess.run(['ps', 'aux', '--sort=-%cpu'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    lines = output.split('\n')[1:]
    processes = []
    for line in lines:
        parts = line.split()
        if len(parts) > 2:
            try:
                cpu_usage = float(parts[2])
                pid = parts[1]
                if cpu_usage > 50.0:
                    processes.append((pid, cpu_usage))
            except ValueError:
                continue
    return processes

# Grafik çizme
def create_cpu_report(cpu_usage):
    plt.figure()
    plt.plot(cpu_usage[::-1], marker='o', label="CPU Kullanımı (%)")  # Yeni veriler en sona
    plt.xlabel("Zaman")
    plt.ylabel("Kullanım Oranı (%)")
    plt.legend()
    plt.grid()
    plt.savefig("cpu_report.png")

# Ana fonksiyon
def main():
    instance_id = "i-0d355e17b8947e5cc"  # EC2 ID’ni yaz
    cpu_usage = get_cpu_utilization(instance_id)
    print(f"📊 CloudWatch CPU verisi: {cpu_usage}")

    if not cpu_usage:
        print("❌ CloudWatch'tan veri alınamadı.")
        return

    latest_cpu = cpu_usage[0]
    print(f"🔍 Son CPU değeri: {latest_cpu}")

    if latest_cpu > 80.0:
        print("🔥 Yüksek CPU kullanımı tespit edildi!")
        send_email_alert(latest_cpu)

        high_cpu_processes = find_high_cpu_processes()
        for pid, usage in high_cpu_processes:
            print(f"⚠️ PID: {pid}, CPU: {usage}%")

        create_cpu_report(cpu_usage)
        print("📈 Grafik oluşturuldu: cpu_report.png")
    else:
        print("✅ CPU kullanımı normal.")

if __name__ == "__main__":
    main()
