from gradio_client import Client, handle_file

client = Client("mrfakename/E2-F5-TTS")
result = client.predict(
    ref_audio=handle_file('src/audio_samples/obama.ogg'),
    ref_text="Mrs Rodham was a remarkable person, to anyone who knows her history knows what a strong, determined, and gifted person she was. For her to have been able to live the life that she did and to see her daughter succeed at the pinnacle of public service in this country, I'm sure was deeply satisfying to her. You know. My thoughts and Chel's thoughs, the entire white house's thoughts go out to the entire Clinton family and I know that she will be remembered as someone who helped make a difference in this country and this world. Alright?",
    gen_text="Fortnight number one victory royale! Yeah, that's what I'm talking about. Getting that victory royale is always an exciting moment in the game. The battle royale format has really changed the gaming landscape over the past few years, bringing players together from all around the world to compete for that coveted first place finish.",
    remove_silence=False,
    api_name="/predict"
)
print(result)
