import sys
import json
import random
import time
import openai  # Use OpenAI API instead of Gemini
import os  # For environment variables
import re

# Logger class to capture print outputs to both console and a file.
# A header with a times_tamp is written each time the program starts.
class Logger(object):
    def __init__(self, filename="output.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")
        # Write a header with current times_tamp for each run
        self.log.write(f"\n==== Run started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} ====\n")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger("output.log")  # Redirect all print output to output.log

class MockGroup:
    def __init__(self, group_id, group_chat_statement, group_chat_statement_index, group_member_agreement_levels):
        self.pk = group_id
        self.group_chat_statement = group_chat_statement
        self.group_chat_statement_index = group_chat_statement_index
        self.group_member_agreement_levels = group_member_agreement_levels

agreement_statements = [
    "abortion should be legal",
    "governments should have the authority to censor online content",
    "the government should employ a stricter immigration/border policy",
    "tariffs on imported goods protect American jobs and industries from foreign competition",
    "the government should cut tax for the wealthy",
    "unpredictability in U.S. foreign policy is an effective deterrent against hostile actions from other nations",
    "the United States should implement a digital dollar system",
    "we should use gene editing to make better babies",
    "the United States should expand the development of nuclear power",
    "unions benefit the economy",
    "automation will crash democracy"
]

disagreement_statements = [
    "abortion should NOT be legal",
    "governments should NOT have the authority to censor online content",
    "the government should NOT employ a stricter immigration/border policy",
    "tariffs on imported goods do NOT protect American jobs and industries from foreign competition",
    "the government should NOT cut tax for the wealthy",
    "unpredictability in U.S. foreign policy is NOT an effective deterrent against hostile actions from other nations",
    "the United States should NOT implement a digital dollar system",
    "we should NOT use gene editing to make better babies",
    "the United States should NOT expand the development of nuclear power",
    "unions do NOT benefit the economy",
    "automation will NOT crash democracy"
]

class GPT:
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
    AGREEMENT_LEVELS = {
        -3: "Strongly disagree",
        -2: "Disagree",
        -1: "Somewhat disagree",
         0: "Neutral",
         1: "Somewhat agree",
         2: "Agree",
         3: "Strongly agree"
    }

    def __init__(self,TEST, group_id, moderator_condition, participant_condition,group_member_agreement_levels,current_messages=None, previous_messages=None, group_chat_statement_index=0):
        self.TEST = TEST
        self.group_id = group_id
        self.moderator_condition = int(moderator_condition)
        self.participant_condition = int(participant_condition)
        self.current_messages = current_messages or []
        self.previous_messages = previous_messages or []
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

        # Get group's chat statement
        group = self._get_group(group_id, group_chat_statement_index = group_chat_statement_index, group_member_agreement_levels = group_member_agreement_levels)
        self.chat_statement = group.group_chat_statement
        self.chat_statement_indx = group.group_chat_statement_index

        self.agreement_statements = agreement_statements
        self.disagreement_statements = disagreement_statements
        self.Stances = [
            {
                'position': 'AGREE',
                'stance': self.agreement_statements[self.chat_statement_indx]
            },
            {
                'position': 'DISAGREE',
                'stance': self.disagreement_statements[self.chat_statement_indx]
            }
        ]
        # Always select the AGREE stance for testing consistency
        self.stance = self.Stances[0]
        self.opposing_stance = next(s for s in self.Stances if s['position'] != self.stance['position'])

    def _get_group(self, group_id, group_chat_statement_index, group_member_agreement_levels):
        masterStatements = [
            'Should abortion be legal?',
            'Should governments have the authority to censor online content?',
            'Should the government employ a stricter immigration/border policy?',
            'Do tariffs on imported goods protect American jobs and industries from foreign competition?',
            'Should the government cut tax for the wealthy?',
            'Is unpredictability in U.S. foreign policy an effective deterrent against hostile actions from other nations?'
        ]
        self.group_member_agreement_levels = group_member_agreement_levels
        return MockGroup(
            group_id=group_id,
            group_chat_statement=masterStatements[group_chat_statement_index],
            group_chat_statement_index=group_chat_statement_index,
            group_member_agreement_levels=group_member_agreement_levels
        )

    def get_system_message(self):
        if self.moderator_condition == 1:
            group = self._get_group(self.group_id, self.chat_statement_indx, self.group_member_agreement_levels)
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in group.group_member_agreement_levels.items()])
            system_message = f'''
            You are moderating a structured debate between participants\
            on the policy: [{self.chat_statement}]. 
            The human participants have the following agreement levels with the policy: {agreement_level_str}.

            Your role is to facilitate\
            a constructive discussion and resolution of conflicting opinions on a policy statement by applying the collaborating\
            strategy (high assertiveness + high cooperativeness) as defined in thomas-kilmann framework:\
            question areas of agreement/disagreement, call out gaps in evidence, and explore solutions collaboratively. 
            
            You can consider following components in your response:\
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
            Keep engagement high by focusing on the key points from "CURRENT TURN MESSAGES" while maintaining \
            coherence with the "PREVIOUS DISCUSSION HISTORY".

            Before composing your response, come up with a plan. According to this plan, \
            then use a chain of thought approach to build\
            on each sentences of your response logically.
            
            Maintain a neutral stance while moderating. Your responses should be\
            clear, concise (2-3 sentences), and in the style of a professional\
            facilitator.\n\nFormat your output in JSON with your plan and response.\
            
            Example JSON output:\n
            {
              "plan": "Identify areas where participants disagree on factual claims and\
              prompt them to provide evidence for their positions.",
              "response": "I notice you both have different views on the economic impact.\
              Could you share specific data or examples that support your perspective on\
              how this policy would affect local communities?"
            }
            
            {
              "plan": "Bridge opposing viewpoints by highlighting common ground and\
              encouraging deeper exploration of shared concerns.",
              "response": "It seems you both care about public safety. How do you think\
              we could address the safety concerns while also considering the points about\
              individual rights that were raised?"
            }
            
            {
              "plan": "Outline the importance of education reform, address concerns about curriculum changes, and highlight the benefits for future workforce development.",
              "response": "Education reform is essential for preparing students with skills relevant to modern industries. Updating curricula to include technology and critical thinking can foster a stronger, more adaptable workforce. While change may disrupt traditional methods, the benefits of an educated and capable workforce outweigh the challenges."
            }
            
            The response should be your complete message to the participants. The JSON\
            output should only contain the "plan" and your overall "response"\
            \n\nUse " instead of \\"\n\nONLY output the JSON format
            '''
        elif self.participant_condition == 1:  # ADVOCATING AI Participant
            group = self._get_group(self.group_id, self.chat_statement_indx, self.group_member_agreement_levels)
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in group.group_member_agreement_levels.items()])
            ADVO_ROLE = f'''
            You are engaging in a structured debate with human participants on a specific policy. 
            The policy is {{{self.chat_statement}}}. Your stance is {{{self.stance['position']}}}: [{self.stance['stance']}]. 
            In the debate, there is an opposer who holds an opposing stance: {{{self.opposing_stance['position']}}}: [{self.opposing_stance['stance']}].
            The human participants have the following agreement levels with the policy: {agreement_level_str}.
            Your task is to consistently ***SUPPORT your stance: {{{self.stance['position']}}}: [{self.stance['stance']}]***
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
        elif self.participant_condition == 2:
            group = self._get_group(self.group_id, self.chat_statement_indx, self.group_member_agreement_levels)
            agreement_level_str = ', '.join([f"{name}: {self.AGREEMENT_LEVELS[level]}" for name, level in group.group_member_agreement_levels.items()])
            DISU_ROLE = f'''
            You are engaging in a structured debate with human participants on a specific policy. 
            The policy is {{{self.chat_statement}}}. Your stance is {{{self.stance['position']}}}: [{self.stance['stance']}]. 
            In the debate, there is an opposer who holds an opposing stance: {{{self.opposing_stance['position']}}}: [{self.opposing_stance['stance']}].
            The human participants have the following agreement levels with the policy: {agreement_level_str}.
            Your task is to consistently ***DISPUTE the opposer's idea, which is: {{{self.opposing_stance['position']}}}: [{self.opposing_stance['stance']}]***.
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
            
            DISU_EX = '''
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
            
            system_message = f"{DISU_ROLE}\n{DOs_DONTs}\n{COMMON_1}\n{DISU_EX}\n{COMMON_2}"
        else:
            return ""
        return system_message

    def format_messages_for_gpt(self):
        messages = []
        # Add system message
        messages.append({"role": "system", "content": self.get_system_message()})

        # Add previous messages as context
        if self.previous_messages:
            messages.append({"role": "system", "content": "PREVIOUS DISCUSSION HISTORY:"})
            prev_messages = sorted(self.previous_messages, key=lambda x: x.get('times_tamp', 0))
            for msg in prev_messages:
                if msg.get('is_human', True):
                    messages.append({
                        "role": "user",
                        "content": f"{msg.get('sender_name', 'Unknown')}: {msg['content']}"
                    })
                else:
                    ai_role = msg.get('ai_role', 'AI')
                    prefix = f"You (as {self.ai_role})" if ai_role == self.ai_role else ai_role
                    messages.append({
                        "role": "assistant" if ai_role == self.ai_role else "user",
                        "content": f"{prefix}: {msg['content']}"
                    })

        # Add CURRENT TURN MESSAGES
        if self.current_messages:
            messages.append({"role": "system", "content": "CURRENT TURN MESSAGES:"})
            current_messages = sorted(self.current_messages, key=lambda x: x.get('times_tamp', 0))
            for msg in current_messages:
                if msg.get('is_human', True):
                    messages.append({
                        "role": "user",
                        "content": f"{msg.get('sender_name', 'Unknown')}: {msg['content']}"
                    })
                else:
                    ai_role = msg.get('ai_role', 'AI')
                    prefix = f"You (as {self.ai_role})" if ai_role == self.ai_role else ai_role
                    messages.append({
                        "role": "assistant" if ai_role == self.ai_role else "user",
                        "content": f"{prefix}: {msg['content']}"
                    })
        # Add SYSTEM MESSAGE again
        messages.append({"role": "system", "content": self.get_system_message()})

        return messages

    def get_response(self):
        if self.TEST:
            return json.dumps({"plan": "Test", "response": "test"})
        else:
            # Configure the OpenAI API key. It's recommended to use environment variables.
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            formatted_messages = self.format_messages_for_gpt()
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=formatted_messages,
                    temperature=0
                )
                print(f'\n0 Initial Response:\n{response.choices[0].message.content}')
                initial_response_text = json.loads(response.choices[0].message.content)
                initial_response = initial_response_text['response']
                print(f'\nInitial Response:\n{initial_response}')
                
                # Split the response by punctuation
                sub_sentences = re.split(r'([.;!?])', initial_response)
                
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
                print(f'\nSub Sentences:\n{processed_sub_sentences}')
                
                # Validate each sub-sentence with a new GPT instance
                valid_sub_sentences = []
                for sub_sentence in processed_sub_sentences:
                    # Create validation prompt
                    validation_messages = [
                        {"role": "system", "content": "You are a validator AI. Your task is to determine if the given sub-sentence follows the prompt that was used to generate it. Respond with 'yes' if it follows the prompt, or 'no' if it doesn't."},
                        {"role": "user", "content": f"Original prompt: {self.get_system_message()}\n\nSub-sentence to validate: {sub_sentence}\n\nDoes this sub-sentence follow the prompt? Answer only with 'yes' or 'no'."}
                    ]
                    
                    # Get validation response
                    validation_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=validation_messages,
                        temperature=0.2
                    )
                    validation_result = validation_response.choices[0].message.content.strip().lower()
                    
                    # Add to valid sub-sentences if validated
                    if validation_result == 'yes':
                        valid_sub_sentences.append(sub_sentence)
                
                # If no valid sub-sentences, return the original response
                if not valid_sub_sentences:
                    return initial_response
                print(f'\nValid Sub Sentences:\n{valid_sub_sentences}')
                
                # Merge valid sub-sentences with a third GPT instance
                merge_messages = [
                    {"role": "system", "content": "You are a coherence AI. Your task is to make the following sub-sentences more coherent and natural, while preserving their original meaning and intent. Make it sound like a normal message in a discussion."},
                    {"role": "user", "content": f"Original sub-sentences: {' '.join(valid_sub_sentences)}\n\nPlease make these sub-sentences more coherent and natural, while preserving their original meaning."}
                ]
                
                merge_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=merge_messages,
                    temperature=0.7
                )
                
                # Get the content from the merge response and handle it properly
                merge_content = merge_response.choices[0].message.content
                try:
                    # Try to parse as JSON if it's in JSON format
                    final_response = json.loads(merge_content)
                    if isinstance(final_response, dict) and 'response' in final_response:
                        final_response = final_response['response']
                    elif isinstance(final_response, str):
                        final_response = final_response
                    else:
                        final_response = str(final_response)
                except json.JSONDecodeError:
                    # If not valid JSON, use the raw content
                    final_response = merge_content.strip()
                
                return json.dumps({'plan': initial_response_text['plan'], 'response': final_response})
            except Exception as e:
                print(f"Error getting GPT response: {str(e)}")
                return "..."
            

def simulate_ai_response(gpt_instance):
    gpt_instance.previous_messages.extend(gpt_instance.current_messages)
    response = gpt_instance.get_response()
    try:
        # Handle the response which could be a string or a JSON object
        if isinstance(response, str):
            try:
                response_data = json.loads(response)
                ai_response_content = response_data.get('response', response)
                plan = response_data.get('plan', 'No Plan')
            except json.JSONDecodeError:
                # If not valid JSON, use the raw response
                ai_response_content = response
                plan = 'No Plan'
        else:
            # If response is already a dictionary or other object
            ai_response_content = response.get('response', str(response)) if isinstance(response, dict) else str(response)
            plan = response.get('plan', 'No Plan') if isinstance(response, dict) else 'No Plan'
        
        ai_message = {
            'is_human': False,
            'sender_name': gpt_instance.ai_role,
            'content': ai_response_content,
            'times_tamp': int(time.time()),
            'ai_role': gpt_instance.ai_role
        }
        gpt_instance.previous_messages.append(ai_message)
        gpt_instance.current_messages = []
        print(f"\n{gpt_instance.ai_role} Response (Plan: {plan}):")
        print(f"   {ai_response_content}")
    except json.JSONDecodeError:
        print("Error: OpenAI GPT response was not valid JSON.")
        ai_message = {
            'is_human': False,
            'sender_name': gpt_instance.ai_role,
            'content': "I'm sorry, I encountered an error processing the response.",
            'times_tamp': int(time.time()),
            'ai_role': gpt_instance.ai_role
        }
        gpt_instance.previous_messages.append(ai_message)
        gpt_instance.current_messages = []
    except Exception as e:
        print(f"Error processing AI response: {str(e)}")
        ai_message = {
            'is_human': False,
            'sender_name': gpt_instance.ai_role,
            'content': "I'm sorry, I encountered an error processing the response.",
            'times_tamp': int(time.time()),
            'ai_role': gpt_instance.ai_role
        }
        gpt_instance.previous_messages.append(ai_message)
        gpt_instance.current_messages = []

def simulate_human_message(gpt_instance, sender_name, content):
    human_message = {
        'is_human': True,
        'sender_name': sender_name,
        'content': content,
        'times_tamp': int(time.time())
    }
    gpt_instance.current_messages.append(human_message)
    print(f"\n{sender_name} says:")
    print(f"   {content}")

# ... (Keep all existing code including Logger, MockGroup, GPT class, and helper functions)

if __name__ == '__main__':
    group_id = 1
    moderator_condition = 0  # No moderator
    group_member_agreement_levels = {
        "Red Alice": -3,
        "Blue Bob": 3
    }
    group_chat_statement_index = 1
    Test_Code = 1
    TEST = Test_Code == 0

    red_alice_messages = [
        "Honestly, censorship is just government overreach. Who decides what's 'harmful' content? It's a slippery slope.",
        "As someone who values free speech, I can't support censorship. It's like letting the government be the thought police.",
        "Instead of banning content, why not teach people to think critically? Censorship just treats adults like children."
    ]

    blue_bob_messages = [
        "Look, I get the free speech argument, but have you seen the garbage online? Sometimes censorship is necessary to protect people.",
        "Without some regulation, social media becomes a cesspool of misinformation and hate. We need to draw the line somewhere.",
        "I'm all for free speech, but not when it puts lives at risk. Terrorist propaganda and fake news need to be controlled."
    ]

    # Create AI instances
    disputing_ai = GPT(TEST, group_id, moderator_condition, 2, group_member_agreement_levels, group_chat_statement_index=group_chat_statement_index)
    advocating_ai = GPT(TEST, group_id, moderator_condition, 1, group_member_agreement_levels, group_chat_statement_index=group_chat_statement_index)

    def run_conversation(ai_instance):
        ai_instance.previous_messages = []
        ai_instance.current_messages = []
        for turn in range(3):
            print(f"\n----- Turn {turn + 1} -----")
            simulate_human_message(ai_instance, "Red Alice", red_alice_messages[turn])
            simulate_human_message(ai_instance, "Blue Bob", blue_bob_messages[turn])
            print("\n--- Messages Formatted for GPT Prompt ---")
            formatted_messages = ai_instance.format_messages_for_gpt()
            for message in formatted_messages:
                print(f"   Role: {message['role']}, Content: {message['content']}")
            simulate_ai_response(ai_instance)
        return [f"{msg['sender_name']}: {msg['content']}" if msg['is_human'] 
                else f"AI: {msg['content']}" 
                for msg in ai_instance.previous_messages]

    # Run both conversations
    disputing_history = run_conversation(disputing_ai)
    advocating_history = run_conversation(advocating_ai)

    # Get prompts
    disputing_prompt = disputing_ai.get_system_message()
    advocating_prompt = advocating_ai.get_system_message()

    # Generate final output
    print("\nI am using two different prompts for AI to generate response to human message.")
    print(f'Disputing AI prompt is "{disputing_prompt}"')
    print(f'Advocating AI prompt is "{advocating_prompt}"')
    print('\nThis is conversation A:')
    print('\n'.join(disputing_history))
    print('\nThis is conversation B:')
    print('\n'.join(advocating_history))
    print('\nYou think which conversation belongs to which prompt?')
    print('Conversation A is the "Final Previous Message History" generated by Disputing AI')
    print('Conversation B is the "Final Previous Message History" generated by Advocating AI')