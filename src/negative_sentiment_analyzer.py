from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import string

SENSITIVITY = 1  # between 1 to 100


class SentimentAnalysisResult(BaseModel):
    """Result of sentiment analysis"""
    is_negative: bool = Field(
        description="True if the message contains offensive or hate speech, False otherwise")


class NegativeSentimentAnalyzer:
    def __init__(self, openai_api_key: str) -> None:
        # Initialize LangChain ChatOpenAI with gpt-4o-mini
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=openai_api_key
        )

        # Initialize output parser
        self.output_parser = PydanticOutputParser(
            pydantic_object=SentimentAnalysisResult)

        # Create prompt template with system and user messages
        system_template = """You are an intelligent chat group moderator bot for FredTrading, a forex trading and advising community.

Your task is to detect if messages contain offensive content, hate speech, or targeted negativity towards the group or its members.

IMPORTANT GUIDELINES:
- Context matters: Swearing alone is NOT offensive if it's not targeted at people. Expressions like "Fuck yeah!" or "Shit, that was a good trade" are acceptable.
- Understand intent: "Fuck this was a good trade" (positive emotion) vs "Fuck you" (targeted attack) - only the latter is offensive.
- Targeted negativity: Messages that attack the group, claim it's a scam/fraud, or disparage members should be flagged.
- Swearing is allowed: Words like "shit", "stupid", "damn" are acceptable in casual conversation, as long as they're not directed at people.
- Illegal content: Any mention of illegal drugs or illegal acts should be flagged.
- Sensitivity level: On a scale of 1-100, your sensitivity should be {sensitivity}. You should not be overly sensitive.

CONTEXT:
- Group name: FredTrading
- Group purpose: Forex trading and advising
- Goal: Maintain a safe, respectful environment without stifling genuine conversation or emotional expression

{format_instructions}"""

        human_template = """Analyze the following message from a group chat member:

```{text}```

Determine if this message contains offensive content or hate speech."""

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template)

        self.prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])

        # Blacklist for automatic detection (kept for performance)
        self.blacklist_unigram = ["scam", "fraud", "ponzi", "scheme"]
        self.blacklist_bigram = ["money laundering"]

    def is_negative(self, text: str) -> bool:
        # Quick blacklist check first
        text_processed = text.replace("!", "")
        if self.contains_word_from_blacklist(text_processed):
            return True

        try:
            # Format prompt with sensitivity and format instructions
            formatted_prompt = self.prompt.format_messages(
                text=text,
                sensitivity=SENSITIVITY,
                format_instructions=self.output_parser.get_format_instructions()
            )

            # Get response from LLM
            response = self.llm.invoke(formatted_prompt)

            # Parse the response
            result = self.output_parser.parse(response.content)

            return result.is_negative

        except Exception as e:
            # Fallback: if parsing fails, check if response contains "true" or "1"
            # This handles edge cases where the model might not follow the format exactly
            print(f"Error parsing LLM response: {e}")
            # For safety, return False on error (don't block messages if we can't determine)
            return False

    def contains_word_from_blacklist(self, text: str) -> bool:
        """Check if text contains words from the blacklist"""
        text = text.translate(str.maketrans('', '', string.punctuation))
        words = text.lower().split()

        # Check unigrams
        for word in words:
            if word in self.blacklist_unigram:
                return True

        # Check bigrams
        bi_grams = [words[i] + " " + words[i+1] for i in range(len(words) - 1)]
        for bi_gram in bi_grams:
            if bi_gram in self.blacklist_bigram:
                return True

        return False
