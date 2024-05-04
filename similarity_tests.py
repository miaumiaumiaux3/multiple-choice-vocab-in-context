import sqlite3
import spacy



target_word = "testing"

language = "English"
filename = 'sowpods'
max_value = 15 #longest word in sowpods is 15 characters long


def insert_similarity_into_db(wordlist, target_word):
    '''Insert the similarity results into the database'''
    batch_count = 0
    query_list = []

    if language == 'English':
        nlp = spacy.load('en_core_web_md')
        target_word_doc = nlp(target_word)
        for word in wordlist:
            word_doc = nlp(word)
            similarity = word_doc.similarity(target_word_doc)
            similarity = round(similarity, 2)

            #build a query and add it to the list
            query_list.append(f"INSERT INTO {target_word}Similarities (word, similarity) VALUES ('{word}', {similarity});")

            if len(query_list) == 1000 or word == wordlist[-1]: #batch insert every 1000 queries, or if it's the last word
                insert_words_into_db(query_list) #insert fully built entries into database
                query_list = [] #reset query list
                batch_count += 1
                print(f"----->{batch_count} / {batches} batches complete<-----")
                continue

#copied from create_database.py, we might want to put this in a separate file and import it to both
def insert_words_into_db(query_list):
    '''Insert a word into the database'''
    for query in query_list:
        cursor.execute(query)

    sqliteConnection.commit()
    print(f"Inserted and committed {len(query_list)} rows into db.\nLast entry was: {query_list[-1]}")

try:

    # Connect to DB and create a cursor
    sqliteConnection = sqlite3.connect(f'{filename}.db')
    cursor = sqliteConnection.cursor()
    print('DB Init')

    # Write a query and execute it with cursor
    query = 'select sqlite_version();'
    cursor.execute(query)

    # Fetch and output result
    result = cursor.fetchall()
    print('SQLite Version is {}'.format(result))

    # Get target word's info from the database
    query = f'''SELECT * FROM {language}Dictionary WHERE word = '{target_word}';'''
    cursor.execute(query)
    result = cursor.fetchone() #if no result, returns None, otherwise tuple of the full row

    if not result:
        print("Word not found in database")
        cursor.close()
        exit()

    #If the word is not the lemma, change the word to the lemma
    if result[1]:
        target_word = result[1]

    if result[2]:
        ppos = result[2]
    else:
        print("Word has no relevant POS tag")
        cursor.close()
        exit()

    ####################################################
    # #If we want to be *inclusive* and add ALL words that share even one ppos tag with the target word
    # pos_queries = ''
    # for char in ppos:
    #     pos_queries += f"ppos LIKE '%{char}%'"
    #     if char != ppos[-1]:
    #         pos_queries += ' OR '
    #
    # # Pull from database to get all lemmas (lemma = 'NULL') where isOOV = 0 and hasVector = 1 (i.e. all words that are in both lemminflect and spaCy vocabularies)
    # # And share at least one ppos with the target word (excluding AUX)
    # query = f'''SELECT word, ppos FROM {language}Dictionary
    #         WHERE isOOV = 0 AND lemma is NULL AND hasVector = 1
    #         AND ({pos_queries}) AND ppos NOT LIKE '%X%';
    #         '''
    #################################################################################

    ######################################################
    #Most EXCLUSIVE, and ONLY include exact ppos matches
    # Pull from database to get all lemmas (lemma = 'NULL') where isOOV = 0 and hasVector = 1 (i.e. all words that are in both lemminflect and spaCy vocabularies)
    # Only get EXACT ppos copies of the target word
    # query = f'''SELECT word, ppos FROM {language}Dictionary
    #         WHERE isOOV = 0 AND lemma is NULL AND hasVector = 1
    #         AND ppos = '{ppos}' AND word != '{target_word}';
    #         '''
    ######################################################

    #Medium inclusive, include exact matches, and for each letter, include the "pure" matching words
    #gets kinda weird for some adverbs, espcially the strange 'RV' ones that like, I have no idea how they are also adverbs
    pos_queries = ''
    for char in ppos:
        pos_queries += f" OR ppos = '{char}' "

    query = f'''SELECT word, ppos FROM {language}Dictionary 
            WHERE isOOV = 0 AND lemma is NULL AND hasVector = 1
            AND (ppos = '{ppos}'{pos_queries}) AND word != '{target_word}';
            '''

    print(query)
    cursor.execute(query)
    result = cursor.fetchall() #if no result, it will be an empty list, if a VARCHAR is 'NULL', it will be None

    # List of words to run similarity tests on
    wordlist = [r[0] for r in result]

    # SQLite doesn't have BIT nor BOOLEAN, INTEGER is the accepted way to store boolean values
    query = f'''CREATE TABLE IF NOT EXISTS {target_word}Similarities (
        word VARCHAR({max_value}) PRIMARY KEY,
        similarity FLOAT(2,2)
    );'''

    # Execute the query to create the (empty) table
    cursor.execute(query)
    sqliteConnection.commit()
    print('Similarity Table created')

    # Calculate batches for a proper loading bar
    batches = len(wordlist) // 1000
    if len(wordlist) % 1000 != 0:
        batches += 1
    print(f"Inserting {len(wordlist)} words in {batches} batches of 1000")

    # Insert the similarity results into the database
    insert_similarity_into_db(wordlist, target_word)


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

