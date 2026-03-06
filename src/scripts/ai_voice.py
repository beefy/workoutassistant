import torch
from TTS.api import TTS


def clone_voice(ref_audio_path, ref_text, gen_text):
    # # Get device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # # List available 🐸TTS models
    print(TTS().list_models())

    # Initialize TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    # List speakers
    print(tts.speakers)

    # Run TTS
    # ❗ XTTS supports both, but many models allow only one of the `speaker` and
    # `speaker_wav` arguments

    # TTS with list of amplitude values as output, clone the voice from `speaker_wav`
    # wav = tts.tts(
    #     text="Hello world!",
    #     speaker_wav="my/cloning/audio.wav",
    #     language="en"
    # )

    # TTS to a file, use a preset speaker
    # tts.tts_to_file(
    #     text="Hello world!",
    #     language="en",
    #     speaker="Craig Gutsy",
    #     file_path="output.wav"
    # )

    tts.tts_to_file(
        text="Hello world!",
        language="en",
        speaker_wav=ref_audio_path,
        file_path="cloned_output.wav"
    )


if __name__ == "__main__":
    clone_voice(
        ref_audio_path='src/audio_samples/obama2.ogg',
        ref_text="Mrs Rodham was a remarkable person, to anyone who knows her history knows what a strong, determined, and gifted person she was. For her to have been able to live the life that she did and to see her daughter succeed at the pinnacle of public service in this country, I'm sure was deeply satisfying to her. You know. My thoughts and Chel's thoughs, the entire white house's thoughts go out to the entire Clinton family and I know that she will be remembered as someone who helped make a difference in this country and this world. Alright?",
        gen_text="Test text to see if voice cloning works!"
    )
