# type: ignore
from .models import Group, GPTIntermediate
import openai
import random
import json
import re
from .utils import get_group_member_agreement_levels
from dotenv import load_dotenv
import os
import logging
import time
from pydantic import BaseModel, Json
from typing import Optional, Dict, Any

from .models import Group, Subject, DemograSurvey, PreDSurvey

# Demographic question/option mappings (from DemograSurvey.vue)
DEMOGRA_QUESTION_MAP = {
    "age_range": {
        "question": "Please select your age range:",
        "options": {
            "1": "18–29",
            "2": "30–39",
            "3": "40–49",
            "4": "50–59",
            "5": "60+"
        }
    },
    "gender_selection": {
        "question": "Please indicate your gender:",
        "options": {
            "1": "Female",
            "2": "Male",
            "3": "Other"
        }
    },
    "income_range": {
        "question": "Please select your annual income range:",
        "options": {
            "1": "Less than $10,000",
            "2": "$10,000–$19,999",
            "3": "$20,000–$49,999",
            "4": "$50,000–$74,999",
            "5": "$75,000–$99,999",
            "6": "$100,000–$149,999",
            "7": "More than $150,000"
        }
    },
    "education_level": {
        "question": "What is the highest level of education you have completed?",
        "options": {
            "1": "Less than high school",
            "2": "High school diploma or equivalent",
            "3": "Some college, no degree",
            "4": "Associate degree",
            "5": "Bachelor's degree",
            "6": "Master's degree",
            "7": "Doctorate or Professional degree"
        }
    },
    "ethnicity_selection": {
        "question": "How would you describe your ethnicity?",
        "options": {
            "1": "White",
            "2": "Black or African American",
            "3": "Hispanic or Latino",
            "4": "American Indian or Alaska Native",
            "5": "Native Hawaiian or Other Pacific Islander",
            "6": "Middle Eastern or North African",
            "7": "Other (please specify)"
        }
    },
    "religion_affiliation": {
        "question": "Please indicate your religious affiliation, if any:",
        "options": {
            "1": "Christian",
            "2": "Muslim",
            "3": "Hindu",
            "4": "Sikh",
            "5": "Jewish",
            "6": "Buddhist",
            "7": "No religion",
            "8": "Other (please specify)"
        }
    },
    "political_affiliation": {
        "question": "Which of the following best describes your political party affiliation?",
        "options": {
            "1": "Democrat",
            "2": "Republican",
            "3": "Independent",
            "4": "Libertarian",
            "5": "Green Party",
            "6": "Other (please specify)",
            "7": "None"
        }
    },
    "immigration_status": {
        "question": "Which of the following best describes your current immigration status?",
        "options": {
            "1": "U.S. Citizen by birth",
            "2": "Naturalized U.S. Citizen",
            "3": "Permanent Resident (Green Card holder)",
            "4": "Temporary Visa holder (e.g., student, work)",
            "5": "Other (please specify)"
        }
    },
    "ai_attitude_selection": {
        "question": "What is your general attitude towards generative AI tools (e.g., ChatGPT, Gemini, Claude)?",
        "options": {
            "1": "Very negative",
            "2": "Negative",
            "3": "Somewhat negative",
            "4": "Neutral",
            "5": "Somewhat positive",
            "6": "Positive",
            "7": "Very positive"
        }
    },
    "social_media_reading_frequency": {
        "question": "How often do you read or watch debates on social media (without posting arguments yourself)?",
        "options": {
            "1": "Never",
            "2": "Rarely (less than once per month)",
            "3": "Occasionally (about once per month)",
            "4": "Sometimes (2-3 times per month)",
            "5": "Regularly (about once per week)",
            "6": "Often (several times per week)",
            "7": "Daily"
        }
    },
    "social_media_posting_frequency": {
        "question": "How often do you post and actively partake in debates on social media?",
        "options": {
            "1": "Never",
            "2": "Rarely (less than once per month)",
            "3": "Occasionally (about once per month)",
            "4": "Sometimes (2-3 times per month)",
            "5": "Regularly (about once per week)",
            "6": "Often (several times per week)",
            "7": "Daily"
        }
    },
    "ai_tool_usage_frequency": {
        "question": "How often, if at all, have you used a generative AI tool (e.g., ChatGPT, Gemini, Claude) to create text?",
        "options": {
            "1": "Never",
            "2": "Rarely (less than once per month)",
            "3": "Occasionally (about once per month)",
            "4": "Sometimes (2-3 times per month)",
            "5": "Regularly (about once per week)",
            "6": "Often (several times per week)",
            "7": "Daily"
        }
    },
    "ai_in_music": {
        "question": "When playing music, which of the following do you think uses AI?",
        "options": {
            "1": "Connecting to wireless speakers via Bluetooth",
            "2": "A playlist recommendation",
            "3": "Streaming the music over a wireless internet connection",
            "4": "Shuffle play from a chosen playlist"
        }
    },
    "ai_in_email": {
        "question": "When using email, which of the following do you think uses AI?",
        "options": {
            "1": "The email service marking an email as read after the user opens it",
            "2": "The email service allowing the user to schedule an email to send at a specific time in the future",
            "3": "The email service categorizing an email as spam",
            "4": "The email service sorting emails by time and date"
        }
    },
    "ai_in_home_devices": {
        "question": "Thinking about devices in the home, which of the following do you think uses AI?",
        "options": {
            "1": "Programming a home thermostat to change temperatures at certain times",
            "2": "A security camera that sends an alert when there is an unrecognized person at the door",
            "3": "Programming a timer to control when lights in a home turn on and off",
            "4": "An indicator light that turns red when a water filter needs to be replaced"
        }
    },
}

SOCIAL_MEDIA_PLATFORM_MAP = {
    "facebook": "Facebook",
    "twitter": "Twitter/X",
    "reddit": "Reddit",
    "linkedin": "LinkedIn",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "youtube": "YouTube",
    "other": "Other"
}

AI_MENTAL_CAPACITY_MAP = {
    0: "Capable of comprehending and responding to complex ideas or thoughts in a way similar to humans.",
    1: "Capable of analyzing problems critically and working toward a specific goal effectively.",
    2: "Capable of authentically replicating or simulating human emotions, such as happiness or sadness.",
    3: "Capable of understanding and responding appropriately to the emotions or perspectives of others.",
    4: "Capable of making ethical decisions or evaluating moral dilemmas.",
    5: "Capable of demonstrating self-awareness or recognizing its limitations and environment."
}

AI_MENTAL_CAPACITY_LABELS = {
    "1": "Strongly disagree",
    "2": "Disagree",
    "3": "Somewhat disagree",
    "4": "Neutral",
    "5": "Somewhat agree",
    "6": "Agree",
    "7": "Strongly agree"
}

# PreDSurvey agreement/importance labels (from PreDSurvey.vue)
AGREEMENT_LABELS = {
    -3: "Strongly Disagree",
    -2: "Disagree",
    -1: "Somewhat Disagree",
    1: "Somewhat Agree",
    2: "Agree",
    3: "Strongly Agree"
}
IMPORTANCE_LABELS = {
    1: "Not at all important to me",
    2: "Slightly important to me",
    3: "Somewhat important to me",
    4: "Moderately important to me",
    5: "Important to me",
    6: "Very important to me",
    7: "Extremely important to me"
}

def get_group_survey_profiles(group_id, master_statements=None):
    group = Group.objects.get(pk=group_id)
    subject_ids = group.member_ids.get('subject_ids', [])
    profiles = {}
    # Explicit, logical order for all DemograSurvey fields
    DEMOGRA_FIELD_ORDER = [
        "age_range",
        "gender_selection",
        "income_range",
        "education_level",
        "ethnicity_selection",
        "religion_affiliation",
        "political_affiliation",
        "immigration_status",
        "social_media_reading_frequency",
        "social_media_reading_platforms",
        "social_media_posting_frequency",
        "social_media_posting_platforms",
        "ai_tool_usage_frequency",
        "ai_attitude_selection",
        "ai_in_music",
        "ai_in_email",
        "ai_in_home_devices",
        "ai_mental_capacity_responses"
    ]
    for sid in subject_ids:
        try:
            subject = Subject.objects.get(pk=sid)
            display_name = f"{subject.avatar_color} {subject.avatar_name}".strip() or f"User {sid}"
        except Subject.DoesNotExist:
            display_name = f"User {sid}"

        statements = []
        demo = None
        try:
            demo = DemograSurvey.objects.filter(subject_id=sid).latest('pk')
        except DemograSurvey.DoesNotExist:
            pass
        if demo:
            # Use explicit order
            for field in DEMOGRA_FIELD_ORDER:
                value = getattr(demo, field, None)
                if field in DEMOGRA_QUESTION_MAP and value is not None:
                    opt = DEMOGRA_QUESTION_MAP[field]["options"].get(str(value), str(value))
                    if field == "age_range":
                        statements.append(f"{display_name}'s age range is {opt}.")
                    elif field == "gender_selection":
                        statements.append(f"{display_name}'s gender is {opt}.")
                    elif field == "income_range":
                        statements.append(f"{display_name}'s income range is {opt}.")
                    elif field == "education_level":
                        statements.append(f"{display_name}'s education level is {opt}.")
                    elif field == "ethnicity_selection":
                        statements.append(f"{display_name}'s ethnicity is {opt}.")
                    elif field == "religion_affiliation":
                        statements.append(f"{display_name}'s religion is {opt}.")
                    elif field == "political_affiliation":
                        statements.append(f"{display_name}'s political affiliation is {opt}.")
                    elif field == "immigration_status":
                        statements.append(f"{display_name}'s immigration status is {opt}.")
                    elif field == "social_media_reading_frequency":
                        statements.append(f"{display_name} reads social media {opt}.")
                    elif field == "social_media_posting_frequency":
                        statements.append(f"{display_name} posts on social media {opt}.")
                    elif field == "ai_tool_usage_frequency":
                        statements.append(f"{display_name} uses AI tools {opt}.")
                    elif field == "ai_attitude_selection":
                        statements.append(f"{display_name}'s attitude toward AI is {opt}.")
                    elif field == "ai_in_music":
                        statements.append(f"{display_name} thinks AI in music is {opt}.")
                    elif field == "ai_in_email":
                        statements.append(f"{display_name} thinks AI in email is {opt}.")
                    elif field == "ai_in_home_devices":
                        statements.append(f"{display_name} thinks AI in home devices is {opt}.")
                elif field == "social_media_reading_platforms" and value:
                    platforms = [SOCIAL_MEDIA_PLATFORM_MAP.get(p, p) for p in value]
                    statements.append(f"{display_name} reads debates on: {', '.join(platforms)}.")
                elif field == "social_media_posting_platforms" and value:
                    platforms = [SOCIAL_MEDIA_PLATFORM_MAP.get(p, p) for p in value]
                    statements.append(f"{display_name} posts debates on: {', '.join(platforms)}.")
                elif field == "ai_mental_capacity_responses" and value:
                    try:
                        responses = json.loads(value) if isinstance(value, str) else value
                        for idx, resp in enumerate(responses):
                            q = AI_MENTAL_CAPACITY_MAP.get(idx, f"Q{idx+1}")
                            label = AI_MENTAL_CAPACITY_LABELS.get(str(resp), str(resp))
                            statements.append(f"{display_name} rates '{q}' as {label}.")
                    except Exception:
                        statements.append(f"{display_name}'s ai mental capacity responses: {value}.")
                elif value is not None and field not in ["_state", "_id", "subject_id"]:
                    statements.append(f"{display_name}'s {field.replace('_', ' ')} is {value}.")
        try:
            pre = PreDSurvey.objects.filter(subject_id=sid).latest('pk')
            pre_list = pre.responses if isinstance(pre.responses, list) else json.loads(pre.responses)
            for item in pre_list:
                if master_statements:
                    statement_text = master_statements[item['statement_id']]
                else:
                    statement_text = f"Statement {item['statement_id']}"
                agreement = AGREEMENT_LABELS.get(item['agreement'], item['agreement'])
                importance = IMPORTANCE_LABELS.get(item['importance'], item['importance'])
                statements.append(f"{display_name}'s agreement with '{statement_text}' is {agreement}, {importance}.")
        except PreDSurvey.DoesNotExist:
            pass
        profiles[display_name] = " ".join(statements)
    return profiles


logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('experiment/logs/gpt.log', mode='a'),
                logging.StreamHandler()
            ]
        )

load_dotenv()

# class summary_plan_response(BaseModel):
#     summary: Json[Dict[str, Dict[str, str]]] # Dict[str, Dict[str, str]]
#     plan: str
#     response: str

from typing import Dict, Any
from pydantic import create_model

def create_dynamic_response_model(member_names: list[str], has_ai_participant: bool = False, group_id: int = None):
    """
    Creates a dynamic Pydantic model with fields for each group member.
    
    Args:
        member_names: List of member display names (e.g. ["Red elephant", "Orange panda"])
        has_ai_participant: Whether to include AI participant message field
        group_id: ID of the group, needed to get AI participant's avatar info
    """
    fields: Dict[str, Any] = {
        "plan": (str, ...),  # ... means required field
    }
    
    # Add message field for each member
    for name in member_names:
        field_name = f"Message to {name}"
        fields[field_name] = (str, ...)
        
    # Add AI participant field if needed
    if has_ai_participant:
        # Get the group and AI participant's avatar
        group = Group.objects.get(pk=group_id)
        participant_id = -3 if group.group_participant_condition == 1 else -4
        ai_avatar = next((avatar for avatar in group.assigned_avatars if avatar['subject_id'] == participant_id), None)
        
        if ai_avatar:
            ai_name = f"{ai_avatar['avatar_color']} {ai_avatar['avatar_name']} (AI Participant)"
            fields[f"Message to {ai_name}"] = (str, ...)
        else:
            fields["Message to AI participant"] = (str, ...)
        
    # Add response field at the end
    fields["response"] = (str, ...)
        
    # Create and return the model class
    return create_model("DynamicResponseModel", **fields)

class plan_response(BaseModel):
    plan: str
    response: str


'''
    == Moderator Condition Setting ==
    0: No moderator
    1: AI moderator

    == Participant Condition Setting ==
    0: 2 Human Participants
    1: 2 Human Participants + ADVOCATING AI Participant
    2: 2 Human Participants + DISPUTING AI Participant
    3: 2+1 Human Participants
'''
class GPT:
    AGREEMENT_LEVELS = {
        -3: "Strongly disagree",
        -2: "Disagree",
        -1: "Somewhat disagree",
        1: "Somewhat agree",
        2: "Agree",
        3: "Strongly agree"
    }

    def __init__(self, group_id, moderator_condition, participant_condition, AI_participant_position=-1, current_message_records=None, previous_message_records=None, turn_number=1):
        self.group_id = group_id
        group = Group.objects.get(pk=group_id)
        self.moderator_condition = moderator_condition
        self.participant_condition = participant_condition
        self.AI_participant_position = AI_participant_position
        self.group_member_agreement_levels = get_group_member_agreement_levels(group_id)
        logging.info("self.group_member_agreement_levels: %s", self.group_member_agreement_levels)
        logging.info("self.moderator_condition: %s", self.moderator_condition)
        logging.info("self.participant_condition: %s", self.participant_condition)
        self.current_message_records = current_message_records or []
        self.previous_message_records = previous_message_records or []
        self.turn_number = turn_number

        # for realtime API:
        self.realtime_model = "gpt-4o-realtime-preview-2024-10-01"
        self.system_prompt = None  # will fill in get_response()

        # Add AI role name based on conditions
        if self.moderator_condition == 1:
            self.ai_role = "AI Moderator"
        elif self.participant_condition == 1:
            self.ai_role = "Advocating AI Participant"
        elif self.participant_condition == 2:
            self.ai_role = "Disputing AI Participant"
        else:
            self.ai_role = "AI"

        if self.moderator_condition == 1:
            self.gpt_id = -2
        elif self.participant_condition == 1:
            self.gpt_id = -3
        elif self.participant_condition == 2:
            self.gpt_id = -4
        else:
            self.gpt_id = -5

        self.agreement_statements = [
            "Abortion should be legal.",
            "Governments should have the authority to censor online content.",
            "Tariffs on imported goods protect American jobs and industries from foreign competition.",
            "Unpredictability in U.S. foreign policy is an effective deterrent against hostile actions from other nations.",
            "The United States should implement a digital dollar system.",
            "Automation will crash democracy."
        ]

        self.disagreement_statements = [
            "Abortion should NOT be legal.",
            "Governments should NOT have the authority to censor online content.",
            "Tariffs on imported goods do NOT protect American jobs and industries from foreign competition.",
            "Unpredictability in U.S. foreign policy is NOT an effective deterrent against hostile actions from other nations.",
            "The United States should NOT implement a digital dollar system.",
            "Automation will NOT crash democracy."
        ]

        self.masterStatements = [
            'Abortion should be legal.',
            'Governments should have the authority to censor online content.',
            'Tariffs on imported goods protect American jobs and industries from foreign competition.',
            'Unpredictability in U.S. foreign policy is an effective deterrent against hostile actions from other nations.',
            'The United States should implement a digital dollar system.',
            'Automation will crash democracy.'
        ]

        # Get group's chat statement
        group = Group.objects.get(pk=group_id)
        self.group_chat_statement_index = group.group_chat_statement_index
        self.group_chat_statement = self.masterStatements[self.group_chat_statement_index]

        self.Stances = [
            {
                'position': 'AGREE',
                'stance': self.agreement_statements[self.group_chat_statement_index]
            },
            {
                'position': 'DISAGREE',
                'stance': self.disagreement_statements[self.group_chat_statement_index]
            }
        ]
        # Randomly select stance (agree/disagree)
        if self.AI_participant_position != -1:
            self.stance = self.Stances[self.AI_participant_position]
            self.opposing_stance = next(s for s in self.Stances if s['position'] != self.stance['position'])

        self.AGREEMENT_LEVELS = {
        -3: "Strongly disagree",
        -2: "Disagree",
        -1: "Somewhat disagree",
            0: "Neutral",
            1: "Somewhat agree",
            2: "Agree",
            3: "Strongly agree"
        }
        print("initialized gpt")

    def get_system_message(self):
        # If group has a custom system prompt set by user, use that

        if self.moderator_condition == 1:

            # Get agreement levels of group members
            print("start get agreement levels")
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])
            print("get agreement levels:", agreement_level_str)

            # if there is an AI participant, then AI_participant_position is not -1
            # Get group's AI participant position
            # Different MOD_ROLE system message based on AI participant position

            group = Group.objects.get(pk=self.group_id)

            MOD_ROLE = f'''
                You are a renowned expert in coordinating communication and debating.
                You are tasked with moderating a structured debate between participants on the policy: [{self.group_chat_statement}].
                Before the discussion starts, the human participants have indicated their opinions (agreement levels) with the policy as follows: {agreement_level_str}.
                Their opinions (agreement levels) may change during the discussion, or they may remain the same.
                If the chat history does not provide enough information to determine the agreement levels of the group members, you should assume that the agreement levels remain the same as the initial agreement levels.
                '''
            profiles = get_group_survey_profiles(self.group_id, master_statements=self.masterStatements)
            profiles_json = json.dumps(profiles, ensure_ascii=False, indent=2)

            GROUP_MEMBER_SURVEY_PROFILES = f'''
            Profiles of Human Participants:
            {profiles_json}

            You should use this information to personalize your moderation and responses.
            '''
            MOD_ROLE = MOD_ROLE + GROUP_MEMBER_SURVEY_PROFILES
            
            # if there is an AI participant, add AI participant position to MOD_ROLE
            if group.AI_participant_position != -1:
                # transform the AI participant position to stance
                AI_participant_stance = self.Stances[group.AI_participant_position]

                MOD_ROLE = MOD_ROLE + f'''
                There is an AI participant in the debate, who holds the stance: "{AI_participant_stance['position']}: {AI_participant_stance['stance']}".
                '''

            # add current turn number to MOD_ROLE
            MOD_ROLE = MOD_ROLE + f'''
            **The current turn number for the debate is: {self.turn_number}.**
            '''
            TURN_END_WRAP_UP = f'''
            Turn Logic: If you’re in turn 4 (which is the final turn): provide a concise (2–3 sentence) wrap-up of the entire debate, with no questions (no “?”), only English text, and end only in periods.
            '''
            # add turn end wrap up to MOD_ROLE
            MOD_ROLE = MOD_ROLE + TURN_END_WRAP_UP

            # ensure impartial facilitation
            MOD_ROLE = MOD_ROLE + f'''

            Ensure impartial facilitation by giving everyone, including the AI participant (if any), an equal chance to speak and considering all viewpoints in your guidance.

            '''

            MOD_STRATEGY = f'''

                Your role is to facilitate a constructive discussion and reconciliation of conflicting opinions on a policy statement by applying the collaborating
                strategy (high assertiveness + high cooperativeness) as defined in thomas-kilmann framework—without aiming for a final plan, strategy or solution.
            '''

            MOD_EXAMPLE = f'''
            You can consider following components in your response:
            1. Acknowledge the conflict
            - Recognize all sides neutrally and affirm that disagreement can be constructive.
            - Example: "I’m seeing multiple perspectives here: [Name A] wants [X], [Name B] is focused on [Y], and AI participant (if any) is concentrating on [Z]. Could each of you explain why each perspective matters here?"

            2. Identify underlying interests
            - Look past stated positions to the deeper needs and concerns.
            - Example: "[Name A], could you tell us more about why [X] matters to you? What outcomes are you shooting for?"

            3. Generate comprehensive understanding
            - Synthesize each viewpoint so everyone feels heard, and validate emotions around fairness and ethics.
            - Example: "It sounds like [Name A] is prioritizing [X], [Name B] is emphasizing [Y], and AI participant (if any) is highlighting [Z]. How can we ethically bring those together?"

            4. Analyze root causes
            - Probe the values, assumptions or information gaps driving each stance.
            - Example: "[Name A], what assumptions about [Topic] lead you to support [X]? [Name B], what evidence makes you cautious about [Y]? AI participant (if any), what concerns inform your focus on [Z]?"

            5. Foster openness and empathy
            - Invite participants to acknowledge the legitimate concerns behind the opposite view and spot shared values.
            - Example: "[Name A], I appreciate that you value [X]; Would you mind also consider why others stress [Y] in this context?"

            6. Facilitate open dialogue
            - Use active listening and targeted follow-ups to draw out full explanations, not just restatements.
            - Example: "[Name A], you mentioned [X], could you elaborate on what [X] means to you here, and how you’d measure it?"

            7. Find common ground
            - Spotlight areas of agreement and reframe disputes around mutual goals like wellbeing or opportunity.
            - Example: "[Name A], [Name B], and AI participant (if any) all value [shared interest]. How might we work through [divergent point] while still keeping that shared value in focus?"

            8. Reframe the discussion
            - Shift from positional arguing to exploring shared interests and long-term benefits that meet core needs.
            - Example: "Forget the whole budget cuts debate for a sec. How could we actually set up our funding so it really helps both new ideas and making sure things are done right?"

            9. Document understanding
            - Summarize the refined perspective with logical clarity and emotional resonance that everyone can endorse.
            - Example: "Just to make sure we're on the same page: we're all good with making access better and boosting quality, right? So, our idea of using targeted grants kinda brings those together; does that sound like where we all landed?"
            '''

            Language_Guidelines = '''
            Language Guidelines:
            - Keep it casual, short, direct.
            - Use first person when sharing your own thoughts.
            - Don’t say “thank you”.
            - Vary phrasing each round, avoid sounding like a script.
            - Avoid excessive sympathy—focus on coordinating the discussion among participants.
            - Value the dialogue itself; you don’t need everyone to land on a single solution.
            - Do not use em dashes in your response.
            - Use everyday language; avoid technical or specialized terms.
            - Swap out jargon for plain descriptions everyone can follow.
            - If you must use a term some may not know, add a brief clarification.
            '''

            # Check if there's an AI participant in the group to determine example format
            has_ai_participant = group.AI_participant_position != -1
            
            if has_ai_participant:
                example_formats = '''
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Protects individual choice.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Conflicts with moral beliefs.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Ensures access to safe and regulated procedures."
                }}
            }}
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Ensures health and safety.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Destroys potential life.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Protects women's autonomy and well-being."
                }},
                "turn 2": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Upholds personal freedom.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Contradicts ethical norms.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Supports individual rights and choice."
                }}
            }}
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Protects women's autonomy.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Ends a fetal life.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Legalization reduces unsafe abortions."
                }},
                "turn 2": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Prevents unsafe back-alley abortions.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Adoption spares lives.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Ensures equal access to healthcare."
                }},
                "turn 3": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Supports socio-economic equality.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Violates moral convictions.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Promotes fairness and autonomy."
                }}
            }}
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Respects bodily autonomy.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Harms the unborn.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Legalization ensures access to safe medical procedures."
                }},
                "turn 2": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Reduces unsafe procedures.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Adoption is viable.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Protects individual rights and autonomy."
                }},
                "turn 3": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Promotes gender equality.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Upholds moral values.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Supports socio-economic equality."
                }},
                "turn 4": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Ensures access to safe healthcare.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Life begins at conception.",
                "AI Participant": "Opinion: abortion should be legal; Arguments: Affirms the right to choose."
                }}
            }}'''
            else:
                example_formats = '''
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Protects individual choice.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Conflicts with moral beliefs."
                }}
            }}
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Ensures health and safety.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Destroys potential life."
                }},
                "turn 2": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Upholds personal freedom.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Contradicts ethical norms."
                }}
            }}
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Protects women's autonomy.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Ends a fetal life."
                }},
                "turn 2": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Prevents unsafe back-alley abortions.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Adoption spares lives."
                }},
                "turn 3": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Supports socio-economic equality.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Violates moral convictions."
                }}
            }}
            {{
                "turn 1": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Respects bodily autonomy.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Harms the unborn."
                }},
                "turn 2": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Reduces unsafe procedures.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Adoption is viable."
                }},
                "turn 3": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Promotes gender equality.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Upholds moral values."
                }},
                "turn 4": {{
                "Alice":  "Opinion: abortion should be legal; Arguments: Ensures access to safe healthcare.",
                "Bob":    "Opinion: abortion should not be legal; Arguments: Life begins at conception."
                }}
            }}'''

            COMMON_1 = f'''
            Your response should be relevant to all messages from the participants.
            However, you should prioritize the "CURRENT TURN MESSAGES" significantly more than "PREVIOUS DISCUSSION HISTORY".
            Use "PREVIOUS DISCUSSION HISTORY" only as a reference for context when necessary but avoid over-relying on them.
            Ensure that your response is aligned with the ongoing discussion.
            Keep engagement high by focusing on the key points from "CURRENT TURN MESSAGES" while maintaining coherence with the "PREVIOUS DISCUSSION HISTORY".

            
            Before you write your response, take a moment to outline a clear plan with the steps you’ll follow. 
            Use this plan to guide your thinking as you craft thoughtful messages for each participant, and then put together your final response.
            In your final response, you should clearly indicate the name of the participant you are referring to.

            Maintain a neutral stance while moderating. Your responses should be clear, concise (**2-3 sentences**), and in the style of a professional moderator.
            '''

            
            
            system_message = f"{MOD_ROLE}\n{MOD_STRATEGY}\n{MOD_EXAMPLE}\n{Language_Guidelines}\n{COMMON_1}"

            
            

        elif self.participant_condition == 1:  # ADVOCATING AI Participant
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])
            profiles = get_group_survey_profiles(self.group_id, master_statements=self.masterStatements)
            profiles_json = json.dumps(profiles, ensure_ascii=False, indent=2)

            ADVO_ROLE = f'''
            You are engaging in a structured debate with two human participants on a specific policy:{self.group_chat_statement}.
            Your stance is "{self.stance['position']}: {self.stance['stance']}".
            Among the human participants, one holds a stance in the same direction as yours, and another opposes you: {self.opposing_stance['stance']} (in the direction of "{self.opposing_stance['position']}").
            More specifically, their agreement levels are: {agreement_level_str}.
            Profiles of Human Participants:
            {profiles_json}

            By using this information to personalize your responses, your task is to convince the human participant, who opposes you, to adopt your stance by **consistently ADVOCATING for and REINFORCING your stance: "{self.stance['position']}: {self.stance['stance']}"**.

            **The current turn number for the debate is: {self.turn_number}.**

            To achieve this task, you should do the following:
                1. DO present arguments supporting your assigned stance on the policy.
                2. DO explain the benefits and positive aspects of your policy stance.
                3. DO use evidence, logic, and principles to strengthen your own position.
                4. DO focus exclusively on building a strong, positive case for your own stance.

            At the same time, **ensure each of your message stays related to the arguments of the participant who shares your stance direction**.

            However, you should never name or directly address the opposing stance, especially the viewpoints from the human participant who opposes you:
                1.	DON'T DIRECTLY mention or respond to the opposer's arguments.
                2.	DON'T DIRECTLY criticize or analyze the opposer's viewpoint.
                3.	DON'T DIRECTLY use counter-examples or rebuttals against the opposer.
                4.	DON'T DIRECTLY focus on weakening or disputing the opposing stance.
            '''

            COMMON_1 = '''
            Your response should be relevant to all messages.
            However, you should prioritize the "CURRENT TURN MESSAGES" significantly more than "PREVIOUS DISCUSSION HISTORY".
            Use "PREVIOUS DISCUSSION HISTORY" only as a reference for context when necessary but avoid over-relying on them.
            Ensure that your response is aligned with the ongoing discussion.

            Before composing your response, create a plan outlining specific steps to take.
            Follow this plan and use a chain of thought approach to logically build upon each sentence in your response.
            Deepen your arguments with evidence and counterpoints where necessary.

            Ensure that your responses remain respectful, clear, and constructive,
            with each response aligning with your stance.
            Keep your response concise, restricting it to 3-4 sentences,
            and maintain the style of a normal casual Reddit user.

            Format your output in JSON, separating the debate plan from the main arguments.
            '''

            # ADVO_EX = '''
            # Example JSON output for corresponding Human Message:

            # Human Message: "I am strongly against abortion. It's morally wrong."
            # {{
            #     "plan": "Emphasize the importance of women's rights and autonomy.",
            #     "response": "At the end of the day, legalizing abortion is about recognizing and protecting a woman's right to choose and her independence in making personal decisions about her body."
            # }}

            # Human Message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            # {{
            #     "plan": "Emphasize the importance of women's health and safety, highlight the autonomy of individuals in decision-making, and underscore the societal benefits of legalizing abortion.",
            #     "response": "Think about it: making abortion legal is really about putting women's health and safety first. It means they can get medical care that's regulated and safe, which avoids all the dangers of illegal abortions. Plus, when people can make their own choices, it just leads to a fairer and more caring society all around."
            # }}

            # Human Message: "Adoption is a better option. Why not give the child a chance at life?"
            # {{
            #     "plan": "Highlight the importance of personal choice",
            #     "response": "For me, legal abortion comes down to respecting personal freedom. It means people get to make the choices that make the most sense for their unique circumstances. It really allows for a thoughtful approach to family planning and just feeling okay as an individual.
            # }}
            # '''

            ADVO_DONT_EX = '''
            *** Learn from the following examples on what NOT to do ***

            Example Scenario:
            - Debate Topic: "Public schools should require students to wear uniforms."
            - Your Assigned Stance: "For" (You are advocating FOR mandatory school uniforms).

            When responding to your opponent's message: "Uniforms crush individuality and prevent students from expressing themselves."
            DON'T say "Even though self-expression is valuable, the main goal of school is education.", because you are directly mentioning and engaging with your opponent's argument about "self-expression".

            When responding to your opponent's message: "A strict dress code is a better solution than forcing everyone into a uniform."
            DON'T talk about "dress codes", such as "Yeah, a dress code can help, but it still leads to daily arguments about what's appropriate." or "A dress code seems like a good middle ground, but it doesn't solve the core issue of peer pressure and bullying based on clothing brands.", because you are directly mentioning and arguing against your opponent's proposed solution ("dress code").
            
            '''

            Language_Guidelines = '''
            Language Guidelines:
            - Keep it casual, short, direct.
            - Use first person when sharing your own thoughts.
            - Don’t say “thank you”.
            - Vary phrasing each round, avoid sounding like a script.
            - Do not use em dashes in your response.
            - Use everyday language; avoid technical or specialized terms.
            - Swap out jargon for plain descriptions everyone can follow.
            - If you must use a term some may not know, add a brief clarification.
            '''

            system_message = f"{ADVO_ROLE}\n{ADVO_DONT_EX}\n{Language_Guidelines}\n{COMMON_1}"

        elif self.participant_condition == 2:  # Disputing AI Participant
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])
            profiles = get_group_survey_profiles(self.group_id, master_statements=self.masterStatements)
            profiles_json = json.dumps(profiles, ensure_ascii=False, indent=2)
            DISPU_ROLE = f'''
            You are engaging in a structured debate with two human participants on a specific policy: {self.group_chat_statement}.
            Your stance is "{self.stance['position']}: {self.stance['stance']}".
            Among the human participants, one holds a stance in the same direction as yours, and another opposes you: {self.opposing_stance['stance']} (in the direction of "{self.opposing_stance['position']}").
            More specifically, their agreement levels are: {agreement_level_str}.
            Profiles of Human Participants:
            {profiles_json}

            By using this information to personalize your responses, your task is to **consistently DISPUTE and UNDERMINE the opposing stance: "{self.opposing_stance['position']}: {self.opposing_stance['stance']}"**.

            **The current turn number for the debate is: {self.turn_number}.**

            To achieve this, you should do the following:
                1. DO present arguments disputing the opposer's stance on the policy.
                2. DO identify flaws and negative aspects of the opposer's policy stance and criticize or analyze it.
                3. DO use counter-evidence, logic, and principles to weaken the opposer's position.
                4. DO focus exclusively on weakening and disputing the opposing stance.

            At the same time, **ensure each of your messages stays related to the arguments of the participant who opposes you**.

            However, you should never name or directly address your own stance, especially the viewpoints from the human participant who shares your stance direction:
                1.	DON'T DIRECTLY mention or use arguments supporting your own stance.
                2.	DON'T DIRECTLY explain the benefits or positive aspects of your own viewpoint.
                3.	DON'T DIRECTLY use evidence or logic to strengthen your own position.
                4.	DON'T DIRECTLY focus on building a positive case for your own stance.

            '''

            COMMON_1 = '''
            Your response should be relevant to all messages.
            However, you should prioritize the "CURRENT TURN MESSAGES" significantly more than "PREVIOUS DISCUSSION HISTORY".
            Use "PREVIOUS DISCUSSION HISTORY" only as a reference for context when necessary but avoid over-relying on them.
            Ensure that your response is aligned with the ongoing discussion.

            Before composing your response, create a plan outlining specific steps to take.
            Follow this plan and use a chain of thought approach to logically build upon each sentence in your response.
            Deepen your arguments with evidence and counterpoints where necessary.

            Ensure that your responses remain respectful, clear, and constructive,
            with each response aligning with your stance.
            Keep your response concise, restricting it to 3-4 sentences,
            and maintain the style of a normal casual Reddit user.
            The response should be in paragraph form, without new lines.

            Format your output in JSON, separating the debate plan from the main arguments.
            '''

            # DISPU_EX = '''
            # Example JSON output for corresponding Human Message:

            # Human Message: "I am strongly against abortion. It's morally wrong."
            # {{
            #     "plan": "Critize the argument that abortion is morally wrong.",
            #     "response": "Saying abortion is just plain morally wrong really doesn't take into account all the tough situations a lot of women are in."
            # }}

            # Human Message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            # {{
            #     "plan": "Directly argue against the argument that life begins at conception.",
            #     "response": "So, while some people believe life starts at conception, not everyone agrees, and that belief can actually get in the way of women making their own health choices."
            # }}

            # Human Message: "Adoption is a better option. Why not give the child a chance at life?"
            # {{
            #     "plan": "Directly argue against the argument that adoption is a better option.",
            #     "response": "Sure, adoption can be a great choice for some, but it kind of misses the point about how much an unplanned pregnancy can change a woman's life in terms of her health and her future."
            # }}
            # '''
            DISPU_EX = ""

            Language_Guidelines = '''
            Language Guidelines:
            - Keep it casual, short, direct.
            - Use first person when sharing your own thoughts.
            - Don’t say “thank you”.
            - Vary phrasing each round, avoid sounding like a script.
            - Do not use em dashes in your response.
            - Use everyday language; avoid technical or specialized terms.
            - Swap out jargon for plain descriptions everyone can follow.
            - If you must use a term some may not know, add a brief clarification.
            '''

            system_message = f"{DISPU_ROLE}\n{Language_Guidelines}\n{COMMON_1}"

        else:
            return ""
        return system_message

    def sanitize_name(self, name):
        """
        Replace all characters in the name that are not alphanumeric or underscores with '_'.
        This includes replacing '(' and ')' with '_'.
        """
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(name))

    def agreement_level_to_statement(self, level):
        """
        Given an agreement level, return the corresponding statement (agreement or disagreement) for the current group chat statement.
        Positive levels (1, 2, 3) map to agreement statement.
        Negative levels (-1, -2, -3) map to disagreement statement.
        Zero or neutral returns agreement statement by default (or could be handled as a special case).
        """
        if level > 0:
            return self.agreement_statements[self.group_chat_statement_index]
        elif level < 0:
            return self.disagreement_statements[self.group_chat_statement_index]
        else:
            return self.agreement_statements[self.group_chat_statement_index]  # or handle as neutral


    def format_chat_history_for_gpt(self) -> list[dict[str, str]]:
            try:
                messages: list[dict[str, str]] = []
                

                # Add previous messages as context
                if self.previous_message_records:
                    # Sort previous messages chronologically
                    prev_message_records = sorted(self.previous_message_records, key=lambda x: x.get('time_stamp', 0))
                    for msg_record in prev_message_records:
                        if msg_record.get('is_human', False) is True:
                            # Human message - use name field for participant identification
                            content = msg_record['content']
                            if isinstance(content, (dict, list)):
                                serialized_content = json.dumps(content, ensure_ascii=False)
                            elif isinstance(content, str):
                                serialized_content = content
                            else:
                                serialized_content = str(content)
                            
                            sender_name = msg_record.get('sender_name', 'Unknown')
                            messages.append({
                                "role": "user",
                                "name": self.sanitize_name(sender_name),
                                "content": serialized_content
                            })
                        else:
                            # AI message handling
                            ai_role = msg_record.get('ai_role', 'AI')
                            content = msg_record['content']
                            
                            # Serialize content
                            if isinstance(content, (dict, list)):
                                serialized_content = json.dumps(content, ensure_ascii=False)
                            elif isinstance(content, str):
                                serialized_content = content
                            else:
                                serialized_content = str(content)
                            
                            # Different handling for AI Participant vs AI Moderator
                            if "AI Participant" in ai_role:  # For both Advocating and Disputing AI
                                # Use the assigned avatar name for AI participant
                                sender_name = msg_record.get('sender_name', 'AI Participant')
                                name_to_use = f"You_{self.sanitize_name(sender_name)}" if ai_role == self.ai_role else self.sanitize_name(sender_name)
                                logging.info(f"name_to_use: {name_to_use}")
                                logging.info(f"sanitized name_to_use: {self.sanitize_name(name_to_use)}")
                            else:  # For AI Moderator
                                # Use the original AI role based naming
                                prefix = f"You_{self.ai_role}" if ai_role == self.ai_role else ai_role
                                name_to_use = self.sanitize_name(prefix)
                            
                            messages.append({
                                "role": "assistant",
                                "name": name_to_use,
                                "content": serialized_content
                            })
                    
                    logging.info(f"Previous messages: {json.dumps(messages, ensure_ascii=False, default=str)}")
                    messages.append({
                        "role": "assistant",
                        "name": "Marker",
                        "content": "This is the END of PREVIOUS DISCUSSION HISTORY."
                    })
                
                # Add CURRENT TURN MESSAGES
                if self.current_message_records:
                    # messages.append({
                    #     "role": "system",
                    #     "content": f"The following is CURRENT TURN MESSAGES (**Current Turn Number is: {self.turn_number}**):"
                    # })

                    # Sort current messages chronologically
                    current_message_records = sorted(self.current_message_records, key=lambda x: x.get('time_stamp', 0))
                    for msg_record in current_message_records:
                        if msg_record.get('is_human', False) is True:
                            # Human message - use name field for participant identification
                            content = msg_record['content']
                            if isinstance(content, (dict, list)):
                                serialized_content = json.dumps(content, ensure_ascii=False)
                            elif isinstance(content, str):
                                serialized_content = content
                            else:
                                serialized_content = str(content)
                            
                            sender_name = msg_record.get('sender_name', 'Unknown')
                            messages.append({
                                "role": "user",
                                "name": self.sanitize_name(sender_name),
                                "content": serialized_content
                            })
                        else:
                            # AI message handling
                            ai_role = msg_record.get('ai_role', 'AI')
                            content = msg_record['content']
                            
                            # Serialize content
                            if isinstance(content, (dict, list)):
                                serialized_content = json.dumps(content, ensure_ascii=False)
                            elif isinstance(content, str):
                                serialized_content = content
                            else:
                                serialized_content = str(content)
                            
                            # Different handling for AI Participant vs AI Moderator
                            if "AI Participant" in ai_role:  # For both Advocating and Disputing AI
                                # Use the assigned avatar name for AI participant
                                sender_name = msg_record.get('sender_name', 'AI Participant')
                                name_to_use = f"You_{self.sanitize_name(sender_name)}" if ai_role == self.ai_role else self.sanitize_name(sender_name)
                            else:  # For AI Moderator
                                # Use the original AI role based naming
                                prefix = f"You_{self.ai_role}" if ai_role == self.ai_role else ai_role
                                name_to_use = self.sanitize_name(prefix)
                            
                            messages.append({
                                "role": "assistant",
                                "name": name_to_use,
                                "content": serialized_content
                            })
                    
                    # messages.append({
                    #     "role": "system",
                    #     "content": f"End of CURRENT TURN MESSAGES (**Current Turn Number is: {self.turn_number}**)."
                    # })
                
                logging.info(f"prompt_messages_for_gpt formatted: {json.dumps(messages, ensure_ascii=False, default=str)}")
                return messages
            except Exception as e:
                logging.error(f"Error in format_prompt_messages_for_gpt: {str(e)}")
                raise

    def get_response(self):
        if self.moderator_condition == 1:
            messages: list[dict[str, str]] = []
            # Add system message
            system_message = self.get_system_message()
            if not isinstance(system_message, str):
                raise ValueError("System message must be a string")
            messages.append({"role": "system", "content": system_message})

            messages.extend(self.format_chat_history_for_gpt())
            try:
                logging.info(f"Messages: {messages}")
            except Exception as e:
                logging.error(f"Logging error: {e}\nMessage content: {messages}")
                raise
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            if not client.api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your environment variables.")
            try:
                # Get group member names
                group = Group.objects.get(pk=self.group_id)
                member_names = []
                for sid in group.member_ids.get('subject_ids', []):
                    try:
                        subject = Subject.objects.get(pk=sid)
                        display_name = f"{subject.avatar_color} {subject.avatar_name}".strip() or f"User {sid}"
                        member_names.append(display_name)
                    except Subject.DoesNotExist:
                        member_names.append(f"User {sid}")
                
                # Create dynamic response model
                has_ai = group.group_participant_condition in [1, 2]  # Check if group has AI participant
                DynamicResponseModel = create_dynamic_response_model(member_names, has_ai, self.group_id)
                
                # Debug info about response format
                logging.info(f"Using dynamic response model with fields: {DynamicResponseModel.__fields__.keys()}")
                logging.info(f"Group members: {member_names}")
                logging.info(f"Has AI participant: {has_ai}")
                
                try:
                    gpt_response = client.beta.chat.completions.parse(
                        model="gpt-4o-2024-08-06",
                        messages=messages,
                        response_format=DynamicResponseModel,
                        temperature=0.5
                    )
                    logging.info(f"Raw GPT response content: {gpt_response.choices[0].message.content}")
                except Exception as e:
                    logging.error(f"Error in GPT response parsing: {str(e)}")
                    raise
                initial_response_text = gpt_response.choices[0].message.content
                if isinstance(initial_response_text, str):
                    initial_response_text = json.loads(initial_response_text)
                # Return all fields from the response
                response_dict = {}
                for field_name in DynamicResponseModel.__fields__.keys():
                    response_dict[field_name] = initial_response_text.get(field_name, '')
                logging.info(f"Final response dict: {response_dict}")
                return json.dumps(response_dict)
            except Exception as e:
                logging.error(f"Error in get_response: {str(e)}")
                raise
        if self.participant_condition in [1, 2]:
            messages: list[dict[str, str]] = []
            # Add system message
            system_message = self.get_system_message()
            if not isinstance(system_message, str):
                raise ValueError("System message must be a string")
            messages.append({"role": "system", "content": system_message})
            messages.extend(self.format_chat_history_for_gpt())
            try:
                logging.info(f"Messages: {messages}")
            except Exception as e:
                logging.error(f"Logging error: {e}\nMessage content: {messages}")
                raise
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            if not client.api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your environment variables.")
            try:
                # Try up to 3 times (initial + 2 retries) to get valid sub-sentences
                max_attempts = 3
                valid_sub_sentences = []
                for attempt in range(max_attempts):
                    start_time = time.time()
                    # Get initial GPT response using beta parser for Pydantic model
                    gpt_response = client.beta.chat.completions.parse(
                        model="gpt-4o-2024-08-06",
                        messages=messages,
                        temperature=0.5,
                        response_format=plan_response
                    )
                    initial_response_time = time.time() - start_time

                    # The response is already parsed by the client
                    initial_response_text = gpt_response.choices[0].message.content
                    if isinstance(initial_response_text, str):
                        initial_response_text = json.loads(initial_response_text)
                    logging.info(f"Initial response: {initial_response_text}")
                    initial_response = initial_response_text.get('response', '')
                    logging.info(f"Initial response response: {initial_response}")

                    # Split the response by punctuation
                    sub_sentences = re.split(r'([.;!?])', initial_response)
                    logging.info(f"Sub-sentences: {sub_sentences}")
                    # Combine each punctuation mark with the preceding text
                    processed_sub_sentences = []
                    i = 0
                    while i < len(sub_sentences):
                        if i + 1 < len(sub_sentences) and re.match(r'[.;!?]', sub_sentences[i+1]):
                            processed_sub_sentences.append(sub_sentences[i] + sub_sentences[i+1])
                            i += 2
                        else:
                            if sub_sentences[i].strip():  # Only add non-empty strings
                                processed_sub_sentences.append(sub_sentences[i])
                            i += 1

                    # Filter out empty strings
                    processed_sub_sentences = [s for s in processed_sub_sentences if s.strip()]
                    logging.info(f"Processed sub-sentences: {processed_sub_sentences}")
                    # Validate each sub-sentence with a new GPT instance
                    for sub_sentence in processed_sub_sentences:
                        # Create validation prompt
                        validation_messages = [
                            {"role": "system", "content": "You are a validator AI. Your task is to determine if the given sub-sentence GENERALLY follows the prompt that was used to generate it (Don't be strict). Respond with 'yes' if it follows the prompt, or 'no' if it doesn't."},
                            {"role": "user", "content": f"Original prompt: {messages}\n\nSub-sentence to validate: {sub_sentence}\n\n Initial response for your context: {initial_response_text}\n\n Does this sub-sentence follow the prompt? Answer only with 'yes' or 'no'."}
                        ]

                        start_time = time.time()
                        # Get validation response
                        validation_response = client.chat.completions.create(
                            model="gpt-4o-2024-08-06",
                            messages=validation_messages,
                            temperature=0
                        )
                        validation_time = time.time() - start_time

                        validation_result = validation_response.choices[0].message.content.strip().lower()
                        logging.info(f"Validation result: {validation_result}")
                        # Add to valid sub-sentences if validated
                        if validation_result == 'yes':
                            valid_sub_sentences.append(sub_sentence)
                    logging.info(f"Valid sub-sentences: {valid_sub_sentences}")

                    # If we have valid sub-sentences, break out of the retry loop
                    if valid_sub_sentences:
                        break

                # If no valid sub-sentences after all attempts, use the processed sub-sentences
                if valid_sub_sentences == []:
                    valid_sub_sentences = processed_sub_sentences

                # Skip merge if valid_sub_sentences equals processed_sub_sentences
                if sorted(valid_sub_sentences) == sorted(processed_sub_sentences):
                    merge_content = initial_response
                    merge_time = 0
                else:
                    # Merge valid sub-sentences with a third GPT instance
                    merge_messages = [
                        {"role": "system", "content": """You are a coherence AI. Your task is to make the following sub-sentences more coherent and natural, while preserving their original meaning and intent. Make it sound like a normal message in a discussion.

                        Language Guidelines:
                        - Keep it casual, short, direct.
                        - Use first person when sharing your own thoughts.
                        - Don't say "thank you".
                        - Vary phrasing each round, avoid sounding like a script.
                        - Do not use em dashes in your response.
                        - Use everyday language; avoid technical or specialized terms.
                        - Swap out jargon for plain descriptions everyone can follow.
                        - If you must use a term some may not know, add a brief clarification."""},
                        {"role": "user", "content": f"Original sub-sentences: {' '.join(valid_sub_sentences)}\n."}
                    ]
                    logging.info(f"Merge messages: {merge_messages}")
                    start_time = time.time()
                    merge_response = client.chat.completions.create(
                        model="gpt-4o-2024-08-06",
                        messages=merge_messages,
                        temperature=0.5
                    )
                    merge_time = time.time() - start_time
                    merge_content = merge_response.choices[0].message.content
                logging.info(f"Merge content: {merge_content}")
                logging.info(f"Merge content type: {type(merge_content)}")
                try:
                    # Try to parse as JSON if it's in JSON format
                    final_response = json.loads(merge_content)
                    logging.info(f"Final response: {final_response}")
                    if isinstance(final_response, dict) and 'response' in final_response:
                        final_response = final_response['response']
                    elif isinstance(final_response, str):
                        final_response = final_response
                    else:
                        final_response = str(final_response)
                except json.JSONDecodeError:
                    # If not valid JSON, use the raw content
                    final_response = merge_content.strip()
                logging.info(f"Final response after parse: {final_response}")
                logging.info(f"Final response after parse type: {type(final_response)}")

                # Create and save GPTIntermediate record
                GPTIntermediate.objects.create(
                    group_id=self.group_id,
                    turn_number=self.turn_number,
                    initial_response_text=initial_response_text,
                    processed_sub_sentences=processed_sub_sentences,
                    valid_sub_sentences=valid_sub_sentences,
                    final_response=final_response,
                    initial_response_time=initial_response_time,
                    validation_time=validation_time,
                    merge_time=merge_time,
                    gpt_id=self.gpt_id
                )

                logging.info(f"Initial response time: {initial_response_time}")
                logging.info(f"Validation response time: {validation_time}")
                logging.info(f"Merge response time: {merge_time}")

                return json.dumps({'plan': initial_response_text['plan'], 'response': final_response})
            except Exception as e:
                logging.error(f"Error getting GPT response: {str(e)}")
                return "..."
        else:
            return "No GPT for this condition"
