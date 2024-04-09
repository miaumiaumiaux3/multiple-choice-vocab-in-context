

import spacy
import lemminflect
from lemminflect import getLemma, getAllLemmas, getInflection, getAllInflections #might not need, as it can be used as a spaCy extension
import collections
from collections.abc import Iterable

def flatten(xs): #flatten a list of lists
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

# Load the en_core_web_md model
nlp = spacy.load("en_core_web_md")
import en_core_web_md

nlp = en_core_web_md.load()

# Sample text from Gemini -- create 100 sentences using the word "dancing" #only produced 50
doc = nlp(
    '''The fireflies danced in the twilight, creating a mesmerizing spectacle. 
    The salsa music was so infectious, everyone ended up dancing.
Feeling shy, she pretended not to see his invitation to dance.
Rain danced on the windowpane, a rhythmic counterpoint to the music inside.
The ballerina's movements were so fluid, it seemed she defied gravity while dancing.
The children danced with wild abandon, lost in their own world of imagination.
The leaves danced in the autumn breeze, a fiery display of red and orange.
He tapped his foot impatiently, eager to get out there and start dancing.
The couple swayed slowly in each other's arms, their love story told in every dance step.
The choreographer envisioned a dance that captured the essence of springtime.
Despite her two left feet, she surprised everyone by dancing the night away.
The tribal dancers moved with a primal energy, their bodies painted in vibrant colors.
The disco ball spun, casting a thousand shimmering reflections on the dancing crowd.
The waves danced on the shore, a constant rhythm against the sandy beach.
They practiced their wedding dance every night, determined to avoid any stumbles.
The breakdancers defied physics with their acrobatic dance moves.
The flamenco dancer's fiery red dress swirled around her as she danced.
The old man sat by the window, reminiscing about the days he spent dancing the night away.
The entire town came together for the annual dance competition, a celebration of local talent.
The raindrops danced on the umbrella, a tiny performance for one.
The melody danced through her head, long after the music had stopped.
He put on his dancing shoes, ready for a night of fun.
The children learned a traditional folk dance from their grandparents.
The street performers danced with such passion, they drew a crowd of onlookers.
The rhythmic pounding of the drums called them to the dance floor.
She dreamt of dancing on a grand stage, bathed in the spotlight.
The tango was a dance of love and desire, filled with smoldering looks and intricate steps.
The robot danced awkwardly, its movements jerky and mechanical.
The synchronized swimmers danced underwater, a graceful ballet in an alien world.
The documentary explored the history of ballroom dancing through the ages.
The bonfire crackled, casting flickering shadows that danced on the walls.
The taste of victory was sweet, and he celebrated by dancing on the field.
The artist's brush danced across the canvas, creating a vibrant masterpiece.
The detective's mind danced with possibilities, trying to solve the case.
He nervously adjusted his tie, preparing to ask her to dance.
The wind danced through the wheat fields, creating waves of gold.
The taste buds danced on her tongue, savoring the exotic flavors.
The flames danced in the fireplace, a warm and comforting sight.
The couple danced under the moonlight, their love story written in the stars.
The melody danced out of the speakers, filling the room with joy.
The party wouldn't be complete without some dancing!
The soloist took center stage, ready to wow the audience with their dancing skills.
The dance instructor patiently corrected their mistakes, helping them improve their technique.
The documentary explored the healing power of dance for people with disabilities.
She took a deep breath and stepped onto the dance floor, ready to conquer her stage fright.
The children giggled as they danced with their stuffed animals, their imaginations running wild.
The competition was fierce, with dancers from all over the world vying for the top prize.
He closed his eyes and let the music take over, his body moving instinctively.
The waltz was a timeless dance, perfect for a romantic evening.
The rhythmic pounding of the drums echoed through the jungle, a call to the ancient dance ritual.'''
)


#print([[w._.lemma(), getAllLemmas(w.text, upos=None)] for w in doc])
pos_count = {}
word_pos_count = {}
word = "dancing" #needs to be able to work for any word in any form
print(getAllLemmas(word, upos = None))
word_lemmas = list(getAllLemmas(word, upos = None).values())
print(word_lemmas, "first entry: ", word_lemmas[0][0])
word_inflections = getAllInflections(word_lemmas[0][0], upos=None) #doesn't work for "Testing"
print(word_inflections)
word_inflection_list = list(flatten(list(word_inflections.values())))
print(word_inflection_list)

for w in doc:
    if w.tag_ in pos_count.keys():
       pos_count[w.tag_] += 1
    else:
       pos_count[w.tag_] = 1
    #print(w.lemma_, w.tag_)
    if w.lemma_ in word_inflection_list:
       if w.tag_ in word_pos_count.keys():
            word_pos_count[w.tag_] += 1
       else:
            word_pos_count[w.tag_] = 1

print(pos_count) #{'DT': 107, 'NNS': 48, 'VBD': 61, 'IN': 76, 'NN': 138, ',': 42, 'VBG': 26, 'JJ': 54, '.': 50, '_SP': 49, 'RB': 18, 'RP': 3, 'PRP': 20, 'TO': 9, 'VB': 14, 'PRP$': 23, 'POS': 5, 'NNP': 1, 'VBN': 10, 'CC': 9, 'WDT': 2, 'CD': 3, 'MD': 1}
print(word_pos_count) #{'VBD': 20, 'VBG': 8, 'VB': 2, 'NN': 17} #for dance, dancing, dances, danced

#problem: "dancer" is not included in the list of inflections for "dancing", and of course neither is "breakdancer" -- should these be included? Is the lemma search too restrictive or should the sample sentences be?