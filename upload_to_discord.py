#!/usr/bin/env python3
import os
import glob
import zipfile
import requests

def upload_report_safe_engine():
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("[-] Error: DISCORD_WEBHOOK_URL variable is missing.")
        return

    # 1. 최신 엑셀 보고서 탐색
    files = glob.glob('reports/passive_recon_report_v*.xlsx')
    if not files:
        print("[-] Error: No excel report found in reports/ folder.")
        return
    
    latest_file = max(files, key=os.path.getmtime)
    file_name = os.path.basename(latest_file)
    
    # 2. 고강도 ZIP 압축 실행 (용량 다이어트)
    zip_file_name = file_name.replace('.xlsx', '.zip')
    zip_file_path = os.path.join('reports', zip_file_name)
    
    print(f"[+] Compressing {file_name} with maximum ZIP efficiency...")
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(latest_file, arcname=file_name)
        
    compressed_size = os.path.getsize(zip_file_path)
    print(f"[+] Compression complete: {compressed_size / 1024 / 1024:.2f} MB")

    DISCORD_LIMIT = 9.5 * 1024 * 1024 # 안전 전송 마지노선 (9.5MB)

    # -----------------------------------------------------------------
    # [Case 1] 압축 결과가 9.5MB 이하인 경우 -> 통째로 단일 파일 직송
    # -----------------------------------------------------------------
    if compressed_size <= DISCORD_LIMIT:
        print("[+] Compressed file is within Discord limits. Transmitting natively...")
        with open(zip_file_path, 'rb') as f:
            payload = {
                'content': f"🚀 **[정찰 완료 - 마스터 보고서]**\n🔒 보안 압축 파일이 안전하게 직송되었습니다.\n📅 원본 파일명: `{file_name}`"
            }
            files_payload = {'file': (zip_file_name, f, 'application/zip')}
            response = requests.post(webhook_url, data=payload, files=files_payload)
            
        if response.status_code in [200, 204]:
            print("[+] [SUCCESS] Native Discord transmission complete!")
        else:
            print(f"[-] Discord error: {response.status_code}, {response.text}")

    # -----------------------------------------------------------------
    # [🔥Case 2 개조] 9.5MB 초과 시 모든 조각을 한 알람(메시지)에 패킹해서 직송
    # -----------------------------------------------------------------
    else:
        print("[!] Warning: Compressed size exceeds limit. Gathering chunks into a single message packet...")
        part_num = 1
        files_payload = {}
        
        # [핵심] 반복문 내에서 전송하지 않고, 파일 스트림 오브젝트들을 하나의 딕셔너리에 다 누적합니다.
        # 바이너리 유실 방지를 위해 파일 핸들러들을 open 상태로 유지하기 위한 리스트 생성
        opened_files = []
        
        with open(zip_file_path, 'rb') as f:
            while True:
                chunk = f.read(int(DISCORD_LIMIT))
                if not chunk:
                    break
                
                chunk_name = f"{zip_file_name}.part{part_num}"
                
                # 가상머신 임시 경로에 각 조각을 바이너리로 잠깐 떨궈놓고 requests에 바인딩
                temp_chunk_path = os.path.join('reports', chunk_name)
                with open(temp_chunk_path, 'wb') as tmp:
                    tmp.write(chunk)
                
                # 전송용 파일 포인터 오픈 후 페이로드 딕셔너리에 탑재
                target_f = open(temp_chunk_path, 'rb')
                opened_files.append(target_f)
                files_payload[f'file[{part_num-1}]'] = (chunk_name, target_f, 'application/octet-stream')
                
                part_num += 1
        
        # 안내 문구 및 터미널 명령어 조립 (딱 1번만 출력됨)
        cmd_win = f"copy /b {zip_file_name}.part* {zip_file_name}"
        cmd_mac = f"cat {zip_file_name}.part* > {zip_file_name}"
        
        payload = {
            'content': (
                f"📦 **[대용량 통합 분할 사출] 마스터 보고서 (총 {part_num - 1}개 조각)**\n"
                f"💡 모든 파일 조각이 단 하나의 알림으로 묶여 배달되었습니다.\n"
                f"ℹ️ 아래 첨부된 파일들을 **모두 한 폴더에 다운로드**한 뒤 터미널에서 병합 명령어를 실행하세요.\n"
                f"```cmd\n"
                f"※ Windows (CMD):\n{cmd_win}\n\n"
                f"※ Mac / Linux:\n{cmd_mac}\n"
                f"```"
            )
        }
        
        print(f"[+] Transmitting all {part_num - 1} files simultaneously in a single Discord request...", flush=True)
        response = requests.post(webhook_url, data=payload, files=files_payload)
        
        # 오픈했던 임시 파일들 깔끔하게 클로즈 및 가상머신 잔여물 청소
        for tf in opened_files:
            tf.close()
        for p in range(1, part_num):
            try: os.remove(os.path.join('reports', f"{zip_file_name}.part{p}"))
            except: pass
            
        if response.status_code in [200, 204]:
            print("[+] [SUCCESS] Consolidated Discord transmission complete!")
        else:
            print(f"[-] Discord error: {response.status_code}, {response.text}")

if __name__ == '__main__':
    upload_report_safe_engine()
