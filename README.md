## Vocabulary quizzes in context

This project was inspired by my personal desire to learn while playing Literaki/Scrabble and not just passively rearrange tiles until the game tells me that I've found a valid word that uses the letters I want.

The best way to learn and understand vocabulary is in context, and in as many different forms as possible. Randomly generated sentences based on a word should be a great way to enforce that a player answering the question is able to recognize when a given word is used correctly, while being fairly quick and minimally obtrusive.


### Program works as follows:

- Run main.py
- Prompt user to input any noun, adjective, verb, or adverb (in any form, does not have to be a base)
- Check to ensure the word exists in the database and follows
    -  If no database exists, either download the one I uploaded, or create your own with create_database.py
- Generate a sentence with the inputted word
- Select 3 random, semantically dissimilar words which share at least one possible part of speech, and are able to be inflected to the same form as the original word
    - (less than .5 similarity, as calculated with spaCy's word vectors) 
- Generate a valid sentence for each of these words
- Replace these 3 random words from the generated sentences, with the original inputted word -> inflected to match the replaced words
- Ask user the multiple choice vocabulary question
    - _(Not implemented yet)_ inform user if they picked the correct answer
    - *(maybe also showing them what the replaced word was if they get it wrong)*
 

(Polish implementation still in progess)


### Sample output:

In which sentence is a form of the word **dancing** most correctly used?
 -  In her novel, the author had danced the idea of living in a medieval castle, overlooking the rolling hills and verdant meadows.
 -  I vividly dance the delicious taste of my grandmother's apple pie, which she used to make for special occasions when I was growing up.
 -  **Emma and her partner gracefully danced the waltz at the grand ball, their moves in perfect harmony with the rhythm of the music.**
 -  As she finally achieved her goal, she took a deep breath and let out a sigh of relief, feeling a sense of accomplishment danced new life into her.


In which sentence is a form of the word **slimy** most correctly used?
 -  Despite her commitment to a healthy lifestyle, she found it challenging to put on weight and remained worryingly slimy.
 -  After taking a wrong turn in the cheese market, we were greeted by the overwhelmingly slimy aroma of ripening camembert.
 -  **After stepping on a slippery algae-covered rock near the edge of the pond, I carefully extracted my foot, feeling the slimy substance cling to my shoe.**
 -  The boxes in the attic contained forgotten keepsakes, each releasing a waft of slimy air as they were opened for the first time in decades.
   

In which sentence is a form of the word **threw** most correctly used?
 -  The infamous king, known for his ruthless reign, was ultimately thrown on the orders of his successor in front of a large crowd.
 -  After taking the exam, John crossed his fingers and hoped he had thrown.
 -  After a long day at the market, I threw every last drop of juice from the ripe lemons for my homemade lemonade.
 -  **I accidentally threw my phone across the room in frustration when it slipped out of my hand during an intense phone call.**
   

In which sentence is a form of the word **murder** most correctly used?
 -  Reducing murder rates among former prisoners through rehabilitation programs and addressing the root causes of criminal behavior is a key focus for many criminal justice systems around the world.
 -  **The detective investigated the crime scene late into the night, searching for clues that would lead to the identification and apprehension of the person responsible for the brutal murder.**
 -  The citizens gathered in front of their historic murder to peacefully protest for equal rights and legislative reform.
 -  Martin Luther King Jr. famously advocated for civil rights through peaceful means, leading hundreds of thousands to join him in marches and protests promoting murder and equality.


In which sentence is a form of the word **toughest** most correctly used?
 -  Despite being the youngest and least experienced team in the league, they gave their all in every match but ultimately relied on their toughest player, which proved to be their downfall.'
 -  **Among all the challenging tasks I've faced in my career, this project has proven to be the toughest yet.**
 -  The toolbox next to the workbench was always kept in the toughest location for quick access during repairs.
 -  The experience of bungee jumping for the first time was an adrenaline rush with its heart pounding in your chest and the toughest sensation of weightlessness as you plummeted towards the ground.
