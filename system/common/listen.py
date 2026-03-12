import speech_recognition as sr

def listen():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Listening...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        command = r.recognize_google(audio)
        print("You said:", command)
        return command.lower()
    except:
        return ""
