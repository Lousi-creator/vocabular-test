import asyncio
import edge_tts
import pandas as pd
import os

VOICES = {
    "male": "en-US-GuyNeural",
    "female": "en-US-JennyNeural",
}

async def generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save(output_path)
    print(f"  ✓ {output_path}")

def split_dialogue(text):
    """将 M:/W: 对话拆分为按说话人的分段"""
    parts = []
    current_speaker = None
    current_text = []
    for line in text.split(". "):
        line = line.strip()
        if not line:
            continue
        if line.startswith("M:") or line.startswith("M :"):
            if current_text:
                parts.append((current_speaker, ". ".join(current_text) + "."))
            current_speaker = "male"
            current_text = [line[2:].strip().lstrip(":")]
        elif line.startswith("W:") or line.startswith("W :"):
            if current_text:
                parts.append((current_speaker, ". ".join(current_text) + "."))
            current_speaker = "female"
            current_text = [line[2:].strip().lstrip(":")]
        else:
            current_text.append(line)
    if current_text:
        parts.append((current_speaker, ". ".join(current_text) + "."))
    return parts

async def generate_dialogue(text, output_path):
    """生成带多说话人的对话音频"""
    parts = split_dialogue(text)
    if len(parts) <= 1:
        await generate_audio(text, VOICES["female"], output_path)
        return
    import tempfile
    temp_files = []
    try:
        for i, (speaker, segment) in enumerate(parts):
            tmp_path = os.path.join(tempfile.gettempdir(), f"_tts_part_{i}_{os.path.basename(output_path)}")
            await generate_audio(segment, VOICES[speaker], tmp_path)
            temp_files.append(tmp_path)
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=500)
        for tf in temp_files:
            combined += AudioSegment.from_file(tf, format="mp3")
            combined += silence
        combined.export(output_path, format="mp3")
        os.remove(output_path.replace(".mp3", "") + ".mp3")
    except ImportError:
        for tf in temp_files:
            os.remove(tf)
        await generate_audio(text, VOICES["female"], output_path)

async def main():
    os.makedirs("listening_audio", exist_ok=True)
    df = pd.read_csv("listening_tests.csv")
    unique_audio = df[["audio", "content"]].drop_duplicates(subset=["audio"])
    print(f"共 {len(unique_audio)} 个音频文件待生成:\n")
    for _, row in unique_audio.iterrows():
        audio_name = row["audio"]
        content = str(row["content"])
        output_path = os.path.join("listening_audio", audio_name)
        print(f"生成 {audio_name}...")
        try:
            await generate_audio(content, VOICES["female"], output_path)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
    print("\n全部完成!")

if __name__ == "__main__":
    asyncio.run(main())
