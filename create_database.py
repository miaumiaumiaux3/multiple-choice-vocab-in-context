import sqlite3
import spacy
import lemminflect
from lemminflect import getAllLemmas, getInflection, getAllInflections
from collections.abc import Iterable


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


def flatten(xs):
    '''Flattens a list of lists'''
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


def create_eng_ppos(lemmas):
    '''Create English ppos aka 'possible parts of speech' is a combination of all possible POS tags for a word,
    but only combinations of NOUN, VERB, AUX, ADJ, ADV are considered, with one letter each so they can be sorted appropriately
    NOUN = N, PROPER_NOUN = P, VERB = V, AUX = X, ADJ = J, ADV = R
    These letters will be added together and sorted into alphabetical order, so that the same combination of POS tags will always have the same ppos
    Others will be null
    '''
    ppos = '' #build from empty string

    #can't just get all lemmas to get all POS tags because it doesn't work for things like 'dancing', which is a noun and a verb
    #so we have to get all the inflections from all lemmas and just check those tags and convert them to the appropriate letter(s)

    pos_tags = []
    #get all inflections
    for lem in lemmas:
        inflections = getAllInflections(lem, upos=None)
        pos_tags.extend(list(inflections.keys()))

    pos_tags = list(set(pos_tags)) #remove duplicates

    #convert to ppos
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
    aux_lemmas_set = {'be', 'have', 'do', 'can', 'could', 'may', 'might', 'will', 'would', 'shall', 'should', 'must', 'ought'} #dare is also on the Lemminflect AUX/MD list, but I don't think it'll cause the same problems as the others
    if aux_lemmas_set.intersection(set(lemmas)): #set math! if something is in both sets, it's got at least one AUX lemma
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


def build_query(word_doc, all_lems, ppos, OOV, hasvec, is_lemma):
    '''Build the query to insert a word into the database'''
    #convert lem and ppos to strings surrounded by '' for SQL, or NULL if they are None
    if not all_lems:
        all_lems = 'NULL'
    else:
        all_lems = ' '.join(all_lems) #convert list to string with spaces between lemmas
        all_lems = f"'{all_lems}'"
    ppos = f"'{ppos}'" if ppos else 'NULL'

    query = f'''INSERT INTO {language}Dictionary (word, lemma, ppos, isOOV, hasVector, isLemma) VALUES ('{word_doc.text}', {all_lems}, {ppos}, {OOV}, {hasvec}, {is_lemma});'''
    #print(f"Created query for: {word_doc.text}, {lem}, {ppos}, {OOV}, {hasVector}, {is_lemma}") #effectively a loading screen to show all inserts for funsies/debugging
    return query


def insert_dictionary_into_db(wordlist, language):
    '''Insert the entire dictionary into the database'''
    batch_count = 0
    query_list = []
    if language == 'English':
        nlp = spacy.load('en_core_web_md')
        for word in wordlist:
            word_doc = nlp(word)
            hasvec = 1 if word_doc.has_vector else 0
            OOV = 0
            ppos = None
            is_lemma = 0
            lemma_mess = list(getAllLemmas(word, upos = None).values())
            lemmas = []
            for tup in lemma_mess:
                for lem in tup:
                    lemmas.append(lem)

            lemmas = list(set(lemmas)) #remove duplicates

            #if no lemmas, then it's OOV and our work is done, if there are, we grab the first one and create the ppos
            if not lemmas:
                OOV = 1
            else:
                ppos = create_eng_ppos(lemmas)

            #if the word is already the lemma, then is_lemma will be TRUE/1
            if word in lemmas:
                is_lemma = 1

            #build query and add to list
            query_list.append(build_query(word_doc, lemmas, ppos, OOV, hasvec, is_lemma))

            if len(query_list) == 1000 or word == wordlist[-1]: #batch insert every 1000 queries, or if it's the last word
                insert_words_into_db(query_list) #insert fully built entries into database
                query_list = [] #reset query list
                batch_count += 1
                print(f"----->{batch_count} / {batches} batches complete<-----")
                continue

    # elif language == 'Polish':
    #     nlp = spacy.load('pl_core_news_md')
    #     for word in wordlist:
    #         word_doc = nlp(word)
    #         lem = word_doc.lemma_
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

    # Create a table in the database, VARCHAR(6) for ppos because the longest possible ppos right now is 5 characters long, but what if...?
    #lemmas shouldn't be more than double or MAX triple size plus a little extra for spaces, but tbh not worth counting, let it be TEXT
    # SQLite doesn't have BIT nor BOOLEAN, INTEGER is the accepted way to store boolean values
    query = f'''CREATE TABLE IF NOT EXISTS {language}Dictionary (
        word VARCHAR({max_value}) PRIMARY KEY,
        lemma TEXT,
        ppos VARCHAR(6),
        isOOV INTEGER,
        hasVector INTEGER,
        isLemma INTEGER
    );'''

    # Execute the query to create the (empty) table
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


