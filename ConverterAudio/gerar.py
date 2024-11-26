import speech_recognition as sr
import os

# Caminho para a pasta onde estão os arquivos .wav
audio_folder = "/Users/macbookprodopedro/Documents/GitHub/IdeiasParaFazerEmPython/ConverterAudio"  # Substitua pelo caminho correto

# Inicializar o reconhecedor
recognizer = sr.Recognizer()

# Lista para armazenar as transcrições
transcriptions = []

# Processar os arquivos de chunk_0.wav a chunk_17.wav
for i in range(18):  # De 0 a 17
    audio_file = os.path.join(audio_folder, f"chunk_{i}.wav")
    
    try:
        with sr.AudioFile(audio_file) as source:
            print(f"Processando {audio_file}...")
            audio_data = recognizer.record(source)
        
        # Tentar transcrever o áudio
        print(f"Transcrevendo {audio_file}...")
        text = recognizer.recognize_google(audio_data, language="pt-BR")
        transcriptions.append(f"chunk_{i}.wav: {text}")
    
    except sr.UnknownValueError:
        transcriptions.append(f"chunk_{i}.wav: Não foi possível reconhecer o áudio.")
    except sr.RequestError as e:
        transcriptions.append(f"chunk_{i}.wav: Erro ao conectar ao serviço de reconhecimento: {e}")

# Salvar ou exibir os resultados
print("\nTranscrições:")
for transcription in transcriptions:
    print(transcription)

# Opcional: salvar em um arquivo de texto
output_file = os.path.join(audio_folder, "transcricoes.txt")
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(transcriptions))
