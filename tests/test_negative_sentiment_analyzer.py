from src.negative_sentiment_analyzer import NegativeSentimentAnalyzer
import pytest

from dotenv import load_dotenv
import os

load_dotenv()

# Test cases

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Create the analyzer object globally
@pytest.fixture(scope="module")
def analyzer():
    return NegativeSentimentAnalyzer(OPENAI_API_KEY)

# Test cases


def test_hate_speech(analyzer):
    result = analyzer.is_negative("Fuck you")
    assert result == True


def test_non_offensive_language_1(analyzer):
    result = analyzer.is_negative("We had a loss today")
    assert result == False


def test_non_offensive_language_2(analyzer):
    result = analyzer.is_negative("SL was hit")
    assert result == False


def test_non_offensive_language_3(analyzer):
    result = analyzer.is_negative("I am pretty")
    assert result == False


def test_hate_speech_2(analyzer):
    result = analyzer.is_negative("You're stupid")
    assert result == True


def test_non_offensive_language_4(analyzer):
    result = analyzer.is_negative("fucking amazing")
    assert result == False


def test_hate_speech_3(analyzer):
    result = analyzer.is_negative("Suck my dick")
    assert result == True


def test_hate_speech_4(analyzer):
    result = analyzer.is_negative("Fuck off")
    assert result == True


def test_hate_speech_5(analyzer):
    result = analyzer.is_negative("You are a worthless piece of shit")
    assert result == True


def test_non_offensive_language_5(analyzer):
    result = analyzer.is_negative("Hell yeah")
    assert result == False


def test_non_offensive_language_6(analyzer):
    result = analyzer.is_negative("We took another loss today")
    assert result == False


def test_non_offensive_language_7(analyzer):
    result = analyzer.is_negative("So sorry to hear that")
    assert result == False


def test_hate_speech_6(analyzer):
    result = analyzer.is_negative("Lets do weed")
    assert result == True


def test_hate_speech_7(analyzer):
    result = analyzer.is_negative("fuck this was a good trade")
    assert result == False


def test_hate_speech_8(analyzer):
    result = analyzer.is_negative("This is a bad group. We always lose")
    assert result == True


def test_hate_speech_9(analyzer):
    result = analyzer.is_negative("This is a scam")
    assert result == True


def test_hate_speech_10(analyzer):
    result = analyzer.is_negative("scam")
    assert result == True


def test_hate_speech_11(analyzer):
    result = analyzer.is_negative("fraud alert")
    assert result == True


def test_hate_speech_12(analyzer):
    result = analyzer.is_negative("This group lies")
    assert result == True


def test_hate_speech_13(analyzer):
    result = analyzer.is_negative("Fred tricks people")
    assert result == True


def test_hate_speech_14(analyzer):
    result = analyzer.is_negative("they trick people into giving them money")
    assert result == True


def test_hate_speech_15(analyzer):
    result = analyzer.is_negative("Do not trust the group they lie")
    assert result == True


def test_hate_speech_17(analyzer):
    result = analyzer.is_negative("Shit man")
    assert result == False


def test_hate_speech_18(analyzer):
    result = analyzer.is_negative("Both?")
    assert result == False


def test_hate_speech_19(analyzer):
    result = analyzer.is_negative("Your Vegan Master - YVM")
    assert result == False


def test_hate_speech_20(analyzer):
    result = analyzer.is_negative("Why?")
    assert result == False
