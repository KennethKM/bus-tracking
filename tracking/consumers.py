# tracking/consumers.py (create new file for WebSockets)
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Bus

class BusTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bus_group_name = 'bus_updates'
        
        # Join room group
        await self.channel_layer.group_add(
            self.bus_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial bus data
        await self.send_initial_buses()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.bus_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'request_update':
            await self.send_initial_buses()
    
    async def bus_update(self, event):
        """Send bus update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'bus_update',
            'bus_id': event['bus_id'],
            'bus_number': event['bus_number'],
            'lat': event['lat'],
            'lng': event['lng'],
            'speed': event['speed'],
            'available_seats': event['available_seats'],
            'occupancy': event['occupancy']
        }))
    
    @database_sync_to_async
    def get_all_buses(self):
        from .serializers import BusSerializer
        buses = Bus.objects.filter(is_active=True).select_related('route')
        return BusSerializer(buses, many=True).data
    
    async def send_initial_buses(self):
        buses = await self.get_all_buses()
        await self.send(text_data=json.dumps({
            'type': 'initial_buses',
            'buses': buses
        }))