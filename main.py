# pip install -U spacy #to get spacy
# pip install lemminflect #to get lemmainflect -> eng only (even pyinflect recommends using lemminflect instead)
# python -m spacy download en_core_web_md ##md size is minimum that has vectors for words
# python -m spacy download pl_core_news_md

import string
import random
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

# #Old version which returned the value instead of setting it in the object, no longer needed
# def create_inflection_set(lemma) -> set:
#     '''Get all inflections with lemminflect and return them as a flattened list'''
#     word_inflections = getAllInflections(lemma, upos=None)
#     print(word_inflections)
#     return set(flatten(list(word_inflections.values())))

def create_inflection_set(word):
    '''Get all inflections with lemminflect and return them as a flattened list'''
    word_inflections = getAllInflections(word.lemma, upos=None)
    print(word_inflections)
    inflection_set = set(flatten(list(word_inflections.values())))
    word.inflections = inflection_set

def find_inflection_in_sentence(word, sentence) -> bool:
    '''Clean the sentence and check if any of the inflections are in current generated sentence
        If so, return True, otherwise return None'''
    if not sentence:
        return False

    words_in_gen_sentence = clean_sentence(sentence)

    for w in words_in_gen_sentence:
        if w in word.inflections:
            word.text = w #set the word's text to the inflected form found in the sentence
            return True
    else:
        return False


def get_goal_pos_tag(word, sentence):
    '''Process sentence with spaCy and get the index of the target word in the sentence, store goal_pos_tag'''
    doc = language.nlp(sentence)
    for token in doc:
        if token.text == word.text:
            word.goal_pos_tag = token.tag_
            return


# #Currently unused and unneeded, but was in the past so... just in case
# def get_word_position(word, sentence) -> int:
#     '''Process sentence with spaCy and get the index of the target word in the sentence, store goal_pos_tag'''
#     doc = language.nlp(sentence)
#
#     for token in doc:
#         if token.text == word.text:
#             word.goal_pos_tag = token.tag_
#             #word.index = token.i
#             return token.i
#     return -1


######################################################################################
# Initialize language
language = lang.LanguageInfo()

#desired_language = input("Enter the language you would like to use: (English or Polish)\n")
desired_language = "English" #Polish implementation is not yet complete

#Load appropriate space model and database filename
language.set_language_name_and_file(desired_language)

#main! to repeat and stuff!
def main():
    # Get target word -- does not need to be a lemma
    # We're gonna need the completely unchanged word later, so don't forget
    original_word = input("Enter a noun, adjective, verb, or adverb:\n")

    #check for invalid input
    while not original_word or not original_word.isalpha() or len(original_word) < 2:
        print("Invalid input. Please enter a word.")
        original_word = input("Enter the target word:\n")

    #original_word = "sounds"
    target_word = lang.WordInfo(original_word)

    try:
        ######################################################################################
        ### Get word info from db: check if exists and get info at the same time
        ###############################################################################

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

        # Create and store all inflections of the target word's main lemma
        create_inflection_set(target_word)
        print(f"Inflections of the target word '{target_word.text}': {target_word.inflections}")

        # Generate sentence from target word
        generated_sentence = language.generate_sentence(target_word.text)
        print(f"Generated sentence: {generated_sentence}")

        ## Make sure the sentence contains a registered inflection of the target word, if not, generate a new sentence
        while not find_inflection_in_sentence(target_word, generated_sentence):
            print("No inflection of the target word found in the generated sentence. Generate a new sentence.")
            generated_sentence = language.generate_sentence(target_word.text)
            print(f"Re-generated sentence: {generated_sentence}")

        #Hurray! We have a complete sentence with the target word inflected in it! :D
        #Add it to the WordInfo object for safe-keeping!
        target_word.sentence = generated_sentence

        #store the goal pos tag for the target word
        # *********Might use this to inflect randomly chosen words later or to change how words are chosen*************
        get_goal_pos_tag(target_word, generated_sentence)


        ################################################################################
        # Now that we've confirmed we have a legit sentence, we need 3 more from other random words
        ###############################################################################
        # Get 3 random words from the database that share at least one ppos tag with the target_word


        # #Medium inclusive, include exact matches, and for each letter, include the "pure" matching words
        # pos_queries = ''
        # for char in target_word.ppos:
        #     pos_queries += f" OR ppos = '{char}' "
        #

        # Almost exclusive:
        # Include only exact ppos matches and "pure" base form of the target_word.goal_pos_tag
        pos_base = target_word.goal_pos_tag[0]
        pos_queries = f" OR ppos = '{pos_base}'" if pos_base != target_word.ppos else ''

        #We'll grab 42 because it's just as fast to get 1 random word (or 100, or more, if we want higher avg similarity)
        query = f'''SELECT word, ppos FROM {language.name}Dictionary 
                WHERE isOOV = 0 AND lemma is NULL AND hasVector = 1
                AND (ppos = '{target_word.ppos}'{pos_queries}) AND word != '{target_word.lemma}'
                ORDER BY RANDOM() LIMIT 42;
                '''

        print(query)
        cursor.execute(query)
        result = cursor.fetchall() #list of tuples (word, ppos)

        #####################################
        #Close the poor SQLite connection, we don't need it anymore
        cursor.close()
        #####################################


        #Choose 3 random words from the SELECTed words with the highest similarity that's still under 0.5
        #This should result in a slightly more balanced set of words that are still definitely and distinctly different from the target word

        #first order by similarity, deleting any that are over 0.5, then grab the top 3
        # only compare lemmas to lemmas!
        dict_words = {}
        for r in result:
            print(r[0], r[1], target_word.lemma, language.nlp(r[0]).similarity(language.nlp(target_word.lemma)))
            simp = language.nlp(r[0]).similarity(language.nlp(target_word.lemma))
            if simp < 0.5:
                dict_words[r] = simp

        top_words = sorted(dict_words, key=dict_words.get, reverse=True)[:21] #top half of similarities
        print(top_words)

        ##****************Testing****************##
        chosen_words = []
        i = 0
        while len(chosen_words) < 3:
            word = getInflection(top_words[i][0], tag=target_word.goal_pos_tag, inflect_oov=False)
            while not word:
                i += 1
                word = getInflection(top_words[i][0], tag=target_word.goal_pos_tag, inflect_oov=False)
                print(i, top_words[i][0], "word>>>", word)
            chosen_words.append((word[0],top_words[i]))
            i += 1

        print(chosen_words)

        word1 = lang.WordInfo(chosen_words[0][0], lemma=chosen_words[0][1][0], ppos=chosen_words[0][1][1])
        word2 = lang.WordInfo(chosen_words[1][0], lemma=chosen_words[1][1][0], ppos=chosen_words[1][1][1])
        word3 = lang.WordInfo(chosen_words[2][0], lemma=chosen_words[2][1][0], ppos=chosen_words[2][1][1])

        #Create new word objects for the top 3 words, intializing them with their text and ppos
        #word1 = lang.WordInfo(top3[0][0], top3[0][1])
        #word2 = lang.WordInfo(top3[1][0], ppos = top3[1][1])
        #word3 = lang.WordInfo(top3[2][0], ppos = top3[2][1])

        top3_wordlist = [word1, word2, word3]

        #Get and set all inflections of our words
        for w in top3_wordlist:
            create_inflection_set(w)
            print(f"Inflections of {w.lemma}: {w.inflections}")


        #Generate sentences for the 3 random words, one at a time
        for w in top3_wordlist:
            generated_sentence = ""
            ## Make sure the sentence contains a registered inflection of the target word, if not, generate a new sentence
            while not find_inflection_in_sentence(w, generated_sentence):
                print(f"No inflection of {w.text} found in the generated sentence. Generating a new sentence.")
                generated_sentence = language.generate_sentence(w.text)
                print(f"Re-generated sentence: {generated_sentence}")

            # # Get index of inflected word in sentence
            # word_index = get_word_position(w, generated_sentence)
            get_goal_pos_tag(w, generated_sentence)
            # Save the sentence in the WordInfo object
            w.sentence = generated_sentence
            print(f"Word-sentence pair: {w.text} -> {w.sentence}")

        ########################################
        # Now we have 4 word-sentence pairs
        # Time to make the replacements
        ########################################

        for w in top3_wordlist:
            #replace the word with the inflected target word
            replacement = getInflection(target_word.lemma, tag = w.goal_pos_tag)[0]
            w.sentence = w.sentence.replace(w.text, replacement)
            print(f"Replacement: {w.text}({w.goal_pos_tag}) -> {replacement}")
            print(f"New sentence: {w.sentence}")

        #Create the final wordlist and shuffle it
        final_wordlist = [target_word]
        final_wordlist.extend(top3_wordlist)
        random.shuffle(final_wordlist)

        #print the final sentences
        print("\n--------------------------------------------")
        print(f"In which sentence is a form of the word {original_word} most correctly used?")
        for w in final_wordlist:
            print(" - " + w.sentence)
        print("---------------------------------------------\n")

        #print the target word's sentence
        print(f"Correct: {target_word.text}({target_word.ppos}:{target_word.goal_pos_tag}) -> {target_word.sentence}")
        print(f"Incorrect: {word1.text}({word1.ppos}:{word1.goal_pos_tag}) -> {word1.sentence}")
        print(f"Incorrect: {word2.text}({word2.ppos}:{word2.goal_pos_tag}) -> {word2.sentence}")
        print(f"Incorrect: {word3.text}({word3.ppos}:{word3.goal_pos_tag}) -> {word3.sentence}")


    # Handle errors
    except sqlite3.Error as error:
        print('Error occurred - ', error)

    # Close DB Connection irrespective of success or failure
    finally:

        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')


#####################################################################
# Main loop
#####################################################################


main()

play_again = input("Would you like to play again? (y/n)\n")
while play_again.lower() == "y":
    main()
    play_again = input("Would you like to play again? (y/n)\n")
else:
    print("Goodbye!")
    exit()

