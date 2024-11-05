"""
{filename}
==============================================================================

| Example of how to generate a voice (TTS - Text To Speech)
|
| The resulting audio sample will be placed in a folder named "results"
| The input is limited to 1000 characters (it will cut at 1000 in backend)
"""

import asyncio
from pathlib import Path

from ex.boilerplate import API

# tts_file = "tts.webm"
tts_file = "tts.webm"


async def main():
    d = Path("results")
    d.mkdir(exist_ok=True)

    async with API() as api_handler:
        api = api_handler.api
        logger = api_handler.logger

        text = "I hope by the time I'm saying this, V3 of text-to-speech will be out!"
        seed = "seedmix:business_coalition|cadence:0006"

        global tts_file
        tts_file = seed + ".webm"

        voice = 0

        opus = False

        version = "v2"

        logger.info(f"Generating a tts voice for {len(text)} characters of text")

        tts = await api.low_level.generate_voice(text, seed, voice, opus, version)
        with open(d / tts_file, "wb") as f:
            f.write(tts)

        logger.info(f"TTS saved in {tts_file}")


if __name__ == "__main__":
    asyncio.run(main())