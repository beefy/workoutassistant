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


def upload_prompt_audio(file_path, purpose):
    # curl --request POST \
    #   --url https://api.minimax.io/v1/files/upload \
    #   --header 'Authorization: Bearer <token>' \
    #   --header 'Content-Type: multipart/form-data' \
    #   --form purpose=prompt_audio \
    #   --form file='@example-file'
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/files/upload"
    headers = {
        "Authorization": f"Bearer {bearer}",
    }
    data = {
        "purpose": purpose,
    }
    files = {
        "file": open(file_path, "rb")
    }
    response = requests.post(url, headers=headers, data=data, files=files)
    if response.status_code != 200:
        raise ValueError(f"Error uploading prompt audio: {response.status_code} {response.text}")
    
    return response.json()


def voice_clone(file_id1, file_id2):
    # curl --request POST \
    #   --url https://api.minimax.io/v1/voice_clone \
    #   --header 'Authorization: Bearer <token>' \
    #   --header 'Content-Type: application/json' \
    #   --data '
    # {
    #   "file_id": 123456789,
    #   "voice_id": "<voice_id>",
    #   "clone_prompt": {
    #     "prompt_audio": 987654321,
    #     "prompt_text": "This voice sounds natural and pleasant."
    #   },
    #   "text": "A gentle breeze sweeps across the soft grass(breath), carrying the fresh scent along with the songs of birds.",
    #   "model": "speech-2.8-hd",
    #   "need_noise_reduction": false,
    #   "need_volume_normalization": false
    # }
    # '
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/voice_clone"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    # generate a random voice id
    # "text": "Man, it's just dang old complicated. You know, man? It's like a dang old rubix cube man, talking about blue red then you get to one side, you mess up the other side. Well, you know bobby, you know life's too short man. Don't want to hold no grudge, man. Bygones be bygones, man. Two weeks, probably three. Hey man, this 911? I need y'all at Megalomart. Boom, man, there's a fire, man. Everywhere. Chuck Mangione. Sir, you are going to have to speak more slowly, I cannot understand you. Dang. Old. Megalomart. I'll tell you what man, y2k man, mainframe going to come on crashing down, like a dang ol apocalypse now. The horror. The horror. I'll tell you what you do, keep that dang old arm straight. Put your left hand still, speed it the hell up. I've been calling y'all people for the better of a month now. 24 hours a day. Hows you supposed to come out here and do anything about that dog if you're dang old computer aint... I'm gunna have some of that fried chicken, french fries, side of fried okra. Dang old fork. Yeah man I'll tell you what that dang old onion soup powder just put a little bit of that you don't need no grilled onions, man. Boomhauer! Yeah! Beer? Yep",
    voice_id = f"cloned_voice_{file_id1}"
    data = {
        "file_id": file_id1,
        "voice_id": voice_id,
        "clone_prompt": {
            "prompt_audio": file_id2,
            "prompt_text": "Dear User,"
        },
        "text": ".",
        "model": "speech-2.8-hd",
        "need_noise_reduction": False,
        "need_volume_normalization": False
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise ValueError(f"Error creating voice clone task: {response.status_code} {response.text}")

    return response.json()

def list_files():
    #     curl --request GET \
    #   --url https://api.minimax.io/v1/files/list \
    #   --header 'Authorization: Bearer <token>'
    bearer = os.getenv("MINIMAX_BEARER_TOKEN")
    if not bearer:
        raise ValueError("MINIMAX_BEARER_TOKEN environment variable not set")
    
    url = "https://api.minimax.io/v1/files/list"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Error listing files: {response.status_code} {response.text}")
    
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


# if __name__ == "__main__":
#     # hank voice_id = "cloned_voice_374706236166550"
#     response1 = upload_prompt_audio("/Users/nate/Code/workoutassistant/downloads/boomhauer.mp3", "voice_clone")
#     response2 = upload_prompt_audio("/Users/nate/Code/workoutassistant/downloads/boomhauer_5.mp3", "prompt_audio")
#     print(response1)
#     print(response2)
#     file_id1 = response1["file"]["file_id"]
#     file_id2 = response2["file"]["file_id"]
#     voice_id = f"cloned_voice_{file_id1}"
#     print(voice_id)
#     response = voice_clone(file_id1, file_id2)
#     print(response)

if __name__ == "__main__":
    response = list_files()
    files = [file for file in response['files'] if file['purpose'] == 't2a_async']
    for file in files:
        # TODO: check if file already exists locally before retrieving content
        content = retrieve_file_content(file['file_id'])
        # write file content to a mp3 file
        with open(f"downloads/{file['file_id']}.mp3", "wb") as f:
            f.write(content)
