import streamlit as st
import requests
from word2word import Word2word
from Levenshtein import ratio
from unidecode import unidecode
from deep_translator import GoogleTranslator 

st.title("Learn from Your Native Language")
st.markdown("""
The algorithm behind this tool is designed to make language learning more intuitive by starting with familiar vocabulary. It begins by retrieving the most common words in the target language, then translates each word into the user’s native language using a bilingual dictionary. To identify which words are most familiar, it calculates a similarity score for each word pair based on Levenshtein distance. The words are then sorted from most to least similar, ensuring that learners are first introduced to vocabulary that closely resembles their native language. This approach builds early confidence and makes the learning process feel more natural and accessible.
""")

st.sidebar.header("Let's Start Learning ✏️")

language_options = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Italian": "it",
    "Spanish": "es",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Swedish": "sv",
    "Danish": "da",
    "Norwegian": "no",
    "Finnish": "fi",
    "Turkish": "tr",
    "Arabic": "ar",
    "Farsi (Persian)": "fa",
    "Hindi": "hi",
    "Russian": "ru",
    "Polish": "pl",
    "Greek": "el",
    "Czech": "cs",
    "Hungarian": "hu",
    "Romanian": "ro"
}

lang_to_learn_label = st.sidebar.selectbox("Language you want to learn", list(language_options.keys()), index=3)
native_lang_label = st.sidebar.selectbox("Your native language", list(language_options.keys()), index=1)

lang_to_learn = language_options[lang_to_learn_label]
native_lang = language_options[native_lang_label]

word_count = st.sidebar.slider("How many words to learn?", min_value=5, max_value=100, value=10)
fallback_lang = "en"

@st.cache_data(show_spinner=False)
def fetch_top_words(language, fallback, buffer_count=None):
    base_url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2016"
    
    def get_words(lang):
        url = f"{base_url}/{lang}/{lang}_50k.txt"
        response = requests.get(url)
        return [line.split()[0] for line in response.text.splitlines()[:buffer_count]]

    words = get_words(language)
    if words:
        return words
    return get_words(fallback) or []

@st.cache_data(show_spinner=False)
def get_translations(top_words, lang_to_learn, native_lang):
    learn2native = Word2word(lang_to_learn, native_lang)
    translations = {}
    for word in top_words:
        try:
            translations[word] = learn2native(word)[0]
        except Exception:
            translations[word] = None
    return translations

@st.cache_data(show_spinner=False)
def get_similarity_scores(translations):
    return {
        word: ratio(unidecode(word.lower()), unidecode(translations[word]).lower())
        for word in translations if translations[word] is not None
    }

@st.cache_data(show_spinner=False)
def get_meanings(words, src_lang, dest_lang):
    meanings = {}
    for word in words:
        try:
            translated = GoogleTranslator(source=src_lang, target=dest_lang).translate(word)
            meanings[word] = translated
        except:
            meanings[word] = "[No translation]"
    return meanings

if lang_to_learn and native_lang:
    with st.spinner("Fetching data and building flashcards..."):
        fetched_words = fetch_top_words(lang_to_learn, fallback_lang, buffer_count=100)
        translations = get_translations(fetched_words, lang_to_learn, native_lang)
        valid_translations = {word: trans for word, trans in translations.items() if trans is not None}
        similarity_scores = get_similarity_scores(valid_translations)
        sorted_matches = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)
        top_matches = sorted_matches[:word_count]

        selected_words = [k for k, _ in top_matches]
        selected_meanings = get_meanings(selected_words, src_lang=lang_to_learn, dest_lang=native_lang)

        st.markdown(
            f"<h3>Flashcards <span style='color:green'>{native_lang}</span> → "
            f"<span style='color:blue'>{lang_to_learn}</span></h3>",
            unsafe_allow_html=True
        )
        for word, score in top_matches:
            st.markdown("---")
            with st.expander(f"{word}"):
                st.write(f"**Translation**: {translations[word]}")
                if score == 1.0:
                    st.markdown(f"<span style='color:green'><b>✅ Exact match to your native language!</b></span>", unsafe_allow_html=True)
                else:
                    st.write(f"**Similarity Score**: {score:.2f}")
