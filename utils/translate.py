import sys
import googletrans

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

def translate_google(text, source, target):
    try:
        translator = googletrans.Translator()
        result = translator.translate(text, src=source, dest=target)
        return result.text
    except Exception as e:
        print(f"Error translate: {e}")
        return
    
def detect_google(text):
    try:
        translator = googletrans.Translator()
        result = translator.detect(text)
        return result.lang.upper()
    except Exception as e:
        print(f"Error detect: {e}")
        return