#!/usr/bin/env python3
import os
import glob
import requests

def upload_report_via_secure_link():
    # GitHub Secrets에서 디스코드 주소 수신
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')

    if not webhook_url:
        print("[-] Error: DISCORD_WEBHOOK_URL environment variable is missing.")
        return

    # reports/ 폴더 내에서 생성된 엑셀 마스터 보고서 목록 탐색
    files = glob.glob('reports/passive_recon_report_v*.xlsx')
    if not files:
        print("[-] Error: No excel report found in reports/ folder.")
        return
    
    # 가장 최근에 생성된 최신 버전 파일 선택
    latest_file = max(files, key=os.path.getmtime)
    file_name = os.path.basename(latest_file)
    file_size = os.path.getsize(latest_file)

    print(f"[+] Found latest report: {file_name} ({file_size / 1024 / 1024:.2f} MB)")
    print(f"[+] Uploading to file.io for secure one-time link generation...")

    # [1단계]: file.io 보안 서버로 파일 업로드 수행 (별도 가입/API Key 필요 없음)
    try:
        with open(latest_file, 'rb') as f:
            # 파일 스트림을 file.io 정문으로 전송
            io_response = requests.post('https://file.io', files={'file': f})
        
        if io_response.status_code == 200:
            io_data = io_response.json()
            if io_data.get('success'):
                secure_link = io_data.get('link')
                expiry = io_data.get('expiry', '14 days')
                print(f"[+] Secure link generated successfully: {secure_link}")
            else:
                print(f"[-] file.io upload failed: {io_data.get('message')}")
                return
        else:
            print(f"[-] file.io server returned status code: {io_response.status_code}")
            return
    except Exception as e:
        print(f"[-] Exception during file.io upload: {str(e)}")
        return

    # [2단계]: 발급된 일회성 링크를 디스코드 채널로 사출
    print(f"[+] Transmitting secure link to Private Discord Channel...")
    
    # 디스코드 가독성을 높이기 위한 마크다운 템플릿 구성
    discord_message = (
        f"🚀 **[정찰 완료 - 대용량 마스터 보고서]**\n"
        f"📊 파일명: `{file_name}`\n"
        f"⚖️ 파일 크기: `{file_size / 1024 / 1024:.2f} MB`\n\n"
        f"🔒 **보안 다운로드 링크 (단 1회성):**\n"
        f"🔗 {secure_link}\n\n"
        f"⚠️ *주의: 이 링크는 딱 **1번만 다운로드**가 가능하며, 다운로드 직후 서버에서 흔적 없이 영구 삭제됩니다!* (미다운로드 시 {expiry} 후 자동 폭파)"
    )
    
    payload = {'content': discord_message}
    response = requests.post(webhook_url, data=payload)

    if response.status_code in [200, 204]:
        print("[+] [SUCCESS] Secure link transmitted to Discord successfully!")
    else:
        print(f"[-] Error sending to Discord: Status {response.status_code}, {response.text}")

if __name__ == '__main__':
    upload_report_via_secure_link()
