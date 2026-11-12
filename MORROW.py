# Importing Necessary Libraries
import nltk
import time
import random
import sys
import json
import threading
from pathlib import Path
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from nltk import ne_chunk
from nltk.tree import Tree
import spacy
from datetime import datetime

# Declaring Constant Variables, Lists, Dictonaries, and Dependencies
MATRIX_STYLE = "\033[0;38;2;51;255;51m"
RESET = "\033[0m"
MIN_WEIGHT = 0.05
MAX_WEIGHT = 0.65
SMALL_LEARNING_RATE = 0.005
LARGE_LEARNING_RATE = 0.1
RELEVANT_THRESHOLD = 80
IRRELEVANT_THRESHOLD = 60
NULL_THRESHOLD = 20
NORM_CURRENT_WEIGHT = 0.6
NORM_MEMORY_WEIGHT = 0.4
LOOKBACK_WINDOW = 5
AREA = random.randint(900, 999)
GROUP = random.randint(1, 99)
SERIAL = random.randint(1, 9999)
DANGER = ["murder", "kill", "stab", "injure", "threat", "hurt", "ammunition",
          "ammo", "explosives", "grenade", "bomb", "toxic", "gas", "poison",
          "radioactive", "weapon", "gun", "guns", "massacre",
          "shoot", "eliminate", "destroy", "threaten"]
NEGATION_WORDS = ["no", "not", "never", "n't"]
HUMAN_KEYWORDS = ["human", "person", "people", "individual", "president", 
                  "leader", "counsel", "minister", "king", "monarch", 
                  "governor", "senator", "mayor"]
NLP = spacy.load("en_core_web_md")

# Declaring Standard Variables, Lists, Dictonaries, and Dependencies
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
negation_score = 0
human_score = 0
current_scores = 0
memory_cycle_counter = 0
perp_identity = None
victim_identity = None

# Print Typewriter effect
def typewriter_print(text, delay=0.03):
    print(MATRIX_STYLE, end="", flush=True)
    for char in text:
        print(char, end="", flush=True) 
        time.sleep(delay) 
    print(RESET)

# Input Typewriter effect
def typewriter_input(text, delay=0.03):
    print(MATRIX_STYLE, end="", flush=True)
    for char in text:
        print(char, end="", flush=True) 
        time.sleep(delay)
    user_input = input(MATRIX_STYLE)
    print(f"{RESET}", end="")
    return user_input

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
    ('corpora','omw-1.4'),
    ('corpora','wordnet')
]
for category, package in nltk_packages:
    try:
        nltk.data.find(f"{category}/{package}")
    except LookupError:
        try:
            nltk.download(package, quiet=True)
        except OSError:
            typewriter_print("[DEPENDENCIES FAILED TO LOAD INITIATING SHUTDOWN]")
            sys.exit(11)

# Print Typewriter effect
def typewriter_print(text, delay=0.03, end="\n"):
    print(MATRIX_STYLE, end="", flush=True)
    for char in text:
        print(char, end="", flush=True) 
        time.sleep(delay) 
    print(RESET, end=end)

# Input Typewriter effect
def typewriter_input(text, delay=0.03, end="\n"):
    print(MATRIX_STYLE, end="", flush=True)
    for char in text:
        print(char, end="", flush=True) 
        time.sleep(delay)
    user_input = input(MATRIX_STYLE)
    print(f"{RESET}", end=end)
    return user_input

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
    ('corpora','omw-1.4'),
    ('corpora','wordnet')
]
for category, package in nltk_packages:
    try:
        nltk.data.find(f"{category}/{package}")
    except LookupError:
        try:
            nltk.download(package, quiet=True)
        except OSError:
            typewriter_print("[DEPENDENCIES FAILED TO LOAD INITIATING SHUTDOWN]")
            sys.exit(11)

# Save File Setup
STATE_FILE = Path(__file__).with_name("MORROW_MEMORY.json")
def load_state():
    global memory_list, evidence_weights
    global NORM_MEMORY_WEIGHT, NORM_CURRENT_WEIGHT, memory_cycle_counter
    global sentiment_memory_list, ssn_registry
    try:
        with open(STATE_FILE, "r") as file:
            state = json.load(file)

        memory_list = state.get("memory_list", [])
        evidence_weights = {
            **evidence_weights,
            **state.get("evidence_weights", {})
        }
        NORM_MEMORY_WEIGHT = state.get("norm_memory_weight", NORM_MEMORY_WEIGHT)
        NORM_CURRENT_WEIGHT = state.get("norm_current_weight", NORM_CURRENT_WEIGHT)
        memory_cycle_counter = state.get("memory_cycle_counter", memory_cycle_counter)
        sentiment_memory_list = state.get("sentiment_memory_list", sentiment_memory_list)
        ssn_registry = state.get("ssn_registry", ssn_registry)
        typewriter_print("[MEMORY LOADED SUCCESSFULLY]")
    except FileNotFoundError:
        typewriter_print("[NO PREVIOUS MEMORY FOUND]")
    except json.JSONDecodeError:
        typewriter_print("[MEMORY FILE CORRUPT - STARTING FRESH]")

def save_state():
    # Do not recreate an empty JSON file immediately after midnight cleanup.
    default_weights = {
        "intent": 0.15,
        "danger": 0.40,
        "negation": 0.25,
        "human": 0.20
    }
    has_saved_data = (
        bool(memory_list)
        or bool(sentiment_memory_list)
        or bool(ssn_registry)
        or memory_cycle_counter != 0
        or evidence_weights != default_weights
        or NORM_MEMORY_WEIGHT != 0.4
        or NORM_CURRENT_WEIGHT != 0.6
    )
    if not has_saved_data:
        return

    state = {
        "memory_list": memory_list,
        "evidence_weights": evidence_weights,
        "norm_memory_weight": NORM_MEMORY_WEIGHT,
        "norm_current_weight": NORM_CURRENT_WEIGHT,
        "memory_cycle_counter": memory_cycle_counter,
        "sentiment_memory_list": sentiment_memory_list,
        "ssn_registry": ssn_registry
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)

# Sentiment Scoring
def calculate_score(text):
    scores = sia.polarity_scores(text)
    if not sentiment_memory_list:
        if scores['pos'] > scores['neg']:
            current_scores = -round(scores['pos'] * 45)
            sentiment_memory_list.append(current_scores)
            return current_scores
        elif scores['neg'] > scores['pos']:
            current_scores = round(scores['neg'] * 130)
            sentiment_memory_list.append(current_scores)
            return current_scores
        else:
            return scores['compound']
        
# Sarcasm Detection
    average_score = sum(sentiment_memory_list) / len(sentiment_memory_list)
    if scores['pos'] > scores['neg']:
        new_calculated_score = -round(scores['pos'] * 45)
        sentiment_memory_list.append(new_calculated_score)
    elif scores['neg'] > scores['pos']:
        new_calculated_score = round(scores['neg'] * 130)
        sentiment_memory_list.append(new_calculated_score)
    else:
        return scores['compound']
    difference = abs(new_calculated_score - average_score)
    if difference >= 50:
        if perp in victim_and_perp or victim in victim_and_perp and victim is not None or perp is not None:
            new_calculated_score *= -0.8
            sentiment_memory_list.append(new_calculated_score)
            return new_calculated_score
    return new_calculated_score

# Welcoming User
typewriter_print("[MORROW]:\n")
typewriter_print("[THREAT ANALYSIS ENGINE]")
typewriter_print("[VERSION: 1.0.0]")

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
        clock_stop.set()
        clock_thread.join(timeout=2)
        typewriter_print("[SYSTEM SHUTDOWN WITH CODE 0]")
        sys.exit(0)

    typewriter_print("[CONTINUING OPERATIONS]")
load_state()

# Midnight Memory Reset
clock_stop = threading.Event()
last_cleanup_date = datetime.now().date()

def delete_daily_memories():
    """Clear all saved memory and delete MORROW_MEMORY.json at midnight."""
    global memory_cycle_counter, sentiment_memory_list, ssn_registry
    global evidence_weights, NORM_CURRENT_WEIGHT, NORM_MEMORY_WEIGHT

    memory_list.clear()
    sentiment_memory_list.clear()
    ssn_registry.clear()
    memory_cycle_counter = 0
    evidence_weights = {
        "intent": 0.15,
        "danger": 0.40,
        "negation": 0.25,
        "human": 0.20
    }
    NORM_CURRENT_WEIGHT = 0.6
    NORM_MEMORY_WEIGHT = 0.4

    try:
        STATE_FILE.unlink()
        typewriter_print("\n[MIDNIGHT CLEANUP: MORROW_MEMORY.JSON DELETED]")
    except FileNotFoundError:
        typewriter_print("\n[MIDNIGHT CLEANUP: MEMORY CLEARED; JSON FILE ALREADY ABSENT]")
    except OSError as error:
        typewriter_print(f"\n[MIDNIGHT CLEANUP ERROR: {error}]")

def background_clock():
    global last_cleanup_date
    while not clock_stop.is_set():
        now = datetime.now()

        # Detect Day Change
        if now.date() != last_cleanup_date:
            delete_daily_memories()
            last_cleanup_date = now.date()

        current_time = now.strftime("%H:%M:%S")
        sys.stdout.write("\033[s")
        sys.stdout.write(f"\033[1;60H\033[K\033[93m[ {current_time} ]\033[0m")
        sys.stdout.write("\033[u")
        sys.stdout.flush()
        clock_stop.wait(1)

clock_thread = threading.Thread(target=background_clock, daemon=True)
clock_thread.start()

while True:
    victim_and_perp.clear()
    verbs = 0
    intent_score = 0
    negation_score = 0
    danger_word_score = 0
    human_score = 0
    human_found = False
    full_name = None
    victim = None
    perp = None
    victim_identity = None
    perp_identity = None
    is_human = False
    danger_word_found = False

    shutdown_sequence()

    # Inputting Text
    norm_sentence = typewriter_input("[I/O STREAM INPUT]: ")

    # Tokenization 
    punctuation = str.maketrans("", "", ".,?!:" + "0123456789")
    new_sentence = norm_sentence.translate(punctuation)
    doc = NLP(new_sentence)
    tokenized_new_sentence = word_tokenize(new_sentence)
    words = new_sentence.split()
    tags = nltk.pos_tag(tokenized_new_sentence)
    spacy_tags = [(token.text, token.tag_) for token in doc]
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    entities = ne_chunk(tags)
    HUMAN_PRONOUN = []

    # Pronoun and Human Detection
    person_synset = wn.synset("person.n.01")
    for word in words:
        for syn in wn.synsets(word, pos=wn.NOUN):
            if any(person_synset in path for path in syn.hypernym_paths()):
                HUMAN_KEYWORDS.append(word.lower())
                break
    for token in doc:
        if token.lemma_.lower() in DANGER:
            danger_word_score = min(danger_word_score + 80, 240)
            danger_word_found = True
            for child in token.children:
                if child.dep_ in ("nsubj", "csubj"):
                    HUMAN_PRONOUN.append(child.text.lower())
                elif child.dep_ in ("dobj", "obj"):
                    HUMAN_PRONOUN.append(child.text.lower())
                elif token.dep_ == "pobj" and token.head.text.lower() == "as":
                    HUMAN_PRONOUN.append(token.head.head.text.lower())
    for i, (word, tag) in enumerate(tags):
        if danger_word_found and doc[i].lemma_.lower() in DANGER:

            # Negation Handling
            start_index = max(0, i - LOOKBACK_WINDOW)
            negation_word = 0
            for prev_idx in range(i - 1, start_index - 1, -1):
                prev_token = doc[prev_idx] 
                prev_word = spacy_tags[prev_idx][0].lower()
                if prev_word in NEGATION_WORDS:
                    negation_word += 1
                    if negation_word % 2 != 0:
                        parent_word = doc[i].head 
                        if parent_word.pos_ == "VERB":
                            negation_score -= 30

            # Non-Human Forward Subject Handling (Victim Check)
            human_found = False
            end_index = min(len(tags), i + 1 + LOOKBACK_WINDOW)
            for next_idx in range(i + 1, end_index):
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                for chunk in entities:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        name_parts = [leaf[0] for leaf in chunk.leaves()]
                        full_name = " ".join(name_parts)
                        if prev_word_lower not in [part.lower() for part in name_parts]:
                            continue
                        if full_name == perp:
                            continue
                        is_human = full_name
                        break
                if persons:
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            full_name = ent.text 
                            name_parts = [token.text for token in ent]
                            if prev_word_lower not in [part.lower() for part in name_parts]:
                                continue
                            if full_name == perp:
                                continue
                            is_human = full_name
                            break
                        else:
                            is_human = False
                    else:
                        is_human = False
                prev_word, prev_tag = tags[next_idx]
                human_noun = (
                    prev_tag in ["NN", "NNS", "NNP"]
                    and prev_word_lower in HUMAN_KEYWORDS
                )
                if prev_tag in ["NN", "NNS", "NNP", "NNPS", "PRP", "PRP$"]:
                    if prev_word_lower not in HUMAN_PRONOUN and not human_noun and not is_human:
                        human_found = False
                    else:
                        if is_human and is_human != perp:
                            victim = is_human
                            victim_identity = is_human
                            victim_and_perp.append(victim)
                            human_found = True
                            break
                        elif (prev_word_lower in HUMAN_PRONOUN or human_noun) and prev_word_lower != str(perp).lower():
                            victim = prev_word
                            if prev_tag in ["NNP", "NNPS"]:
                                if full_name:
                                    victim_identity = full_name 
                                else: 
                                    victim_identity = None
                            else: 
                                victim_identity = None
                            victim_and_perp.append(victim)
                            human_found = True
                            break
                        elif prev_word_lower == str(perp).lower():
                            victim = prev_word
                            victim_and_perp.append(victim)
                            human_found = True
                            break
            if not human_found:
                human_score -= 120
                human_found = False

            # Non-Human Backward Subject Handling (Perp Check)
            human_found = False
            for next_idx in range(i - 1, max(-1, i - 1 - LOOKBACK_WINDOW), -1):
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                for chunk in entities:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        name_parts = [leaf[0] for leaf in chunk.leaves()]
                        full_name = " ".join(name_parts)
                        if prev_word_lower not in [part.lower() for part in name_parts]:
                            continue
                        if full_name == victim:
                            continue
                        is_human = full_name
                        break
                if persons:
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            full_name = ent.text 
                            name_parts = [token.text for token in ent]
                            if prev_word_lower not in [part.lower() for part in name_parts]:
                                continue
                            if full_name == perp:
                                continue
                            is_human = full_name
                            break
                        else:
                            is_human = False
                    else:
                        is_human = False
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                human_noun = (
                    prev_tag in ["NN", "NNS", "NNP"]
                    and prev_word_lower in HUMAN_KEYWORDS
                )
                if prev_tag in ["NN", "NNS", "NNP"  , "NNPS", "PRP", "PRP$"]:
                    if prev_word_lower not in HUMAN_PRONOUN and not human_noun and not is_human:
                        human_found = False
                    else:
                        if is_human and str(victim).lower() != str(is_human).lower():
                            perp = is_human
                            perp_identity = is_human
                            victim_and_perp.append(perp)
                            human_found = True
                            break
                        elif (prev_word_lower in HUMAN_PRONOUN or human_noun) and prev_word_lower != str(victim).lower():
                            perp = prev_word
                            if prev_tag in ["NNP", "NNPS"]:
                                if full_name:
                                    perp_identity = full_name 
                                else:
                                    perp_identity = full_name
                            else: 
                                perp_identity = None
                            victim_and_perp.append(perp)
                            human_found = True
                            break
                        elif prev_word_lower == str(victim).lower():
                            perp = prev_word
                            victim_and_perp.append(perp)
                            human_found = True
                            break
            if not human_found:
                human_score -= 120
                human_found = False
                            
        # Modal Word Detection
        if i > 0:
            prev_word, prev_tag = tags[i - 1]
            valid_victim = (
                prev_tag in ["NN", "NNS", "NNP", "NNPS", "PRP", "PRP$"]
                or prev_word.lower() in HUMAN_KEYWORDS
                )
            if valid_victim and tag == "MD":
                verbs += 1

                if word.lower() in ["will", "'ll", "must"]:
                    intent_score += 30
                elif word.lower() in ["shall"]:
                    intent_score += 25
                elif word.lower() in ["could", "may", "might", "would"]:
                    intent_score += 20

    # Calculating Individual Scores
    related_memories = retrieve_memories(
        memory_list,
        victim,
        perp
    )

    # Adjusting Memory Weights
    NORM_MEMORY_WEIGHT = 0.4 * len(related_memories)/ (len(related_memories) + 20)
    NORM_CURRENT_WEIGHT = 1.0 - NORM_MEMORY_WEIGHT
    if related_memories:
        memory_sentiment_score = sum(
            memory["sentiment"]
            for memory in related_memories
        ) / len(related_memories)
    else:
        memory_sentiment_score = 0
    sentiment_score = calculate_score(norm_sentence)
    combined_evidence_score = (intent_score * evidence_weights["intent"]) + (danger_word_score * evidence_weights["danger"]) + (negation_score * evidence_weights["negation"]) + (human_score * evidence_weights["human"]) 

    # Scoring System
    total_score = 0
    if not related_memories:
        if combined_evidence_score > 0:
            total_score = (sentiment_score + combined_evidence_score)
        else:
            total_score = sentiment_score / 2
    elif combined_evidence_score > 0:
        total_score = (NORM_MEMORY_WEIGHT * memory_sentiment_score + NORM_CURRENT_WEIGHT * sentiment_score + combined_evidence_score)
    else:
        total_score = (NORM_MEMORY_WEIGHT * memory_sentiment_score + NORM_CURRENT_WEIGHT * sentiment_score) / 2
    total_score = max(0, min(total_score, 100))

    # Distance To Thresholds
    distance_to_relevant = abs(total_score - RELEVANT_THRESHOLD)
    distance_to_irrelevant = abs(total_score - IRRELEVANT_THRESHOLD)
    distance_to_null_threat = abs(total_score - NULL_THRESHOLD)
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
    typewriter_print(f"[CONFIDENCE SCORE]: {total_score:.3f}%\n[CLASSIFICATION]: {classification}")

    # Person Of Interest SSN numbers
    if classification in ("RELEVANT", "IRRELEVANT"):
        if perp_identity is not None or victim_identity is not None:
            if victim_identity in ssn_registry:
                ssn_number = ssn_registry[victim_identity]
            elif perp_identity in ssn_registry:
                ssn_number = ssn_registry[perp_identity]
            else:
                ssn_number = f"{AREA}-{GROUP:02d}-{SERIAL:04d}"

                # Random SSN number generation        
                if None not in (victim_identity, perp_identity):
                    choice = random.randint(1, 2)
                    if choice == 1:
                        ssn_registry[victim_identity] = ssn_number
                        choice = 2
                    else:
                        ssn_registry[perp_identity] = ssn_number
                        choice = 1  
                elif victim_identity is not None:
                    ssn_registry[victim_identity] = ssn_number
                    choice = 2
                elif perp_identity is not None:
                    ssn_registry[perp_identity] = ssn_number
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
        learning_rate = LARGE_LEARNING_RATE
    else:
        correct_classification = classification
        learning_rate = SMALL_LEARNING_RATE
    target_scores = {
        "RELEVANT": RELEVANT_THRESHOLD,
        "IRRELEVANT": IRRELEVANT_THRESHOLD,
        "NULL_THREAT": NULL_THRESHOLD
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
                MIN_WEIGHT,
                min(
                    evidence_weights[feature],
                    MAX_WEIGHT
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
    typewriter_print(f"[HUMAN EVIDENCE]: {human_score}")
    typewriter_print(f"[MEMORY SENTIMENT]: {memory_sentiment_score:.0f}")
    typewriter_print(f"[CURRENT SENTIMENT]: {sentiment_score:.0f}")
    typewriter_print(f"[MEMORY WEIGHT]: {NORM_MEMORY_WEIGHT:.3f}")
    typewriter_print(f"[CURRENT WEIGHT]: {NORM_CURRENT_WEIGHT:.3f}")
        
    # Saving Important Memories
    memory = {
        "text": norm_sentence, 
        "sentiment": sentiment_score, 
        "intent_evidence": intent_score, 
        "danger_evidence": danger_word_score, 
        "negation": negation_score, 
        "pronoun adjustment": human_score, 
        "combined_total_evidence": combined_evidence_score, 
        "classification": correct_classification,
        "score": total_score,
        "victim": victim,
        "perp": perp,
        
    }
    if total_score >= IRRELEVANT_THRESHOLD:
        memory_list.append(memory)
        memory_cycle_counter += 1
    elif verbs >= 1 and victim or perp:
            memory_list.append(memory)
            memory_cycle_counter += 1
    save_state()