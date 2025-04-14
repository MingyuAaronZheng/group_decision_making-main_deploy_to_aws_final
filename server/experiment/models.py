from django.db import models
from django.db.models import JSONField

class Subject(models.Model):
	_id = models.AutoField(auto_created = True, primary_key=True)
	worker_id = models.CharField(max_length=60)
	# assignment_id = models.CharField(max_length=60)
	study_id = models.CharField(max_length=60)
	session_id = models.CharField(max_length=60)
	group_id = models.IntegerField(default = -1)
	is_third_person = models.BooleanField(default=False)
	active = models.BooleanField(default=True)  # Track if user is currently active
	confirmed_instructions = models.BooleanField(default=False)  # Track if third person has confirmed instructions
	random_third_person_prompt = models.IntegerField(default=-1)  # Track if third person has confirmed instructions
	
	# Time stamps
	start_time = models.DateTimeField(default = None, blank=True, null = True)
	end_time = models.DateTimeField(default = None, blank=True, null = True)
	pair_start_time = models.DateTimeField(default = None, blank=True, null = True)
	pair_end_time = models.DateTimeField(default = None, blank=True, null = True)
	last_active_time = models.DateTimeField(default = None, blank=True, null = True)
	'''
	== moderator_condition Setting == 
	0: No AI Moderator
	1: AI Moderator
	'''
	moderator_condition = models.IntegerField(default=-1)
	'''
	== participant_condition Setting ==
	0: 2 Human Participants
	1: 2 Human Participants + ADVOCATING AI Participant
	2: 2 Human Participants + DISPUTING AI Participant
	3: 2+1 Human Participants
	'''
	participant_condition = models.IntegerField(default=-1)
	bonus = models.FloatField(default=0)
	# is_qualified = models.BooleanField(default=False)
	is_complete = models.BooleanField(default=False)
	is_paid = models.BooleanField(default=False)
	is_interest = models.BooleanField(default=False)
	avatar_name = models.CharField(max_length=60, default = None, null = True)
	avatar_color = models.CharField(max_length=60, default = None, null = True)
	# individual_responses = JSONField(default=list)

	def __str__(self):
		return str(self._id)

class Group(models.Model):
	def memeber_default():
		return {"subject_ids": []}
		# {"subject_ids": []}

	_id = models.AutoField(auto_created = True, primary_key=True)
	size = models.IntegerField(default = -1)
	current_size = models.IntegerField(default = 0)
	is_activated = models.BooleanField(default = True)
	has_capacity = models.BooleanField(default = True)
	third_person_id = models.IntegerField(default = -1)  # Track who is the third person
	group_participant_condition = models.IntegerField(default = -1)
	group_moderator_condition = models.IntegerField(default = -1)
	group_chat_statement_index = models.IntegerField(default = -1)
	member_ids = JSONField(default = memeber_default)
	activate_member_ids = JSONField(default = memeber_default)
	chatting = models.BooleanField(default=False)  # New field to track active chat status
	current_turn = models.IntegerField(default=0)  # Track current turn number
	turn_messages = JSONField(default=dict)  # Track who has sent messages in current turn
	# Format: {turn_number: [subject_ids_who_sent_messages]}
	chat_started = models.BooleanField(default=False)  # Track if welcome message has been sent
	group_member_agreement_levels = JSONField(default=dict)  # Track member agreement levels
	# Format: {subject_id: agreement_level}

	def __str__(self):
		return str(self._id)


class MessageRecord(models.Model):
	_id = models.AutoField(auto_created = True, primary_key = True)
	subject_id = models.IntegerField(default = None, null = True)
	group_id = models.IntegerField(default = None, null = True)
	message = models.CharField(max_length= 2048, null = True)
	time_stamp = models.DateTimeField(auto_now_add=True, blank=True)

	def __str__(self):
		return str(self._id)


class DemograSurvey(models.Model):
    _id = models.AutoField(auto_created=True, primary_key=True)
    subject_id = models.IntegerField(default=None)  # ID for the subject
    age_range = models.CharField(max_length=1)  # Single-digit option (1-7)
    gender_selection = models.CharField(max_length=1)  # Single-digit option (1-7)
    income_range = models.CharField(max_length=1)  # Single-digit option (1-7)
    education_level = models.CharField(max_length=1)  # Single-digit option (1-7)
    ethnicity_selection = models.CharField(max_length=1)  # Single-digit option (1-7)
    religion_affiliation = models.CharField(max_length=1)  # Single-digit option (1-9)
    political_affiliation = models.CharField(max_length=1)  # Single-digit option (1-8)
    immigration_status = models.CharField(max_length=1)  # Single-digit option (1-6)
    social_media_reading_frequency = models.CharField(max_length=1)  # Single-digit option (1-7)
    social_media_posting_frequency = models.CharField(max_length=1)  # Single-digit option (1-7)
    ai_tool_usage_frequency = models.CharField(max_length=1)  # Single-digit option (1-7)
    ai_attitude_selection = models.CharField(max_length=1)  # Single-digit option (1-7)
    ai_in_music = models.CharField(max_length=1)  # single-digit option (1-7)
    ai_in_email = models.CharField(max_length=1)  # single-digit option (1-7)
    ai_in_home_devices = models.CharField(max_length=1)  # single-digit option (1-7)
    ai_mental_capacity_responses = models.TextField()  # JSON data for AI mental capacity responses
    social_media_reading_platforms = models.JSONField(default=list)
    social_media_posting_platforms = models.JSONField(default=list)
    def __str__(self):
        return f"Survey ID: {self._id}, Subject ID: {self.subject_id}"

class PreDSurvey(models.Model):
	_id = models.AutoField(auto_created=True, primary_key=True)
	subject_id = models.IntegerField(default = None)
	responses = JSONField(default=list)

	def __str__(self):
		return str(self._id)

class PostSurvey(models.Model):
	_id = models.AutoField(auto_created=True, primary_key=True)
	subject_id = models.IntegerField(default = None)
	mental_demand = models.CharField(max_length=1)
	physical_demand = models.CharField(max_length=1)
	temporal_demand = models.CharField(max_length=1)
	performance = models.CharField(max_length=1)
	effort = models.CharField(max_length=1)
	frustration = models.CharField(max_length=1)
	timeline = models.CharField(max_length=1)
	precision = models.CharField(max_length=1)
	usefulness = models.CharField(max_length=1)
	da_collaboration = models.CharField(max_length=1)
	da_satisfaction = models.CharField(max_length=1)
	da_quality = models.CharField(max_length=1)
	da_recommend = models.CharField(max_length=1)
	da_future = models.CharField(max_length=1)

	def __str__(self):
		return str(self._id)

class PostDOSurvey(models.Model):
    _id = models.AutoField(auto_created=True, primary_key=True)
    subject_id = models.IntegerField(default=None)
    
    # Policy Attitudes and Personal Importance
    policy_responses = JSONField(default=list)
    # Format: [
    #   {
    #     "statement_id": 1,
    #     "agreement": -3 to 3,
    #     "importance": 1 to 7
    #   },
    #   ...
    # ]
    
    # Conversation Quality
    conversation_quality = models.IntegerField(null=True)  # 1-7
    conversation_responses = JSONField(default=list)  # Array of 1-7 responses
    
    # Democratic Reciprocity
    reciprocity_responses = JSONField(default=list)  # Array of 1-7 responses
    
    # Reflection
    reflection = models.TextField(null=True, blank=True)
    
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PostDOSurvey {self._id} - Subject {self.subject_id}"

class PostDFSurvey(models.Model):
    _id = models.AutoField(auto_created=True, primary_key=True)
    subject_id = models.IntegerField(default=None)
    
    # Reflection
    reflection = models.TextField()
    
    # Attention Checks
    attention_check_1 = models.CharField(max_length=10)  # Answer to 35 + 47
    attention_check_2 = models.IntegerField()  # Should be 7 (Strongly Agree)
    
    # Critical Thinking
    critical_thinking_responses = JSONField(default=list)  # Array of 1-7 responses
    
    # AI Tool Usage
    used_ai_tool = models.BooleanField()
    
    # AI Interaction Quality
    ai_participant_responses = JSONField(default=list, null=True)  # Array of 1-7 responses
    ai_moderator_responses = JSONField(default=list, null=True)  # Array of 1-7 responses
    
    # Cost of Communication
    cost_responses = JSONField(default=list)  # Array of 1-7 responses
    
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PostDFSurvey {self._id} - Subject {self.subject_id}"
