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


def get_word_info(word, desired_language, cursor):
    '''Get target word's info from the database'''
    query = f'''SELECT * FROM {desired_language}Dictionary WHERE word = '{word}';'''
    cursor.execute(query)
    result = cursor.fetchone() #if no result, returns None, otherwise tuple of the full row

    return result

# #Old version which returned the value instead of setting it in the object, no longer needed
# def create_inflection_set(lemma) -> set:
#     '''Get all inflections with lemminflect and return them as a flattened list'''
#     word_inflections = getAllInflections(lemma, upos=None)
#     print(word_inflections)
#     return set(flatten(list(word_inflections.values())))

# def create_inflection_set(word):
#     '''Get all inflections with lemminflect and return them as a flattened list'''
#
#     word_inflections = getAllInflections(word.lemma, upos=None)
#     print(word_inflections)
#     inflection_set = set(flatten(list(word_inflections.values())))
#     word.inflections = inflection_set

def create_inflection_set(word):
    '''Get all inflections from all lemmas with lemminflect and set them in the object'''
    all_inflections = []
    for lem in word.lemmas:
        inflections = getAllInflections(lem, upos=None) #returns dict of {pos_tag: (inflection1, inflection2, ...)}
        all_inflections.append(inflections)

    combined_inflection_list = []
    for inflections in all_inflections:
        combined_inflection_list.extend(flatten(list(inflections.values())))

    word.inflections = set(combined_inflection_list)


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
        # if token.text == word.text and token.pos_ != "PROPN": #old check, generates fewer sentences and usually works fine
        if token.text == word.text and token.pos_ != "PROPN":
            if token.tag_[0] not in list(word.ppos): #if the word in the sentence is in a form that can be inflected to the target word's pos tag
                print(f"Cannot make inflection from {token.text}<{word.lemmas[0]}({word.ppos}) to ({token.tag_})")
                return -1 #regen sentence
            #store the goal pos tag and index for the target word
            word.goal_pos_tag = token.tag_
            word.index = token.i
            print(f"{word.text} with pos: {word.goal_pos_tag} found at index: {word.index}")
            return token.i
    print("Target word not found in sentence")
    return -1


def generate_sentence_with_inflection(word):
    '''Generate a sentence with the target word inflected in it
    Make sure the sentence contains a registered inflection of the target word, if not, repeat the process
    '''

    #reset to the original_word
    word.text = word.original_word

    #Generate a sentence with the target word with LLM
    generated_sentence = language.generate_sentence(word.text)
    print(f"Generated sentence with {word.text}: {generated_sentence}")

    #Make sure the sentence contains a registered inflection of the target word
    if not find_inflection_in_sentence(word, generated_sentence):
        print("No appropriate inflection found in sentence, regenerating")
        generate_sentence_with_inflection(word) #call self until an inflection is found

    #Make sure the word in the sentence is not a proper noun, assign its index and goal pos tag to WordInfo object
    elif set_word_position_and_goal_pos_tag(word, generated_sentence) == -1:
        print("Unable to set word position and goal_pos_tag, regenerating")
        generate_sentence_with_inflection(word)

    else:
        #Hurray! We have a complete sentence with the target word inflected appropriately in it! :D
        #Add the sentence to the WordInfo object for safe-keeping!
        word.sentence = generated_sentence
        print("Appropriate inflection found in sentence!")



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
        #(word, lemma, ppos, hasVector, isLemma)
        #(str, str, str, int, int)

        if not result:
            print("Target word not found in database, please pick another word." + "\n" + "-" * 13)
            main()

        if result[1]: #lemmas are in the second column
            target_word.lemmas = result[1].split() #split string of lemmas into list

        if result[4]: #is_lemma is the 5th column
            print("Word is a lemma")

        if result[2]: #ppos is the 3rd column
            target_word.ppos = result[2]
        else:
            print("Word has no relevant POS tag in lemminflect, please pick another word." + "\n" + "-" * 13)
            main()

        if not result[3]: #hasVector is the 5th column
            print("Word has no vector in spaCy, please pick another word." + "\n" + "-" * 13)
            main()

        # Create and store all inflections of the target word's main lemma
        create_inflection_set(target_word)
        print(f"Inflections of the target word '{target_word.text}': {target_word.inflections}")

        # Generate sentence from target word, run all checks in the process
        generate_sentence_with_inflection(target_word)
        print(f"Target word-sentence pair: {target_word.text} -> {target_word.sentence}")


        ################################################################################
        # Now that we've confirmed we have a legit sentence, we need 3 more from other random words
        ###############################################################################
        # Get 3 random words from the database that share at least one ppos tag with the target_word


        # #Medium inclusive, include exact matches, and for each letter, include the "pure" matching words
        # word_logic = ''
        # for char in target_word.ppos:
        #     word_logic += f" OR ppos = '{char}' "
        #

        # Almost exclusive:
        # Include only exact ppos matches and "pure" base form of the target_word.goal_pos_tag
        word_logic = f" AND (ppos = '{target_word.ppos}'"
        pos_base = target_word.goal_pos_tag[0]
        if pos_base != target_word.ppos and pos_base in list(target_word.ppos):
            word_logic += f" OR ppos = '{pos_base}'"
        word_logic += ')'
        # And exclude the target word from the results
        for lem in target_word.lemmas:
            word_logic += f" AND word != '{lem}'"

        #We'll grab 42 because it's just as fast to get 1 random word (or 100, or more, if we want higher avg similarity)
        query = f'''SELECT word, ppos, lemmas FROM {language.name}Dictionary 
                WHERE isLemma = 1 AND hasVector = 1
                {word_logic}
                ORDER BY RANDOM() LIMIT 42;
                '''

        print(query)
        cursor.execute(query)
        result = cursor.fetchall() #list of tuples (word, ppos)
        print("Results:", result[:5])

        #####################################
        #Close the poor SQLite connection, we don't need it anymore
        cursor.close()
        #####################################


        #Choose 3 random words from the SELECTed words with the highest similarity that's still under 0.5
        #This should result in a slightly more balanced set of words that are still definitely and distinctly different from the target word

        #first order by similarity, deleting any that are over 0.5, then grab the top 3
        #only making similarity comparisons to the original word (because there could be more than one lemma)
        dict_words = {}
        for r in result:
            print(r[0], r[1], target_word.original_word, language.nlp(r[0]).similarity(language.nlp(target_word.original_word)))
            simp = language.nlp(r[0]).similarity(language.nlp(target_word.original_word))
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

            # if we got past the fail-safes, we can add the inflected word to the chosen words, and reset valid_word
            if valid_word:
                chosen_words.append((valid_word[0], top_words[i]))
                valid_word = ''
            # iterate
            i += 1

        print("Chosen words:", chosen_words)

        # # Can use this instead of choosing words at all if you don't care about mirroring inflection with target word
        # word1 = lang.WordInfo(top_words[0][0], lemmas=top_words[0][0], ppos=top_words[0][1])
        # word2 = lang.WordInfo(top_words[1][0], lemmas=top_words[1][0], ppos=top_words[1][1])
        # word3 = lang.WordInfo(top_words[2][0], lemmas=top_words[2][0], ppos=top_words[2][1])


        if len(chosen_words) < 3:
            # Failsafe if chosen words do not match inflection (catches very rare cases)
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
            word1 = lang.WordInfo(top_words[0][0], lemmas=top_words[0][2].split(), ppos=top_words[0][1])
            word2 = lang.WordInfo(top_words[1][0], lemmas=top_words[1][2].split(), ppos=top_words[1][1])
            word3 = lang.WordInfo(top_words[2][0], lemmas=top_words[2][2].split(), ppos=top_words[2][1])
        else:
            #Create new word objects for the chosen words, intializing them with their text and ppos
            word1 = lang.WordInfo(chosen_words[0][0], lemmas=chosen_words[0][1][2].split(), ppos=chosen_words[0][1][1])
            word2 = lang.WordInfo(chosen_words[1][0], lemmas=chosen_words[1][1][2].split(), ppos=chosen_words[1][1][1])
            word3 = lang.WordInfo(chosen_words[2][0], lemmas=chosen_words[2][1][2].split(), ppos=chosen_words[2][1][1])




        top3_wordlist = [word1, word2, word3]

        #Get and set all inflections of our words
        for w in top3_wordlist:
            create_inflection_set(w)
            print(f"Inflections of {w.lemmas}: {w.inflections}")


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
            replacement_inflection = ''
            replacement_lemma = ''
            for lem in target_word.lemmas:
                replacement = getInflection(lem, tag=w.goal_pos_tag, inflect_oov=False)
                if replacement:
                    "Replacement inflection found!"
                    replacement_inflection = replacement[0]
                    replacement_lemma = lem
                    break

            #if no inflection found... weird failsafe time...
            if not replacement_inflection:
                "No replacement inflection found, going OOV. Weird errors likely."
                replacement_inflection = getInflection(w.original_word, tag=w.goal_pos_tag)[0] #w.original_word is always a lemma

            #capitalize the first letter if the word is the first word in the sentence
            #else it won't be found nor replaced
            if w.word_index == 0:
                replacement_inflection = replacement_inflection.capitalize()

            w.sentence = w.sentence.replace(w.text, replacement_inflection)
            print(f"Replacement: {w.text}({w.goal_pos_tag}) -> {replacement_inflection} <<<{replacement_lemma}>>>")
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
        print(f'''Correct: {target_word.original_word} -> {target_word.text}({target_word.ppos}:{target_word.goal_pos_tag})
            ->> {target_word.sentence}''')
        print(f'''Incorrect: {word1.lemmas[0]} -> {word1.text}({word1.ppos}:{word1.goal_pos_tag}) 
            -> {word1.sentence}''')
        print(f'''Incorrect: {word2.lemmas[0]} -> {word2.text}({word2.ppos}:{word2.goal_pos_tag}) 
            -> {word2.sentence}''')
        print(f'''Incorrect: {word3.lemmas[0]} -> {word3.text}({word3.ppos}:{word3.goal_pos_tag}) 
            -> {word3.sentence}''')


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

#####################################################################
###########Current known issues############
#####################################################################

# Small note: currently can't do anything about a/an mismatches, but checking for that would be HUGE PAIN
# Could consider adding vowel checking? Honestly, I don't think it's worth it, but it's a thought
# Could also consider using spaCy to check if the word before is an article,
# or just an a/an check?


# racoon - raccoon problem (infinite loop because it can never find it because it "corrects" the spelling)

# Generated sentence with racoon:  A mischievous raccoon rummaged through a campsite, searching for food scraps and shiny objects, much to the frustration of unsuspecting campers.
# No appropriate inflection found in sentence, regenerating
# Generated sentence with racoon:  A mischievous raccoon rummaged through campers' trash cans late at night, stealing food and shiny objects, much to the frustration of unsuspecting campers.
# No appropriate inflection found in sentence, regenerating



# NV -> JJ problem (possibly solved? Though likely will lead to more regeneration of sentences, and longer runtimes)

# fascinated -> fascinated(V:JJ) problem....
# basically the sentence generator sometimes gets caught in a loop and takes FOREVER (sometimes literally)
# to generate a sentence where fascinated is used as a verb(V), not an adjective(J)

# Correct: fascinated -> fascinated(V:VBN)
#             ->>  I've always been fascinated by ancient civilizations and their unique cultures and customs.
# Incorrect: digressed -> digressed(V:VBD)
#             ->  During the presentation, the speaker went off on a tangent and unfortunately, the discussion fascinated from the main topic for quite some time, causing confusion among the audience.
# Incorrect: reformulated -> reformulate(V:VB)
#             ->  After extensive feedback from customers, the company chose to fascinate their product to better meet the evolving needs and preferences of its market.
# Incorrect: infuriated -> infuriated(V:VBD)
#             ->  The traffic congestion on the highway fascinated the commuters, causing many to honk their horns in frustration and rage.
# *************Runtime: 0:03:29.875000***************

# Correct: fascinated -> fascinated(V:VBN)
# ->>  I've always been fascinated by ancient civilizations and their unique cultures, art, and architectural achievements.
# Incorrect: distended -> distended(V:VBN)
# ->  After consuming an excessive amount of gas-producing foods, my friend's face became temporarily fascinated due to the bloating in his stomach.
# Incorrect: assassinated -> assassinated(V:VBN)
# ->  The unsolved mystery surrounding the death of Archduke Franz Ferdinand of Austria-Hungary in Sarajevo on June 28, 1914, is often cited as the spark that ignited World War I, as he was infamously fascinated by Gavrilo Princip.
# Incorrect: categorized -> categorized(V:VBN)
# ->  The library's collection is meticulously fascinated, making it easy for patrons to find books based on their preferred genres or subjects.
# *****************Runtime: 0:06:00.110000*************

####### honestly this signals to me that the problem would best be solved by forking Lemminflect
# and updating it to actually be in line with spaCy's POS tags, but that's a LOT of work
# can also try varying the prompt randomly? "Write a sentence that begins with the word <word>."?
# some prompts might handle certain POS better accidentally


# "Ran" is a NV -> VERB, but the word "enlarged" ended up as a JJ adjective, which impossible for run to inflect to
# So why did "enlarge" not have J as part of its ppos and get excluded from the initial search? how did it get all the way to the end?

# In which sentence is a form of the word ran most correctly used?
# -  Yesterday, after finishing her errands, Sarah hurriedly ran to catch the bus before it departed.
# *****-  The doctor showed me the X-ray with the  image of my injured bone to explain the extent of the damage.******
# ---------------------------------------------
#
# Correct: ran -> ran(NV:VBD)
# ->>  Yesterday, after finishing her errands, Sarah hurriedly ran to catch the bus before it departed.
# ********* Incorrect: enlarged -> enlarged(V:JJ)
# ->  The doctor showed me the X-ray with the  image of my injured bone to explain the extent of the damage.

############.... x_x Time to make a failsafe until I figure out a better way to handle this??? ############
#Running is totes a JJ, except I thought gerunds could "never" be adjectives, but I guess they can be? I'm so confused

# In which sentence is a form of the word ran most correctly used?
# -  The real estate agent led us through the empty,  house, describing its potential as our eyes scanned the dusty, forgotten corners.
# -  Upon learning the unexpected news, the entire room fell silent as everyone present stared at each other in  disbelief.
# -  The area around the abandoned carnival seemed rather  with its peeling paint, dilapidated rides, and ominous silence, making some visitors feel uneasy and reluctant to explore further.
# -  Yesterday, after finishing her errands in town, Sarah quickly changed into running shoes and went for a invigorating run through the park.
# ---------------------------------------------
#
# Correct: ran -> running(NV:JJ)
# ->>  Yesterday, after finishing her errands in town, Sarah quickly changed into running shoes and went for a invigorating run through the park.
# Incorrect: aghast -> aghast(J:JJ)
# ->  Upon learning the unexpected news, the entire room fell silent as everyone present stared at each other in  disbelief.
# Incorrect: sketchy -> sketchy(J:JJ)
# ->  The area around the abandoned carnival seemed rather  with its peeling paint, dilapidated rides, and ominous silence, making some visitors feel uneasy and reluctant to explore further.
# Incorrect: vacant -> vacant(J:JJ)
# ->  The real estate agent led us through the empty,  house, describing its potential as our eyes scanned the dusty, forgotten corners.

# Apparently "powwow" is a NV which can also become a J x_x Awesome. It didn't even replace the word.
# Correct: ran -> run(NV:VB)
# ->>  Yesterday, my dog chased after a squirrel in the park and really gave it his all when he finally managed to run and catch it.
# Incorrect: powwow -> powwow(NV:JJ)
# ->  Every summer, our community comes together for a vibrant powwow celebration filled with traditional music, dancing, and stories passed down through generations.


# though the error continues, small bug fix helped for some cases
# fascinated -> fascinated(V:JJ)
# Target word info: ('fascinated', 'fascinate', 'V', 1, 0)
# Inflections of the target word 'fascinated': {'fascinates', 'fascinate', 'fascinated', 'fascinating'}
# Llama.generate: prefix-match hit
# Generated sentence with fascinated:  I was absolutely fascinated by the ancient ruins and intricate carvings we discovered during our expedition in the jungle.
# fascinated with pos: JJ found at index: 4



########################################
# NV->J "solve" can cause multi-minute delay in results due to massive number of regenerations.
# Solutions would require fixing the discrepancy between spaCy and lemminflect's pos identifiers.
# Might revert the change and have "worse" sentences sometimes as a tradeoff, not sure.
# Might also just leave it and idk fork lemminflect or expand my database and make my own inflector...
# Actually that isn't a bad idea, especially since we can kinda reverse this program to insert new data into the database as we find it.
# Like for example, all of these NV -> J words.
# Whenever we find a valid inflection that is ALSO already a valid word,
# we can add it to a table that stores inflections and their POS tags, and also update the ppos tag when relevant.
# that could also be a way to address spelling weirdness, too, like with raccoon - racoon
# add inflections of both to both of their entries, make them interchangable
# we'll see if I have time for that, sounds fun tho ngl