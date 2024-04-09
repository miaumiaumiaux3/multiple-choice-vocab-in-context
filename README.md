## Vocabulary in context

This project was inspired by my personal desire to learn while playing Literaki/Scrabble and not just passively rearrange tiles until a valid word is found. 

The best way to learn and understand vocabulary is in context, and in as many different forms as possible. Randomly generated sentences based on a word should be a great way to enforce that a player answering the question is able to recognize when a given word is used correctly, while being fairly quick and minimally obtrusive.

Program should work as follows:
- Input word in any form/inflection
- Generate a sentences with this word
- Identify POS (part of speech) to make sure it's a verb, noun, adjective or adverb
- Use wordgame dictionary of the appropriate language to obtain 3 random, semantiacally unrelated words (likely at least .5 distance between vector norms) with the same POS
- Generate a sentence for each of these words
- Replace these 3 random words from the generated sentences, with the original inputted word -- inflected to match the replaced words
- Ask user the multiple choice question and informs them if they picked the correct answer (maybe also showing them what the replaced word was if they get it wrong)

Sample question with "dancing" as the inputted word:

"Which of these sentences is correct?"
a) The criminal danced a man
b) I dance off the counter
c) The monkey was dancing a banana
*d) He dances the tango*
    
