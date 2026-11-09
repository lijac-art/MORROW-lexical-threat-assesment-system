"""
MORROW: sarcasm detection + backward/forward subject detection.

Only temporary sentiment history is kept, because the original sarcasm detector
compares the current sentiment with recent sentiment. Nothing is written to disk.
Run normally to start MORROW, or run `python morrow_sarcasm.py --test`
to run the built-in tests.
"""

from __future__ import annotations

import sys
import unittest
from collections import deque

import nltk

try:
    import spacy
    from nltk.sentiment import SentimentIntensityAnalyzer
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install with: pip install spacy nltk\n"
        "Then install the spaCy model with: python -m spacy download en_core_web_md"
    ) from exc


MODEL_NAME = "en_core_web_md"
SUBJECT_DEPS = {"nsubj", "nsubjpass", "csubj", "csubjpass"}
HUMAN_PRONOUNS = {
    "i", "me", "we", "us", "you", "he", "him", "she", "her",
    "they", "them", "who", "someone", "somebody", "everyone",
}
HUMAN_NOUNS = {
    "person", "people", "man", "woman", "boy", "girl", "doctor",
    "nurse", "teacher", "police", "officer", "president", "leader",
    "minister", "king", "queen", "student", "worker", "driver",
}
SARCASM_CUES = {
    "yeah right", "sure", "totally", "just great", "great job",
    "what a genius", "brilliant", "lovely", "wonderful",
}
HISTORY_LIMIT = 20
SUBJECT_WINDOW = 5


def load_nlp():
    try:
        return spacy.load(MODEL_NAME)
    except OSError as exc:
        raise SystemExit(
            f"spaCy model '{MODEL_NAME}' is missing. Install it with:\n"
            f"python -m spacy download {MODEL_NAME}"
        ) from exc


class SarcasmDetector:
    """Uses VADER plus a small, temporary rolling sentiment baseline."""

    def __init__(self, analyzer, history_limit=HISTORY_LIMIT):
        self.analyzer = analyzer
        self.history = deque(maxlen=history_limit)

    def analyse(self, text: str) -> dict:
        scores = self.analyzer.polarity_scores(text)
        compound = float(scores["compound"])
        lower = text.lower()

        cue_found = any(cue in lower for cue in SARCASM_CUES)
        positive_words = float(scores.get("pos", 0.0))
        negative_words = float(scores.get("neg", 0.0))

        # A sharp change from recent sentiment is supporting evidence only.
        history_shift = False
        if self.history:
            baseline = sum(self.history) / len(self.history)
            history_shift = abs(compound - baseline) >= 0.65

        # Sarcasm is uncertain, so require a cue or a clear positive/negative
        # clash rather than treating every negative sentence as sarcastic.
        polarity_clash = positive_words >= 0.25 and negative_words >= 0.20
        detected = cue_found or (polarity_clash and history_shift)

        reason_parts = []
        if cue_found:
            reason_parts.append("sarcasm phrase detected")
        if polarity_clash:
            reason_parts.append("positive/negative sentiment clash")
        if history_shift:
            reason_parts.append("large shift from recent sentiment")
        reason = "; ".join(reason_parts) if reason_parts else "no strong sarcasm signal"

        self.history.append(compound)
        return {
            "sarcastic": detected,
            "compound": compound,
            "reason": reason,
        }


def detect_subjects(doc, window: int = SUBJECT_WINDOW) -> dict:
    """
    Find grammatical subjects on either side of their governing verb.

    spaCy's dependency parser identifies the grammatical relationship; the
    positional check labels a subject as backward (before its verb) or forward
    (after its verb). This handles both 'John hit Sam' and 'Sam was hit by John'
    when the parser assigns the relevant subject dependency.
    """
    backward = []
    forward = []
    all_subjects = []

    seen = set()
    for token in doc:
        if token.pos_ not in {"VERB", "AUX"}:
            continue

        # First use the parser's grammatical subject links.
        candidates = {
            child.i: child for child in token.children
            if child.dep_ in SUBJECT_DEPS and abs(child.i - token.i) <= window
        }

        # Also scan both sides of the verb. This preserves MORROW's original
        # backward/forward window behaviour for names, pronouns and person
        # nouns, including an object/person mentioned after the verb.
        for nearby in doc:
            if nearby.i == token.i or abs(nearby.i - token.i) > window:
                continue
            word = nearby.text.lower()
            is_person_candidate = (
                nearby.dep_ in SUBJECT_DEPS
                or getattr(nearby, "ent_type_", "") == "PERSON"
                or nearby.pos_ == "PROPN"
                or word in HUMAN_PRONOUNS
                or word in HUMAN_NOUNS
            )
            if is_person_candidate:
                candidates.setdefault(nearby.i, nearby)

        for subject in candidates.values():
            key = (subject.i, token.i)
            if key in seen:
                continue
            seen.add(key)
            item = {
                "text": subject.text,
                "verb": token.text,
                "dependency": subject.dep_,
            }
            if subject.i < token.i:
                backward.append(item)
            elif subject.i > token.i:
                forward.append(item)
            all_subjects.append(item)

    # Include standalone human pronouns/nouns only when spaCy marks them as
    # subjects. This avoids labelling every person mentioned as the subject.
    return {
        "backward": backward,
        "forward": forward,
        "subjects": all_subjects,
    }


def make_sentiment_analyzer():
    """Load VADER, downloading its small data file if it is not installed."""
    try:
        return SentimentIntensityAnalyzer()
    except LookupError:
        print("[SETUP] Downloading the NLTK VADER sentiment lexicon...")
        if not nltk.download("vader_lexicon", quiet=False):
            raise SystemExit(
                "Could not download VADER. Check your internet connection, then run: "
                "python -m nltk.downloader vader_lexicon"
            )
        return SentimentIntensityAnalyzer()


def main():
    nlp = load_nlp()
    detector = SarcasmDetector(make_sentiment_analyzer())

    print("[MORROW: SARCASM + SUBJECT DETECTION]")
    print("Type 'quit' to exit. Recent sentiment is kept only during this run.\n")

    while True:
        try:
            sentence = input("[INPUT]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[EXIT]")
            break

        if sentence.lower() in {"quit", "exit"}:
            print("[EXIT]")
            break
        if not sentence:
            continue

        doc = nlp(sentence)
        sarcasm = detector.analyse(sentence)
        subjects = detect_subjects(doc)

        print(f"[SARCASM]: {'DETECTED' if sarcasm['sarcastic'] else 'NOT DETECTED'}")
        print(f"[SENTIMENT]: {sarcasm['compound']:.3f}")
        print(f"[REASON]: {sarcasm['reason']}")
        print(f"[BACKWARD SUBJECTS]: {[s['text'] for s in subjects['backward']]}")
        print(f"[FORWARD SUBJECTS]: {[s['text'] for s in subjects['forward']]}")
        if not subjects["subjects"]:
            print("[SUBJECTS]: No grammatical subject found.")
        print()


# ---------------------------- Automatic tests ----------------------------

class FakeToken:
    def __init__(self, text, index, pos, dep=""):
        self.text = text
        self.i = index
        self.pos_ = pos
        self.dep_ = dep
        self.ent_type_ = ""
        self.children = []


class FakeDoc(list):
    pass


class FakeSentiment:
    def __init__(self, results):
        self.results = iter(results)

    def polarity_scores(self, text):
        return next(self.results)


class SarcasmAndSubjectTests(unittest.TestCase):
    def test_backward_subject(self):
        john = FakeToken("John", 0, "PROPN", "nsubj")
        hit = FakeToken("hit", 1, "VERB")
        hit.children.append(john)
        result = detect_subjects(FakeDoc([john, hit]))
        self.assertEqual([x["text"] for x in result["backward"]], ["John"])
        self.assertEqual(result["forward"], [])

    def test_forward_subject(self):
        sam = FakeToken("Sam", 2, "PROPN", "nsubj")
        arrive = FakeToken("arrived", 1, "VERB")
        arrive.children.append(sam)
        result = detect_subjects(FakeDoc([arrive, FakeToken("then", 0, "ADV"), sam]))
        self.assertEqual([x["text"] for x in result["forward"]], ["Sam"])

    def test_forward_person_candidate_after_verb(self):
        verb = FakeToken("helped", 1, "VERB")
        mary = FakeToken("Mary", 2, "PROPN")
        result = detect_subjects(FakeDoc([FakeToken("then", 0, "ADV"), verb, mary]))
        self.assertEqual([x["text"] for x in result["forward"]], ["Mary"])

    def test_subject_window(self):
        far_subject = FakeToken("John", 0, "PROPN", "nsubj")
        verb = FakeToken("hit", 8, "VERB")
        verb.children.append(far_subject)
        result = detect_subjects(FakeDoc([far_subject, verb]), window=5)
        self.assertEqual(result["subjects"], [])

    def test_sarcasm_phrase(self):
        analyzer = FakeSentiment([{"compound": 0.2, "pos": 0.3, "neg": 0.0}])
        result = SarcasmDetector(analyzer).analyse("Yeah right, that's brilliant.")
        self.assertTrue(result["sarcastic"])

    def test_no_automatic_sarcasm_for_plain_negative_sentence(self):
        analyzer = FakeSentiment([{"compound": -0.7, "pos": 0.0, "neg": 0.7}])
        result = SarcasmDetector(analyzer).analyse("I hate being sick.")
        self.assertFalse(result["sarcastic"])

    def test_history_is_temporary_and_bounded(self):
        analyzer = FakeSentiment([
            {"compound": 0.1, "pos": 0.1, "neg": 0.0},
            {"compound": 0.2, "pos": 0.1, "neg": 0.0},
            {"compound": 0.3, "pos": 0.1, "neg": 0.0},
        ])
        detector = SarcasmDetector(analyzer, history_limit=2)
        detector.analyse("Fine.")
        detector.analyse("Okay.")
        detector.analyse("Sure.")
        self.assertEqual(len(detector.history), 2)


def run_tests():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SarcasmAndSubjectTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    if "--test" in sys.argv:
        raise SystemExit(0 if run_tests() else 1)

    # Run the checks automatically before starting the interactive program.
    print("[SELF-TEST] Running MORROW checks before startup...")
    if not run_tests():
        raise SystemExit("[SELF-TEST FAILED] MORROW will not start.")
    main()