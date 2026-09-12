import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Bus

class BusTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bus_group_name = 'bus_updates'
        
        await self.channel_layer.group_add(
            self.bus_group_name,
            self.channel_name
        )
        
        await self.accept()
        print("✅ WebSocket connected!")
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to bus tracking!'
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.bus_group_name,
            self.channel_name
        )
        print("❌ WebSocket disconnected")
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            print(f"📨 Received: {text_data_json}")
            
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'received': text_data_json
            }))
        except Exception as e:
            print(f"Error: {e}")
    
    async def bus_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'bus_update',
            'bus_id': event.get('bus_id'),
            'bus_number': event.get('bus_number'),
            'lat': event.get('lat'),
            'lng': event.get('lng'),
            'speed': event.get('speed'),
            'available_seats': event.get('available_seats'),
            'occupancy': event.get('occupancy'),
            'route_progress': event.get('route_progress'),
            'direction': event.get('direction')
        }))