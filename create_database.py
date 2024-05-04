import sqlite3
import spacy
import lemminflect
from lemminflect import getAllLemmas, getInflection, getAllInflections


language = "English" #for now, just testing with english
filename = 'sowpods.txt'
if '.' in filename: #remove file extension if it exists
    filename = filename[:filename.index('.')]

try:
    with open(f'{filename}.txt') as f:
        wordlist = f.read().splitlines()
except FileNotFoundError:
    print(f"File {filename}.txt not found")
    exit()

longest_word = max(wordlist, key=len)
max_value = len(longest_word)
print(f"The longest word in {filename} is: {longest_word} with length {len(longest_word)}")

#calculate how many batches this will take to keep a count of progress
batches = len(wordlist) // 1000
if len(wordlist) % 1000 != 0:
    batches += 1
print(f"Inserting {len(wordlist)} words in {batches} batches of 1000")

def create_eng_ppos(lemma):
    '''Create English ppos aka 'possible parts of speech' is a combination of all possible POS tags for a word,
    but only combinations of NOUN, VERB, AUX, ADJ, ADV are considered, with one letter each so they can be sorted appropriately
    NOUN = N, PROPER_NOUN = P, VERB = V, AUX = X, ADJ = J, ADV = R
    These letters will be added together and sorted into alphabetical order, so that the same combination of POS tags will always have the same ppos
    Others will be null
    '''
    ppos = '' #build from empty string

    #can't just get all lemmas to get all POS tags because it doesn't work for things like 'dancing', which is a noun and a verb
    #so we have to get all the inflections and just check those tags and convert them to the appropriate letter(s)

    #get all inflections
    inflections = getAllInflections(lemma, upos=None)
    pos_tags = list(inflections.keys())
    if 'JJ' in pos_tags: #JJ is adjective
        ppos += 'J'
    if 'NN' in pos_tags: #NN is noun
        ppos += 'N'
    if 'NNP' in pos_tags: #NNP is proper noun
        ppos += 'P'
    if 'RB' in pos_tags: #RB is adverb
        ppos += 'R'
    if 'VB' in pos_tags: #VB is verb
        ppos += 'V'
    # 'AUX' is not a POS tag that appears in "getAllInflections", but it's important to know
    # It only shows up in getAllLemmas(), so we could do an extra check... or... we could just give it manually to the very few lemmas that have it
    aux_lemmas = ['be', 'have', 'do', 'can', 'could', 'may', 'might', 'will', 'would', 'shall', 'should', 'must', 'ought'] #dare is also on the Lemminflect AUX/MD list, but I don't think it'll cause the same problems as the others
    if lemma in aux_lemmas:
        ppos += 'X'

    if ppos != '':
        ppos = ''.join(sorted(ppos))
        #should already be sorted, but just in case something gets added to above and I forget to re-alphabetize
    else:
        ppos = None

    return ppos

###### When doing commits for every query -- 15:06 started - reached  "transaminations" by 16:06 x_x ######
# This takes REALLY long if we commit after every insert, best would be to batch it into groups of 1000 queries and then loop though them.
###16:30 started 1000 batch insert, ended ~16:45 HUUUGE improvement!!!######
def insert_words_into_db(query_list):
    '''Insert a word into the database'''
    for query in query_list:
        cursor.execute(query)

    sqliteConnection.commit()
    print(f"Inserted and committed {len(query_list)} rows into db.\nLast entry was: {query_list[-1]}")


def build_query(word_doc, lem, ppos, OOV):
    '''Build the query to insert a word into the database'''
    #convert lem and ppos to strings surrounded by '' for SQL, or NULL if they are None
    if lem:
        lem = f"'{lem}'"
    else:
        lem = 'NULL'
    if ppos:
        ppos = f"'{ppos}'"
    else:
        ppos = 'NULL'

    query = f'''INSERT INTO {language}Dictionary (word, lemma, ppos, isOOV) VALUES ('{word_doc.text}', {lem}, {ppos}, {OOV});'''
    #print(f"Created query for: {word_doc.text}, {lem}, {ppos}, {OOV}") #effectively a loading screen to show all inserts for funsies/debugging
    return query


def insert_dictionary_into_db(wordlist, language):
    '''Insert the entire dictionary into the database'''
    batch_count = 0
    if language == 'English':
        nlp = spacy.load('en_core_web_md')
        query_list = []
        for word in wordlist:
            word_doc = nlp(word)
            #lem = word_doc.lemma_ #should work for any language in spacy, but we need to do an OOV lemminflect check
            OOV = 0
            ppos = None
            main_lem = None
            lems = list(getAllLemmas(word, upos = None).values())
            if not lems:
                OOV = 1
            else:
                main_lem = lems[0][0]
                ppos = create_eng_ppos(main_lem)

            #if the word is already the lemma, the lemma needs to be reset to "NULL" in the database instead
            if word == main_lem:
                main_lem = None

            #build query and add to list
            query_list.append(build_query(word_doc, main_lem, ppos, OOV))

            if len(query_list) == 1000 or word == wordlist[-1]: #batch insert every 1000 queries, or if it's the last word
                insert_words_into_db(query_list) #insert fully built entry into database
                query_list = [] #reset query list
                batch_count += 1
                print(f"----->{batch_count} / {batches} batches complete<-----")
                continue

    elif language == 'Polish':
        nlp = spacy.load('pl_core_news_md')
        for word in wordlist:
            word_doc = nlp(word)
            lem = word_doc.lemma_
    else:
        print('Language not supported')
        exit()


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

    # Create a table in the database, VARCHAR numbers are currently arbitrary, but definitely far more than sufficient
    # SQLite doesn't have BIT nor BOOLEAN, INTEGER is the accepted way to store boolean values
    query = f'''CREATE TABLE IF NOT EXISTS {language}Dictionary (
        word VARCHAR({max_value}) PRIMARY KEY,
        lemma VARCHAR({max_value}),
        ppos VARCHAR(6),
        isOOV INTEGER
    );'''

    # Execute the query
    cursor.execute(query)
    sqliteConnection.commit()
    print('Table created')

    # Insert data into the table
    insert_dictionary_into_db(wordlist, language)


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


