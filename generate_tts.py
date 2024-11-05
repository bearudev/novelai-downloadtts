import asyncio
from pathlib import Path
import json

from ex.boilerplate import API, dumps
from novelai_api.utils import decrypt_user_data
import ffmpeg
from pydub import AudioSegment
import io
import os
import numpy as np
import soundfile as sf
import tempfile
from pydub import AudioSegment



# this will change during runtime
tts_file = "results/tts.webm"
audioSpeed = 1.5

async def generateTTS(_str):
    d = Path("results")
    d.mkdir(exist_ok=True)

    async with API() as api_handler:
        api = api_handler.api
        logger = api_handler.logger

        texts = [_str]  # noqa: E501  # pylint: disable=C0301

        if len(_str) > 1000:
            texts = split_string_to_chunks(_str)
        
        print(f"Generating audio for {len(texts)} chunks.")

        voice = "Crina"

        seed = 0

        # opus = False
        opus = True

        version = "v1"

        output_files  = []

        for i, text in enumerate(texts, start=1):
            tts = await api.low_level.generate_voice(text, voice, seed, opus, version)

            # Save each audio chunk to a temporary file on disk
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(tts)
                temp_file.flush()  # Ensure data is written
                output_files.append(temp_file.name)  # Keep track of the file path
            
            print(f"({i}/{len(texts)})")
        
        merge_audio_data(output_files, tts_file)  # Call the merge function
        logger.info(f"TTS saved in {tts_file}")

dump_file = Path(__file__).parent / "results" / "story.txt"

def merge_audio_data(input_files, output_file):
    # Create a text file for ffmpeg concat
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as concat_file:
        for file in input_files:
            concat_file.write(f"file '{file}'\n".encode('utf-8'))
        concat_file.flush()

        # Use ffmpeg to concatenate the audio files
        try:
            (
                ffmpeg
                .input(concat_file.name, format='concat', safe=0)
                .output(output_file, c='copy')
                .run(overwrite_output=True)
            )
            print(f'Merged audio written to {output_file}')
        except ffmpeg.Error as e:
            print(f'Error: {e}')

    # Clean up temporary files
    for file in input_files:
        os.remove(file)
    os.remove(concat_file.name)

def split_string_to_chunks(text, max_length=1000):
    words = text.split()  # Split the text into words
    chunks = []
    current_chunk = []

    for word in words:
        # Check if adding the next word exceeds the max length
        if len(' '.join(current_chunk + [word])) <= max_length:
            current_chunk.append(word)  # Add word to the current chunk
        else:
            # Join the current chunk into a string and reset for the next chunk
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]  # Start a new chunk with the current word

    # Add the last chunk if there's any remaining text
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

async def getLastStoryAsTxt():
    async with API() as api_handler:
        api = api_handler.api
        key = api_handler.encryption_key

        keystore = await api.high_level.get_keystore(key)

        story = (await api.high_level.download_user_stories())[0]
        decrypt_user_data(story, keystore)

        storycontent_id = story["data"]["remoteStoryId"]
        global tts_file
        tts_file = f"results/{story["data"]["title"]}.webm"

        print("Getting latest story...")
        story_contents = await api.low_level.download_object("storycontent", storycontent_id)
        decrypt_user_data(story_contents, keystore, True)

        dump_file.parent.mkdir(exist_ok=True)
        dump_file.write_text(dumps(story_contents), "utf-8")

        print(dump_file)
        target_file = open(dump_file, encoding='utf-8')

        json_object = json.loads(target_file.read())
        texts = []
        for section in json_object["data"]["document"]["sections"].items():
            texts.append(section[1]["text"])
        target_file.close()
        target_file = open(dump_file, "w")
        texts_str = ""
        for text in texts:
            texts_str += "\n" + text + "\n"
        target_file.write(texts_str)
        print("Story has been fetched.")
        target_file.close()
        return texts_str

def changeAudioSpeed(audioFile):
    print("Changing speed...")
    global audioSpeed
    ffmpeg.input(audioFile).filter('atempo', audioSpeed).output("temp_output.webm").run(overwrite_output=True)
    os.replace("temp_output.webm", audioFile)
    if os.path.exists("temp_output.webm"):
        os.remove("temp_output.webm")

async def main():
    #generate full audio of latest story\
    await generateTTS(await getLastStoryAsTxt())
    global audioSpeed
    if audioSpeed != 1.0:
        changeAudioSpeed(tts_file)
    
    print("Process Complete!")

if __name__ == "__main__":
    asyncio.run(main())