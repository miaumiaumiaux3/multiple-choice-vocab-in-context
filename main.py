# pip install -U spacy #to get spacy
# pip install lemminflect #to get lemmainflect -> eng only (even pyinflect recommends using lemminflect instead)
# python -m spacy download en_core_web_md ##md size is minimum that has vectors for words
# python -m spacy download pl_core_news_md

import string
import spacy
from lemminflect import getLemma, getAllLemmas, getInflection, getAllInflections, getAllInflectionsOOV, getAllLemmasOOV #some of these don't work :<
from collections.abc import Iterable

import sqlite3

import language_helper as lang

def flatten(xs):
    '''Flattens a list of lists'''
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

def clean_sentence(sentence):
    '''Make lowercase, remove punctuation and split into words'''
    sentence = sentence.lower().translate(str.maketrans('', '', string.punctuation))
    word_list = sentence.split()
    return word_list


def get_word_info(word, language, cursor):
    '''Get target word's info from the database'''
    query = f'''SELECT * FROM {language}Dictionary WHERE word = '{word}';'''
    cursor.execute(query)
    result = cursor.fetchone() #if no result, returns None, otherwise tuple of the full row

    return result

def create_inflection_set(lemma) -> set:
    '''Get all inflections with lemminflect and return them as a flattened list'''
    word_inflections = getAllInflections(lemma, upos=None)
    print(word_inflections)
    return set(flatten(list(word_inflections.values())))


def find_inflection_in_sentence(word, sentence) -> bool:
    '''Clean the sentence and check if any of the inflections are in current generated sentence
        If so, return True, otherwise return None'''
    words_in_gen_sentence = clean_sentence(sentence)

    for w in words_in_gen_sentence:
        if w in word.inflections:
            word.text = w #set the word's text to the inflected form found in the sentence
            return True
    else:
        return False


def get_word_position(word, sentence) -> int:
    '''Process sentence with spaCy and get the index of the target word in the sentence, store goal_pos_tag'''
    doc = language.nlp(sentence)

    for token in doc:
        if token.text == word.text:
            word.goal_pos_tag = token.tag_
            return token.i
    return -1



######################################################################################
# Initialize language
language = lang.LanguageInfo()

#desired_language = input("Enter the language you would like to use: (English or Polish)\n")
desired_language = "English" #Polish implementation is not yet complete

#Load appropriate space model and database filename
language.set_language_name_and_file(desired_language)

# Get target word, any word in any form
#original_word = input("Enter the target word:\n")
#check for blank input, if blank, ask again
#target_word = lang.WordInfo(original_word)

target_word = lang.WordInfo("sound")

######################################################################################
### Get word info from db: check if exists and get info at the same time
###############################################################################
try:

    # Connect to DB and create a cursor
    sqliteConnection = sqlite3.connect(f'{language.filename}.db')
    cursor = sqliteConnection.cursor()
    print('DB Init')

    # Check if the target word is in the database and get its info
    result = get_word_info(target_word.text, language.name, cursor)
    print(f"Target word info: {result}")

    if not result:
        print("Target word not found in database")
        cursor.close()
        exit()

    if result[1]: #lemma is the 2nd column
        target_word.lemma = result[1]
    else:
        print("Word is already the lemma")
        target_word.lemma = target_word.text

    if result[2]: #ppos is the 3rd column
        target_word.ppos = result[2]
    else:
        print("Word has no relevant POS tag")
        cursor.close()
        exit()

    if not result[4]: #hasVector is the 5th column
        print("Word has no vector")
        cursor.close()
        exit()

    # Get all inflections of the target word's main lemma
    target_word.inflections = create_inflection_set(target_word.lemma)
    print(f"Inflections of the target word: {target_word.inflections}")

    # Generate sentence from target word
    generated_sentence = language.generate_sentence(target_word.text)
    print(f"Generated sentence: {generated_sentence}")

    ## Make sure the sentence contains a registered inflection of the target word, if not, generate a new sentence
    while not find_inflection_in_sentence(target_word, generated_sentence):
        print("No inflection of the target word found in the generated sentence. Generate a new sentence.")
        generated_sentence = language.generate_sentence(target_word.text)
        print(f"Re-generated sentence: {generated_sentence}")

    #Hurray! We have a complete sentence with the target word inflected in it! :D
    #Let's start grouping our words and sentences
    word_sentence_pairs = [(target_word, generated_sentence)]
    print(f"Word-sentence pairs: {word_sentence_pairs}")


    ################################################################################
    # Now that we've confirmed we have a legit sentence, we need 3 more from other random words
    ###############################################################################

    # Get 3 random words from the database that share at least one ppos tag with the target_word
    #Medium inclusive, include exact matches, and for each letter, include the "pure" matching words
    pos_queries = ''
    for char in target_word.ppos:
        pos_queries += f" OR ppos = '{char}' "


    #We'll grab 12 because it's just as fast to get 1 random word as it is to get 24 (or 100, or more, if we want higher avg similarity)
    query = f'''SELECT word, ppos FROM {language.name}Dictionary 
            WHERE isOOV = 0 AND lemma is NULL AND hasVector = 1
            AND (ppos = '{target_word.ppos}'{pos_queries}) AND word != '{target_word.text}'
            ORDER BY RANDOM() LIMIT 24;
            '''

    print(query)
    cursor.execute(query)
    result = cursor.fetchall() #list of tuples (word, ppos)
    print(result)

    #####################################
    #Close the poor SQLite connection, we don't need it anymore
    cursor.close()
    #####################################


    #Choose 3 random words from the SELECTed words with the highest similarity that's still under 0.5
    #This should result in a slightly more balanced set of words that are still definitely and distinctly different from the target word

    #first order by similarity, deleting any that are over 0.5, then grab the top 3\

    dict_words = {}
    for r in result:
        print(r[0], target_word.text, language.nlp(r[0]).similarity(language.nlp(target_word.text)))
        simp = language.nlp(r[0]).similarity(language.nlp(target_word.text))
        if simp < 0.5:
            dict_words[r] = simp

    top_3 = sorted(dict_words, key=dict_words.get, reverse=True)[:3]
    print(top_3)

    word1 = lang.WordInfo(top_3[0][0], top_3[0][1])
    word2 = lang.WordInfo(top_3[1][0], top_3[1][1])
    word3 = lang.WordInfo(top_3[2][0], top_3[2][1])

    potential_words = [word1, word2, word3]


    for j in range(0, len(potential_words) -1):
        #Generate sentences for the 3 random words, one at a time
        generated_sentence = language.generate_sentence(potential_words[j].text)
        ## Make sure the sentence contains a registered inflection of the target word, if not, generate a new sentence
        while not find_inflection_in_sentence(potential_words[j], generated_sentence):
            print(f"No inflection of {potential_words[j].text} found in the generated sentence. Generating a new sentence.")
            generated_sentence = language.generate_sentence(potential_words[j].text)
            print(f"Re-generated sentence: {generated_sentence}")

        # #Get index of inflected word in sentence
        word_index = get_word_position(potential_words[j], generated_sentence)
        word_sentence_pairs.append((potential_words[j], generated_sentence, word_index))
        print(f"Word-sentence pairs: {word_sentence_pairs}")

    ########################################
    # Now we have 4 word-sentence pairs
    # Time to make the replacements
    ########################################

    # CURRENT ISSUE --
    #Re-generated sentence:  Once you press the self-destruct button, the data on this hard drive will be wiped irreversibly, leaving no trace of the information it once contained.
    #No inflection of irreversibly found in the generated sentence. Generating a new sentence.
    #not finding inflection



# Handle errors
except sqlite3.Error as error:
    print('Error occurred - ', error)

# Close DB Connection irrespective of success or failure
finally:

    if sqliteConnection:
        sqliteConnection.close()
        print('SQLite Connection closed')
######################################################################################








