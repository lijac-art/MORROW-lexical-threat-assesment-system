# Importing Necessary Libraries
import nltk
import time
import random
import sys
import json
from pathlib import Path
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk import ne_chunk
from nltk.tree import Tree
import spacy
from datetime import datetime

# Print Typewriter effect
def typewriter_print(text, delay=0.02):
    for char in text:
        print(char, end="", flush=True) 
        time.sleep(delay)
    print()

# Input Typewriter effect
def typewriter_input(text, delay=0.02):
    for char in text:
        print(char, end="", flush=True) 
        time.sleep(delay)
    print("", end="")
    user_response = input() 
    return user_response

# Declaring Essential NLTK dependencies
nltk_packages = [
    ('tokenizers', 'punkt'),
    ('tokenizers', 'punkt_tab'),
    ('taggers', 'averaged_perceptron_tagger'),
    ('taggers', 'averaged_perceptron_tagger_eng'),
    ('sentiment', 'vader_lexicon'),
    ('chunkers', 'maxent_ne_chunker'),
    ('chunkers', 'maxent_ne_chunker_tab'),
    ('corpora', 'words'),
    ('corpora','omw-1.4')
]
for category, package in nltk_packages:
    try:
        nltk.data.find(f"{category}/{package}")
    except LookupError:
        try:
            nltk.download(package, quiet=True)
        except OSError:
            typewriter_print("[DEPENDENCIES FAILED TO LOAD INITIATING SHUTDOWN]")
            sys.exit()

# Importanting NLP dependencies
nlp = spacy.load("en_core_web_sm")

# Declaring Variables, Lists, and Dictionaries
danger = ["murder", "kill", "stab", "injure", "threaten", "hurt", "ammunition",
          "ammo", "explosives", "grenade", "bomb", "toxic", "gas", "poison",
          "radioactive", "weapon", "gun", "guns", "massacre", "kills",
          "killing", "shoot", "eliminate", "destroy", "threaten"]
negation_words = ["no", "not", "never", "n't"]
human_keywords = ["human", "person", "people", "individual", "president", 
                  "leader", "counsel", "minister", "king", "monarch", 
                  "governor", "senator", "mayor"]
evidence_weights = {
    "intent": 0.15,
    "danger": 0.40,
    "negation": 0.25,
    "human": 0.20
}
ssn_registry = {}
memory_list = []
sentiment_memory_list = []
victim_and_perp = []
ssn_numbers = []
min_weight = 0.05
max_weight = 0.65
small_learning_rate = 0.005
large_learning_rate = 0.1
memory_length = 50000
time_of_load = datetime.now().strftime("%I:%M:%S")
relevant_threshold = 80
irrelevant_threshold = 60
null_threshold = 25
norm_current_weight = 0.6
norm_memory_weight = 0.4
lookback_window = 5
negation_score = 0
human_score = 0
current_scores = 0
memory_cycle_counter = 0

# Save File Setup
STATE_FILE = Path(__file__).with_name("MORROW_MEMORY.json")

def load_state():
    global memory_list, evidence_weights
    global norm_memory_weight, norm_current_weight, memory_cycle_counter
    try:
        with open(STATE_FILE, "r") as file:
            state = json.load(file)

        memory_list = state.get("memory_list", [])
        evidence_weights = {
            **evidence_weights,
            **state.get("evidence_weights", {})
        }
        norm_memory_weight = state.get("norm_memory_weight", norm_memory_weight)
        norm_current_weight = state.get("norm_current_weight", norm_current_weight)
        memory_cycle_counter = state.get("memory_cycle_counter", memory_cycle_counter)
        typewriter_print("[MEMORY LOADED SUCCESSFULLY]")
    except FileNotFoundError:
        typewriter_print("[NO PREVIOUS MEMORY FOUND]")
    except json.JSONDecodeError:
        typewriter_print("[MEMORY FILE CORRUPT - STARTING FRESH]")

def save_state():
    state = {
        "memory_list": memory_list,
        "evidence_weights": evidence_weights,
        "norm_memory_weight": norm_memory_weight,
        "norm_current_weight": norm_current_weight,
        "memory_cycle_counter": memory_cycle_counter
    }

    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Sentiment Scoring
def calculate_score(text):
    scores = sia.polarity_scores(text)
    if not sentiment_memory_list:
        if scores['pos'] > scores['neg']:
            current_scores = -round(scores['pos'] * 40)
            sentiment_memory_list.append(current_scores)
            return current_scores
        elif scores['neg'] > scores['pos']:
            current_scores = round(scores['neg'] * 110)
            sentiment_memory_list.append(current_scores)
            return current_scores
        else:
            return scores['compound']
        
# Sarcasm Detection
    previous_score = sentiment_memory_list[-1]  
    if scores['pos'] > scores['neg']:
        new_calculated_score = -round(scores['pos'] * 40)
        sentiment_memory_list.append(new_calculated_score)
    elif scores['neg'] > scores['pos']:
        new_calculated_score = round(scores['neg'] * 110)
        sentiment_memory_list.append(new_calculated_score)
    else:
        return scores['compound']
    difference = abs(new_calculated_score - previous_score)
    if difference >= 30:
        if perp in victim_and_perp or victim in victim_and_perp and None not in (victim,perp):
            new_calculated_score *= -0.75
            sentiment_memory_list.append(new_calculated_score)
            return new_calculated_score
    return new_calculated_score

# Welcoming User
typewriter_print("[MORROW]:\n")
typewriter_print("[THREAT ANALYSIS ENGINE]")
typewriter_print("[VERSION: 0.9.1]")
typewriter_print(f"[APPROXIMATE TIME]: {time_of_load}")

# Memory Loading
sia = SentimentIntensityAnalyzer()
def retrieve_memories(memory_list, victim, perp):
    if not victim or not perp:
        return []
    return [
        memory
        for memory in memory_list
        if memory.get("victim") == victim and memory.get("perp") == perp       
    ]

# Shutdown Sequence 
def shutdown_sequence():
    request = typewriter_input("[1 TO CONTINUE OPERATIONS, 0 TO INITIATE SHUTDOWN]: ")
    if request == "0":
        delay = round(random.uniform(5, 10))
        typewriter_print("[INITIATING ATEXIT]")
        time.sleep(delay/3)
        typewriter_print("[TERMINATING INSTANCES]")
        time.sleep(delay/3)
        typewriter_print("[PURGING MEMORY HEAP]")
        time.sleep(delay/3)
        typewriter_print("[BEGINNGING JSON SERALIZATION]")
        save_state()
        typewriter_print("[SYSTEM SHUTDOWN WITH CODE 0]")
        sys.exit(0)

    typewriter_print("[CONTINUING OPERATIONS]")

load_state()

while True:
    victim_and_perp.clear()
    terms_verbs = 0
    intent_score = 0
    negation_score = 0
    danger_word_score = 0
    human_score = 0
    full_name = None
    victim = None
    perp = None
    victim_identify = None
    perp_identify = None
    is_human = False
    shutdown_sequence()

    # Inputting Text
    norm_sentence = typewriter_input("[I/O STREAM INPUT]: ")
    doc = nlp(norm_sentence)
    punctuation = str.maketrans("", "", ".,?!:" + "0123456789")
    new_sentence = norm_sentence.translate(punctuation)
    tokenized_new_sentence = word_tokenize(new_sentence)
    tags = nltk.pos_tag(tokenized_new_sentence)
    pronouns = [word for word, pos in tags if pos in ('PRP', 'PRP$')]
    entities = ne_chunk(tags)

    for i, (word, tag) in enumerate(tags):
        if word.lower() in danger:
            danger_word_score = min(danger_word_score + 60, 180)

            # Negation Handling
            start_index = max(0, i - lookback_window)
            negation_word = 0
            for prev_idx in range(i - 1, start_index - 1, -1):
                prev_token = doc[prev_idx] 
                prev_word = tags[prev_idx][0].lower()
                if prev_word in negation_words:
                    negation_word += 1
            if negation_word % 2 != 0:
                 parent_word = doc[i].head 
                 if parent_word.pos_ == "VERB":
                    negation_score -= 100

            # Non-Human Forward Subject Handling (Victim Check)
            human_found = False
            end_index = min(len(tags), i + 1 + lookback_window)
            for next_idx in range(i + 1, end_index):
                prev_word, prev_tag = tags[next_idx]
                is_human = False
                for chunk in entities:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        name_parts = [leaf[0] for leaf in chunk.leaves()]
                        full_name = " ".join(name_parts)
                        if prev_word not in name_parts:
                            continue
                        if full_name == perp:
                            continue
                        is_human = full_name
                        break
                    else:
                        is_human = False
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                human_pronoun = prev_word_lower in ["she", "her", "he", "him", "us", "them", "mine", "you", "his", "our", 
                                                     "guy", "someone", "anyone", "everyone", "boy", "girl", "women", "man", 
                                                     "child", "adult", "friend", "their", "me", "intruder", "president", "leader", "prime minister"]
                human_noun = (
                    prev_tag in ["NN", "NNS", "NNP"]
                    and prev_word_lower in human_keywords
                )
                if prev_tag in ["NN", "NNS", "NNP", "NNPS", "PRP", "PRP$"]:
                    if not human_pronoun and not human_noun and not is_human:
                        human_found = False
                    else:
                        if perp != is_human:
                            victim = is_human
                            victim_identify = is_human
                            victim_and_perp.append(victim)
                            human_found = True
                            break
                        else:
                            victim = prev_word
                            victim_and_perp.append(victim)
                            human_found = True
                            break
            if human_found == False:
                human_score -= 150

            # Non-Human Backward Subject Handling (Perp Check)
            human_found = False      
            for next_idx in range(i - 1, max(-1, i - 1 - lookback_window), -1):
                prev_word, prev_tag = tags[next_idx]
                is_human = False
                for chunk in entities:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        name_parts = [leaf[0] for leaf in chunk.leaves()]
                        full_name = " ".join(name_parts)
                        if prev_word not in name_parts:
                            continue
                        if full_name == victim:
                            continue
                        is_human = full_name
                        break
                    else:
                        is_human = False
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                human_pronoun = prev_word_lower in ["i", "my", "myself", "you", "your", "yourself",
                                                    "he", "him", "his", "himself", "she", "her", "hers", "herself", 
                                                    "we", "us", "our", "ours", "ourselves", "they", "them",
                                                      "their", "theirs", "themselves", "guy", "someone", "man",
                                                        "women", "boy", "girl", "child", "adult", "friend"]
                human_noun = (
                    prev_tag in ["NN", "NNS", "NNP"]
                    and prev_word_lower in human_keywords
                )
                if prev_tag in ["NN", "NNS", "NNP", "NNPS", "PRP", "PRP$"]:
                    if not human_pronoun and not human_noun and not is_human:
                        human_found = False
                    else:
                        if victim != is_human:
                            perp = is_human
                            perp_identify = is_human
                            victim_and_perp.append(perp)
                            human_found = True
                            break
                        else:
                            perp = prev_word
                            victim_and_perp.append(perp)
                            human_found = True
                            break
            if human_found == False:
                human_score -= 150
                        
        # Modal Word Detection
        if i > 0:
            prev_word, prev_tag = tags[i - 1]
            valid_victim = (
                prev_tag in ["NN", "NNS", "NNP", "NNPS", "PRP", "PRP$"]
                or prev_word.lower() in human_keywords
            )

            if valid_victim and tag == "MD":
                terms_verbs += 1

                if word.lower() in ["will", "'ll", "must"]:
                    intent_score += 25
                elif word.lower() in ["shall"]:
                    intent_score += 20
                elif word.lower() in ["could", "may", "might", "would"]:
                    intent_score += 15

    # Calculating Individual Scores
    related_memories = retrieve_memories(
        memory_list,
        victim,
        perp
    )

    # Adjusting Memory Weights
    norm_memory_weight = 0.4 * len(related_memories)/ (len(related_memories) + 20)
    norm_current_weight = 1.0 - norm_memory_weight

    if related_memories:
        score_one = sum(
            memory["sentiment"]
            for memory in related_memories
        ) / len(related_memories)
    else:
        score_one = 0

    score_two = calculate_score(norm_sentence)
    combined_evidence_score = (intent_score * evidence_weights["intent"]) + (danger_word_score * evidence_weights["danger"]) + (negation_score * evidence_weights["negation"]) + (human_score * evidence_weights["human"]) 

    # Scoring System
    total_score = 0
    if not related_memories:
        if combined_evidence_score > 0:
            total_score = (score_two + combined_evidence_score)
        else:
            total_score = score_two / 2
    elif combined_evidence_score > 0:
        total_score = (norm_memory_weight * score_one + norm_current_weight * score_two + combined_evidence_score)
    else:
        total_score = (norm_memory_weight * score_one + norm_current_weight * score_two) / 2
    total_score = max(0, min(total_score, 100))

    # Distance To Thresholds
    distance_to_relevant = abs(total_score - relevant_threshold)
    distance_to_irrelevant = abs(total_score - irrelevant_threshold)
    distance_to_null_threat = abs(total_score - null_threshold)

    if distance_to_relevant == min(
        distance_to_relevant,
        distance_to_irrelevant,
        distance_to_null_threat
    ):
        classification = "RELEVANT"
    elif distance_to_irrelevant == min(
         distance_to_relevant,
         distance_to_irrelevant,
         distance_to_null_threat
    ):
        classification = "IRRELEVANT"
    else:
        classification = "NULL_THREAT"

    typewriter_print(f"[CONFIDENCE SCORE]: {total_score:.3f}\n[CLASSIFICATION]: {classification}")

    # Person Of Interest SSN numbers
    if classification in ("RELEVANT", "IRRELEVANT"):
        if perp_identify is not None or victim_identify is not None:
            if victim_identify in ssn_registry:
                ssn_number = ssn_registry[victim_identify]
            elif perp_identify in ssn_registry:
                ssn_number = ssn_registry[perp_identify]
            else:
                area = random.randint(900, 999)
                group = random.randint(1, 99)
                serial = random.randint(1, 9999)
                ssn_number = f"{area}-{group:02d}-{serial:04d}"

                # Random SSN number generation        
                if victim_identify is not None and perp_identify is not None:
                    choice = random.randint(1, 2)
                    if choice == 1:
                        ssn_registry[victim_identify] = ssn_number
                        choice = 2
                    else:
                        ssn_registry[perp_identify] = ssn_number
                        choice = 1  
                elif victim_identify is not None:
                    ssn_registry[victim_identify] = ssn_number
                    choice = 2
                elif perp_identify is not None:
                    ssn_registry[perp_identify] = ssn_number
                    choice = 1
                else:
                    typewriter_print("[NOT ABLE TO DETECT PERPETRATOR OR VICTIM]")    

            typewriter_print(f"[SOCIAL SECURITY NUMBER]: {ssn_number}")
            
    # Feedback and updating weights
    feedback = typewriter_input("[WAS THE CLASSIFICATION WRONG? (Y/N)]: ").lower()
    if feedback == "y":
        correct_classification = typewriter_input(
            "[CORRECT CLASSIFICATION - "
            "RELEVANT / IRRELEVANT / NULL_THREAT]: "
        ).upper()
        learning_rate = large_learning_rate
    else:
        correct_classification = classification
        learning_rate = small_learning_rate

    target_scores = {
        "RELEVANT": relevant_threshold,
        "IRRELEVANT": irrelevant_threshold,
        "NULL_THREAT": null_threshold
    }

    target_score = target_scores.get(
        correct_classification,
        total_score
    )

    error = target_score - total_score
    error_normalized = error / 100

    feature_values = {
        "intent": intent_score,
        "danger": danger_word_score,
        "negation": negation_score,
        "human": human_score
    }

    for feature, value in feature_values.items():
        if value != 0:
            old_weight = evidence_weights[feature]
            direction = 1 if value > 0 else -1

            adjustment = (
                learning_rate
                * error_normalized
                * direction
            )

            evidence_weights[feature] += adjustment
            evidence_weights[feature] = max(
                min_weight,
                min(
                    evidence_weights[feature],
                    max_weight
                )
            )

            typewriter_print(
                f"[{feature.upper()} WEIGHT]: "
                f"{old_weight:.3f} -> "
                f"{evidence_weights[feature]:.3f}"
            )

    save_state()

    # Showing Reasoning behind Score
    typewriter_print("[ACCUMULATORS]\n\n")
    typewriter_print(f"[VICTIM]: {victim}")
    typewriter_print(f"[PERPETRATOR]: {perp}")
    typewriter_print(f"[COMBINED EVIDENCE]: {combined_evidence_score:.0f}")
    typewriter_print(f"[NEGATION ADJUSTMENT]: {negation_score:.0f}")
    typewriter_print(f"[INTENT EVIDENCE]: {intent_score:.0f}")
    typewriter_print(f"[DANGER EVIDENCE]: {danger_word_score:.0f}")
    typewriter_print(f"[PRONOUN EVIDENCE]: {human_score}")
    typewriter_print(f"[MEMORY SENTIMENT]: {score_one:.0f}")
    typewriter_print(f"[CURRENT SENTIMENT]: {score_two:.0f}")
    typewriter_print(f"[MEMORY WEIGHT]: {norm_memory_weight:.3f}")
    typewriter_print(f"[CURRENT WEIGHT]: {norm_current_weight:.3f}")
    current_time = datetime.now().strftime("%I:%M:%S")
    typewriter_print(f"[TIME]: {current_time}")

    # Saving Important Memories
    memory = {
        "text": norm_sentence, 
        "sentiment": score_two, 
        "intent_evidence": intent_score, 
        "danger_evidence": danger_word_score, 
        "negation": negation_score, 
        "pronoun adjustment": human_score, 
        "combined_total_evidence": combined_evidence_score, 
        "classification": correct_classification,
        "score": total_score,
        "victim": victim,
        "perp": perp,
        "time": current_time,
        
    }
    if total_score >= irrelevant_threshold:
        memory_list.append(memory)
        memory_cycle_counter += 1
    elif terms_verbs >= 1:
            memory_list.append(memory)
            memory_cycle_counter += 1

    # Keep memory list size capped within boundaries
    if len(memory_list) > memory_length:
        memory_list.pop(0)

    save_state()
