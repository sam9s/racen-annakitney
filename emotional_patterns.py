"""
Emotional Pattern Mapping System for SOMERA

This module defines the cross-pillar emotional pattern system that enables
SOMERA to recognize emotional patterns and their root causes across all three
pillars: Career, Relationship, and Wellness.

The key insight: emotions don't sit neatly in one pillar. Someone feeling "rejected"
could be experiencing this in relationships AND career simultaneously. The root cause
(e.g., childhood patterns of seeking validation) often manifests across all three pillars.
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass


@dataclass
class EmotionalPattern:
    """Represents an emotional pattern with its root causes and manifestations."""
    pattern_id: str
    name: str
    keywords: List[str]
    root_causes: List[str]
    career_manifestations: List[str]
    relationship_manifestations: List[str]
    wellness_manifestations: List[str]
    probing_questions: List[str]


EMOTIONAL_PATTERNS: Dict[str, EmotionalPattern] = {
    "not_enough": EmotionalPattern(
        pattern_id="not_enough",
        name="Never Feeling Enough",
        keywords=[
            "not enough", "never enough", "not good enough", "inadequate",
            "imposter", "fraud", "don't deserve", "unworthy", "worthless",
            "not qualified", "not smart enough", "don't measure up"
        ],
        root_causes=[
            "Childhood comparison to siblings/cousins",
            "Parental expectations that were never satisfied",
            "Conditional love - love based on achievements",
            "Emotional neglect - opinions not valued"
        ],
        career_manifestations=[
            "Overworking but never feeling satisfied",
            "Can't accept compliments or recognition",
            "Hesitates to ask for raise/promotion",
            "Constantly seeking external validation from managers"
        ],
        relationship_manifestations=[
            "Feeling like you have to earn love",
            "Over-giving to prove your worth",
            "Attracting partners who don't appreciate you",
            "Fear of abandonment if you're not 'perfect'"
        ],
        wellness_manifestations=[
            "Neglecting self-care because 'you don't deserve it'",
            "Chronic stress from always trying to prove yourself",
            "Exhaustion from overachieving",
            "Digestive issues from holding tension"
        ],
        probing_questions=[
            "When did you first start feeling this way about yourself?",
            "Were you compared to others growing up?",
            "Do you notice this feeling in other areas of your life too?",
            "What would 'being enough' look like for you?"
        ]
    ),
    
    "fear_of_judgment": EmotionalPattern(
        pattern_id="fear_of_judgment",
        name="Fear of Being Judged",
        keywords=[
            "judged", "judgment", "what will people think", "being seen",
            "scared to speak up", "afraid to share", "fear of rejection",
            "afraid of criticism", "fear of failure", "embarrassed"
        ],
        root_causes=[
            "Critical or controlling parents",
            "Punishment for expressing opinions",
            "Being told to 'stay quiet' or 'behave'",
            "Public humiliation in childhood"
        ],
        career_manifestations=[
            "Avoids difficult conversations with manager",
            "Hesitates to share ideas in meetings",
            "Stays silent even when having valuable input",
            "Triggered by feedback - feels like personal attack"
        ],
        relationship_manifestations=[
            "Can't express true feelings to partner",
            "Hides authentic self from loved ones",
            "Fear of conflict leads to resentment",
            "People-pleasing to avoid judgment"
        ],
        wellness_manifestations=[
            "Throat issues from swallowed words",
            "Anxiety about social situations",
            "Stress from constantly monitoring how others see you",
            "Insomnia from replaying interactions"
        ],
        probing_questions=[
            "What happens in your body when you think about speaking up?",
            "Can you remember a time when expressing yourself led to a negative reaction?",
            "Is there a specific person whose judgment you fear most?",
            "What would you say if you knew no one would judge you?"
        ]
    ),
    
    "rejection": EmotionalPattern(
        pattern_id="rejection",
        name="Fear of Rejection / Feeling Rejected",
        keywords=[
            "rejected", "rejection", "abandoned", "left out", "ignored",
            "overlooked", "invisible", "unseen", "unheard", "dismissed",
            "not valued", "undervalued", "unappreciated", "pushed away"
        ],
        root_causes=[
            "Emotional neglect in childhood",
            "Feeling invisible to parents",
            "Being the 'forgotten' child",
            "Early experiences of abandonment"
        ],
        career_manifestations=[
            "Feels overlooked for promotions",
            "Believes voice doesn't matter at work",
            "Over-explains to justify worth",
            "Sensitive to being left out of meetings/decisions"
        ],
        relationship_manifestations=[
            "Fear of abandonment by partner",
            "Clingy behavior or complete withdrawal",
            "Chooses unavailable partners (familiar pattern)",
            "Feels unloved even when loved"
        ],
        wellness_manifestations=[
            "Heart chakra blocks - chest tightness",
            "Depression from chronic feeling of isolation",
            "Comfort eating to fill emotional void",
            "Low energy from carrying sadness"
        ],
        probing_questions=[
            "When did you first feel this way - unseen or unheard?",
            "Who in your life made you feel invisible?",
            "Do you notice this pattern repeating with different people?",
            "What would feeling truly seen and valued look like for you?"
        ]
    ),
    
    "seeking_validation": EmotionalPattern(
        pattern_id="seeking_validation",
        name="Seeking External Validation",
        keywords=[
            "validation", "approval", "recognition", "prove myself",
            "need to be liked", "want others to notice", "seek praise",
            "need appreciation", "want acknowledgment", "external approval"
        ],
        root_causes=[
            "Conditional love from parents",
            "Only praised for achievements, not being",
            "Learned that love must be earned",
            "Comparison culture in family"
        ],
        career_manifestations=[
            "Overworking to be noticed by manager",
            "Takes on extra tasks hoping for approval",
            "Crushed when work isn't acknowledged",
            "Defines self-worth by performance reviews"
        ],
        relationship_manifestations=[
            "Constantly needs partner's reassurance",
            "Loses identity in relationships",
            "Becomes what others want you to be",
            "Feels empty without external validation"
        ],
        wellness_manifestations=[
            "Solar plexus imbalance - self-worth issues",
            "Burnout from constant striving",
            "Anxiety about what others think",
            "Physical tension from always 'performing'"
        ],
        probing_questions=[
            "What would it feel like if you didn't need anyone's approval?",
            "When you achieve something, who do you want to notice?",
            "Can you remember when you first started needing external validation?",
            "What's underneath the need for others to see you?"
        ]
    ),
    
    "boundary_issues": EmotionalPattern(
        pattern_id="boundary_issues",
        name="Difficulty Setting Boundaries",
        keywords=[
            "can't say no", "boundaries", "people pleaser", "taken advantage",
            "overwhelmed", "too much on my plate", "always helping others",
            "guilt when I say no", "doormat", "resentful", "overcommitted"
        ],
        root_causes=[
            "Learned that being helpful = being worthy",
            "Love was conditional on compliance",
            "Taught that your needs don't matter",
            "Responsibility was placed on you too young"
        ],
        career_manifestations=[
            "Can't say no to extra work",
            "Takes on everyone's problems",
            "Stays late while others leave",
            "Feels guilty taking vacation"
        ],
        relationship_manifestations=[
            "Over-giving to the point of resentment",
            "Attracts takers/narcissistic partners",
            "Loses self in trying to please others",
            "Feels responsible for everyone's happiness"
        ],
        wellness_manifestations=[
            "Chronic exhaustion from giving too much",
            "Adrenal fatigue",
            "Resentment stored in body",
            "Digestive issues from swallowing anger"
        ],
        probing_questions=[
            "What happens inside you when you think about saying no?",
            "When did you learn that your needs came last?",
            "What's the worst thing you imagine happening if you set a boundary?",
            "What would you do with the energy if you stopped over-giving?"
        ]
    ),
    
    "stuck_patterns": EmotionalPattern(
        pattern_id="stuck_patterns",
        name="Feeling Stuck / Repeating Patterns",
        keywords=[
            "stuck", "same patterns", "keep repeating", "can't move forward",
            "trapped", "cycle", "going in circles", "no progress",
            "history repeating", "same mistakes", "can't change"
        ],
        root_causes=[
            "Subconscious blueprint running the show",
            "Unresolved emotions creating energetic blocks",
            "Limiting beliefs from childhood",
            "Fear of the unknown keeping you in comfort zone"
        ],
        career_manifestations=[
            "Same job issues with different employers",
            "Can't seem to advance despite effort",
            "Keeps attracting same type of difficult boss",
            "Sabotages opportunities unconsciously"
        ],
        relationship_manifestations=[
            "Attracts same type of partner repeatedly",
            "Same arguments with different people",
            "Patterns from parents' relationship showing up",
            "Can't seem to maintain healthy connections"
        ],
        wellness_manifestations=[
            "Chronic health issues that won't resolve",
            "Same stress patterns despite changes",
            "Can't stick to healthy habits",
            "Body holding onto old trauma"
        ],
        probing_questions=[
            "If you look back, when did this pattern first start?",
            "What's the common thread in these repeating situations?",
            "What would breaking this pattern mean for you?",
            "What part of you might be comfortable with this familiar pattern?"
        ]
    ),
    
    "parental_resentment": EmotionalPattern(
        pattern_id="parental_resentment",
        name="Unresolved Resentment Towards Parents",
        keywords=[
            "parents", "mother", "father", "childhood", "upbringing",
            "resentment", "anger at parents", "family trauma", "forgiveness",
            "childhood wounds", "inner child", "raised", "growing up"
        ],
        root_causes=[
            "Feeling unheard as a child",
            "Being controlled or criticized",
            "Emotional neglect or absence",
            "Comparison to siblings"
        ],
        career_manifestations=[
            "Triggered by authority figures (boss = parent pattern)",
            "Resistance to leadership/feedback",
            "Overworking to prove worth to invisible parent",
            "Fear of success (fear of surpassing parents)"
        ],
        relationship_manifestations=[
            "Choosing partners who mirror parental patterns",
            "Difficulty trusting intimate partners",
            "Recreating family dynamics in marriage",
            "Can't receive love fully"
        ],
        wellness_manifestations=[
            "Resentment vibrates low - chronic fatigue",
            "Liver/digestive issues from held anger",
            "High blood pressure from suppressed emotions",
            "Root chakra imbalance - feeling unsafe"
        ],
        probing_questions=[
            "If your inner child could say something to your parents, what would it be?",
            "What did you need from them that you didn't receive?",
            "Do you see any of their patterns showing up in your life now?",
            "What would forgiving them mean for you?"
        ]
    ),
    
    "overwhelm_exhaustion": EmotionalPattern(
        pattern_id="overwhelm_exhaustion",
        name="Overwhelm and Exhaustion",
        keywords=[
            "overwhelmed", "exhausted", "burnout", "tired", "drained",
            "can't cope", "too much", "stressed", "at my limit", "no energy",
            "running on empty", "worn out", "depleted"
        ],
        root_causes=[
            "Took on adult responsibilities too young",
            "Never learned it's okay to rest",
            "Self-worth tied to productivity",
            "Operating from masculine energy (work work work)"
        ],
        career_manifestations=[
            "Burnout from overworking",
            "Can't disconnect from work",
            "Feels guilty when not productive",
            "Takes on too many responsibilities"
        ],
        relationship_manifestations=[
            "No energy left for partner/family",
            "Resentment from always giving",
            "Feels alone in carrying everything",
            "Intimacy suffers from exhaustion"
        ],
        wellness_manifestations=[
            "Physical exhaustion/chronic fatigue",
            "Adrenal burnout",
            "Insomnia from racing mind",
            "Body breaks down from stress"
        ],
        probing_questions=[
            "What would it feel like to truly rest without guilt?",
            "When did you learn that you had to carry everything?",
            "What are you afraid would happen if you stopped?",
            "What would you do if you had energy and time for yourself?"
        ]
    ),
    
    "disconnection": EmotionalPattern(
        pattern_id="disconnection",
        name="Feeling Disconnected / Lonely",
        keywords=[
            "disconnected", "lonely", "isolated", "alone", "no one understands",
            "don't belong", "outsider", "can't connect", "empty", "hollow",
            "going through motions", "lost myself"
        ],
        root_causes=[
            "Emotional neglect - not seen for who you really are",
            "Hiding true self to fit in",
            "Lost connection to soul purpose",
            "Living life for others, not yourself"
        ],
        career_manifestations=[
            "Job feels meaningless",
            "Going through the motions at work",
            "Misaligned with soul purpose",
            "Successful on paper but empty inside"
        ],
        relationship_manifestations=[
            "Surface-level connections only",
            "Can't be authentic with loved ones",
            "Feels lonely even when surrounded by people",
            "Marriage feels like roommates"
        ],
        wellness_manifestations=[
            "Heart chakra closed",
            "Depression from disconnection",
            "Numbness - not feeling emotions fully",
            "Physical heart issues from emotional blocks"
        ],
        probing_questions=[
            "When did you last feel truly connected - to yourself or others?",
            "What parts of yourself do you hide from others?",
            "What would it look like to show up as your real self?",
            "What's underneath the loneliness?"
        ]
    ),
    
    "misalignment": EmotionalPattern(
        pattern_id="misalignment",
        name="Soul Misalignment / Not Living True Purpose",
        keywords=[
            "misaligned", "purpose", "meant for more", "not living my truth",
            "wrong path", "unfulfilled", "something missing", "existential",
            "is this all there is", "not my passion", "settling"
        ],
        root_causes=[
            "Following expected path instead of authentic one",
            "Suppressed true calling to meet expectations",
            "Fear of judgment if you pursue what you love",
            "Never given permission to explore who you really are"
        ],
        career_manifestations=[
            "Job feels like golden cage",
            "Successful but unhappy",
            "Knows there's something more but can't name it",
            "Energy drain from inauthentic work"
        ],
        relationship_manifestations=[
            "Attracts people who don't see real you",
            "Relationships feel shallow",
            "Partner doesn't support your dreams",
            "Lost sense of self in the relationship"
        ],
        wellness_manifestations=[
            "Crown chakra blocked - disconnected from purpose",
            "Throat chakra blocked - not speaking truth",
            "Chronic low energy from living inauthentically",
            "Autoimmune issues from body attacking 'false self'"
        ],
        probing_questions=[
            "If fear and judgment weren't factors, what would you do?",
            "What lit you up as a child before the world told you who to be?",
            "What does your wisest self know about your true path?",
            "What would 'alignment' feel like in your body?"
        ]
    )
}


PILLAR_KEYWORDS = {
    "career": [
        "job", "work", "career", "boss", "manager", "colleague", "coworker",
        "office", "meeting", "promotion", "raise", "salary", "corporate",
        "business", "professional", "workplace", "project", "deadline",
        "interview", "fired", "laid off", "performance", "review"
    ],
    "relationship": [
        "marriage", "husband", "wife", "partner", "spouse", "boyfriend",
        "girlfriend", "relationship", "dating", "love", "family", "parents",
        "children", "kids", "divorce", "separation", "communication",
        "intimacy", "trust", "commitment", "in-laws", "sibling"
    ],
    "wellness": [
        "health", "tired", "exhausted", "sick", "pain", "sleep", "stress",
        "anxiety", "depression", "energy", "body", "weight", "exercise",
        "meditation", "healing", "self-care", "burnout", "mental health",
        "physical", "emotional", "spiritual", "balance"
    ]
}


def identify_emotional_patterns(text: str) -> List[EmotionalPattern]:
    """
    Identify emotional patterns present in the user's message.
    Returns a list of matching patterns ordered by relevance.
    """
    text_lower = text.lower()
    pattern_scores: Dict[str, int] = {}
    
    for pattern_id, pattern in EMOTIONAL_PATTERNS.items():
        score = 0
        for keyword in pattern.keywords:
            if keyword in text_lower:
                score += 1
        if score > 0:
            pattern_scores[pattern_id] = score
    
    sorted_patterns = sorted(
        pattern_scores.keys(), 
        key=lambda x: pattern_scores[x], 
        reverse=True
    )
    
    return [EMOTIONAL_PATTERNS[pid] for pid in sorted_patterns[:3]]


def identify_pillars(text: str) -> List[str]:
    """
    Identify which life pillars are being discussed.
    Returns a list of pillars (career, relationship, wellness).
    """
    text_lower = text.lower()
    pillars = []
    
    for pillar, keywords in PILLAR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if pillar not in pillars:
                    pillars.append(pillar)
                break
    
    return pillars


def get_cross_pillar_manifestations(pattern: EmotionalPattern, primary_pillar: str = None) -> Dict[str, List[str]]:
    """
    Get how an emotional pattern manifests across all pillars.
    If primary_pillar is specified, it's listed first.
    """
    manifestations = {
        "career": pattern.career_manifestations,
        "relationship": pattern.relationship_manifestations,
        "wellness": pattern.wellness_manifestations
    }
    
    if primary_pillar and primary_pillar in manifestations:
        ordered = {primary_pillar: manifestations[primary_pillar]}
        for pillar in manifestations:
            if pillar != primary_pillar:
                ordered[pillar] = manifestations[pillar]
        return ordered
    
    return manifestations


def get_pattern_probing_questions(pattern_id: str) -> List[str]:
    """Get probing questions for a specific emotional pattern."""
    if pattern_id in EMOTIONAL_PATTERNS:
        return EMOTIONAL_PATTERNS[pattern_id].probing_questions
    return []


def get_root_causes(pattern_id: str) -> List[str]:
    """Get root causes for a specific emotional pattern."""
    if pattern_id in EMOTIONAL_PATTERNS:
        return EMOTIONAL_PATTERNS[pattern_id].root_causes
    return []


def build_enhanced_search_query(user_message: str, conversation_history: List[dict] = None) -> dict:
    """
    Build an enhanced search query that includes emotional pattern context.
    
    Returns a dict with:
    - primary_query: The main search query
    - pattern_queries: Additional queries based on identified patterns
    - pillars: Identified pillars
    - patterns: Identified emotional patterns
    """
    patterns = identify_emotional_patterns(user_message)
    pillars = identify_pillars(user_message)
    
    context_messages = []
    if conversation_history:
        for msg in conversation_history[-6:]:
            if msg.get("role") == "user":
                context_messages.append(msg.get("content", ""))
    
    all_text = user_message + " " + " ".join(context_messages)
    all_patterns = identify_emotional_patterns(all_text)
    all_pillars = identify_pillars(all_text)
    
    pattern_queries = []
    for pattern in all_patterns[:2]:
        pattern_queries.append(f"{pattern.name} {' '.join(pattern.keywords[:3])}")
    
    return {
        "primary_query": user_message,
        "pattern_queries": pattern_queries,
        "pillars": all_pillars,
        "patterns": all_patterns,
        "pattern_ids": [p.pattern_id for p in all_patterns]
    }


def get_cross_pillar_awareness_context(patterns: List[EmotionalPattern], primary_pillar: str = None) -> str:
    """
    Generate context text about how identified patterns manifest across pillars.
    This helps SOMERA probe about other life areas.
    """
    if not patterns:
        return ""
    
    context_parts = []
    
    for pattern in patterns[:2]:
        manifestations = get_cross_pillar_manifestations(pattern, primary_pillar)
        
        part = f"**{pattern.name}** often shows up as:\n"
        for pillar, manifests in manifestations.items():
            pillar_name = pillar.title()
            part += f"- In {pillar_name}: {manifests[0]}\n"
        
        part += f"\nRoot causes: {', '.join(pattern.root_causes[:2])}"
        part += f"\n\nProbing questions to consider: {pattern.probing_questions[0]}"
        
        context_parts.append(part)
    
    return "\n\n---\n\n".join(context_parts)


PATTERN_TO_TOPICS = {
    "not_enough": ["career", "confidence", "self-worth", "validation"],
    "fear_of_judgment": ["career", "confidence", "speaking up", "boundaries"],
    "rejection": ["relationships", "career", "self-worth", "loneliness"],
    "seeking_validation": ["career", "relationships", "self-worth", "boundaries"],
    "boundary_issues": ["career", "relationships", "exhaustion", "self-care"],
    "stuck_patterns": ["career", "relationships", "healing", "patterns"],
    "parental_resentment": ["relationships", "healing", "inner child", "forgiveness"],
    "overwhelm_exhaustion": ["career", "wellness", "burnout", "balance"],
    "disconnection": ["relationships", "wellness", "purpose", "loneliness"],
    "misalignment": ["career", "purpose", "fulfillment", "alignment"]
}


def get_relevant_content_topics(pattern_ids: List[str]) -> List[str]:
    """
    Get relevant content topics based on identified emotional patterns.
    Used to improve RAG retrieval.
    """
    topics = set()
    for pattern_id in pattern_ids:
        if pattern_id in PATTERN_TO_TOPICS:
            topics.update(PATTERN_TO_TOPICS[pattern_id])
    return list(topics)
