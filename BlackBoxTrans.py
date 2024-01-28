import googletrans
import speech_recognition as sr
from gtts import gTTS
import playsound

print(googletrans.LANGUAGES)
recognizer = sr.Recognizer()
translator = googletrans.Translator()
input_language = 'fr'
output_language = 'tr'

try:
    with sr.Microphone() as source:
        print('Speak Now')
        voice = recognizer.listen(source, phrase_time_limit=5)
        txt = recognizer.recognize_google(voice, language=input_language, show_all=True)
        if 'transcript' in txt and len(txt['transcript']) > 0:
            txt = txt['transcript'][0]
except Exception as e:
    print(f'Error: {e}')

translated = translator.translate(txt, src=input_language, dest=output_language)
converted_audio = gTTS(translated.text, lang=output_language, slow=False)
converted_audio.save('translated.mp3')
playsound.playsound('translated.mp3', block=False)
print(translated.text)