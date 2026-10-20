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
import builtins
import spacy
from datetime import datetime

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
            print("[DEPENDENCIES FAILED TO LOAD INITIATING SHUTDOWN]")
            sys.exit()

# Importanting NLP dependencies
nlp = spacy.load("en_core_web_sm")

# Declaring Variables
danger = ["murder", "kill", "stab", "injure", "threaten", "hurt", "ammunition",
          "ammo", "explosives", "grenade", "bomb", "toxic", "gas", "poison",
          "radioactive", "weapon", "gun", "guns", "massacre", "kills",
          "killing", "shoot", "eliminate", "destroy"]
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
memory_list = []
sentiment_memory_list = []
min_weight = 0.05
max_weight = 0.65
small_learning_rate = 0.005
large_learning_rate = 0.1
memory_length = 50000
relevant_threshold = 80
irrelevant_threshold = 60
null_threshold = 25
norm_current_weight = 0.6
norm_memory_weight = 0.4
lookback_window = 5
negation_score = 0
human_score = 0
sentiment_memory_list = []
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
        print("[MEMORY LOADED SUCCESSFULLY]")
    except FileNotFoundError:
        print("[NO PREVIOUS MEMORY FOUND]")
    except json.JSONDecodeError:
        print("[MEMORY FILE CORRUPT - STARTING FRESH]")

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
            current_scores = -round(scores['pos'] * 35)
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
        new_calculated_score = -round(scores['pos'] * 35)
        sentiment_memory_list.append(new_calculated_score)
    elif scores['neg'] > scores['pos']:
        new_calculated_score = round(scores['neg'] * 110)
        sentiment_memory_list.append(new_calculated_score)
    else:
        return scores['compound']
    difference = abs(new_calculated_score - previous_score)
    if difference >= 25 and None not in (victim, perp):
        new_calculated_score *= -0.5
        sentiment_memory_list.append(new_calculated_score)
        return new_calculated_score
    return new_calculated_score

# Welcoming User
print("[MORROW]:\n")
print("[THREAT ANALYSIS ENGINE]")
print("[VERSION: 0.8.8]")

# Memory Loading
sia = SentimentIntensityAnalyzer()
def retrieve_memories(memory_list, victim, perp):
    if not victim and not perp:
        return []
    return [
        memory
        for memory in memory_list
        if memory["victim"] == victim and memory["victim"] is not None
        and memory["perp"] == perp and memory["perp"] is not None
        
    ]

# Shutdown Sequence 
def shutdown_sequence():
    request = input("[0 TO CONTINUE OPERATIONS, 1 TO INITIATE SHUTDOWN]: ")
    if request == "1":
        delay = round(random.uniform(5, 10))
        print("[INITIATING ATEXIT]")
        time.sleep(delay/3)
        print("[TERMINATING INSTANCES]")
        time.sleep(delay/3)
        print("[PURGING MEMORY HEAP]")
        time.sleep(delay/3)
        print("[BEGINGING JSON SERALIZATION]")
        save_state()
        sys.exit(0)

    print("[CONTINUING OPERATIONS]")

load_state()

while True:
    terms_verbs = 0
    intent_score = 0
    negation_score = 0
    danger_word_score = 0
    human_score = 0
    victim = None
    perp = None  
    current_time = datetime.now().strftime("%I:%M %p")
    shutdown_sequence()

    # Inputting Text
    norm_sentence = input("[I/O STREAM INPUT]: ")
    doc = nlp(norm_sentence)
    punctuation = str.maketrans("", "", ".,?!:" + "0123456789")
    new_sentence = norm_sentence.translate(punctuation)
    tokenized_new_sentence = word_tokenize(new_sentence)
    tags = nltk.pos_tag(tokenized_new_sentence)
    pronouns = [word for word, pos in tags if pos in ('PRP', 'PRP$')]
    entities = ne_chunk(tags)

    for i, (word, tag) in enumerate(tags):
        if word.lower() in danger:
            danger_word_score = min(danger_word_score + 40, 100)

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
                    negation_score -= 40

            # Non-Human Forward Subject Handling
            end_index = min(len(tags), i + 1 + lookback_window)
            for next_idx in range(i + 1, end_index):
                prev_word, prev_tag = tags[next_idx]
                is_human = False
                for chunk in entities:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        full_name = is_human = " ".join([leaf[0] for leaf in chunk.leaves()])
                        if prev_word in full_name:
                            is_human = full_name
                            break
                    else:
                        is_human = False
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                human_pronoun = prev_word_lower in ["she", "her", "he", "him", "us", "them", "mine", "you", "his", "our", "their", "guy", "someone", "anyone", "everyone", "boy", "girl", "women", "man", "child", "adult", "friend"]
                human_noun = (
                    prev_tag in ["NN", "NNS", "NNP"]
                    and prev_word_lower in human_keywords
                )
                if prev_tag in ["NN", "NNS", "NNP", "NNPS", "PRP", "PRP$"]:
                    if not human_pronoun and not human_noun and not is_human:
                        human_score -= 60
                        break
                    else:
                        if is_human == False:
                            victim = prev_word
                            break
                        else:
                            victim = is_human
                            break

            # Non-Human Backward Subject Handling      
            for next_idx in range(i - 1, max(-1, i - 1 - lookback_window), -1):
                is_human = False
                prev_word, prev_tag = tags[next_idx]
                for chunk in entities:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        full_name = is_human = " ".join([leaf[0] for leaf in chunk.leaves()])
                        if prev_word in full_name:
                            is_human = full_name
                            break
                    else:
                        is_human = False
                prev_word, prev_tag = tags[next_idx]
                prev_word_lower = prev_word.lower()
                human_pronoun = prev_word_lower in ["i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself",
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
                        human_score -= 60
                        break
                    else:
                        if is_human == False:
                            perp = prev_word
                            break
                        else:
                            perp = is_human
                            break

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
                    intent_score += 20
                elif word.lower() in ["shall"]:
                    intent_score += 15
                elif word.lower() in ["could", "may", "might", "would"]:
                    intent_score += 5

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

    print(f"[CONFIDENCE SCORE]: {total_score}\n[CLASSIFICATION]: {classification}")
    if classification in ("RELEVANT", "IRRELEVANT"):
        area =  random.randint(900,999)
        group = random.randint(1,99)
        serial = random.randint(1, 9999)
        print(f"[NUMBER]: {area:03d}-{group:02d}-{serial:04d}") 
    feedback = input("[WAS THE CLASSIFICATION WRONG? (Y/N)]: ").strip().lower()

    if feedback == "y":
        correct_classification = input(
            "[CORRECT CLASSIFICATION - "
            "RELEVANT / IRRELEVANT / NULL_THREAT]: "
        ).strip().upper()

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

            print(
                f"[{feature.upper()} WEIGHT]: "
                f"{old_weight:.3f} -> "
                f"{evidence_weights[feature]:.3f}"
            )
            
    save_state()

    # Showing Reasoning behind Score
    print("[ACCUMULATORS]", end="\n\n")
    print(f"[VICTIM]: {victim}")
    print(f"[PERPETRATOR]: {perp}")
    print(f"[COMBINED EVIDENCE]: {combined_evidence_score:.0f}")
    print(f"[NEGATION ADJUSTMENT]: {negation_score:.0f}")
    print(f"[INTENT EVIDENCE]: {intent_score:.0f}")
    print(f"[DANGER EVIDENCE]: {danger_word_score:.0f}")
    print(f"[PRONOUN EVIDENCE]: {human_score}")
    print(f"[MEMORY SENTIMENT]: {score_one:.0f}")
    print(f"[CURRENT SENTIMENT]: {score_two:.0f}")
    print(f"[MEMORY WEIGHT]: {norm_memory_weight:.3f}")
    print(f"[CURRENT WEIGHT]: {norm_current_weight:.3f}")
    print(f"[TIME]: {current_time}")

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
        "time": current_time
        
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