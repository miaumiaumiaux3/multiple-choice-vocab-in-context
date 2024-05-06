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

def create_inflection_list(lemma):
    '''Get all inflections with lemminflect and return them as a flattened list'''
    word_inflections = getAllInflections(lemma, upos=None)
    return set(flatten(list(word_inflections.values())))



######################################################################################
# Initialize language
language = lang.LanguageInfo()

#desired_language = input("Enter the language you would like to use: (English or Polish)\n")
desired_language = "English" #Polish implementation is not yet complete

#Load appropriate space model and database filename
language.set_language_name_and_file(desired_language)


# Get target word, any word in any form
#target_word = input("Enter the target word:\n")
target_word = lang.WordInfo("sound")

######################################################################################
###Get word info from db: check if exists and get into at the same time
try:

    # Connect to DB and create a cursor
    sqliteConnection = sqlite3.connect(f'{language.filename}.db')
    cursor = sqliteConnection.cursor()
    print('DB Init')

    # Check if the target word is in the database and get its info
    result = get_word_info(target_word, language, cursor)
    print(f"Target word info: {result}")

    if not result:
        print("Target word not found in database")
        cursor.close()
        exit()

    if result[1]:
        target_lemma = result[1]

    if result[2]:
        target_ppos = result[2]
    else:
        print("Word has no relevant POS tag")

    # Get all inflections of the target word's main lemma
    word_inflection_list = create_inflection_list(target_lemma)

    # Generate sentence from target word
    generated_sentence = language.generate_sentence(target_word)

    ## Make sure the sentence contains a registered inflection of the target word, if not, generate a new sentence
    words_in_gen_sentence = clean_sentence(generated_sentence)

    # Close the cursor
    cursor.close()

# Handle errors
except sqlite3.Error as error:
    print('Error occurred - ', error)

# Close DB Connection irrespective of success or failure
finally:

    if sqliteConnection:
        sqliteConnection.close()
        print('SQLite Connection closed')
######################################################################################



#check if any of the inflections are in the generated sentence
inflected_word = None
inflection_in_sentence = False
for inf in word_inflection_list:
    if inf in words_in_gen_sentence:
        inflection_in_sentence = True
        inflected_word = inf
        break

print(inflected_word, inflection_in_sentence)

if inflection_in_sentence:
    #process generated_sentence with spaCy
    doc = language.nlp(generated_sentence)

    # Get the index of the target word in the sentence
    word_index = None
    for token in doc:
        if token.text == inflected_word:
            word_index = token.i
            break

    # Get the POS tag of the target word
    word_pos = doc[word_index].pos_
    word_tag = doc[word_index].tag_
    print(target_word, inflected_word, word_index, word_pos, word_tag)
else:
    print("No inflection of the target word found in the generated sentence. Generate a new sentence.")

# Search for words in the dictionary with the same possible POS tag(s) that are very dissimilar to the target word

###Can we do it randomly? Or do we need to copy the entire massive dictionary and add data to each entry?###
#Let's make a database? :3 We can make a script that turns our dictionary into a database, and then we can query it


