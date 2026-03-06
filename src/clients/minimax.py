import os
import requests


def retrieve_file_content(file_id):
    #     curl --request GET \
    #   --url https://api.minimax.io/v1/files/retrieve_content?file_id=<file_id> \
    #   --header 'Authorization: Bearer <token>'
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/files/retrieve_content"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    params = {
        "file_id": file_id
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(f"Error retrieving file content: {response.status_code} {response.text}")
    
    return response.content


def check_speech_gen_task_status(task_id = None):
    #     curl --request GET \
    #   --url https://api.minimax.io/v1/query/t2a_async_query_v2?task_id=<task_id> \
    #   --header 'Authorization: Bearer <token>'

    # response:
    # {
    #     "task_id": 95157322514444,
    #     "status": "Processing",
    #     "file_id": 95157322514496,
    #     "base_resp": {
    #         "status_code": 0,
    #         "status_msg": "success"
    #     }
    # }
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/query/t2a_async_query_v2"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    if task_id:
        params = {
            "task_id": task_id
        }
    else:
        params = {}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(f"Error checking task status: {response.status_code} {response.text}")
    
    return response.json()


def create_speech_gen_task(voice_id, text):
    # curl --request POST \
    # --url https://api.minimax.io/v1/t2a_async_v2 \
    # --header 'Authorization: Bearer <token>' \
    # --header 'Content-Type: application/json' \
    # --data '
    #     {
    #     "model": "speech-2.8-hd",
    #     "text": "Omg(sighs), the real danger is not that computers start thinking like people, but that people start thinking like computers. Computers can only help us with simple tasks.",
    #     "voice_setting": {
    #         "voice_id": "English_expressive_narrator",
    #         "speed": 1,
    #         "vol": 1,
    #         "pitch": 1
    #     },
    #     "audio_setting": {
    #         "audio_sample_rate": 32000,
    #         "bitrate": 128000,
    #         "format": "mp3",
    #         "channel": 2
    #     },
    #     "pronunciation_dict": {
    #         "tone": [
    #         "Omg/Oh my god"
    #         ]
    #     },
    #     "language_boost": "auto",
    #     "voice_modify": {
    #         "pitch": 0,
    #         "intensity": 0,
    #         "timbre": 0,
    #         "sound_effects": "spacious_echo"
    #     }
    #     }
    #     '

    # response
    # {
    #     "task_id": 95157322514444,
    #     "task_token": "eyJhbGciOiJSUz",
    #     "file_id": 95157322514444,
    #     "usage_characters": 101,
    #     "base_resp": {
    #         "status_code": 0,
    #         "status_msg": "success"
    #     }
    # }
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/t2a_async_v2"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "speech-2.8-hd",
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 1,
            "vol": 1,
            "pitch": 1
        },
        "audio_setting": {
            "audio_sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 2
        },
        "pronunciation_dict": {
            "tone": []
        },
        "language_boost": "auto",
        "voice_modify": {
            "pitch": 0,
            "intensity": 0,
            "timbre": 0,
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise ValueError(f"Error creating speech generation task: {response.status_code} {response.text}")
    
    return response.json()


def get_voice():
    # curl --request POST \
    #     --url https://api.minimax.io/v1/get_voice \
    #     --header 'Authorization: Bearer <token>' \
    #     --header 'Content-Type: application/json' \
    #     --data '
    #         {
    #         "voice_type": "all"
    #         }
    #         '

    # response:
    #     {
    #   "system_voice": [
    #     {
    #       "voice_id": "Chinese (Mandarin)_Reliable_Executive",
    #       "description": [
    #         "A steady and reliable male executive voice in standard Mandarin, conveying a trustworthy impression."
    #       ],
    #       "voice_name": "Steady Executive",
    #       "created_time": "1970-01-01"
    #     },
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/get_voice"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    data = {
        "voice_type": "voice_cloning"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise ValueError(f"Error fetching voices: {response.status_code} {response.text}")
    
    return response.json()


# if __name__ == "__main__":
#     obama_voice_id = "moss_audio_8dd65fdb-19a0-11f1-a9eb-d68e15ebe5cd"
#     text = "The quick brown fox jumps over the lazy dog."
#     # response = create_speech_gen_task(obama_voice_id, text)
#     # print(response)
#     # task_id = response["task_id"]
#     # task_id = 373883102101766
#     # response = check_speech_gen_task_status(task_id)
#     # print(response)
#     # if response["status"] == "Success":
#     #     print("Task completed successfully, retrieving file content...")
#     #     file_id = response["file_id"]

#     file_id = 373883102101766
#     file_content = retrieve_file_content(file_id)

#     # write file content to a mp3 file
#     with open("output.mp3", "wb") as f:
#         f.write(file_content)
