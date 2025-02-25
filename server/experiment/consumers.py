import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Subject, Group, MessageRecord
from random import sample
import random
from datetime import datetime

TEST_MODE = True 

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Add 'chat_' prefix to match the group_send in views.py
        self.chat_group_name = f"chat_{self.room_name}"

        print("Successfully connect chat consumer")
        # Join the chat group
        async_to_sync(self.channel_layer.group_add)(
            self.chat_group_name,
            self.channel_name
        )
        print("Successfully add to group")
        
        self.accept()

    def disconnect(self, close_code):
        print(close_code)
        group = Group.objects.get(pk = self.room_name)

        if close_code == 4000:
            group.is_activated = False
            group.save()

        subject_id = int(self.channel_map[self.channel_name])
        
        if group.has_capacity == True: # leave when pairing
            group.activate_member_ids['subject_ids'].remove(subject_id)
            group.member_ids['subject_ids'].remove(subject_id)
            group.current_size = group.current_size - 1
            response = {
                "code": 931,
                "leaving_subject": self.channel_map[self.channel_name]
            }
        else: #leave when formal task
            group.activate_member_ids['subject_ids'].remove(self.channel_map[self.channel_name])
            response = {
                "code": 901,
                "leaving_subject": self.channel_map[self.channel_name]
            }
        
        group.save()
        
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                'type': 'chat_message',
                'message': response
            }
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        code = text_data_json['code']
        # Print received data for debugging
        print("Received WebSocket data:", text_data_json)
        response = self.chat_code_to_message(text_data_json['code'], text_data_json['data'])
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message': response
            }
        )

    def chat_message(self, event):
        # Receives broadcast message and sends to WebSocket
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))

    def chat_code_to_message(self, code, data):
        if code == 100:  # Enter room
            subject_id = data['subject_id']
            
            # Get all members in the group
            group = Group.objects.get(pk=self.room_name)
            
            # Add member to active members if not already there
            if subject_id not in group.activate_member_ids['subject_ids']:
                group.activate_member_ids['subject_ids'].append(subject_id)
                group.save()
            
            # Get user list for response
            user_list = []
            for member_id in group.member_ids['subject_ids']:
                subject = Subject.objects.get(pk=member_id)
                user_list.append({
                    'subject_id': subject.id,
                    'avatar_name': subject.avatar_name,
                    'avatar_color': subject.avatar_color,
                    "is_activated": 1 if member_id in group.activate_member_ids['subject_ids'] else 0
                })
            
            response = {
                "code": 101,
                "user_list": user_list,
                "startable": True,
                "task_list": []
            }
            return response
        elif code == 200: #Send message from human
            subject_id = data['subject_id']
            group_id = data['group_id']
            msg = data['msg']

            # Create record and broadcast
            message_record = MessageRecord.objects.create(
                subject_id=subject_id, 
                group_id=group_id, 
                message=msg
            )

            response = {
                "code": 201,
                "message": {
                    "id": message_record._id,
                    "sender": {"subject_id": subject_id},
                    "content": msg,
                    "timestamp": str(message_record.time_stamp)
                }
            }
        elif code == 202:  # Typing events
            event_type = data.get('event')
            if event_type == 'user_typing':
                response = {
                    "code": 203,  # Code for typing notification
                    "typing_info": {
                        "subject_id": data['subject_id'],
                        "avatar_name": data['avatar_name'],
                        "avatar_color": data['avatar_color'],
                        "is_typing": True
                    }
                }
            elif event_type == 'user_stopped_typing':
                response = {
                    "code": 203,  # Same code, different status
                    "typing_info": {
                        "subject_id": data['subject_id'],
                        "is_typing": False
                    }
                }
        elif code == 777: # GPT response
            subject_id = -1
            group_id = data['group_id']
            instance_id = data['instance_id']
            task_no = data['task_no']
            msg = data['msg']

            message_record = MessageRecord.objects.create(subject_id=subject_id, group_id=group_id, instance_id=instance_id, task_no=task_no, message=msg)

            response = {
                "code": 778,
                "message": {
                    "id": message_record._id,
                    "sender": {
                        "subject_id": subject_id
                    },
                    "content": msg,
                    "timestamp": str(message_record.time_stamp)
                }
            }
        elif code == 201: #Send message from AI
            # Handle AI messages (already saved to DB in views.py)
            subject_id = data['message']['sender']['subject_id']
            msg = data['message']['content']
            
            # Just broadcast, record was already created in views.py
            response = {
                "code": 201,
                "message": {
                    "sender": {
                        "subject_id": subject_id  # AI's ID for proper icon display
                    },
                    "content": msg,
                    "timestamp": data['message'].get('timestamp', str(datetime.now()))
                }
            }
        elif code == 902:  # Ready to end discussion
            subject_id = data['subject_id']
            group_id = data['group_id']
            
            try:
                group = Group.objects.get(pk=group_id)
                
                # Mark the subject as ready
                if 'ready_members' not in group.member_ids:
                    group.member_ids['ready_members'] = []
                
                if subject_id not in group.member_ids['ready_members']:
                    group.member_ids['ready_members'].append(subject_id)
                    group.save()
                
                # Check if all human members are ready
                human_members = [id for id in group.member_ids['subject_ids'] if id > 0]
                all_ready = all(id in group.member_ids['ready_members'] for id in human_members)
                
                response = {
                    "code": 903,  # Ready status update code
                    "ready_members": group.member_ids['ready_members'],
                    "all_ready": all_ready
                }
                
                return response
                
            except Group.DoesNotExist:
                return None

        return response



