# pip install -U spacy #to get spacy
# pip install lemminflect #to get lemmainflect -> eng only (even pyinflect recommends using lemminflect instead)
# python -m spacy download en_core_web_md ##md size is minimum that has vectors for words
# python -m spacy download pl_core_news_md

import time
from datetime import timedelta
import string
import random
from collections.abc import Iterable

import spacy
from lemminflect import getLemma, getAllLemmas, getInflection, getAllInflections, getAllInflectionsOOV, getAllLemmasOOV #some of these don't work :<

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
    punctuation_without_apostrophe = '.,?!:;()[]{}@#$%^&*<>~-_=+|/"'
    sentence = sentence.lower().translate(str.maketrans('', '', punctuation_without_apostrophe))
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


# #Currently unused and unneeded, but was in the past so... just in case
# def get_goal_pos_tag(word, sentence):
#     '''Process sentence with spaCy and get the index of the target word in the sentence, store goal_pos_tag'''
#     doc = language.nlp(sentence)
#     for token in doc:
#         if token.text == word.text:
#             word.goal_pos_tag = token.tag_
#             return

def set_word_position_and_goal_pos_tag(word, sentence) -> int:
    '''Process sentence with spaCy and get the index of the target word in the sentence, store goal_pos_tag'''
    doc = language.nlp(sentence)

    for token in doc:
        #if the token is the target word and not a proper noun
        if token.text == word.text and token.pos_ != "PROPN":
            #store the goal pos tag and index for the target word
            word.goal_pos_tag = token.tag_
            word.index = token.i
            print(f"{word.text} with pos: {word.goal_pos_tag} found at index: {word.index}")
            return token.i
    return -1


def generate_sentence_with_inflection(word):
    '''Generate a sentence with the target word inflected in it
    Make sure the sentence contains a registered inflection of the target word, if not, repeat the process
    '''

    #Generate a sentence with the target word with LLM
    generated_sentence = language.generate_sentence(word.text)
    print(f"Generated sentence with {word.text}: {generated_sentence}")

    #Make sure the sentence contains a registered inflection of the target word
    if not find_inflection_in_sentence(word, generated_sentence):
        print("No appropriate inflection found in sentence, regenerating")
        generate_sentence_with_inflection(word) #call self until an inflection is found

    #Make sure the word in the sentence is not a proper noun, assign its index and goal pos tag to WordInfo object
    elif set_word_position_and_goal_pos_tag(word, generated_sentence) == -1:
        print("Target word not found in sentence, regenerating")
        generate_sentence_with_inflection(word)

    else:
        #Hurray! We have a complete sentence with the target word inflected appropriately in it! :D
        #Add the sentence to the WordInfo object for safe-keeping!
        word.sentence = generated_sentence
        print("Appropriate inflection found in sentence!")
        print(f"Target word-sentence pair: {word.text} -> {word.sentence}")



######################################################################################
# Initialize language
language = lang.LanguageInfo()

#desired_language = input("Enter the language you would like to use: (English or Polish)\n")
desired_language = "English" #Polish implementation is not yet complete

#Load appropriate space model and database filename
language.set_language_name_and_file(desired_language)

#main! to repeat and stuff!
def main():
    #start timer
    start_time = time.monotonic()

    # Get target word -- does not need to be a lemma
    # We're gonna need the completely unchanged word later, so don't forget
    original_word = input("Enter a noun, adjective, verb, or adverb:\n")

    #check for invalid input
    while not original_word or not original_word.isalpha() or len(original_word) < 2:
        print("Invalid input. Please enter a word.")
        original_word = input("Enter the target word:\n")

    original_word = original_word.lower()
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
            print("Target word not found in database, please pick another word." + "\n" + "-" * 13)
            main()

        if result[1]: #lemma is the 2nd column
            target_word.lemma = result[1]
        else:
            print("Word is already the lemma")
            target_word.lemma = target_word.text

        if result[2]: #ppos is the 3rd column
            target_word.ppos = result[2]
        else:
            print("Word has no relevant POS tag in lemminflect, please pick another word." + "\n" + "-" * 13)
            main()

        if not result[4]: #hasVector is the 5th column
            print("Word has no vector in spaCy, please pick another word." + "\n" + "-" * 13)
            main()

        # Create and store all inflections of the target word's main lemma
        create_inflection_set(target_word)
        print(f"Inflections of the target word '{target_word.text}': {target_word.inflections}")

        # Generate sentence from target word, run all checks in the process
        generate_sentence_with_inflection(target_word)


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

        # From the top 21, check in descending order for the first 3 that have the same inflection as the target word
        # If this ever goes past 21, this will break and crash, but honestly it almost never goes past the first 3
        chosen_words = []
        i = 0
        valid_word = ''
        while len(chosen_words) < 3 and not valid_word:
            if i >= len(top_words):
                print("Not enough words in the top 21 with the same inflection as the target word" + "\n" + "-" * 13)
                break #might be safer to restart the program, but this might also work, let's see

            valid_word = getInflection(top_words[i][0], tag=target_word.goal_pos_tag, inflect_oov=False)
            print(i, top_words[i][0], "valid_word>>>", valid_word)

            # if we got past the fail-safes, we can add the word to the chosen words, and reset valid_word
            if valid_word:
                chosen_words.append((valid_word[0], top_words[i]))
                valid_word = ''
            # iterate
            i += 1

        print("Chosen words:", chosen_words)

        # # Can use this instead of choosing words at all if you don't care about mirroring inflection with target word
        # word1 = lang.WordInfo(top_words[0][0], lemma=top_words[0][0], ppos=top_words[0][1])
        # word2 = lang.WordInfo(top_words[1][0], lemma=top_words[1][0], ppos=top_words[1][1])
        # word3 = lang.WordInfo(top_words[2][0], lemma=top_words[2][0], ppos=top_words[2][1])


        if len(chosen_words) < 3:
            # Failsafe if chosen words do not match inflection
            #   like with "carving" where lemminflect doesn't believe it can be a verb,
            #   but spaCy does, so they fight and no one wins
            print("Not enough chosen words, reverting to default top 3 words")

            #First remove chosen words from top_words list:
            for c in chosen_words:
                top_words.remove(c)
            #Then re-add any chosen words to the front, just in case there were valid options
            for c in chosen_words:
                top_words.insert(0, c)

            # Create new word objects for the top 3 words, intializing them with their text and ppos
            word1 = lang.WordInfo(top_words[0][0], lemma=top_words[0][0], ppos=top_words[0][1])
            word2 = lang.WordInfo(top_words[1][0], lemma=top_words[1][0], ppos=top_words[1][1])
            word3 = lang.WordInfo(top_words[2][0], lemma=top_words[2][0], ppos=top_words[2][1])
        else:
            #Create new word objects for the chosen words, intializing them with their text and ppos
            word1 = lang.WordInfo(chosen_words[0][0], lemma=chosen_words[0][1][0], ppos=chosen_words[0][1][1])
            word2 = lang.WordInfo(chosen_words[1][0], lemma=chosen_words[1][1][0], ppos=chosen_words[1][1][1])
            word3 = lang.WordInfo(chosen_words[2][0], lemma=chosen_words[2][1][0], ppos=chosen_words[2][1][1])




        top3_wordlist = [word1, word2, word3]

        #Get and set all inflections of our words
        for w in top3_wordlist:
            create_inflection_set(w)
            print(f"Inflections of {w.lemma}: {w.inflections}")


        #Generate sentences for the 3 random words, one at a time
        for w in top3_wordlist:
            generate_sentence_with_inflection(w)
            print(f"Word-sentence pair: {w.text} -> {w.sentence}")

        ########################################
        # Now we have 4 word-sentence pairs
        # Time to make the replacements
        ########################################

        for w in top3_wordlist:
            #replace the word with the inflected target word
            replacement = getInflection(target_word.lemma, tag = w.goal_pos_tag)[0]

            #capitalize the first letter if the word is the first word in the sentence
            #else it won't be found nor replaced
            if w.word_index == 0:
                replacement = replacement.capitalize()

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

        #end timer
        end_time = time.monotonic()
        print('Runtime: ' + str(timedelta(seconds=end_time - start_time)))

        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')




#####################################################################
# Main loop
#####################################################################


main()

play_again = input("Would you like to generate another vocab quiz question? (y/n)\n")
while play_again.lower() == "y":
    main()
    play_again = input("Would you like to generate another vocab quiz question? (y/n)\n")
else:
    print("Goodbye!")
    exit()


###########Current known issues############
# we need to actually get ALL lemmas and all inflections of all lemmas, this requires editing both the database
# and create_inflection_set

# Small note: currently can't do anything about a/an mismatches, but checking for that would be HUGE PAIN
# Could consider adding vowel checking? Honestly, I don't think it's worth it, but it's a thought
