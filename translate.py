import googletrans
import speech_recognition as sr
import gtts
import playsound

# gtts means google text to speech
print(googletrans.LANGUAGES)
recognizer = sr.Recognizer()
translator = googletrans.Translator()
input_language = 'fr'
output_language = 'tr'

try:
    with sr.Microphone() as source:
        print('Speak Now')
        voice = recognizer.listen(source)
        txt = recognizer.recognize_google(voice, language=input_language)
        # print(txt)


except:
    pass

translated = translator.translate(txt, output_language)
converted_audio = gtts.gTTS(translated.text, lang=output_language)
converted_audio.save('translated.mp3')
playsound.playsound('translated.mp3')
print(translated.text)
