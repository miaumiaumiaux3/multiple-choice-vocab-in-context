import generate_sentence_pl as gen_pl
import generate_sentence_en as gen_en

import spacy


class WordInfo:
    def __init__(self, word, ppos = ""):
        self.text = word
        self.lemma = ""
        self.ppos = ppos
        self.inflections = set()
        self.sentence = ""
        self.goal_pos_tag = ""

class LanguageInfo:
    def __init__(self):
        self.name = ""
        self.filename = ""
        self.nlp = None
        self.model = None
        self.model_already_initialized = False

    def set_language_name_and_file(self, desired_language):
        if desired_language.lower() in ["english", "eng", "en"]:
            self.name = "English"
            self.filename = 'sowpods'
            self.nlp = spacy.load("en_core_web_md")

        elif desired_language.lower() in ["polish", "pol", "pl"]:
            self.name = "Polish"
            self.filename = 'slowa'
            self.nlp = spacy.load("pl_core_news_md")

        else:
            print('Language not supported')
            exit()

    def generate_sentence(self, target_word) -> str:
        if self.name == "English":
            if not self.model_already_initialized:
                self.model = gen_en.load_model()
                self.model_already_initialized = True
            generated_sentence = gen_en.generate_sample_sentence(self.model, target_word)

        elif self.name == "Polish":
            if not self.model_already_initialized:
                self.model = gen_pl.load_model()
                self.model_already_initialized = True
            generated_sentence = gen_pl.generate_sample_sentence(self.model, target_word)

        else:
            print('Language not supported')
            exit()
        return generated_sentence
