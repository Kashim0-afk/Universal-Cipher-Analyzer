import base64
import string
from collections import Counter
import re
import itertools

# Frequency tables
ENGLISH_FREQ = {
    'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
    'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3,
    'l': 4.0, 'c': 2.8, 'u': 2.8, 'm': 2.4, 'w': 2.4
}

ITALIAN_FREQ = {
    'a': 11.7, 'e': 11.8, 'i': 11.3, 'o': 9.8, 'u': 3.0,
    'l': 6.5, 'r': 6.4, 't': 5.6, 's': 5.0, 'n': 6.9,
    'c': 4.5, 'd': 3.7, 'p': 3.0, 'm': 2.5, 'v': 2.1
}

# Word lists
ITALIAN_WORDS = {
    'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 
    'e', 'ed', 'che', 'di', 'in', 'con', 'su', 'per', 'tra', 'fra',
    'ciao', 'sono', 'io', 'da', 'me', 'si', 'no', 'non', 'hai',
    'ho', 'ha', 'sei', 'è', 'mi', 'ti', 'ci', 'vi', 'qui', 'qua',
    'che', 'ahahahah', 'hahaha', 'ahah'  # Aggiunte risate comuni in italiano
}

ENGLISH_WORDS = {
    'the', 'be', 'by', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
    'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'at',
    'hello', 'from', 'me', 'by', 'know', 'yes', 'no', 'are', 'is',
    'am', 'my', 'your', 'his', 'her', 'their', 'this', 'that',
    'haha', 'hahaha', 'lol'  # Aggiunte risate comuni in inglese
}

def detect_language_blocks(text):
    """
    Split text into blocks and detect language for each block
    Returns: list of tuples (language, text_block)
    """
    # Divide il testo in blocchi basati su spazi multipli o punteggiatura
    blocks = [block.strip() for block in re.split(r'(?:[\s.!?]){2,}', text) if block.strip()]
    
    block_languages = []
    for block in blocks:
        words = set(re.findall(r'\b\w+\b', block.lower()))
        italian_matches = len(words.intersection(ITALIAN_WORDS)) * 2  # Peso maggiore per match esatti
        english_matches = len(words.intersection(ENGLISH_WORDS)) * 2
        
        # Analisi frequenza lettere per supporto aggiuntivo
        letter_freq = Counter(char.lower() for char in block if char.isalpha())
        total_letters = sum(letter_freq.values()) or 1
        
        # Calcola punteggio basato su frequenze per ogni lingua
        it_freq_score = sum(abs(ITALIAN_FREQ.get(char, 0) - (count/total_letters*100))
                           for char, count in letter_freq.items())
        en_freq_score = sum(abs(ENGLISH_FREQ.get(char, 0) - (count/total_letters*100))
                           for char, count in letter_freq.items())
        
        # Combina i punteggi (più basso è meglio per freq_score)
        italian_score = italian_matches - (it_freq_score * 0.1)
        english_score = english_matches - (en_freq_score * 0.1)
        
        block_languages.append(('it' if italian_score > english_score else 'en', block))
    
    return block_languages

def calculate_frequency_score(text, reference_freq):
    """
    Improved frequency analysis scoring with better handling of short texts
    """
    text = ''.join(char.lower() for char in text if char.isalpha())
    if not text:
        return 0
    
    freq = Counter(text)
    total = len(text)
    score = 0
    
    # Calcola il punteggio con peso maggiore per le lettere più comuni
    for char, ref_freq in reference_freq.items():
        observed_freq = (freq.get(char, 0) / total) * 100
        weight = ref_freq / max(reference_freq.values())  # Peso basato sulla frequenza attesa
        score += (100 - abs(observed_freq - ref_freq)) * weight
    
    return score / sum(weight for _, weight in reference_freq.items())

def calculate_language_specific_score(text, lang):
    """
    Calculate score based on specific language with improved scoring system
    """
    words = set(re.findall(r'\b\w+\b', text.lower()))
    word_list = ITALIAN_WORDS if lang == 'it' else ENGLISH_WORDS
    freq_table = ITALIAN_FREQ if lang == 'it' else ENGLISH_FREQ
    
    # Punteggio basato su parole riconosciute
    word_matches = len(words.intersection(word_list))
    word_score = word_matches * 15  # Aumentato il peso delle parole riconosciute
    
    # Punteggio basato su frequenza lettere
    freq_score = calculate_frequency_score(text, freq_table)
    
    # Bonus per lunghezza parole tipiche della lingua
    avg_word_length = sum(len(word) for word in words) / (len(words) if words else 1)
    length_bonus = 10 if (lang == 'it' and 4 <= avg_word_length <= 8) or \
                       (lang == 'en' and 3 <= avg_word_length <= 7) else 0
    
    return word_score + freq_score + length_bonus

def get_reference_frequencies(lang):
    """
    Get appropriate frequency table based on detected language
    """
    if lang == 'mixed':
        return {k: (ITALIAN_FREQ.get(k, 0) + ENGLISH_FREQ.get(k, 0))/2 
               for k in set(ITALIAN_FREQ) | set(ENGLISH_FREQ)}
    return ITALIAN_FREQ if lang == 'it' else ENGLISH_FREQ

def decrypt_caesar(text, key):
    """
    Enhanced Caesar cipher decryption with case preservation
    """
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('A') if char.isupper() else ord('a')
            decrypted = chr((ord(char) - ascii_offset - key) % 26 + ascii_offset)
            result += decrypted
        else:
            result += char
    return result

def try_all_caesar(text, lang):
    """
    Improved Caesar cipher analysis with language-specific scoring
    """
    results = []
    scores = []
    
    for key in range(26):
        decrypted = decrypt_caesar(text, key)
        score = calculate_language_specific_score(decrypted, lang)
        scores.append((score, key, decrypted))
        results.append(f"Chiave {key}: {decrypted}")
    
    return results, sorted(scores, reverse=True)[:3]

def vigenere_decrypt(text, key):
    """
    Enhanced Vigenère cipher decryption with improved handling
    """
    result = ""
    key = key.upper()
    key_length = len(key)
    key_index = 0
    
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % key_length]) - ord('A')
            ascii_offset = ord('A') if char.isupper() else ord('a')
            decrypted = chr((ord(char.upper()) - ord('A') - shift) % 26 + ascii_offset)
            result += decrypted if char.isupper() else decrypted.lower()
            key_index += 1
        else:
            result += char
    
    return result

def try_vigenere_decrypt(text, lang):
    """
    Improved Vigenère analysis with language-specific keys and scoring
    """
    # Chiavi specifiche per lingua
    common_keys = {
        'it': [
            'CIAO', 'IO', 'TU', 'NOI', 'SI', 'ME', 'TE', 'MI', 'TI', 'DA',
            'ROMA', 'CASA', 'VITA', 'AMORE', 'TUTTO', 'PROVA'
        ],
        'en': [
            'HI', 'ME', 'YOU', 'WE', 'BY', 'TO', 'HEY', 'FROM', 'HELLO',
            'LOVE', 'TEST', 'HOME', 'LIFE', 'WORLD', 'FRIEND'
        ]
    }
    
    selected_keys = common_keys[lang]
    results = []
    
    # Prova tutte le chiavi comuni per la lingua specifica
    for key in selected_keys:
        decrypted = vigenere_decrypt(text, key)
        score = calculate_language_specific_score(decrypted, lang)
        
        if score > 30:  # Soglia minima per risultati significativi
            results.append({
                'key': key,
                'decoded': decrypted,
                'score': score
            })
    
    # Se non trova risultati, prova chiavi brevi
    if not results:
        for length in range(2, 5):
            for chars in itertools.product(string.ascii_uppercase, repeat=length):
                key = ''.join(chars)
                decrypted = vigenere_decrypt(text, key)
                score = calculate_language_specific_score(decrypted, lang)
                
                if score > 30:
                    results.append({
                        'key': key,
                        'decoded': decrypted,
                        'score': score
                    })
                
                if len(results) >= 5:
                    break
    
    return sorted(results, key=lambda x: x['score'], reverse=True)[:5]

def frequency_analysis(text, lang):
    """
    Enhanced frequency analysis with language-specific handling
    """
    text = ''.join(char.lower() for char in text if char.isalpha())
    if not text:
        return None
    
    total_chars = len(text)
    freq = Counter(text)
    frequencies = {char: count/total_chars * 100 for char, count in freq.items()}
    
    ref_freq = get_reference_frequencies(lang)
    
    # Migliore sistema di sostituzione basato sulla lingua
    substitutions = {}
    freq_sorted = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    ref_sorted = sorted(ref_freq.items(), key=lambda x: x[1], reverse=True)
    
    for (obs_char, _), (exp_char, _) in zip(freq_sorted, ref_sorted):
        substitutions[obs_char] = exp_char
    
    return {
        'calculated_frequencies': dict(sorted(frequencies.items(), key=lambda x: x[1], reverse=True)),
        'possible_substitutions': substitutions,
        'detected_language': {'en': 'English', 'it': 'Italian'}[lang]
    }

def try_base64_decode(text):
    """
    Enhanced Base64 decoding with better error handling
    """
    try:
        # Rimuove spazi e padding se necessario
        text = text.strip().replace(' ', '')
        missing_padding = len(text) % 4
        if missing_padding:
            text += '=' * (4 - missing_padding)
        
        decoded = base64.b64decode(text).decode('utf-8')
        return {'success': True, 'result': decoded}
    except:
        return {'success': False, 'result': "Non è un testo codificato in Base64 valido."}

def analyze_text_block(text, lang):
    """
    Analyze a single block of text with specified language
    """
    return {
        "language": lang,
        "caesar_attempts": try_all_caesar(text, lang),
        "vigenere_attempts": try_vigenere_decrypt(text, lang),
        "frequency_analysis": frequency_analysis(text, lang),
        "base64_attempt": try_base64_decode(text)
    }

def analyze_mixed_text(encrypted_text):
    """
    Main analysis function for mixed language text with line-by-line processing
    """
    # Dividi il testo in righe
    lines = [line.strip() for line in encrypted_text.split('\n') if line.strip()]
    results = []
    
    for line in lines:
        # Rileva la lingua per questa riga
        blocks = detect_language_blocks(line)
        line_results = []
        
        for lang, block in blocks:
            block_results = analyze_text_block(block, lang)
            line_results.append(block_results)
        
        results.extend(line_results)
    
    return results

def print_results(results):
    """
    Print results with improved line-by-line formatting
    """
    for i, block_results in enumerate(results, 1):
        print(f"\n=== RIGA {i} ===")
        print(f"Lingua rilevata: {block_results['frequency_analysis']['detected_language']}")
        
        print("\n--- CIFRARIO DI CESARE ---")
        for score, key, text in block_results["caesar_attempts"][1]:
            print(f"Chiave {key} (punteggio: {score:.2f}): {text}")
        
        print("\n--- CIFRARIO DI VIGENÈRE ---")
        for attempt in block_results["vigenere_attempts"]:
            if attempt['score'] > 30:  # Mostra solo risultati significativi
                print(f"Chiave: {attempt['key']}")
                print(f"Decrittato: {attempt['decoded']}")
                print(f"Punteggio: {attempt['score']:.2f}\n")


def print_welcome():
    """
    Print welcome message and instructions
    """
    print("\n" + "="*60)
    print("Decrittatore Universale con Supporto Multilingua IT/EN")
    print("="*60)
    print("\nQuesto programma supporta:")
    print("- Testo in italiano")
    print("- Testo in inglese")
    print("- Testo misto italiano/inglese")
    print("- Cifrari: Cesare, Vigenère, Base64")
    print("\nInserisci il testo da decifrare e il programma tenterà")
    print("automaticamente di rilevare la lingua e il tipo di cifratura.")
    print("="*60 + "\n")

def main():
    print_welcome()
    
    while True:
        print("\nOpzioni disponibili:")
        print("1. Decrittazione nuovo testo")
        print("2. Aiuto e istruzioni")
        print("q. Uscita")
        
        choice = input("\nScelta: ").strip()
        
        if choice == 'q':
            print("\nGrazie per aver utilizzato il decrittatore universale!")
            break
            
        elif choice == '2':
            print("\n=== AIUTO E ISTRUZIONI ===")
            print("- Puoi inserire più righe di testo")
            print("- Ogni riga verrà analizzata separatamente")
            print("- Il programma rileverà automaticamente la lingua per ogni riga")
            print("- Supporta testo misto italiano/inglese")
            input("\nPremi Enter per continuare...")
            continue
            
        elif choice == '1':
            print("\nInserisci il testo da decifrare (una o più righe).")
            print("Per terminare l'input, premi Enter due volte.\n")
            
            lines = []
            while True:
                line = input().strip()
                if not line and lines:  # Doppio Enter per terminare
                    break
                if line:
                    lines.append(line)
            
            if not lines:
                print("Errore: inserire almeno una riga di testo")
                continue
            
            encrypted_text = '\n'.join(lines)
            print("\nAnalisi in corso...")
            results = analyze_mixed_text(encrypted_text)
            print_results(results)
        
        else:
            if len(choice) > 1:  # Se è stato incollato del testo
                results = analyze_mixed_text(choice)
                print_results(results)
            else:
                print("\nScelta non valida. Inserire '1', '2' o 'q'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgramma terminato dall'utente.")
    except Exception as e:
        print(f"\nErrore imprevisto: {str(e)}")