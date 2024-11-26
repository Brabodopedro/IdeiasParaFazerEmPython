from pydub import AudioSegment

# Carregar o áudio
audio = AudioSegment.from_file("/Users/macbookprodopedro/Documents/GitHub/IdeiasParaFazerEmPython/ConverterAudio/audio.wav")

# Dividir em partes de 1 minuto (60.000 ms)
audio_chunks = [audio[i:i + 60000] for i in range(0, len(audio), 60000)]

# Exportar as partes
for i, chunk in enumerate(audio_chunks):
    chunk.export(f"chunk_{i}.wav", format="wav")
