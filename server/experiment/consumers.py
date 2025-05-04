import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Subject, Group, MessageRecord
from random import sample
import random
from datetime import datetime
from .views import record_message
from channels.db import database_sync_to_async

TEST_MODE = True

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Add 'chat_' prefix to match the group_send in views.py
        self.chat_group_name = f"chat_{self.room_name}"
        # in consumers.py, inside connect()
        print(">>> CHANNEL LAYER CLASS:", self.channel_layer.__class__.__name__)


        # Initialize channel_map as a class variable if it doesn't exist
        if not hasattr(ChatConsumer, 'channel_map'):
            ChatConsumer.channel_map = {}

        print("Successfully connect chat consumer")
        # Join the chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        print("Successfully add to group")


    async def disconnect(self, close_code):
        print(close_code)
        group = await database_sync_to_async(Group.objects.get)(pk = self.room_name)

        if close_code == 4000:
            group.is_activated = False
            await database_sync_to_async(group.save)()

        # Check if channel_map exists and contains this channel
        if hasattr(ChatConsumer, 'channel_map') and self.channel_name in ChatConsumer.channel_map:
            subject_id = int(ChatConsumer.channel_map[self.channel_name])

            if group.has_capacity == True: # leave when pairing
                group.activate_member_ids['subject_ids'].remove(subject_id)
                group.member_ids['subject_ids'].remove(subject_id)
                group.current_size = group.current_size - 1
                response = {
                    "code": 931,
                    "leaving_subject": ChatConsumer.channel_map[self.channel_name]
                }
            else: #leave when formal task
                group.activate_member_ids['subject_ids'].remove(ChatConsumer.channel_map[self.channel_name])
                response = {
                    "code": 901,
                    "leaving_subject": ChatConsumer.channel_map[self.channel_name]
                }

            await database_sync_to_async(group.save)()

            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat_message',
                    'message': response
                }
            )
        else:
            print(f"Channel {self.channel_name} not found in channel_map or channel_map not initialized")

    async def receive(self, text_data):
        print(f"Raw WebSocket message received: {text_data}")
        try:
            text_data_json = json.loads(text_data)
            if 'code' not in text_data_json or 'data' not in text_data_json:
                raise ValueError("WebSocket message must contain 'code' and 'data' fields")

            # Print received data for debugging
            print("Received WebSocket data:", text_data_json)
            response = await self.chat_code_to_message(text_data_json['code'], text_data_json['data'])
            print(f"Response: {response}")
            # If response has error, send directly and abort broadcasting
            if isinstance(response, dict) and response.get('error'):
                await self.send(text_data=json.dumps(response))
                return
            # Send message to room group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': response
                }
            )
        except json.JSONDecodeError as e:
            print(f"Error decoding WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Invalid message format. Must be valid JSON.'
            }))
        except ValueError as e:
            print(f"Invalid WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
        except Exception as e:
            print(f"Unexpected error processing WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'error': 'An unexpected error occurred.'
            }))

    async def chat_message(self, event):
        # Receives broadcast message and sends to WebSocket
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def chat_code_to_message(self, code, data):
        if code == 100:  # Enter room
            subject_id = data['subject_id']

            # Store the subject_id in the channel_map
            ChatConsumer.channel_map[self.channel_name] = subject_id

            # Get all members in the group
            try:
                group = await database_sync_to_async(Group.objects.get)(pk=self.room_name)
            except Group.DoesNotExist:
                print(f"Group not found: {self.room_name}")
                return {"code": 404, "error": f"Group {self.room_name} not found"}

            # Add member to active members if not already there
            if subject_id not in group.activate_member_ids['subject_ids']:
                group.activate_member_ids['subject_ids'].append(subject_id)
                await database_sync_to_async(group.save)()
            # check if group has capacity
            await database_sync_to_async(group.refresh_from_db)()
            print(f"Group {self.room_name} has {len(group.activate_member_ids['subject_ids'])} members")
            print(f"Group size: {group.size}")
            if len(group.activate_member_ids['subject_ids']) < group.size:
                return {
                    "code": 101,
                    "startable": False
                }
            else: # if group does not have capacity

                response = {
                    "code": 101,
                    "startable": True,
                    "third_person_id": group.third_person_id,
                    "has_capacity": group.has_capacity,
                    "group_id": group._id,
                    "group_capacity": group.size,
                    "moderator_condition": group.group_moderator_condition,
                    "participant_condition": group.group_participant_condition,
                    "chat_statement_indx": group.group_chat_statement_index,
                    "assigned_avatars": group.assigned_avatars,
                    "random_third_person_prompt": group.random_third_person_prompt
                }

            return response

        elif code == 200: #Send message from human
            subject_id = data['subject_id']
            group_id = data['group_id']
            msg = data['msg']
            try:
                group = await database_sync_to_async(Group.objects.get)(pk=group_id)
            except Group.DoesNotExist:
                print(f"Group not found: {group_id}")
                return {"code": 404, "error": f"Group {group_id} not found"}
            # Create record and broadcast
            # Only record human messages for turn tracking
            body = {
                    'subject_id': subject_id,
                    'group_id': group_id,
                    'message': msg
                }
            await database_sync_to_async(group.refresh_from_db)()
            # Print sender avatar information
            subject = await database_sync_to_async(Subject.objects.get)(pk=subject_id)
            await database_sync_to_async(subject.refresh_from_db)()
            print(f"subject_id: {subject_id}")
            print(f"subject: {subject}")
            print(f"group_id: {group_id}")
            print(f"Message from: {subject.avatar_name} (Color: {subject.avatar_color})")
            print(f"group.current_turn: {group.current_turn}")

            response = {
                "code": 201,
                "message": {
                    "sender": {
                        "subject_id": subject_id,
                        "avatar_name": subject.avatar_name,
                        "avatar_color": subject.avatar_color
                    },
                    "content": msg
                }
            }
            import threading
            try:
                threading.Thread(target=record_message, args=(body,)).start()
            except Exception as error:
                print(f'Error recording message: {error}')
            return response
        elif code == 202:  # Typing events
            event_type = data.get('event')
            subject_id = data.get('subject_id')

            # Log typing event for debugging
            print(f"Received typing event: {event_type} from subject {subject_id}")

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
            else:
                response = {
                    "code": 400,
                    "error": "Unknown typing event"
                }

            # Log the response for debugging
            print(f"Sending typing response: {response}")
            return response
        elif code == 777: # GPT response
            subject_id = -1
            group_id = data['group_id']
            instance_id = data['instance_id']
            task_no = data['task_no']
            msg = data['msg']

            message_record = await database_sync_to_async(MessageRecord.objects.create)(subject_id=subject_id, group_id=group_id, instance_id=instance_id, task_no=task_no, message=msg)

            response = {
                "code": 778,
                "message": {
                    "id": message_record._id,
                    "sender": {
                        "subject_id": subject_id,
                        "avatar_name": "AI",
                        "avatar_color": "#4b5563"
                    },
                    "content": msg,
                    "timestamp": str(message_record.time_stamp)
                }
            }
            return response
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
            return response
        elif code == 902:  # Ready to end discussion
            subject_id = data['subject_id']
            group_id = data['group_id']

            try:
                group = await database_sync_to_async(Group.objects.get)(pk=group_id)

                # Mark the subject as ready
                if 'ready_members' not in group.member_ids:
                    group.member_ids['ready_members'] = []

                if subject_id not in group.member_ids['ready_members']:
                    group.member_ids['ready_members'].append(subject_id)
                    await database_sync_to_async(group.save)()

                # Fetch subject for avatar info
                subject_obj = await database_sync_to_async(Subject.objects.get)(pk=subject_id)

                # Check if all human members are ready
                human_members = [id for id in group.member_ids['subject_ids'] if id > 0]
                all_ready = all(id in group.member_ids['ready_members'] for id in human_members)

                # Compose ready status response with avatar info
                response = {
                    "code": 903,  # Ready status update code
                    "ready_members": group.member_ids['ready_members'],
                    "all_ready": all_ready,
                    "message": {
                        "sender": {
                            "subject_id": subject_id,
                            "avatar_name": subject_obj.avatar_name,
                            "avatar_color": subject_obj.avatar_color
                        }
                    }
                }

                return response

            except Group.DoesNotExist:
                return None
        else:
            # Default response for unhandled codes
            return {
                "code": 400,
                "error": f"Unhandled message code: {code}"
            }
