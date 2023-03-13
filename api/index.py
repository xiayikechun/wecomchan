import os
import base64
import json
import logging

import requests
from http.server import BaseHTTPRequestHandler


def send_to_wecom(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "text",
            "text": {
                "content": text
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return str(response)
    else:
        return None


def send_to_wecom_markdown(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "markdown",
            "markdown": {
                "content": text
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return str(response)
    else:
        return None


def send_to_wecom_pic(base64_content, wecom_cid, wecom_aid, wecom_secret, wecom_touid):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        upload_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image'
        upload_response = requests.post(upload_url, files={
            "picture": base64.b64decode(base64_content)
        }).json()

        logging.info('upload response: ' + str(upload_response))

        media_id = upload_response['media_id']

        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return str(response)
    else:
        return None


def send_to_wecom_file(base64_content, file_name, wecom_cid, wecom_aid, wecom_secret, wecom_touid):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        upload_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=file'
        upload_response = requests.post(upload_url + "&debug=1", files={
            "media": (file_name, base64.b64decode(base64_content))  # 此处上传中文文件名文件旧版本 urllib 有 bug.
        }).json()

        logging.info('upload response: ' + str(upload_response))

        media_id = upload_response['media_id']

        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "file",
            "file": {
                "media_id": media_id
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return str(response)
    else:
        return None


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        wecom_id = os.getenv("wecom_id")
        request_body = self.rfile.read(int(self.headers['content-length'])).decode('utf-8')
        path = str(self.path)

        logging.info("request body: " + request_body)
        logging.info("path_info: " + path)

        if path == "/api" or path == "/api/" or path == "/api/index":
            send_key = os.getenv("send_key")
            wecom_agentid = os.getenv("wecom_agentid")
            wecom_secret = os.getenv("wecom_secret")
        else:
            response = '{"code": -6, "msg": "invalid path info"}'
            self.send_response(403)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            return

        try:
            input_json = json.loads(request_body)
            if input_json['key'] != send_key:
                status = '403 Forbidden'
                response = '{"code": -2, "msg": "invalid send key"}'
                self.send_response(403)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
                return
        except Exception as e:
            logging.exception(e)
            status = '403 Forbidden'
            response = '{"code": -1, "msg": "invalid json input"}'
            self.send_response(403)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            return

        wecom_touid = input_json.get('uid', '@all')

        logging.info("wecom_touid: " + str(wecom_touid))

        code = 0
        msg = "ok"
        status = '200 OK'

        try:
            if 'type' not in input_json or input_json['type'] == 'text':
                result = send_to_wecom(input_json['msg'], wecom_id, wecom_agentid, wecom_secret, wecom_touid)
            elif input_json['type'] == 'image':
                result = send_to_wecom_pic(input_json['msg'], wecom_id, wecom_agentid, wecom_secret, wecom_touid)
            elif input_json['type'] == 'markdown':
                result = send_to_wecom_markdown(input_json['msg'], wecom_id, wecom_agentid, wecom_secret, wecom_touid)
            elif input_json['type'] == 'file':
                if 'filename' in input_json:
                    result = send_to_wecom_file(input_json['msg'], input_json['filename'], wecom_id, wecom_agentid,
                                                wecom_secret, wecom_touid)
                else:
                    result = send_to_wecom_file(input_json['msg'], "Wepush推送", wecom_id, wecom_agentid, wecom_secret,
                                                wecom_touid)
                    msg = "filename not found. using default."
            else:
                code = -5
                msg = "invalid msg type. type should be text(default), image, markdown or file."
                status = "500 Internal Server Error"
                result = ""

            logging.info('wechat api response: ' + str(result))
            if result is None:
                status = "500 Internal Server Error"
                code = -4
                msg = "wechat api error: wrong config?"
        except Exception as e:
            status = "500 Internal Server Error"
            code = -3
            msg = "unexpected error: " + str(e)
            logging.exception(e)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"code": code, "msg": msg})
        self.wfile.write(response.encode('utf-8'))
        return
