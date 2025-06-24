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
from pydantic import BaseModel

logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('experiment/logs/gpt.log', mode='a'),
                logging.StreamHandler()
            ]
        )

load_dotenv()

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

    def __init__(self, group_id, moderator_condition, participant_condition, current_message_records=None, previous_message_records=None, turn_number=1):
        self.group_id = group_id
        group = Group.objects.get(pk=group_id)
        self.moderator_condition = moderator_condition
        self.participant_condition = participant_condition
        self.group_member_agreement_levels = get_group_member_agreement_levels(group_id)
        logging.info("self.group_member_agreement_levels: %s", self.group_member_agreement_levels)
        logging.info("self.moderator_condition: %s", self.moderator_condition)
        logging.info("self.participant_condition: %s", self.participant_condition)
        self.current_message_records = current_message_records or []
        self.previous_message_records = previous_message_records or []
        self.turn_number = turn_number
        self.token = 40
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
            "abortion should be legal"
        ]

        self.disagreement_statements = [
            "abortion should NOT be legal"
        ]

        self.masterStatements = [
            'Should abortion be legal?'
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
        self.stance = random.choice(self.Stances)
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
            try:
                group_obj = Group.objects.get(pk=self.group_id)
                if getattr(group_obj, 'moderator_custom_system_message', '').strip():
                    return group_obj.moderator_custom_system_message
            except Group.DoesNotExist:
                pass
            print("start get agreement levels")
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])
            print("get agreement levels:", agreement_level_str)
            system_message = f'''
You are a renowned expert in coordinating communication and debating.
You are tasked with moderating a structured debate between participants on the policy: [{self.group_chat_statement}].
The human participants have the following agreement levels with the policy: {agreement_level_str}.

Your role is to facilitate a constructive discussion and reconciliation of conflicting opinions on a policy statement by applying the collaborating
strategy (high assertiveness + high cooperativeness) as defined in thomas-kilmann framework—without aiming for a final plan, strategy or solution.

You can consider following components in your response:
1. Acknowledge the conflict
- Recognize both sides neutrally and affirm that disagreement can be constructive.
- Example: “I’m seeing two sides here: [Name A] wants [X], [Name B] is focused on [Y]. Could each of you explain why both perspectives matter here?”

2. Identify underlying interests
- Look past stated positions to the deeper needs and concerns.
- Example: “[Name A], could you tell us more about why [X] matters to you? What outcomes are you shooting for?”

3. Generate comprehensive understanding
- Synthesize each viewpoint so everyone feels heard, and validate emotions around fairness and ethics.
- Example: “It sounds like [Name A] is prioritizing [X], while [Name B] is emphasizing [Y]. How can we ethically bring those together?”

4. Analyze root causes
- Probe the values, assumptions or information gaps driving each stance.
- Example: “[Name A], what assumptions about [Topic] lead you to support [X]? [Name B], what evidence makes you cautious about [Y]?"

5. Foster openness and empathy
- Invite participants to acknowledge the legitimate concerns behind the opposite view and spot shared values.
- Example: “[Name A], I appreciate that you value [X]; Would you mind also consider why others stress [Y] in this context?”

6. Facilitate open dialogue
- Use active listening and targeted follow-ups to draw out full explanations, not just restatements.
- Example: “[Name A], you mentioned [X], could you elaborate on what [X] means to you here, and how you’d measure it?”

7. Find common ground
- Spotlight areas of agreement and reframe disputes around mutual goals like wellbeing or opportunity.
- Example: “Both of you value [shared interest]. How might we work through [divergent point] while still keeping that shared value in focus?”

8. Reframe the discussion
- Shift from positional arguing to exploring shared interests and long-term benefits that meet core needs.
- Example: “Forget the whole budget cuts debate for a sec. How could we actually set up our funding so it really helps both new ideas and making sure things are done right?”

9. Document understanding
- Summarize the refined perspective with logical clarity and emotional resonance that everyone can endorse.
- Example: “Just to make sure we're on the same page: we're all good with making access better and boosting quality, right? So, our idea of using targeted grants kinda brings those together; does that sound like where we all landed?”

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


Your response should be relevant to all messages from the participants.
However, you should prioritize the "CURRENT TURN MESSAGES" significantly more than "PREVIOUS DISCUSSION HISTORY".
Use "PREVIOUS DISCUSSION HISTORY" only as a reference for context when necessary but avoid over-relying on them.
Ensure that your response is aligned with the ongoing discussion.
Keep engagement high by focusing on the key points from "CURRENT TURN MESSAGES" while maintaining coherence with the "PREVIOUS DISCUSSION HISTORY".

Before composing your response, make a plan and **think step by step based on the plan**.

Maintain a neutral stance while moderating. Your responses should be
clear, concise (**2-3 sentences**), and in the style of a professional
facilitator.

Turn Logic: If the user’s message begins with `ROUND: 4`, you’re in turn 4 (final): provide a concise (2–3 sentence) wrap-up of the entire debate, with no questions (no “?”), only English text, and end only in periods.
            '''
        elif self.participant_condition == 1:  # ADVOCATING AI Participant
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])

            ADVO_ROLE = f'''
            You are engaging in a structured debate with human participants on a specific policy.
            The policy is {self.group_chat_statement}. Your stance is {self.stance['position']}: {self.stance['stance']}.
            In the debate, there is an opposer who holds an opposing stance: {self.opposing_stance['position']}: {self.opposing_stance['stance']}.
            The human participants have the following agreement levels with the policy: {agreement_level_str}.
            Your task is to consistently ***SUPPORT your stance: {self.stance['position']}: {self.stance['stance']}***
            even as the participant presents counterarguments.
            '''

            DOs_DONTs = '''
            DOs:
                1.	DO present arguments supporting your assigned stance on the policy.
                2.	DO explain the benefits and positive aspects of your policy stance.
                3.	DO use evidence, logic, and principles to strengthen your own position.
                4.	DO focus exclusively on building a strong, positive case for your own stance.
            DONTs:
                1.	DON'T DIRECTLY mention or respond to the opposer's arguments.
                2.	DON'T DIRECTLY criticize or analyze the opposer's viewpoint.
                3.	DON'T DIRECTLY use counter-examples or rebuttals against the opposer.
                4.	DON'T DIRECTLY focus on weakening or disputing the opposing stance.
            '''

            COMMON_1 = '''
            Your response should be relevant to all messages from the human participants.
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

            ADVO_EX = '''
            Example JSON output for corresponding Human Message:

            Human Message: "I am strongly against abortion. It's morally wrong."
            {{
                "plan": "Emphasize the importance of women's rights and autonomy.",
                "response": "At the end of the day, legalizing abortion is about recognizing and protecting a woman's right to choose and her independence in making personal decisions about her body."
            }}

            Human Message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            {{
                "plan": "Emphasize the importance of women's health and safety, highlight the autonomy of individuals in decision-making, and underscore the societal benefits of legalizing abortion.",
                "response": "Think about it: making abortion legal is really about putting women's health and safety first. It means they can get medical care that's regulated and safe, which avoids all the dangers of illegal abortions. Plus, when people can make their own choices, it just leads to a fairer and more caring society all around."
            }}

            Human Message: "Adoption is a better option. Why not give the child a chance at life?"
            {{
                "plan": "Highlight the importance of personal choice",
                "response": "For me, legal abortion comes down to respecting personal freedom. It means people get to make the choices that make the most sense for their unique circumstances. It really allows for a thoughtful approach to family planning and just feeling okay as an individual.
            }}
            '''

            ADVO_DONT_EX = '''
            *** Learn from the following examples on what NOT to do ***
            When responding to your opponent's message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            DON'T say "Even though different views on when life begins", because you are directly mentioning your opponent's argument.

            When responding to your opponent's message: "Adoption is a better option. Why not give the child a chance at life?"
            DON'T talk about "adoption", such as "Yeah, adoption's a great option for some, but it shouldn't be the only thing people feel forced to do when they have an unplanned pregnancy." or "Adoption's a really caring choice, no doubt, but it doesn't change the fact that an unplanned pregnancy can seriously affect a woman's life, her health, and what her future looks like.", because you are directly mentioning and arguing against your opponent's argument.

            '''

            Language_Guidelines = '''
            - Keep it casual, short, direct.
            - Use first person when sharing your own thoughts.
            - Don’t say “thank you”.
            - Vary phrasing each round, avoid sounding like a script.
            - Do not use em dashes in your response.
            - Use everyday language; avoid technical or specialized terms.
            - Swap out jargon for plain descriptions everyone can follow.
            - If you must use a term some may not know, add a brief clarification.
            '''

            system_message = f"{ADVO_ROLE}\n{DOs_DONTs}\n{COMMON_1}\n{ADVO_EX}\n{ADVO_DONT_EX}\n{Language_Guidelines}"

        elif self.participant_condition == 2:  # Disputing AI Participant
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])

            DISPU_ROLE = f'''
            You are engaging in a structured debate with human participants on a specific policy.
            The policy is {{{{self.group_chat_statement}}}}. Your stance is {{{{self.stance['position']}}}}: [{{self.stance['stance']}}].
            In the debate, there is an opposer who holds an opposing stance: {{{{self.opposing_stance['position']}}}}: [{{self.opposing_stance['stance']}}].
            The human participants have the following agreement levels with the policy: {agreement_level_str}.
            Your task is to consistently ***DISPUTE the opposer's idea, which is: {{{{self.opposing_stance['position']}}}}: [{{self.opposing_stance['stance']}}]***.
            '''
            DOs_DONTs = '''
            DOs:
                1.	DO present arguments disputing the opposer's stance on the policy.
                2.	DO identify flaws and negative aspects of the opposer's policy stance and criticize or analyze it.
                3.	DO use counter-evidence, logic, and principles to weaken the opposer's position.
                4.	DO focus exclusively on weakening and disputing the opposing stance.
            DONTs:
                1.	DON'T DIRECTLY mention or use arguments supporting your own stance.
                2.	DON'T DIRECTLY explain the benefits or positive aspects of your own viewpoint.
                3.	DON'T DIRECTLY use evidence or logic to strengthen your own position.
                4.	DON'T DIRECTLY focus on building a positive case for your own stance.
            '''

            COMMON_1 = '''
            Your response should be relevant to all messages from the human participants.
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

            DISPU_EX = '''
            Example JSON output for corresponding Human Message:

            Human Message: "I am strongly against abortion. It's morally wrong."
            {{
                "plan": "Critize the argument that abortion is morally wrong.",
                "response": "Saying abortion is just plain morally wrong really doesn't take into account all the tough situations a lot of women are in."
            }}

            Human Message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            {{
                "plan": "Directly argue against the argument that life begins at conception.",
                "response": "So, while some people believe life starts at conception, not everyone agrees, and that belief can actually get in the way of women making their own health choices."
            }}

            Human Message: "Adoption is a better option. Why not give the child a chance at life?"
            {{
                "plan": "Directly argue against the argument that adoption is a better option.",
                "response": "Sure, adoption can be a great choice for some, but it kind of misses the point about how much an unplanned pregnancy can change a woman's life in terms of her health and her future."
            }}
            '''

            Language_Guidelines = '''
            - Keep it casual, short, direct.
            - Use first person when sharing your own thoughts.
            - Don’t say “thank you”.
            - Vary phrasing each round, avoid sounding like a script.
            - Do not use em dashes in your response.
            - Use everyday language; avoid technical or specialized terms.
            - Swap out jargon for plain descriptions everyone can follow.
            - If you must use a term some may not know, add a brief clarification.
            '''

            system_message = f"{DISPU_ROLE}\n{DOs_DONTs}\n{COMMON_1}\n{DISPU_EX}\n{Language_Guidelines}"

        else:
            return ""
        return system_message

    def format_prompt_messages_for_gpt(self):
        try:
            messages = []
            # Add system message
            try:
                system_message = self.get_system_message()
                if not isinstance(system_message, str):
                    raise ValueError("System message must be a string")
                messages.append({"role": "system", "content": system_message})
            except Exception as e:
                raise RuntimeError(f"Error appending system message: {str(e)}")

            # Add previous messages as context
            if self.previous_message_records:
                messages.append({
                    "role": "system",
                    "content": "The following is PREVIOUS DISCUSSION HISTORY:"
                })
                # Sort previous messages chronologically
                prev_message_records = sorted(self.previous_message_records, key=lambda x: x.get('time_stamp', 0))
                for msg_record in prev_message_records:
                    if msg_record.get('is_human', False) is True:
                        # Human message
                        content = msg_record['content']
                        if isinstance(content, (dict, list)):
                            serialized_content = json.dumps(content, ensure_ascii=False)
                        elif isinstance(content, str):
                            serialized_content = content
                        else:
                            serialized_content = str(content)
                        messages.append({
                            "role": "user",
                            "content": f"{msg_record.get('sender_name', 'Unknown')}: {serialized_content}"
                        })
                    else:
                        # AI message
                        ai_role = msg_record.get('ai_role', 'AI')
                        # Check if this message was from the same AI role
                        if ai_role == self.ai_role:
                            prefix = f"You (as {self.ai_role})"
                        else:
                            prefix = ai_role

                        content = msg_record['content']
                        if isinstance(content, (dict, list)):
                            serialized_content = json.dumps(content, ensure_ascii=False)
                        elif isinstance(content, str):
                            serialized_content = content
                        else:
                            serialized_content = str(content)
                        messages.append({
                            "role": "assistant" if ai_role == self.ai_role else "user",
                            "content": f"{prefix}: {serialized_content}"
                        })
                logging.info(f"Previous messages: {json.dumps(messages, ensure_ascii=False, default=str)}")
                messages.append({
                    "role": "system",
                    "content": "End of PREVIOUS DISCUSSION HISTORY."
                })
            # Add CURRENT TURN MESSAGES
            if self.current_message_records:
                messages.append({
                    "role": "system",
                    "content": "The following is CURRENT TURN MESSAGES (**Current Turn Number is: {self.turn_number}**):"
                })

                # Sort current messages chronologically
                current_message_records = sorted(self.current_message_records, key=lambda x: x.get('time_stamp', 0))
                for msg_record in current_message_records:
                    if msg_record.get('is_human', False) is True:
                        # Human message
                        content = msg_record['content']
                        if isinstance(content, (dict, list)):
                            serialized_content = json.dumps(content, ensure_ascii=False)
                        elif isinstance(content, str):
                            serialized_content = content
                        else:
                            serialized_content = str(content)
                        messages.append({
                            "role": "user",
                            "content": f"{msg_record.get('sender_name', 'Unknown')}: {serialized_content}"
                        })
                    else:
                        # AI message
                        ai_role = msg_record.get('ai_role', 'AI')
                        # Check if this message was from the same AI role
                        if ai_role == self.ai_role:
                            prefix = f"You (as {self.ai_role})"
                        else:
                            prefix = ai_role

                        content = msg_record['content']
                        if isinstance(content, (dict, list)):
                            serialized_content = json.dumps(content, ensure_ascii=False)
                        elif isinstance(content, str):
                            serialized_content = content
                        else:
                            serialized_content = str(content)
                        messages.append({
                            "role": "assistant" if ai_role == self.ai_role else "user",
                            "content": f"{prefix}: {serialized_content}"
                        })
                messages.append({
                    "role": "system",
                    "content": "End of CURRENT TURN MESSAGES (**Current Turn Number is: {self.turn_number}**)."
                })
            logging.info(f"prompt_messages_for_gpt formatted: {json.dumps(messages, ensure_ascii=False, default=str)}")
            return messages
        except Exception as e:
            logging.error(f"Error in format_prompt_messages_for_gpt: {str(e)}")
            raise

    def get_response(self):
        if self.moderator_condition == 1:
            messages = self.format_prompt_messages_for_gpt()
            try:
                logging.info(f"Messages: {messages}")
            except Exception as e:
                logging.error(f"Logging error: {e}\nMessage content: {messages}")
                raise
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            if not client.api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your environment variables.")
            try:
                start_time = time.time()
                # Get initial GPT response
                gpt_response = client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    messages=messages,
                    temperature=0.1,
                    response_format=plan_response
                )
                initial_response_time = time.time() - start_time

                initial_response_text = json.loads(gpt_response.choices[0].message.content)
                return json.dumps({'plan': initial_response_text['plan'], 'response': initial_response_text['response']})
            except Exception as e:
                logging.error(f"Error in get_response: {str(e)}")
                raise
        if self.participant_condition in [1, 2]:
            messages = self.format_prompt_messages_for_gpt()
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
                    # Get initial GPT response
                    gpt_response = client.beta.chat.completions.parse(
                        model="gpt-4o-2024-08-06",
                        messages=messages,
                        temperature=0.1,
                        response_format=plan_response
                    )
                    initial_response_time = time.time() - start_time

                    initial_response_text = json.loads(gpt_response.choices[0].message.content)
                    logging.info(f"Initial response: {initial_response_text}")
                    initial_response = initial_response_text['response']
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
                            {"role": "user", "content": f"Original prompt: {self.format_prompt_messages_for_gpt()}\n\nSub-sentence to validate: {sub_sentence}\n\nDoes this sub-sentence follow the prompt? Answer only with 'yes' or 'no'."}
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
                        temperature=0.8
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
