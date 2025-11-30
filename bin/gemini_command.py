#!/usr/bin/env python
# coding=utf-8

import sys
import json
import requests
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators

@Configuration()
class GeminiCommand(StreamingCommand):

    prompt = Option(doc='The instruction for AI', require=True)
    field = Option(doc='The field containing the log data', require=False, default='_raw')
    model = Option(doc='Gemini model version', require=False, default='gemini-1.5-flash')

    def stream(self, records):
        API_KEY = "YOUR_GOOGLE_API_KEY_HERE"
	# PROXIES = {
	#     "http": "http://127.0.0.1:10809", 
	#     "https": "http://127.0.0.1:10809",
	# }
	PROXIES = {}

        base_url = "https://generativelanguage.googleapis.com/v1beta/models/"

        for record in records:
            log_data = record.get(self.field, "")
            if not log_data:
                yield record
                continue
            full_prompt = f"{self.prompt}. Log Data: {log_data}"
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            url = f"{base_url}{self.model}:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}

            try:
                response = requests.post(
                    url, 
                    headers=headers, 
                    data=json.dumps(payload), 
                    timeout=30, 
                    proxies=PROXIES
                )
                
                if response.status_code == 200:
                    resp_json = response.json()
                    try:
                        ai_text = resp_json['candidates'][0]['content']['parts'][0]['text']
                        record['gemini_response'] = ai_text
                        record['gemini_status'] = "Success"
                    except (KeyError, IndexError):
                         record['gemini_response'] = "Error parsing JSON structure"
                         record['gemini_status'] = "Parse Error"
                else:
                    record['gemini_response'] = f"Google API Error ({response.status_code}): {response.text}"
                    record['gemini_status'] = "API Fail"

            except Exception as e:
                record['gemini_response'] = f"Connection Error: {str(e)}"
                record['gemini_status'] = "Exception"

            yield record

dispatch(GeminiCommand, sys.argv, sys.stdin, sys.stdout, __name__)