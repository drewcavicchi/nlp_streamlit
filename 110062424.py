import re
from collections import Counter
import streamlit as st
import random

def words(text): return re.findall(r'\w+', text.lower())

if "words" not in st.session_state:
    st.session_state['words'] = Counter(words(open('big.txt').read()))
WORDS = st.session_state['words']
def P(word, N=sum(WORDS.values())): 
    "Probability of `word`."
    return WORDS[word] / N

def correction(word, e3 = False): 
    "Most probable spelling correction for word."
    return max(candidates(word, e3), key=P)

def candidates(word, e3 = False): 
    "Generate possible spelling corrections for word."
    if e3:
        dist1_edits = edits1(word)
        dist2_edits = (e2 for e1 in dist1_edits for e2 in edits1(e1))
        dist3_edits = (e3 for e2 in dist2_edits for e3 in edits3(e2))
        return (known([word]) or known(dist1_edits) or known(dist2_edits) or known(dist3_edits) or [word])
    else:
        return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])

def known(words): 
    "The subset of `words` that appear in the dictionary of WORDS."
    return set(w for w in words if w in WORDS)

def edits1(word):
    "All edits that are one edit away from `word`."
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)

def edits2(word): 
    "All edits that are two edits away from `word`."
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))

def edits3(word):
    '''
    only allowing the following type of edits for distance 3:
    insert vowel next to another vowel
    replacement of a vowel for another vowel
    replacing close consonants c and s
    '''
    vowels = "aeiouy"
    splits = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    inserts = [L + c + R              for L, R in splits for c in vowels if (L in vowels) or (R in vowels)]
    replaces_v = [L + c + R[1:]           for L, R in splits if R for c in vowels if R[0] in vowels]
    replaces_cs = [L + c + R[1:]           for L, R in splits if R for c in "cs" if R[0] in "cs"]
    return set(inserts + replaces_cs + replaces_v)


def unit_tests():
    assert correction('speling') == 'spelling'              # insert
    assert correction('korrectud') == 'corrected'           # replace 2
    assert correction('bycycle') == 'bicycle'               # replace
    assert correction('inconvient') == 'inconvenient'       # insert 2
    assert correction('arrainged') == 'arranged'            # delete
    assert correction('peotry') =='poetry'                  # transpose
    assert correction('peotryy') =='poetry'                 # transpose + delete
    assert correction('word') == 'word'                     # known
    assert correction('quintessential') == 'quintessential' # unknown
    assert words('This is a TEST.') == ['this', 'is', 'a', 'test']
    assert Counter(words('This is a test. 123; A TEST this is.')) == (
           Counter({'123': 1, 'a': 2, 'is': 2, 'test': 2, 'this': 2}))
    # assert len(WORDS) == 32192
    # assert sum(WORDS.values()) == 1115504
    # assert WORDS.most_common(10) == [
    #  ('the', 79808),
    #  ('of', 40024),
    #  ('and', 38311),
    #  ('to', 28765),
    #  ('in', 22020),
    #  ('a', 21124),
    #  ('that', 12512),
    #  ('he', 12401),
    #  ('was', 11410),
    #  ('it', 10681)]
    # assert WORDS['the'] == 79808
    assert P('quintessential') == 0
    assert 0.07 < P('the') < 0.08
    return 'unit_tests pass'

def spelltest(tests, verbose=False, e3 = False):
    # if e3 is flagged, will include a restrained set of distance 3 correction candidates
    "Run correction(wrong) on all (right, wrong) pairs; report results."
    import time
    start = time.process_time()
    good, unknown = 0, 0
    n = len(tests)
    for right, wrong in tests:
        w = correction(wrong, e3)
        good += (w == right)
        if w != right:
            unknown += (right not in WORDS)
            if verbose:
                print('correction({}) => {} ({}); expected {} ({})'
                      .format(wrong, w, WORDS[w], right, WORDS[right]))
    dt = time.process_time() - start
    print('{:.0%} of {} correct ({:.0%} unknown) at {:.0f} words per second '
          .format(good / n, n, unknown / n, n / dt))
    
def Testset(lines):
    "Parse 'right: wrong1 wrong2' lines into [('right', 'wrong1'), ('right', 'wrong2')] pairs."
    return [(right, wrong)
            for (right, wrongs) in (line.split(':') for line in lines)
            for wrong in wrongs.split()]




# print(unit_tests())
# spelltest(Testset(open('development_set.txt')), e3=True) # Development set

example_list = [
    "bananna",
    "apple",
    "run",
    "kitten",
    "airplyne",
    "spellling",
    "sunday",
    "friendlee",
    "hapening",
    "random",
    "werd",
    "friendshipe",
    "ending",
    "lost",
    "excellent",
    "therefore",
    "seventeen",
    "currect",
    "word",
    "particular"]


st.title("Spellchecker Demo")
with st.sidebar:
    show_original_word = st.checkbox("Show original Word")

word = st.selectbox("Select a word:", example_list)
typed_word = st.text_input("or type your own word!")
if typed_word:
    word = typed_word
if show_original_word:
    st.markdown(f"original word: *{word}*")

word_correction = correction(word, e3 = True)
if word_correction == word:
    st.success(f"{word} is the correct spelling!" )
else:
    st.error(f"Correction: {word_correction}")
