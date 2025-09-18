import winsound

import gtts
import speech_recognition as sr
from deep_translator import GoogleTranslator

# gtts means google text to speech
print(GoogleTranslator(source='en').get_supported_languages())
recognizer = sr.Recognizer()
input_language = 'fr'
output_language = 'tr'
translator = GoogleTranslator(source=input_language, target=output_language)

txt = "Bonjour, je veux manger un gateau "

try:
    with sr.Microphone() as source:
        print('Speak Now')
        voice = recognizer.listen(source)
        txt = recognizer.recognize_google(voice, language=input_language)
        # print(txt)


except:
    pass

translated = translator.translate(txt)
converted_audio = gtts.gTTS(translated, lang=output_language)
converted_audio.save('translated.mp3')
winsound.PlaySound('translated.mp3', winsound.SND_FILENAME)
print(translated)
