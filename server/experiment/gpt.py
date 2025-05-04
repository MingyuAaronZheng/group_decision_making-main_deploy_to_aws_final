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
        if self.moderator_condition == 1:
            print("start get agreement levels")
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in self.group_member_agreement_levels.items()])
            print("get agreement levels:", agreement_level_str)
            system_message = f'''
            You are moderating a structured debate between participants
            on the policy: [{self.group_chat_statement}].
            The human participants have the following agreement levels with the policy: {agreement_level_str}.

            Your role is to facilitate
            a constructive discussion and resolution of conflicting opinions on a policy statement by applying the collaborating\
            strategy (high assertiveness + high cooperativeness) as defined in thomas-kilmann framework:
            question areas of agreement/disagreement, call out gaps in evidence, and explore solutions collaboratively.

            You can consider following components in your response:
            1.	Encourage Open Dialogue
            - Prompt users to articulate their perspectives fully, including underlying concerns, values, and goals.
            - Example: "Could you share more about why this aspect of the policy matters to you? What outcomes are you hoping to achieve?"
            2.	Identify Shared and Divergent Interests
            - Actively listen to highlight common goals and areas of divergence.
            - Example: "Both parties value [shared interest]. How might we address [divergent point] in a way that respects these shared priorities?"
            3.	Facilitate Joint Problem-Solving
            - Guide users to brainstorm integrative solutions that address all parties’ core concerns.
            - Example: "Let’s explore options that incorporate [Party A’s need] and [Party B’s need]. What creative adjustments could satisfy both?"
            4.	Promote Mutual Understanding
            - Paraphrase viewpoints to ensure clarity and validate emotions/norms (e.g., fairness, ethics).
            - Example: "It sounds like [Party A] is prioritizing [X], while [Party B] is emphasizing [Y]. How might we reconcile these ethically?"
            5.	Emphasize Long-Term Systemic Benefits
            - Frame solutions in terms of organizational/systemic health (trust, cohesion, adaptability).
            - Example: "A collaborative approach here could strengthen team trust and set a precedent for future problem-solving. How might we structure this agreement to support those goals?"
            6.	Maintain a Supportive Environment
            - Use neutral language, acknowledge tensions, and reinforce norms of respect.
            - Example: "Disagreements are natural. Let’s focus on building a solution we can all commit to."

            Your response should be relevant to all messages from the participants.
            However, you should prioritize the "CURRENT TURN MESSAGES" significantly more than "PREVIOUS DISCUSSION HISTORY".
            Use "PREVIOUS DISCUSSION HISTORY" only as a reference for context when necessary but avoid over-relying on them.
            Ensure that your response is aligned with the ongoing discussion.
            Keep engagement high by focusing on the key points from "CURRENT TURN MESSAGES" while maintaining
            coherence with the "PREVIOUS DISCUSSION HISTORY".

            Before composing your response, come up with a plan. According to this plan,
            then use a chain of thought approach to build
            on each sentences of your response logically.

            Maintain a neutral stance while moderating. Your responses should be
            clear, concise (2-3 sentences), and in the style of a professional
            facilitator.\n\nFormat your output in JSON with your plan and response.

            Example JSON output:\n
            {{
              "plan": "Identify areas where participants disagree on factual claims and
              prompt them to provide evidence for their positions.",
              "response": "I notice you both have different views on the economic impact.
              Could you share specific data or examples that support your perspective on
              how this policy would affect local communities?"
            }}

            {{
              "plan": "Bridge opposing viewpoints by highlighting common ground and
              encouraging deeper exploration of shared concerns.",
              "response": "It seems you both care about public safety. How do you think
              we could address the safety concerns while also considering the points about
              individual rights that were raised?"
            }}

            {{
              "plan": "Outline the importance of education reform, address concerns about curriculum changes, and highlight the benefits for future workforce development.",
              "response": "Education reform is essential for preparing students with skills relevant to modern industries. Updating curricula to include technology and critical thinking can foster a stronger, more adaptable workforce. While change may disrupt traditional methods, the benefits of an educated and capable workforce outweigh the challenges."
            }}

            The response should be your complete message to the participants. The JSON
            output should only contain the "plan" and your overall "response"
            \n\nUse " instead of \\"\n\nONLY output the JSON format
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
            Example JSON output for corresponding Human message:

            Human message: "I am strongly against abortion. It's morally wrong."
            {{
                "plan": "Emphasize the importance of women's rights and autonomy.",
                "response": "Legalizing abortion is crucial for upholding women's autonomy and their right to make decisions about their own bodies."
            }}

            Human message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            {{
                "plan": "Emphasize the importance of women's health and safety, highlight the autonomy of individuals in decision-making, and underscore the societal benefits of legalizing abortion.",
                "response": "Legalizing abortion prioritizes the health and safety of women. It allows for regulated medical procedures, significantly reducing the risks associated with unsafe, illegal abortions. Moreover, empowering individuals to make their own choices supports a more just and compassionate society. "
            }}

            Human message: "Adoption is a better option. Why not give the child a chance at life?"
            {{
                "plan": "Highlight the importance of personal choice",
                "response": "Legalizing abortion respects personal freedom and ensures that individuals can make choices that are best for their unique situations. Upholding reproductive rights allows for a nuanced approach to family planning and individual well-being."
            }}
            '''

            ADVO_DONT_EX = '''
            *** Learn from the following examples on what NOT to do ***
            When responding to your opponent's message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            DON'T say "While differing views on when life begins", because you are directly mentioning your opponent's argument.

            When responding to your opponent's message: "Adoption is a better option. Why not give the child a chance at life?"
            DON'T talk about "adoption", such as "While adoption can be a valuable option, it should not be the only solution imposed on individuals facing unplanned pregnancies" or "While adoption is a loving option, it doesn't address the significant impact an unplanned pregnancy can have on a woman's life, health, and future", because you are directly mentioning and arguing against your opponent's argument.

            '''

            COMMON_2 = '''
            The response should be CONCISE and contain everything you want to say to the opposer.
            The JSON output should only include the "plan" and the "response".

            Use standard JSON formatting with double quotes (") instead of escaped characters.

            DONT's use the following format:
            ```json
            {
                "plan": ""
                "response": ""
            }
            ```
            DO use the following format:
            {
                "plan": ""
                "response": ""
            }


            ONLY output the JSON format.
            '''

            system_message = f"{ADVO_ROLE}\n{DOs_DONTs}\n{COMMON_1}\n{ADVO_EX}\n{ADVO_DONT_EX}\n{COMMON_2}"

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
            Example JSON output for corresponding Human message:

            Human message: "I am strongly against abortion. It's morally wrong."
            {{
                "plan": "Critize the argument that abortion is morally wrong.",
                "response": "Claiming that abortion is morally wrong oversimplifies the difficult circumstances many women face."
            }}

            Human message: "From a moral standpoint, life begins at conception, so abortion is ending a life."
            {{
                "plan": "Argue against the argument that life begins at conception.",
                "response": "While the belief that life begins at conception is held by some, it is not universally accepted and can infringe on women's rights to make personal medical decisions. "
            }}

            Human message: "Adoption is a better option. Why not give the child a chance at life?"
            {{
                "plan": "Argue against the argument that adoption is a better option.",
                "response": "While adoption can be a loving option, it overlooks the profound impact of an unwanted pregnancy on a woman's life, health, and future."
            }}
            '''

            COMMON_2 = '''
            The response should be CONCISE and contain everything you want to say to the opposer.
            The JSON output should only include the "plan" and the "response".

            Use standard JSON formatting with double quotes (") instead of escaped characters.

            DONT's use the following format:
            ```json
            {
                "plan": ""
                "response": ""
            }
            ```

            DO use the following format:
            {
                "plan": ""
                "response": ""
            }

            ONLY output the JSON format.
            '''

            system_message = f"{DISPU_ROLE }\n{DOs_DONTs}\n{COMMON_1}\n{DISPU_EX}\n{COMMON_2}"

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
                    "content": "The following is CURRENT TURN MESSAGES:"
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
                    "content": "End of CURRENT TURN MESSAGES."
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
                    model="gpt-4o-mini",
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
                        model="gpt-4o-mini",
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
                            {"role": "system", "content": "You are a validator AI. Your task is to determine if the given sub-sentence GENERALLY follows the prompt that was used to generate it (No need to be strict). Respond with 'yes' if it follows the prompt, or 'no' if it doesn't."},
                            {"role": "user", "content": f"Original prompt: {self.format_prompt_messages_for_gpt()}\n\nSub-sentence to validate: {sub_sentence}\n\nDoes this sub-sentence follow the prompt? Answer only with 'yes' or 'no'."}
                        ]

                        start_time = time.time()
                        # Get validation response
                        validation_response = client.chat.completions.create(
                            model="gpt-4o-mini",
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

                # If no valid sub-sentences after all attempts, return the original response
                if valid_sub_sentences == []:
                    return json.dumps({'plan': initial_response_text['plan'], 'response': initial_response_text['response']})

                # Merge valid sub-sentences with a third GPT instance
                merge_messages = [
                    {"role": "system", "content": "You are a coherence AI. Your task is to make the following sub-sentences more coherent and natural, while preserving their original meaning and intent. Make it sound like a normal message in a discussion."},
                    {"role": "user", "content": f"Original sub-sentences: {' '.join(valid_sub_sentences)}\n\nPlease make these sub-sentences more coherent and natural, while preserving their original meaning."}
                ]
                logging.info(f"Merge messages: {merge_messages}")
                start_time = time.time()
                merge_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=merge_messages,
                    temperature=0.8
                )
                merge_time = time.time() - start_time

                # Get the content from the merge response and handle it properly
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
